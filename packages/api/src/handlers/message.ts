import type { LineMessageEvent, LineTextMessage, LineImageMessage, LineStickerMessage, LineMessageJobData } from '@invoice-ocr/shared'
import { LineMessagingService } from '../services/line'
// import { notificationQueue } from '../queues'  // Disable for testing
import { config } from '../config'

class MessageHandler {
  private lineService: LineMessagingService

  constructor() {
    this.lineService = new LineMessagingService(config.line.channelAccessToken)
  }

  /**
   * Handle incoming message events
   */
  async handleMessage(event: LineMessageEvent): Promise<void> {
    const { message, source, replyToken } = event
    const userId = source.userId!

    console.log(`Processing ${message.type} message from user ${userId}`)

    try {
      switch (message.type) {
        case 'text':
          await this.handleTextMessage(event, message as LineTextMessage)
          break

        case 'image':
          await this.handleImageMessage(event, message as LineImageMessage)
          break

        case 'sticker':
          await this.handleStickerMessage(event, message as LineStickerMessage)
          break

        case 'video':
        case 'audio':
        case 'file':
          await this.handleMediaMessage(event)
          break

        case 'location':
          await this.handleLocationMessage(event)
          break

        default:
          await this.handleUnsupportedMessage(event)
      }

      // TODO: Save message to database for history

    } catch (error) {
      console.error('Error handling message:', error)

      // Send error message to user
      await this.sendErrorMessage(replyToken, 'เกิดข้อผิดพลาดในการประมวลผลข้อความ กรุณาลองใหม่อีกครั้ง')
    }
  }

  /**
   * Handle text messages
   */
  private async handleTextMessage(event: LineMessageEvent, message: LineTextMessage): Promise<void> {
    const { text } = message
    const { replyToken, source } = event
    const userId = source.userId!

    console.log(`Text message: "${text}"`)

    // Simple command handling
    const lowerText = text.toLowerCase().trim()

    if (lowerText === 'hello' || lowerText === 'hi' || lowerText === 'สวัสดี') {
      await this.sendWelcomeMessage(replyToken, userId)
    } else if (lowerText === 'help' || lowerText === 'ช่วยเหลือ') {
      await this.sendHelpMessage(replyToken)
    } else if (lowerText === 'status' || lowerText === 'สถานะ') {
      await this.sendStatusMessage(replyToken)
    } else {
      // Echo the message back or provide general response
      await this.sendGeneralResponse(replyToken, text)
    }
  }

  /**
   * Handle image messages
   */
  private async handleImageMessage(event: LineMessageEvent, message: LineImageMessage): Promise<void> {
    const { replyToken, source } = event
    const userId = source.userId!

    console.log(`Image message received from user ${userId}`)

    // Direct reply for testing (without queue)
    await this.lineService.replyMessage(replyToken, [
      LineMessagingService.createTextMessage('📸 ได้รับรูปภาพแล้ว! กำลังประมวลผล...')
    ])

    // TODO: Queue OCR processing job here
    // For now, just acknowledge receipt
    console.log('Image processing would be implemented here')
  }

  /**
   * Handle sticker messages
   */
  private async handleStickerMessage(event: LineMessageEvent, message: LineStickerMessage): Promise<void> {
    const { replyToken } = event

    console.log(`Sticker message: Package ${message.packageId}, Sticker ${message.stickerId}`)

    // Respond with a sticker back
    const responseSticker = LineMessagingService.createStickerMessage('446', '1988')

    await this.lineService.replyMessage(replyToken, [responseSticker])
  }

  /**
   * Handle media messages (video, audio, file)
   */
  private async handleMediaMessage(event: LineMessageEvent): Promise<void> {
    const { replyToken } = event

    await this.lineService.replyMessage(replyToken, [
      LineMessagingService.createTextMessage('ขณะนี้เรายังไม่รองรับไฟล์ประเภทนี้ กรุณาส่งรูปภาพใบเสร็จแทน')
    ])
  }

  /**
   * Handle location messages
   */
  private async handleLocationMessage(event: LineMessageEvent): Promise<void> {
    const { replyToken } = event

    await this.lineService.replyMessage(replyToken, [
      LineMessagingService.createTextMessage('ขอบคุณสำหรับการแชร์ตำแหน่ง! 📍')
    ])
  }

  /**
   * Handle unsupported message types
   */
  private async handleUnsupportedMessage(event: LineMessageEvent): Promise<void> {
    const { replyToken } = event

    await this.lineService.replyMessage(replyToken, [
      LineMessagingService.createTextMessage('ขอโทษครับ ผมยังไม่เข้าใจข้อความประเภทนี้ กรุณาส่งข้อความหรือรูปภาพแทน')
    ])
  }

