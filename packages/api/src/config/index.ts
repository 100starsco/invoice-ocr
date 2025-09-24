import { environmentConfig } from './environment'
import { serverConfig } from './server'
import { lineConfig } from './line'
import { databaseConfig } from './database'
import { queueConfig } from './queue'
import { serviceConfig } from './services'
import { storageConfig } from './storage'
import { validateConfig } from './validator'
import type { ApiConfig } from './types'

export const config: ApiConfig = {
  environment: environmentConfig,
  server: serverConfig,
  line: lineConfig,
  database: databaseConfig,
  queue: queueConfig,
  services: serviceConfig,
  storage: storageConfig
}

// Validate configuration on module load
try {
  validateConfig(config)
} catch (error) {
  console.error('Configuration validation failed:', error)
  process.exit(1)
}

export * from './types'
export { validateConfig } from './validator'