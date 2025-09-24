import { Worker } from 'bullmq'
import type { LineMessageEvent } from '@invoice-ocr/shared'
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

interface LineMessageJobData {
  event: LineMessageEvent
  timestamp: number
  webhookId: string
}

interface LineMessageJobResult {
  success: boolean
  timestamp: number
  messageId: string
  userId: string
  processingTimeMs: number
  error?: string
}

class LineMessageIncomingWorker {
  private worker: Worker

  constructor() {
    this.worker = new Worker(
      'line-messages',
      async (job) => {
        console.log(`Processing incoming LINE message job: ${job.name}`)
        return this.processLineMessage(job.data)
      },
      {
        connection: redis,
        concurrency: 10, // Higher concurrency for messages
        removeOnComplete: { count: 100 },
        removeOnFail: { count: 50 }
      }
    )

    this.worker.on('completed', (job, result) => {
      console.log(`LINE message job ${job.id} completed:`, result)
    })

    this.worker.on('failed', (job, err) => {
      console.error(`LINE message job ${job?.id} failed:`, err)
    })

    this.worker.on('error', (err) => {
      console.error('LINE message worker error:', err)
    })

    console.log('LINE Message Incoming Worker started')
  }

  private async processLineMessage(data: LineMessageJobData): Promise<LineMessageJobResult> {
    const { event, timestamp, webhookId } = data
    const startTime = Date.now()

    console.log(`Processing LINE message: ${event.message.type} from user: ${event.source.userId}`)

    try {
      if (!event.source.userId) {
        throw new Error('Message event without user ID')
      }

      // Delegate to message handler
      await messageHandler.handleMessage(event)

      const processingTime = Date.now() - startTime

      return {
        success: true,
        timestamp: Date.now(),
        messageId: event.message.id,
        userId: event.source.userId,
        processingTimeMs: processingTime
      }
    } catch (error) {
      console.error(`Error processing LINE message:`, error)
      const processingTime = Date.now() - startTime

      return {
        success: false,
        timestamp: Date.now(),
        messageId: event.message.id,
        userId: event.source.userId || 'unknown',
        processingTimeMs: processingTime,
        error: error instanceof Error ? error.message : String(error)
      }
    }
  }

  async stop(): Promise<void> {
    await this.worker.close()
    console.log('LINE Message Incoming Worker stopped')
  }
}

// Create and export the worker instance
export const lineMessageIncomingWorker = new LineMessageIncomingWorker()