import type { QueueConfig } from './types'

// Parse Redis URL to extract components
function parseRedisUrl(url: string) {
  try {
    const parsedUrl = new URL(url)
    return {
      host: parsedUrl.hostname || 'localhost',
      port: parseInt(parsedUrl.port) || 6379,
      password: parsedUrl.password || undefined,
      db: 0
    }
  } catch {
    return {
      host: 'localhost',
      port: 6379,
      password: undefined,
      db: 0
    }
  }
}

const queueRedisUrl = process.env.QUEUE_REDIS_URL || process.env.REDIS_URL || 'redis://localhost:6379'
const redisConfig = parseRedisUrl(queueRedisUrl)

export const queueConfig: QueueConfig = {
  redis: {
    host: redisConfig.host,
    port: redisConfig.port,
    password: redisConfig.password,
    db: redisConfig.db
  },
  queues: {
    imageProcessing: 'image-processing',
    ocrRequest: 'ocr-request',
    notification: 'notification'
  },
  defaultJobOptions: {
    removeOnComplete: 100,
    removeOnFail: 50,
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000
    }
  },
  concurrency: {
    imageProcessing: 5,
    ocrRequest: 3,
    notification: 10
  },
  dashboard: {
    enabled: process.env.QUEUE_DASHBOARD_ENABLED !== 'false',
    path: '/admin/queues'
  }
}