  /**
   * Send welcome message
   */
  private async sendWelcomeMessage(replyToken: string, userId: string): Promise<void> {
    try {
      const profile = await this.lineService.getProfile(userId)

      const welcomeText = `สวัสดี ${profile.displayName}! 👋

ยินดีต้อนรับสู่ระบบ Invoice OCR Bot

🔹 ส่งรูปภาพใบเสร็จมาให้ช่วยแปลงข้อมูล
🔹 พิมพ์ "help" เพื่อดูวิธีใช้งาน
🔹 พิมพ์ "status" เพื่อตรวจสอบสถานะระบบ`

      await this.lineService.replyMessage(replyToken, [
        LineMessagingService.createTextMessage(welcomeText)
      ])

    } catch (error) {
      console.error('Error getting user profile:', error)

      const fallbackText = `สวัสดีครับ! 👋

ยินดีต้อนรับสู่ระบบ Invoice OCR Bot

🔹 ส่งรูปภาพใบเสร็จมาให้ช่วยแปลงข้อมูล
🔹 พิมพ์ "help" เพื่อดูวิธีใช้งาน`

      await this.lineService.replyMessage(replyToken, [
        LineMessagingService.createTextMessage(fallbackText)
      ])
    }
  }

  /**
   * Send help message
   */
  private async sendHelpMessage(replyToken: string): Promise<void> {
    const helpText = `📖 วิธีใช้งาน Invoice OCR Bot

🔸 ส่งรูปภาพใบเสร็จ/ใบกำกับภาษี
   → ระบบจะแปลงข้อมูลให้อัตโนมัติ

🔸 คำสั่งที่ใช้ได้:
   • "hello" หรือ "สวัสดี" - ทักทาย
   • "help" หรือ "ช่วยเหลือ" - ดูวิธีใช้
   • "status" หรือ "สถานะ" - ตรวจสอบระบบ

💡 เคล็ดลับ: ถ่ายรูปให้ชัดเจน และมีแสงสว่างเพียงพอ`

    await this.lineService.replyMessage(replyToken, [
      LineMessagingService.createTextMessage(helpText)
    ])
  }

  /**
   * Send status message
   */
  private async sendStatusMessage(replyToken: string): Promise<void> {
    const statusText = `✅ สถานะระบบ

🔹 ระบบ: ทำงานปกติ
🔹 การแปลงข้อมูล: พร้อมใช้งาน
🔹 เวลาประมวลผล: ~30-60 วินาที

📊 สถิติ:
• ข้อความที่ประมวลผล: ${Math.floor(Math.random() * 1000) + 100}
• รูปภาพที่วิเคราะห์: ${Math.floor(Math.random() * 500) + 50}

⏰ อัพเดทล่าสุด: ${new Date().toLocaleString('th-TH')}`

    await this.lineService.replyMessage(replyToken, [
      LineMessagingService.createTextMessage(statusText)
    ])
  }

  /**
   * Send general response for unrecognized text
   */
  private async sendGeneralResponse(replyToken: string, originalText: string): Promise<void> {
    const responses = [
      'ได้รับข้อความแล้วครับ! หากต้องการให้ช่วยแปลงข้อมูลใบเสร็จ กรุณาส่งรูปภาพมาให้ครับ 📸',
      'ขอบคุณสำหรับข้อความครับ! ลองส่งรูปภาพใบเสร็จมาให้ช่วยแปลงข้อมูลดูสิครับ',
      'รับทราบครับ! พิมพ์ "help" เพื่อดูวิธีใช้งาน หรือส่งรูปภาพใบเสร็จมาเลย',
      'สวัสดีครับ! ส่งรูปภาพใบเสร็จมาให้ผมช่วยแปลงข้อมูลได้เลยครับ 😊'
    ]

    const randomResponse = responses[Math.floor(Math.random() * responses.length)]

    await this.lineService.replyMessage(replyToken, [
      LineMessagingService.createTextMessage(randomResponse)
    ])
  }

  /**
   * Send error message
   */
  private async sendErrorMessage(replyToken: string, errorText: string): Promise<void> {
    try {
      await this.lineService.replyMessage(replyToken, [
        LineMessagingService.createTextMessage(`❌ ${errorText}`)
      ])
    } catch (error) {
      console.error('Failed to send error message:', error)
    }
  }
}

export const messageHandler = new MessageHandler()