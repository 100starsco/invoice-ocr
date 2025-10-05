/**
 * Service Authentication Middleware
 *
 * Provides API key authentication for service-to-service communication.
 */

import type { Context, Next } from 'hono'
import { HTTPException } from 'hono/http-exception'

// Get service API key from environment
const SERVICE_API_KEY = process.env.SERVICE_API_KEY

/**
 * Verify API key middleware
 *
 * Requires valid API key in X-API-Key header for protected endpoints.
 */
export const verifyApiKey = async (c: Context, next: Next) => {
  if (!SERVICE_API_KEY) {
    throw new HTTPException(500, { message: 'Service API key not configured' })
  }

  const apiKey = c.req.header('X-API-Key')

  if (!apiKey) {
    throw new HTTPException(401, {
      message: 'API key required',
      res: new Response('API key required', {
        status: 401,
        headers: { 'WWW-Authenticate': 'X-API-Key' }
      })
    })
  }

  if (apiKey !== SERVICE_API_KEY) {
    throw new HTTPException(401, {
      message: 'Invalid API key',
      res: new Response('Invalid API key', {
        status: 401,
        headers: { 'WWW-Authenticate': 'X-API-Key' }
      })
    })
  }

  await next()
}

/**
 * Optional API key middleware
 *
 * Checks API key if present but doesn't require it.
 * Sets c.set('authenticated', true) if valid key provided.
 */
export const optionalApiKey = async (c: Context, next: Next) => {
  if (!SERVICE_API_KEY) {
    c.set('authenticated', false)
    await next()
    return
  }

  const apiKey = c.req.header('X-API-Key')

  if (apiKey && apiKey === SERVICE_API_KEY) {
    c.set('authenticated', true)
  } else {
    c.set('authenticated', false)
  }

  await next()
}

/**
 * Generate API key header for outgoing requests
 */
export function getApiKeyHeader(): { [key: string]: string } {
  if (!SERVICE_API_KEY) {
    return {}
  }

  return {
    'X-API-Key': SERVICE_API_KEY
  }
}