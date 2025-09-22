import type { ApiConfig } from './types'

export function validateEnvVar(name: string, value: string | undefined, required = true): string {
  if (required && !value) {
    throw new Error(`Environment variable ${name} is required but not set`)
  }
  return value || ''
}

export function validatePort(value: string | undefined, defaultPort: number): number {
  if (!value) return defaultPort

  const port = parseInt(value, 10)
  if (isNaN(port) || port < 1 || port > 65535) {
    throw new Error(`Invalid port number: ${value}`)
  }
  return port
}

export function validateUrl(name: string, value: string | undefined, required = true): string {
  const url = validateEnvVar(name, value, required)

  if (url && required) {
    try {
      new URL(url)
    } catch {
      throw new Error(`Invalid URL for ${name}: ${url}`)
    }
  }

  return url
}

export function validateConfig(config: ApiConfig): void {
  // Validate LINE configuration
  if (!config.line.channelSecret) {
    throw new Error('LINE_CHANNEL_SECRET is required')
  }
  if (!config.line.channelAccessToken) {
    throw new Error('LINE_CHANNEL_ACCESS_TOKEN is required')
  }

  // Validate database URLs
  validateUrl('DATABASE_URL', config.database.postgresql.url)
  validateUrl('MONGODB_URI', config.database.mongodb.uri)
  validateUrl('REDIS_URL', config.database.redis.url)

  // Validate service URLs
  validateUrl('OCR_SERVICE_URL', config.services.ocrServiceUrl)

  // Validate server config
  if (config.server.port < 1 || config.server.port > 65535) {
    throw new Error(`Invalid server port: ${config.server.port}`)
  }
}