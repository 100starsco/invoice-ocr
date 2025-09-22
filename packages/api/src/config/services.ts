import type { ServiceConfig } from './types'

export const serviceConfig: ServiceConfig = {
  ocrServiceUrl: process.env.OCR_SERVICE_URL || 'http://localhost:8001'
}