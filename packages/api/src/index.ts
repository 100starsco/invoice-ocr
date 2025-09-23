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
// import './workers/line-message'  // Disable worker for testing

const app = new Hono()

app.use('*', cors())

// Setup Bull Board Dashboard
// TODO: Fix HonoAdapter configuration
// if (config.queue.dashboard.enabled) {
//   const serverAdapter = new HonoAdapter()
//   createBullBoard({
//     queues: queues.map(queue => new BullMQAdapter(queue)),
//     serverAdapter: serverAdapter
//   })
//   serverAdapter.setBasePath(config.queue.dashboard.path)
//   app.route(config.queue.dashboard.path, serverAdapter)
//   console.log(`Queue dashboard available at: http://localhost:${config.server.port}${config.queue.dashboard.path}`)
// }

app.get('/health', (c) => {
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
app.route(config.line.webhookPath, webhook)

app.get('/', (c) => {
  return c.json({
    message: 'Invoice OCR API',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      webhook: config.line.webhookPath
    }
  })
})

serve({
  fetch: app.fetch,
  port: config.server.port
})

console.log(`API server running on http://localhost:${config.server.port}`)
console.log(`Health check available at http://localhost:${config.server.port}/health`)