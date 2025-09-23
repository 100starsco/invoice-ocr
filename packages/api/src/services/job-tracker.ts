import { eq } from 'drizzle-orm'
import type { Job } from 'bullmq'
import { db, jobs, lineEvents, lineMessages } from '../db'
import type { LineEvent, LineMessageEvent } from '@invoice-ocr/shared'

export interface JobTrackingData {
  jobId: string
  queueName: string
  jobName: string
  data: any
  priority?: number
  maxAttempts?: number
  parentJobId?: string
  metadata?: any
}

export interface LineEventTrackingData {
  event: LineEvent
  webhookId: string
  jobId?: string
}

export class JobTrackingService {
  /**
   * Create a new job record in the database
   */
  static async createJob(data: JobTrackingData) {
    const [job] = await db.insert(jobs).values({
      jobId: data.jobId,
      queueName: data.queueName,
      jobName: data.jobName,
      data: data.data,
      priority: data.priority,
      maxAttempts: data.maxAttempts,
      parentJobId: data.parentJobId,
      metadata: data.metadata,
      status: 'pending'
    }).returning()

    return job
  }

  /**
   * Update job status
   */
  static async updateJobStatus(
    jobId: string,
    status: string,
    additionalData?: {
      result?: any
      error?: any
      startedAt?: Date
      completedAt?: Date
      failedAt?: Date
      attempts?: number
      processingTimeMs?: number
      workerInstance?: string
    }
  ) {
    const updateData: any = {
      status,
      updatedAt: new Date()
    }

    if (additionalData) {
      Object.assign(updateData, additionalData)
    }

    const [updatedJob] = await db
      .update(jobs)
      .set(updateData)
      .where(eq(jobs.jobId, jobId))
      .returning()

    return updatedJob
  }

  /**
   * Mark job as started
   */
  static async markJobStarted(jobId: string, workerInstance?: string) {
    return this.updateJobStatus(jobId, 'active', {
      startedAt: new Date(),
      workerInstance
    })
  }

  /**
   * Mark job as completed
   */
  static async markJobCompleted(jobId: string, result: any, processingTimeMs?: number) {
    return this.updateJobStatus(jobId, 'completed', {
      result,
      completedAt: new Date(),
      processingTimeMs
    })
  }

  /**
   * Mark job as failed
   */
  static async markJobFailed(jobId: string, error: any, attempts: number) {
    return this.updateJobStatus(jobId, 'failed', {
      error: typeof error === 'string' ? { message: error } : error,
      failedAt: new Date(),
      attempts
    })
  }

  /**
   * Track LINE event
   */
  static async trackLineEvent(data: LineEventTrackingData) {
    const event = data.event

    const [lineEvent] = await db.insert(lineEvents).values({
      eventType: event.type,
      eventId: event.type === 'message' ? (event as LineMessageEvent).message.id : undefined,
      replyToken: event.replyToken,
      userId: event.source.userId,
      groupId: event.source.groupId,
      roomId: event.source.roomId,
      eventData: event,
      webhookId: data.webhookId,
      jobId: data.jobId,
      processed: false,
      receivedAt: new Date(event.timestamp)
    }).returning()

    // If this is a message event, also track the message
    if (event.type === 'message') {
      const messageEvent = event as LineMessageEvent
      await this.trackLineMessage(messageEvent, lineEvent.id)
    }

    return lineEvent
  }

  /**
   * Track LINE message
   */
  static async trackLineMessage(event: LineMessageEvent, eventId: string) {
    const [message] = await db.insert(lineMessages).values({
      messageId: event.message.id,
      messageType: event.message.type,
      content: event.message,
      userId: event.source.userId!,
      eventId,
      replyToken: event.replyToken,
      sentAt: new Date(event.timestamp),
      responded: false
    }).returning()

    return message
  }

  /**
   * Mark LINE event as processed
   */
  static async markLineEventProcessed(eventId: string, success: boolean, error?: string) {
    const updateData: any = {
      processed: true,
      processingCompletedAt: new Date(),
      updatedAt: new Date()
    }

    if (!success && error) {
      updateData.processingError = error
    }

    const [updatedEvent] = await db
      .update(lineEvents)
      .set(updateData)
      .where(eq(lineEvents.id, eventId))
      .returning()

    return updatedEvent
  }

  /**
   * Mark LINE message as responded
   */
  static async markLineMessageResponded(
    messageId: string,
    responseType: string,
    responseJobId?: string
  ) {
    const [updatedMessage] = await db
      .update(lineMessages)
      .set({
        responded: true,
        responseType,
        responseJobId,
        updatedAt: new Date()
      })
      .where(eq(lineMessages.messageId, messageId))
      .returning()

    return updatedMessage
  }

  /**
   * Get job by ID
   */
  static async getJob(jobId: string) {
    const [job] = await db
      .select()
      .from(jobs)
      .where(eq(jobs.jobId, jobId))
      .limit(1)

    return job
  }

  /**
   * Get LINE event by ID
   */
  static async getLineEvent(eventId: string) {
    const [event] = await db
      .select()
      .from(lineEvents)
      .where(eq(lineEvents.id, eventId))
      .limit(1)

    return event
  }

  /**
   * Track job from BullMQ Job instance
   */
  static async trackBullMQJob(job: Job, queueName: string) {
    return this.createJob({
      jobId: job.id!,
      queueName,
      jobName: job.name,
      data: job.data,
      priority: job.opts.priority,
      maxAttempts: job.opts.attempts,
      metadata: {
        delay: job.opts.delay,
        backoff: job.opts.backoff,
        removeOnComplete: job.opts.removeOnComplete,
        removeOnFail: job.opts.removeOnFail
      }
    })
  }
}