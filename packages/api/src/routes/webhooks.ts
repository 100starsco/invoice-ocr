/**
 * Webhook Handlers
 *
 * Handles incoming webhooks from external services.
 */

import { Hono } from 'hono'
import { LineMessagingService } from '../services/line'
import { config } from '../config'
import { verifyWebhookSignature } from '../utils/webhook-signatures'
import type { Context } from 'hono'

const app = new Hono()

// Initialize LINE service
const lineService = new LineMessagingService(config.line.channelAccessToken)

/**
 * OCR webhook payload interfaces
 */
interface OCRWebhookPayload {
  event: 'job.completed' | 'job.failed'
  job_id: string
  user_id: string
  message_id: string
  timestamp: string
  processing_time: number
  result?: {
    vendor: string
    amount: number
    date: string
    invoice_number?: string
    confidence_score: number
    invoice_summary: string
    line_items?: Array<{
      description: string
      amount: number
      confidence: number
    }>
  }
  error?: string
  stage?: string
}

/**
 * OCR Service Webhook Handler
 *
 * Receives notifications when OCR jobs complete or fail.
 */
app.post('/ocr', async (c: Context) => {
  try {
    const payload: OCRWebhookPayload = await c.req.json()

    // Verify webhook signature
    const signatureHeader = c.req.header('X-Webhook-Signature')
    const isSignatureValid = verifyWebhookSignature(payload, signatureHeader)

    if (!isSignatureValid) {
      console.warn('Webhook received with invalid signature (continuing in development mode)', {
        event: payload?.event || 'unknown',
        job_id: payload?.job_id,
        user_id: payload?.user_id,
        has_signature: !!signatureHeader,
        node_env: process.env.NODE_ENV
      })

      // In development, we allow unsigned webhooks for testing
      // In production, you should enable strict signature validation
      if (process.env.NODE_ENV === 'production') {
        return c.json({ status: 'error', message: 'Invalid webhook signature' }, 401)
      }
    } else {
      console.log('Webhook signature verified successfully')
    }

    console.log(`OCR webhook received: ${payload.event} for job ${payload.job_id} (user: ${payload.user_id})`)

    // Validate required fields
    if (!payload.job_id || !payload.user_id || !payload.event) {
      console.error('Invalid webhook payload - missing required fields')
      return c.json({ status: 'error', message: 'Missing required fields' }, 400)
    }

    switch (payload.event) {
      case 'job.completed':
        await handleJobCompleted(payload)
        break
      case 'job.failed':
        await handleJobFailed(payload)
        break
      default:
        console.warn(`Unknown webhook event: ${payload.event}`)
        return c.json({ status: 'error', message: 'Unknown event type' }, 400)
    }

    return c.json({ status: 'ok', processed_at: new Date().toISOString() })

  } catch (error) {
    console.error('Webhook processing error:', error)
    return c.json({
      status: 'error',
      message: 'Internal processing error',
      error: error.message
    }, 500)
  }
})

/**
 * Handle successful OCR job completion
 */
async function handleJobCompleted(payload: OCRWebhookPayload): Promise<void> {
  const { user_id, result, processing_time } = payload

  if (!result) {
    console.error('Job completed but no result provided')
    return
  }

  try {
    if (result.confidence_score >= 0.8) {
      // High confidence - send result directly
      const message = formatHighConfidenceMessage(result, processing_time)
      await lineService.pushMessage(user_id, [
        LineMessagingService.createTextMessage(message)
      ])

      console.log(`Sent high-confidence result to user ${user_id}`)

    } else {
      // Low confidence - send review link and preliminary results
      const reviewLink = await generateReviewLink(payload.job_id)
      const message = formatLowConfidenceMessage(result, reviewLink, processing_time)

      await lineService.pushMessage(user_id, [
        LineMessagingService.createTextMessage(message)
      ])

      console.log(`Sent low-confidence result with review link to user ${user_id}`)
    }

  } catch (error) {
    console.error(`Failed to send completion message to user ${user_id}:`, error)

    // Send fallback message
    try {
      await lineService.pushMessage(user_id, [
        LineMessagingService.createTextMessage('✅ ประมวลผลใบเสร็จเสร็จแล้ว แต่เกิดข้อผิดพลาดในการส่งผลลัพธ์ กรุณาติดต่อผู้ดูแลระบบ')
      ])
    } catch (fallbackError) {
      console.error(`Failed to send fallback message:`, fallbackError)
    }
  }
}

/**
 * Handle failed OCR job
 */
