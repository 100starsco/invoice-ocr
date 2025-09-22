import { environmentConfig } from './environment'
import { liffConfig } from './liff'
import { apiConfig } from './api'
import { validateConfig } from './validator'
import type { WebConfig } from './types'

export const config: WebConfig = {
  environment: environmentConfig,
  liff: liffConfig,
  api: apiConfig
}

// Validate configuration on module load
try {
  validateConfig(config)
} catch (error) {
  console.error('Configuration validation failed:', error)
  throw error
}

export * from './types'
export { validateConfig } from './validator'