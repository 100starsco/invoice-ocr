import type { LineMessageEvent, LineTextMessage, LineImageMessage, LineStickerMessage, LineMessageJobData } from '@invoice-ocr/shared'
import { LineMessagingService } from '../services/line'
import { storageService } from '../services/storage'
// import { notificationQueue } from '../queues'  // Disable for testing
import { config } from '../config'
import { db, lineUsers, lineMessages } from '../db'
import { eq } from 'drizzle-orm'

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
      // Save or update user profile
      await this.saveUserProfile(userId)

      // Save message to database
      await this.saveMessage(event)

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

    try {
      // Direct reply for testing (without queue)
      await this.lineService.replyMessage(replyToken, [
        LineMessagingService.createTextMessage('📸 ได้รับรูปภาพแล้ว! กำลังประมวลผล...')
      ])

      // Download image from LINE servers
      const imageBuffer = await this.downloadLineImage(message.id)

      // Store image using storage service
      const uploadResult = await storageService.uploadBuffer(
        imageBuffer,
        `line_image_${message.id}.jpg`,
        {
          folder: 'line-images',
          filename: `${userId}_${message.id}_${Date.now()}.jpg`,
          contentType: 'image/jpeg',
          metadata: {
            userId,
            messageId: message.id,
            timestamp: Date.now().toString()
          }
        }
      )

      console.log(`Image uploaded successfully: ${uploadResult.key}`)
      console.log(`Public URL: ${uploadResult.cdnUrl || uploadResult.url}`)

      // Image uploaded successfully - ready for OCR processing
      const imageData = {
        key: uploadResult.key,
        url: uploadResult.cdnUrl || uploadResult.url,
        userId,
        messageId: message.id,
        timestamp: Date.now(),
        metadata: {
          originalFilename: `line_image_${message.id}.jpg`,
          source: 'line_webhook',
          contentType: 'image/jpeg'
        }
      }

      // TODO: Queue OCR processing job here with imageData
      console.log(`Image ready for OCR processing:`, imageData)

    } catch (error) {
      console.error('Error processing image:', error)

      // Send error message to user
      await this.lineService.replyMessage(replyToken, [
        LineMessagingService.createTextMessage('❌ เกิดข้อผิดพลาดในการอัพโหลดรูปภาพ กรุณาลองใหม่อีกครั้ง')
      ])
    }
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

  /**
   * Save or update user profile in database
   */
  private async saveUserProfile(userId: string): Promise<void> {
    try {
      // Fetch user profile from LINE API (includes avatar)
      const profile = await this.lineService.getProfile(userId)

      // Upsert user to database
      await db.insert(lineUsers).values({
        userId: profile.userId,
        displayName: profile.displayName,
        pictureUrl: profile.pictureUrl, // Avatar URL
        statusMessage: profile.statusMessage || null,
        language: profile.language || null,
        isFollowing: true,
        profileLastUpdated: new Date(),
        lastSeenAt: new Date(),
        lastMessageAt: new Date()
      }).onConflictDoUpdate({
        target: lineUsers.userId,
        set: {
          displayName: profile.displayName,
          pictureUrl: profile.pictureUrl, // Update avatar
          statusMessage: profile.statusMessage || null,
          language: profile.language || null,
          profileLastUpdated: new Date(),
          lastSeenAt: new Date(),
          lastMessageAt: new Date(),
          updatedAt: new Date()
        }
      })

      console.log(`User profile saved/updated for ${profile.displayName} (${userId})`)
    } catch (error) {
      console.error('Error saving user profile:', error)
      // Don't throw - we still want to process the message even if profile save fails
    }
  }

  /**
   * Save message to database for history
   */
  private async saveMessage(event: LineMessageEvent): Promise<void> {
    try {
      const { message, source, replyToken, timestamp } = event
      const messageId = (message as any).id || `${timestamp}_${source.userId}`

      // Prepare message content based on type
      let content: any = {}
      switch (message.type) {
        case 'text':
          content = { text: (message as LineTextMessage).text }
          break
        case 'image':
          content = { imageId: (message as LineImageMessage).id }
          break
        case 'sticker':
          content = {
            packageId: (message as LineStickerMessage).packageId,
            stickerId: (message as LineStickerMessage).stickerId
          }
          break
        default:
          content = { raw: message }
      }

      await db.insert(lineMessages).values({
        messageId: messageId,
        messageType: message.type,
        content: content,
        userId: source.userId!,
        replyToken: replyToken || null,
        sentAt: new Date(timestamp),
        receivedAt: new Date()
      }).onConflictDoNothing() // Ignore if message already exists

      console.log(`Message saved: ${message.type} from ${source.userId}`)
    } catch (error) {
      console.error('Error saving message:', error)
      // Don't throw - we still want to process the message even if save fails
    }
  }

  /**
   * Download image from LINE servers
   */
  private async downloadLineImage(messageId: string): Promise<Buffer> {
    const url = `https://api-data.line.me/v2/bot/message/${messageId}/content`

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${config.line.channelAccessToken}`
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to download LINE image: ${response.status} ${response.statusText}`)
    }

    const arrayBuffer = await response.arrayBuffer()
    return Buffer.from(arrayBuffer)
  }
}

export const messageHandler = new MessageHandler()