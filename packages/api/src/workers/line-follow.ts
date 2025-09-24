import { Worker } from 'bullmq'
import type { LineEvent } from '@invoice-ocr/shared'
import { LineMessagingService } from '../services/line'
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

interface LineFollowJobData {
  event: LineEvent
  timestamp: number
  webhookId: string
}

interface LineFollowJobResult {
  success: boolean
  timestamp: number
  eventType: string
  userId: string
  processingTimeMs: number
  error?: string
}

class LineFollowWorker {
  private worker: Worker

  constructor() {
    this.worker = new Worker(
      'line-follow',
      async (job) => {
        console.log(`Processing LINE follow job: ${job.name}`)
        return this.processFollowEvent(job.data)
      },
      {
        connection: redis,
        concurrency: 5,
        removeOnComplete: { count: 100 },
        removeOnFail: { count: 50 }
      }
    )

    this.worker.on('completed', (job, result) => {
      console.log(`LINE follow job ${job.id} completed:`, result)
    })

    this.worker.on('failed', (job, err) => {
      console.error(`LINE follow job ${job?.id} failed:`, err)
    })

    this.worker.on('error', (err) => {
      console.error('LINE follow worker error:', err)
    })

    console.log('LINE Follow Worker started')
  }

  private async processFollowEvent(data: LineFollowJobData): Promise<LineFollowJobResult> {
    const { event, timestamp, webhookId } = data
    const startTime = Date.now()

    console.log(`Processing LINE ${event.type} event from user: ${event.source.userId}`)

    try {
      if (!event.source.userId) {
        throw new Error(`${event.type} event without user ID`)
      }

      switch (event.type) {
        case 'follow':
          await this.handleFollowEvent(event)
          break
        case 'unfollow':
          await this.handleUnfollowEvent(event)
          break
        default:
          throw new Error(`Unsupported event type: ${event.type}`)
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
      console.error(`Error processing LINE ${event.type} event:`, error)
      const processingTime = Date.now() - startTime

      return {
        success: false,
        timestamp: Date.now(),
        eventType: event.type,
        userId: event.source.userId || 'unknown',
        processingTimeMs: processingTime,
        error: error instanceof Error ? error.message : String(error)
      }
    }
  }

  /**
   * Handle user follow events
   */
  private async handleFollowEvent(event: LineEvent): Promise<void> {
    console.log(`User ${event.source.userId} followed the bot`)

    try {
      // Get user profile
      const lineService = new LineMessagingService(config.line.channelAccessToken)
      const profile = await lineService.getProfile(event.source.userId!)

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
      throw error
    }
  }

  /**
   * Handle user unfollow events
   */
  private async handleUnfollowEvent(event: LineEvent): Promise<void> {
    console.log(`User ${event.source.userId} unfollowed the bot`)

    // TODO: Update user status in database
  }

  async stop(): Promise<void> {
    await this.worker.close()
    console.log('LINE Follow Worker stopped')
  }
}

// Create and export the worker instance
export const lineFollowWorker = new LineFollowWorker()