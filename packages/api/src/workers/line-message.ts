import { Worker, Job } from 'bullmq'
import type { LineMessageJobData, LineMessageJobResult } from '@invoice-ocr/shared'
import { LineMessagingService } from '../services/line'
import { config } from '../config'
import { redis } from '../queues'

class LineMessageWorker {
  private worker: Worker
  private lineService: LineMessagingService

  constructor() {
    this.lineService = new LineMessagingService(config.line.channelAccessToken)

    // Create BullMQ worker
    this.worker = new Worker(
      config.queue.queues.notification,
      this.processJob.bind(this),
      {
        connection: redis,
        concurrency: config.queue.concurrency.notification
      }
    )

    this.setupEventHandlers()
    console.log(`LINE message worker started with concurrency: ${config.queue.concurrency.notification}`)
  }

  /**
   * Process LINE message jobs
   */
  private async processJob(job: Job<LineMessageJobData>): Promise<LineMessageJobResult> {
    const { data } = job
    const startTime = Date.now()

    try {
      console.log(`Processing LINE message job ${job.id}: ${data.type}`)

      let result: LineMessageJobResult

      switch (data.type) {
        case 'reply':
          result = await this.processReplyMessage(data)
          break

        case 'push':
          result = await this.processPushMessage(data)
          break

        case 'multicast':
          result = await this.processMulticastMessage(data)
          break

        case 'broadcast':
          result = await this.processBroadcastMessage(data)
          break

        default:
          throw new Error(`Unsupported message type: ${(data as any).type}`)
      }

      const processingTime = Date.now() - startTime
      console.log(`Job ${job.id} completed in ${processingTime}ms`)

      return result

    } catch (error) {
      const processingTime = Date.now() - startTime
      console.error(`Job ${job.id} failed after ${processingTime}ms:`, error)

      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      }
    }
  }

  /**
   * Process reply message
   */
  private async processReplyMessage(data: LineMessageJobData): Promise<LineMessageJobResult> {
    if (!data.replyToken) {
      throw new Error('Reply token is required for reply messages')
    }

    if (!data.messages || data.messages.length === 0) {
      throw new Error('Messages array is required and cannot be empty')
    }

    await this.lineService.replyMessage(
      data.replyToken,
      data.messages,
      data.notificationDisabled
    )

    return {
      success: true,
      timestamp: Date.now()
    }
  }

  /**
   * Process push message
   */
  private async processPushMessage(data: LineMessageJobData): Promise<LineMessageJobResult> {
    if (!data.to || typeof data.to !== 'string') {
      throw new Error('Target user ID is required for push messages')
    }

    if (!data.messages || data.messages.length === 0) {
      throw new Error('Messages array is required and cannot be empty')
    }

    await this.lineService.pushMessage(
      data.to,
      data.messages,
      data.notificationDisabled
    )

    return {
      success: true,
      timestamp: Date.now()
    }
  }

  /**
   * Process multicast message
   */
  private async processMulticastMessage(data: LineMessageJobData): Promise<LineMessageJobResult> {
    if (!data.to || !Array.isArray(data.to)) {
      throw new Error('Target user IDs array is required for multicast messages')
    }

    if (!data.messages || data.messages.length === 0) {
      throw new Error('Messages array is required and cannot be empty')
    }

    await this.lineService.multicastMessage(
      data.to,
      data.messages,
      data.notificationDisabled
    )

    return {
      success: true,
      timestamp: Date.now()
    }
  }

  /**
   * Process broadcast message
   */
  private async processBroadcastMessage(data: LineMessageJobData): Promise<LineMessageJobResult> {
    if (!data.messages || data.messages.length === 0) {
      throw new Error('Messages array is required and cannot be empty')
    }

    await this.lineService.broadcastMessage(
      data.messages,
      data.notificationDisabled
    )

    return {
      success: true,
      timestamp: Date.now()
    }
  }

  /**
   * Setup event handlers for worker
   */
  private setupEventHandlers(): void {
    this.worker.on('ready', () => {
      console.log('LINE message worker is ready')
    })

    this.worker.on('active', (job) => {
      console.log(`Job ${job.id} started processing`)
    })

    this.worker.on('completed', (job, result) => {
      console.log(`Job ${job.id} completed:`, result)
    })

    this.worker.on('failed', (job, error) => {
      console.error(`Job ${job?.id} failed:`, error)
    })

    this.worker.on('stalled', (jobId) => {
      console.warn(`Job ${jobId} stalled`)
    })

    this.worker.on('error', (error) => {
      console.error('Worker error:', error)
    })

    this.worker.on('closed', () => {
      console.log('LINE message worker closed')
    })

    // Handle Redis connection events are handled by the redis instance directly
  }

  /**
   * Get worker status and statistics
   */
  async getStats() {
    return {
      isRunning: this.worker.isRunning(),
      isPaused: this.worker.isPaused()
    }
  }

  /**
   * Gracefully close the worker
   */
  async close(): Promise<void> {
    console.log('Closing LINE message worker...')
    await this.worker.close()
  }

  /**
   * Pause the worker
   */
  async pause(): Promise<void> {
    console.log('Pausing LINE message worker...')
    await this.worker.pause()
  }

  /**
   * Resume the worker
   */
  async resume(): Promise<void> {
    console.log('Resuming LINE message worker...')
    await this.worker.resume()
  }
}

// Create and export worker instance
export const lineMessageWorker = new LineMessageWorker()

// Graceful shutdown handling
process.on('SIGINT', async () => {
  console.log('Received SIGINT, shutting down LINE message worker gracefully...')
  await lineMessageWorker.close()
  process.exit(0)
})

process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, shutting down LINE message worker gracefully...')
  await lineMessageWorker.close()
  process.exit(0)
})