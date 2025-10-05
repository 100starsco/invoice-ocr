import 'dotenv/config'
import { serve } from '@hono/node-server'
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { createBullBoard } from '@bull-board/api'
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter'
import { HonoAdapter } from '@bull-board/hono'
import { config } from './config'
import { queues } from './queues'
import { webhook } from './routes/webhook'
import webhooks from './routes/webhooks'
import { admin } from './routes/admin'
import { docs } from './routes/docs'
import { images } from './routes/images'
import './workers/line-event'  // Enable LINE event worker
import './workers/line-message-incoming'  // Enable LINE incoming message worker
import './workers/line-follow'  // Enable LINE follow worker
import './workers/line-user'  // Enable LINE user management worker

const app = new Hono()

app.use('*', cors())

// Setup Bull Board Dashboard (disabled for now due to compatibility issues)
// if (config.queue.dashboard.enabled) {
//   const serverAdapter = new HonoAdapter()

//   createBullBoard({
//     queues: queues.map(queue => new BullMQAdapter(queue)),
//     serverAdapter: serverAdapter
//   })

//   app.mount(config.queue.dashboard.path, serverAdapter.getApp())
//   console.log(`Queue dashboard available at: http://localhost:${config.server.port}${config.queue.dashboard.path}`)
// }

// API routes with /api prefix
const api = new Hono()

api.get('/health', (c) => {
  return c.json({
    status: 'healthy',
    service: 'api',
    timestamp: new Date().toISOString(),
    queues: {
      queues: config.queue.queues
    }
  })
})

// LINE webhook routes
api.route('/webhook', webhook)

// External service webhooks (OCR, etc.)
api.route('/webhooks', webhooks)

// Admin routes
api.route('/admin', admin)

// Documentation routes
api.route('/docs', docs)

// Image proxy routes
api.route('/images', images)

// Mount API routes with /api prefix
app.route('/api', api)

app.get('/', (c) => {
  return c.json({
    message: 'Invoice OCR API',
    version: '1.0.0',
    endpoints: {
      health: '/api/health',
      webhook: '/api/webhook',
      webhooks: '/api/webhooks',
      admin: '/api/admin',
      docs: '/api/docs/ui',
      images: '/api/images'
    }
  })
})

serve({
  fetch: app.fetch,
  port: config.server.port
})

console.log(`API server running on http://localhost:${config.server.port}`)
console.log(`Health check available at http://localhost:${config.server.port}/api/health`)
console.log(`Admin endpoints available at http://localhost:${config.server.port}/api/admin`)