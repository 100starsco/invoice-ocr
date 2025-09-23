import { createBullBoard } from '@bull-board/api'
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter'
import { ExpressAdapter } from '@bull-board/express'
import express from 'express'
import { Queue } from 'bullmq'
import Redis from 'ioredis'
import basicAuth from 'express-basic-auth'

// Create Redis connection
const redis = new Redis({
  host: 'localhost',
  port: 6379,
  maxRetriesPerRequest: null
})

// Create queues
const queues = [
  new Queue('line-events', { connection: redis }),
  new Queue('line-messages', { connection: redis }),
  new Queue('line-follow', { connection: redis }),
  new Queue('line-user-management', { connection: redis }),
  new Queue('image-processing', { connection: redis }),
  new Queue('ocr-request', { connection: redis }),
  new Queue('notification', { connection: redis })
]

const serverAdapter = new ExpressAdapter()
serverAdapter.setBasePath('/admin/queues')

createBullBoard({
  queues: queues.map(queue => new BullMQAdapter(queue)),
  serverAdapter: serverAdapter
})

const app = express()

// Add basic authentication protection
app.use('/admin/queues', basicAuth({
  users: { 'admin': 'queue123' },
  challenge: true,
  realm: 'Queue Dashboard'
}))

app.use('/admin/queues', serverAdapter.getRouter())

const PORT = 3001
app.listen(PORT, () => {
  console.log(`Queue Dashboard running at http://localhost:${PORT}/admin/queues`)
})