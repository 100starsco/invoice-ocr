import { Hono } from 'hono'
import type { LineWebhookBody, LineEvent } from '@invoice-ocr/shared'
import { LineMessagingService } from '../services/line'
import { JobTrackingService } from '../services/job-tracker'
import { config } from '../config'
import { lineEventQueue, lineMessageQueue, lineFollowQueue, lineUserQueue } from '../queues'

const webhook = new Hono()

// LINE webhook endpoint
webhook.post('/', async (c) => {
  try {
    // Get the raw body for signature verification
    const body = await c.req.text()
    const signature = c.req.header('x-line-signature')

    if (!signature) {
      console.error('Missing LINE signature header')
      return c.json({ error: 'Missing signature' }, 400)
    }

    // Validate the webhook signature
    const isValidSignature = await LineMessagingService.validateSignature(
      body,
      signature,
      config.line.channelSecret
    )

    if (!isValidSignature) {
      console.warn('Invalid LINE webhook signature (continuing in development mode)', {
        has_signature: !!signature,
        node_env: process.env.NODE_ENV,
        events_count: JSON.parse(body).events?.length || 0
      })

      // In development, we allow unsigned webhooks for testing
      // In production, you should enable strict signature validation
      if (process.env.NODE_ENV === 'production') {
        return c.json({ error: 'Invalid signature' }, 401)
      }
    }

    // Parse the webhook body
    let webhookBody: LineWebhookBody
    try {
      webhookBody = JSON.parse(body)
    } catch (error) {
      console.error('Failed to parse webhook body:', error)
      return c.json({ error: 'Invalid JSON' }, 400)
    }

    // Validate webhook body structure
    if (!webhookBody.events || !Array.isArray(webhookBody.events)) {
      console.error('Invalid webhook body structure')
      return c.json({ error: 'Invalid webhook body' }, 400)
    }

    console.log(`Received ${webhookBody.events.length} LINE events`)

    // Queue each event for processing to the appropriate specialized queue
    for (const event of webhookBody.events) {
      try {
        let targetQueue
        let queueName

        // Route events to specialized queues
        switch (event.type) {
          case 'message':
            targetQueue = lineMessageQueue
            queueName = 'line-messages'
            break
          case 'follow':
          case 'unfollow':
            targetQueue = lineFollowQueue
            queueName = 'line-follow'
            break
          case 'join':
          case 'leave':
            targetQueue = lineUserQueue
            queueName = 'line-user-management'
            break
          default:
            // Fall back to general LINE event queue for other event types
            targetQueue = lineEventQueue
            queueName = 'line-events'
        }

        const job = await targetQueue.add(
          `line-event-${event.type}`,
          {
            event,
            timestamp: Date.now(),
            webhookId: webhookBody.destination
          },
          {
            attempts: 3,
            backoff: {
              type: 'exponential',
              delay: 2000
            },
            priority: event.type === 'message' ? 10 : 5 // Higher priority for messages
          }
        )

        // Track job and event in database
        const trackedJob = await JobTrackingService.trackBullMQJob(job, queueName)
        const trackedEvent = await JobTrackingService.trackLineEvent({
          event,
          webhookId: webhookBody.destination,
          jobId: trackedJob.id
        })

        console.log(`Queued LINE event: ${event.type} to ${queueName} (Job ID: ${job.id}, Event ID: ${trackedEvent.id})`)
      } catch (error) {
        console.error('Error queuing LINE event:', error)
        // Continue queuing other events even if one fails
      }
    }

    // LINE expects a 200 response
    return c.json({ success: true })

  } catch (error) {
    console.error('Webhook error:', error)
    return c.json({ error: 'Internal server error' }, 500)
  }
})

export { webhook }