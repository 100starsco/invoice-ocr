import type { WebConfig } from './types'

export function validateEnvVar(name: string, value: string | undefined, required = true): string {
  if (required && !value) {
    throw new Error(`Environment variable ${name} is required but not set`)
  }
  return value || ''
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

export function validateConfig(config: WebConfig): void {
  // Validate LIFF configuration
  if (!config.liff.liffId) {
    throw new Error('VITE_LIFF_ID is required')
  }
  if (!config.liff.channelId) {
    throw new Error('VITE_LINE_CHANNEL_ID is required')
  }

  // Validate API URL
  validateUrl('VITE_API_URL', config.api.baseUrl)
}