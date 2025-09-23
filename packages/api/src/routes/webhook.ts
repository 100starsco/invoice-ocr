import { Hono } from 'hono'
import type { LineWebhookBody, LineEvent, LineMessageEvent } from '@invoice-ocr/shared'
import { LineMessagingService } from '../services/line'
import { config } from '../config'
import { messageHandler } from '../handlers/message'

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
      console.error('Invalid LINE webhook signature')
      return c.json({ error: 'Invalid signature' }, 401)
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

    // Process each event
    for (const event of webhookBody.events) {
      try {
        await processEvent(event)
      } catch (error) {
        console.error('Error processing LINE event:', error)
        // Continue processing other events even if one fails
      }
    }

    // LINE expects a 200 response
    return c.json({ success: true })

  } catch (error) {
    console.error('Webhook error:', error)
    return c.json({ error: 'Internal server error' }, 500)
  }
})

/**
 * Process individual LINE events
 */
async function processEvent(event: LineEvent): Promise<void> {
  console.log(`Processing LINE event: ${event.type}`)

  switch (event.type) {
    case 'message':
      await handleMessageEvent(event as LineMessageEvent)
      break

    case 'follow':
      await handleFollowEvent(event)
      break

    case 'unfollow':
      await handleUnfollowEvent(event)
      break

    case 'join':
      await handleJoinEvent(event)
      break

    case 'leave':
      await handleLeaveEvent(event)
      break

    case 'postback':
      await handlePostbackEvent(event)
      break

    default:
      console.log(`Unhandled event type: ${event.type}`)
  }
}

/**
 * Handle incoming message events
 */
async function handleMessageEvent(event: LineMessageEvent): Promise<void> {
  if (!event.source.userId) {
    console.log('Message event without user ID, skipping')
    return
  }

  // Delegate to message handler
  await messageHandler.handleMessage(event)
}

/**
 * Handle user follow events
 */
async function handleFollowEvent(event: LineEvent): Promise<void> {
  if (!event.source.userId) {
    console.log('Follow event without user ID, skipping')
    return
  }

  console.log(`User ${event.source.userId} followed the bot`)

  try {
    // Get user profile
    const lineService = new LineMessagingService(config.line.channelAccessToken)
    const profile = await lineService.getProfile(event.source.userId)

    console.log(`New follower: ${profile.displayName} (${profile.userId})`)

    // Send welcome message if reply token is available
    if (event.replyToken) {
      const welcomeMessage = LineMessagingService.createTextMessage(
        `สวัสดี ${profile.displayName}! 👋\n\nยินดีต้อนรับเข้าสู่ระบบ Invoice OCR\nคุณสามารถส่งรูปภาพใบเสร็จมาให้เราช่วยแปลงข้อมูลได้เลย!`
      )

      await lineService.replyMessage(event.replyToken, [welcomeMessage])
    }

    // TODO: Save user to database

  } catch (error) {
    console.error('Error handling follow event:', error)
  }
}

/**
 * Handle user unfollow events
 */
async function handleUnfollowEvent(event: LineEvent): Promise<void> {
  if (!event.source.userId) {
    console.log('Unfollow event without user ID, skipping')
    return
  }

  console.log(`User ${event.source.userId} unfollowed the bot`)

  // TODO: Update user status in database
}

/**
 * Handle bot join group/room events
 */
async function handleJoinEvent(event: LineEvent): Promise<void> {
  console.log(`Bot joined group/room: ${event.source.groupId || event.source.roomId}`)

  try {
    // Send introduction message if reply token is available
    if (event.replyToken) {
      const lineService = new LineMessagingService(config.line.channelAccessToken)
      const introMessage = LineMessagingService.createTextMessage(
        'สวัสดีครับ! 👋\n\nผมเป็นบอทช่วยแปลงข้อมูลจากใบเสร็จ\nส่งรูปภาพใบเสร็จมาให้ผมช่วยแปลงข้อมูลได้เลยครับ!'
      )

      await lineService.replyMessage(event.replyToken, [introMessage])
    }
  } catch (error) {
    console.error('Error handling join event:', error)
  }
}

/**
 * Handle bot leave group/room events
 */
async function handleLeaveEvent(event: LineEvent): Promise<void> {
  console.log(`Bot left group/room: ${event.source.groupId || event.source.roomId}`)
  // No action needed for leave events
}

/**
 * Handle postback events (from buttons, quick replies, etc.)
 */
async function handlePostbackEvent(event: LineEvent): Promise<void> {
  if (!event.postback) {
    console.log('Postback event without postback data, skipping')
    return
  }

  console.log(`Postback received: ${event.postback.data}`)

  try {
    // Parse postback data
    const postbackData = event.postback.data
    const userId = event.source.userId

    if (!userId) {
      console.log('Postback event without user ID, skipping')
      return
    }

    // Handle different postback actions
    if (postbackData.startsWith('action=')) {
      const action = postbackData.split('=')[1]

      // TODO: Implement specific postback actions
      console.log(`Processing postback action: ${action}`)
    }

  } catch (error) {
    console.error('Error handling postback event:', error)
  }
}

export { webhook }