import { Worker } from 'bullmq'
import type { LineEvent, LineMessageEvent } from '@invoice-ocr/shared'
import { LineMessagingService } from '../services/line'
import { JobTrackingService } from '../services/job-tracker'
import { messageHandler } from '../handlers/message'
import { config } from '../config'
import Redis from 'ioredis'

// Create dedicated Redis connection for this worker
const redis = new Redis({
  host: config.queue.redis.host,
  port: config.queue.redis.port,
  password: config.queue.redis.password,
  db: config.queue.redis.db,
  maxRetriesPerRequest: null, // Required for BullMQ
  enableReadyCheck: true,
  lazyConnect: true
})

interface LineEventJobData {
  event: LineEvent
  timestamp: number
  webhookId: string
}

interface LineEventJobResult {
  success: boolean
  timestamp: number
  eventType: string
  userId?: string
  processingTimeMs: number
  error?: string
}

class LineEventWorker {
  private worker: Worker

  constructor() {
    this.worker = new Worker(
      'line-events',
      async (job) => {
        console.log(`Processing LINE event job: ${job.name}`)
        return this.processLineEvent(job.data)
      },
      {
        connection: redis,
        concurrency: 5,
        removeOnComplete: { count: 100 },
        removeOnFail: { count: 50 }
      }
    )

    this.worker.on('completed', (job, result) => {
      console.log(`LINE event job ${job.id} completed:`, result)
    })

    this.worker.on('failed', (job, err) => {
      console.error(`LINE event job ${job?.id} failed:`, err)
    })

    this.worker.on('error', (err) => {
      console.error('LINE event worker error:', err)
    })

    console.log('LINE Event Worker started')
  }

  private async processLineEvent(data: LineEventJobData): Promise<LineEventJobResult> {
    const { event, timestamp, webhookId } = data
    const startTime = Date.now()

    console.log(`Processing LINE event: ${event.type} from webhook: ${webhookId}`)

    try {
      // Mark job as started in database
      // Note: We can't access the job ID directly here, so this would need to be tracked differently
      // For now, we'll track processing times in the result

      switch (event.type) {
        case 'message':
          await this.handleMessageEvent(event as LineMessageEvent)
          break

        case 'follow':
          await this.handleFollowEvent(event)
          break

        case 'unfollow':
          await this.handleUnfollowEvent(event)
          break

        case 'join':
          await this.handleJoinEvent(event)
          break

        case 'leave':
          await this.handleLeaveEvent(event)
          break

        case 'postback':
          await this.handlePostbackEvent(event)
          break

        default:
          console.log(`Unhandled event type: ${event.type}`)
      }

      const processingTime = Date.now() - startTime

      return {
        success: true,
        timestamp: Date.now(),
        eventType: event.type,
        userId: event.source.userId,
        processingTimeMs: processingTime
      }
    } catch (error) {
      console.error(`Error processing LINE event ${event.type}:`, error)
      const processingTime = Date.now() - startTime

      // Return error information
      return {
        success: false,
        timestamp: Date.now(),
        eventType: event.type,
        userId: event.source.userId,
        processingTimeMs: processingTime,
        error: error instanceof Error ? error.message : String(error)
      }
    }
  }

  /**
   * Handle incoming message events
   */
  private async handleMessageEvent(event: LineMessageEvent): Promise<void> {
    if (!event.source.userId) {
      console.log('Message event without user ID, skipping')
      return
    }

    // Delegate to message handler
    await messageHandler.handleMessage(event)
  }

  /**
   * Handle user follow events
   */
  private async handleFollowEvent(event: LineEvent): Promise<void> {
    if (!event.source.userId) {
      console.log('Follow event without user ID, skipping')
      return
    }

    console.log(`User ${event.source.userId} followed the bot`)

    try {
      // Get user profile
      const lineService = new LineMessagingService(config.line.channelAccessToken)
      const profile = await lineService.getProfile(event.source.userId)

      console.log(`New follower: ${profile.displayName} (${profile.userId})`)

      // Send welcome message if reply token is available
      if (event.replyToken) {
        const welcomeMessage = LineMessagingService.createTextMessage(
          `สวัสดี ${profile.displayName}! 👋\n\nยินดีต้อนรับเข้าสู่ระบบ Invoice OCR\nคุณสามารถส่งรูปภาพใบเสร็จมาให้เราช่วยแปลงข้อมูลได้เลย!`
        )

        await lineService.replyMessage(event.replyToken, [welcomeMessage])
      }

      // TODO: Save user to database

    } catch (error) {
      console.error('Error handling follow event:', error)
    }
  }

  /**
   * Handle user unfollow events
   */
  private async handleUnfollowEvent(event: LineEvent): Promise<void> {
    if (!event.source.userId) {
      console.log('Unfollow event without user ID, skipping')
      return
    }

    console.log(`User ${event.source.userId} unfollowed the bot`)

    // TODO: Update user status in database
  }

  /**
   * Handle bot join group/room events
   */
  private async handleJoinEvent(event: LineEvent): Promise<void> {
    console.log(`Bot joined group/room: ${event.source.groupId || event.source.roomId}`)

    try {
      // Send introduction message if reply token is available
      if (event.replyToken) {
        const lineService = new LineMessagingService(config.line.channelAccessToken)
        const introMessage = LineMessagingService.createTextMessage(
          'สวัสดีครับ! 👋\n\nผมเป็นบอทช่วยแปลงข้อมูลจากใบเสร็จ\nส่งรูปภาพใบเสร็จมาให้ผมช่วยแปลงข้อมูลได้เลยครับ!'
        )

        await lineService.replyMessage(event.replyToken, [introMessage])
      }
    } catch (error) {
      console.error('Error handling join event:', error)
    }
  }

  /**
   * Handle bot leave group/room events
   */
  private async handleLeaveEvent(event: LineEvent): Promise<void> {
    console.log(`Bot left group/room: ${event.source.groupId || event.source.roomId}`)
    // No action needed for leave events
  }

  /**
   * Handle postback events (from buttons, quick replies, etc.)
   */
  private async handlePostbackEvent(event: LineEvent): Promise<void> {
    if (!event.postback) {
      console.log('Postback event without postback data, skipping')
      return
    }

    console.log(`Postback received: ${event.postback.data}`)

    try {
      // Parse postback data
      const postbackData = event.postback.data
      const userId = event.source.userId

      if (!userId) {
        console.log('Postback event without user ID, skipping')
        return
      }

      // Handle different postback actions
      if (postbackData.startsWith('action=')) {
        const action = postbackData.split('=')[1]

        // TODO: Implement specific postback actions
        console.log(`Processing postback action: ${action}`)
      }

    } catch (error) {
      console.error('Error handling postback event:', error)
    }
  }

  async stop(): Promise<void> {
    await this.worker.close()
    console.log('LINE Event Worker stopped')
  }
}

// Create and export the worker instance
export const lineEventWorker = new LineEventWorker()