async function handleJobFailed(payload: OCRWebhookPayload): Promise<void> {
  const { user_id, error, stage } = payload

  try {
    let message = '❌ ขออภัย ไม่สามารถประมวลผลใบเสร็จได้\n\n'

    // Add specific error information based on stage
    switch (stage) {
      case 'downloading':
        message += '📱 ไม่สามารถดาวน์โหลดรูปภาพได้ กรุณาส่งรูปใหม่'
        break
      case 'document_classification':
        message += '📋 รูปภาพนี้ไม่ใช่ใบเสร็จหรือเอกสาร\n\n'
        message += '💡 กรุณาส่งรูปใบเสร็จ ใบกำกับภาษี หรือเอกสารที่มีข้อความ\n'
        message += '📷 เคล็ดลับการถ่ายรูป:\n'
        message += '• ถ่ายใบเสร็จให้เต็มเฟรม\n'
        message += '• ใช้แสงสว่างเพียงพอ\n'
        message += '• หลีกเลี่ยงเงาและแสงสะท้อน\n'
        message += '• ตรวจสอบให้ข้อความชัดเจน'
        break
      case 'preprocessing':
        message += '🔍 รูปภาพไม่ชัดเจนเพียงพอ กรุณาถ่ายใหม่ในที่แสงสว่าง'
        break
      case 'ocr_extraction':
        message += '📄 ไม่สามารถอ่านข้อความจากรูปได้ กรุณาตรวจสอบความชัดของรูปภาพ'
        break
      default:
        message += '⚠️ เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่อีกครั้ง'
    }

    message += '\n\n💡 เคล็ดลับ: ถ่ายรูปในแสงสว่าง ให้ใบเสร็จเต็มเฟรม และไม่มีเงาบังข้อความ'

    await lineService.pushMessage(user_id, [{
      type: 'text',
      text: message
    }])

    console.log(`Sent failure message to user ${user_id} (stage: ${stage})`)

  } catch (error) {
    console.error(`Failed to send failure message to user ${user_id}:`, error)
  }
}

/**
 * Format message for high confidence results
 */
function formatHighConfidenceMessage(result: any, processingTime: number): string {
  let message = '✅ ประมวลผลใบเสร็จสำเร็จแล้ว!\n\n'
  message += `🏪 ร้าน: ${result.vendor}\n`
  message += `💰 จำนวนเงิน: ${result.amount.toLocaleString()}฿\n`
  message += `📅 วันที่: ${formatThaiDate(result.date)}\n`

  if (result.invoice_number) {
    message += `📄 เลขใบเสร็จ: ${result.invoice_number}\n`
  }

  message += `🎯 ความเชื่อมั่น: ${Math.round(result.confidence_score * 100)}%\n`
  message += `⏱️ เวลาประมวลผล: ${processingTime.toFixed(1)} วินาที`

  // Add line items if available and not too long
  if (result.line_items && result.line_items.length > 0 && result.line_items.length <= 5) {
    message += '\n\n📋 รายละเอียด:'
    result.line_items.forEach((item: any) => {
      message += `\n• ${item.description}: ${item.amount.toLocaleString()}฿`
    })
  }

  return message
}

/**
 * Format message for low confidence results
 */
function formatLowConfidenceMessage(result: any, reviewLink: string, processingTime: number): string {
  let message = '⚠️ ประมวลผลเสร็จแล้ว แต่ต้องการตรวจสอบ\n\n'
  message += `📋 ผลลัพธ์เบื้องต้น:\n`
  message += `🏪 ร้าน: ${result.vendor}\n`
  message += `💰 จำนวน: ${result.amount.toLocaleString()}฿\n`
  message += `📅 วันที่: ${formatThaiDate(result.date)}\n`
  message += `🎯 ความเชื่อมั่น: ${Math.round(result.confidence_score * 100)}%\n\n`
  message += `🔍 กรุณาตรวจสอบและแก้ไขข้อมูล:\n${reviewLink}\n\n`
  message += `⏱️ เวลาประมวลผล: ${processingTime.toFixed(1)} วินาที`

  return message
}

/**
 * Generate review link for LIFF app
 */
async function generateReviewLink(jobId: string): Promise<string> {
  const liffId = config.liff?.id || process.env.VITE_LIFF_ID

  if (!liffId) {
    console.warn('LIFF ID not configured, returning fallback link')
    return `${process.env.API_BASE_URL}/review/${jobId}`
  }

  return `https://liff.line.me/${liffId}/review/${jobId}`
}

/**
 * Format date for Thai locale
 */
function formatThaiDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('th-TH', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch (error) {
    return dateString
  }
}

/**
 * Health check endpoint for webhooks
 */
app.get('/health', (c) => {
  return c.json({
    status: 'ok',
    service: 'webhooks',
    timestamp: new Date().toISOString()
  })
})

export default app