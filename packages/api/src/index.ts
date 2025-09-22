import { serve } from '@hono/node-server'
import { Hono } from 'hono'
import { cors } from 'hono/cors'

const app = new Hono()

app.use('*', cors())

app.get('/health', (c) => {
  return c.json({
    status: 'healthy',
    service: 'api',
    timestamp: new Date().toISOString()
  })
})

app.get('/', (c) => {
  return c.json({
    message: 'Invoice OCR API',
    version: '1.0.0'
  })
})

const port = process.env.PORT ? parseInt(process.env.PORT) : 3000

serve({
  fetch: app.fetch,
  port
})

console.log(`API server running on http://localhost:${port}`)
console.log(`Health check available at http://localhost:${port}/health`)