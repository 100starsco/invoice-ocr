import { Queue } from 'bullmq'
import Redis from 'ioredis'
import { config } from '../config'

// Create Redis connection for Bull MQ
const redis = new Redis({
  host: config.queue.redis.host,
  port: config.queue.redis.port,
  password: config.queue.redis.password,
  db: config.queue.redis.db,
  maxRetriesPerRequest: null, // Required for BullMQ
  enableReadyCheck: true,
  lazyConnect: true
})

// Create minimal queue instances for dashboard monitoring
export const imageProcessingQueue = new Queue(config.queue.queues.imageProcessing, {
  connection: redis,
  defaultJobOptions: config.queue.defaultJobOptions
})

export const ocrRequestQueue = new Queue(config.queue.queues.ocrRequest, {
  connection: redis,
  defaultJobOptions: config.queue.defaultJobOptions
})

export const notificationQueue = new Queue(config.queue.queues.notification, {
  connection: redis,
  defaultJobOptions: config.queue.defaultJobOptions
})

// Export all queues for dashboard
export const queues = [
  imageProcessingQueue,
  ocrRequestQueue,
  notificationQueue
]

// Handle Redis connection events
redis.on('connect', () => {
  console.log(`Connected to Redis for queues: ${config.queue.redis.host}:${config.queue.redis.port}`)
})

redis.on('error', (error) => {
  console.error('Redis queue connection error:', error)
})

export { redis }