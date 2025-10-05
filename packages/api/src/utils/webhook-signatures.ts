/**
 * Webhook Signature Utilities
 *
 * Provides HMAC-SHA256 signature generation and verification for webhook security.
 */

import crypto from 'crypto'

// Get webhook secret from environment
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || ''

/**
 * Generate HMAC-SHA256 signature for webhook payload
 *
 * @param payload - Webhook payload object
 * @returns Hex-encoded signature string with sha256= prefix
 */
export function generateWebhookSignature(payload: any): string {
  if (!WEBHOOK_SECRET) {
    throw new Error('WEBHOOK_SECRET not configured')
  }

  // Convert payload to JSON string (deterministic sorting for consistency)
  const payloadJson = JSON.stringify(payload, Object.keys(payload).sort())

  // Generate HMAC-SHA256 signature
  const signature = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payloadJson)
    .digest('hex')

  // Return with sha256= prefix (standard webhook format)
  return `sha256=${signature}`
}

/**
 * Verify webhook signature
 *
 * @param payload - Webhook payload object
 * @param signatureHeader - Signature from X-Webhook-Signature header
 * @returns True if signature is valid, false otherwise
 */
export function verifyWebhookSignature(
  payload: any,
  signatureHeader: string | undefined
): boolean {
  if (!WEBHOOK_SECRET || !signatureHeader) {
    return false
  }

  try {
    // Generate expected signature
    const expectedSignature = generateWebhookSignature(payload)

    // Compare signatures (using timingSafeEqual for timing attack protection)
    const expectedBuffer = Buffer.from(expectedSignature)
    const receivedBuffer = Buffer.from(signatureHeader)

    if (expectedBuffer.length !== receivedBuffer.length) {
      return false
    }

    return crypto.timingSafeEqual(expectedBuffer, receivedBuffer)
  } catch (error) {
    console.error('Error verifying webhook signature:', error)
    return false
  }
}

/**
 * Middleware to verify webhook signature
 *
 * @param strictMode - If true, rejects requests without valid signature
 * @returns Hono middleware function
 */
export function webhookSignatureMiddleware(strictMode = true) {
  return async (c: any, next: any) => {
    const signatureHeader = c.req.header('X-Webhook-Signature')

    // Parse request body
    const body = await c.req.json()

    // Verify signature
    const isValid = verifyWebhookSignature(body, signatureHeader)

    if (strictMode && !isValid) {
      return c.json(
        { error: 'Invalid webhook signature' },
        401
      )
    }

    // Store verification result in context
    c.set('webhookVerified', isValid)

    // Store parsed body for handler
    c.set('webhookPayload', body)

    await next()
  }
}

/**
 * Get signature headers for outgoing webhook
 *
 * @param payload - Webhook payload
 * @returns Headers object with signature
 */
export function getWebhookSignatureHeaders(payload: any): { [key: string]: string } {
  try {
    const signature = generateWebhookSignature(payload)
    return {
      'X-Webhook-Signature': signature
    }
  } catch (error) {
    console.warn('Unable to generate webhook signature:', error)
    return {}
  }
}