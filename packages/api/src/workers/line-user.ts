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

interface LineUserJobData {
  event: LineEvent
  timestamp: number
  webhookId: string
}

interface LineUserJobResult {
  success: boolean
  timestamp: number
  eventType: string
  groupId?: string
  roomId?: string
  processingTimeMs: number
  error?: string
}

class LineUserWorker {
  private worker: Worker

  constructor() {
    this.worker = new Worker(
      'line-user-management',
      async (job) => {
        console.log(`Processing LINE user management job: ${job.name}`)
        return this.processUserEvent(job.data)
      },
      {
        connection: redis,
        concurrency: 3,
        removeOnComplete: 100,
        removeOnFail: 50
      }
    )

    this.worker.on('completed', (job, result) => {
      console.log(`LINE user management job ${job.id} completed:`, result)
    })

    this.worker.on('failed', (job, err) => {
      console.error(`LINE user management job ${job?.id} failed:`, err)
    })

    this.worker.on('error', (err) => {
      console.error('LINE user management worker error:', err)
    })

    console.log('LINE User Management Worker started')
  }

  private async processUserEvent(data: LineUserJobData): Promise<LineUserJobResult> {
    const { event, timestamp, webhookId } = data
    const startTime = Date.now()

    console.log(`Processing LINE ${event.type} event`)

    try {
      switch (event.type) {
        case 'join':
          await this.handleJoinEvent(event)
          break
        case 'leave':
          await this.handleLeaveEvent(event)
          break
        default:
          throw new Error(`Unsupported event type: ${event.type}`)
      }

      const processingTime = Date.now() - startTime

      return {
        success: true,
        timestamp: Date.now(),
        eventType: event.type,
        groupId: event.source.groupId,
        roomId: event.source.roomId,
        processingTimeMs: processingTime
      }
    } catch (error) {
      console.error(`Error processing LINE ${event.type} event:`, error)
      const processingTime = Date.now() - startTime

      return {
        success: false,
        timestamp: Date.now(),
        eventType: event.type,
        groupId: event.source.groupId,
        roomId: event.source.roomId,
        processingTimeMs: processingTime,
        error: error instanceof Error ? error.message : String(error)
      }
    }
  }

  /**
   * Handle bot join group/room events
   */
  private async handleJoinEvent(event: LineEvent): Promise<void> {
    const groupOrRoomId = event.source.groupId || event.source.roomId
    console.log(`Bot joined group/room: ${groupOrRoomId}`)

    try {
      // Send introduction message if reply token is available
      if (event.replyToken) {
        const lineService = new LineMessagingService(config.line.channelAccessToken)
        const introMessage = LineMessagingService.createTextMessage(
          'สวัสดีครับ! 👋\n\nผมเป็นบอทช่วยแปลงข้อมูลจากใบเสร็จ\nส่งรูปภาพใบเสร็จมาให้ผมช่วยแปลงข้อมูลได้เลยครับ!'
        )

        await lineService.replyMessage(event.replyToken, [introMessage])
      }

      // TODO: Save group/room information to database

    } catch (error) {
      console.error('Error handling join event:', error)
      throw error
    }
  }

  /**
   * Handle bot leave group/room events
   */
  private async handleLeaveEvent(event: LineEvent): Promise<void> {
    const groupOrRoomId = event.source.groupId || event.source.roomId
    console.log(`Bot left group/room: ${groupOrRoomId}`)

    // TODO: Update group/room status in database
    // No action needed for leave events beyond logging
  }

  async stop(): Promise<void> {
    await this.worker.close()
    console.log('LINE User Management Worker stopped')
  }
}

// Create and export the worker instance
export const lineUserWorker = new LineUserWorker()