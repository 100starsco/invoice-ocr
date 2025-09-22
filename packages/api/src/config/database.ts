import type { DatabaseConfig } from './types'

export const databaseConfig: DatabaseConfig = {
  postgresql: {
    url: process.env.DATABASE_URL || 'postgresql://user:password@localhost:5432/invoice_db'
  },
  mongodb: {
    uri: process.env.MONGODB_URI || 'mongodb://localhost:27017/ocr_results'
  },
  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379'
  }
}