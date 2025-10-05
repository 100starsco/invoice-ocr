/**
 * OCR Service Client
 *
 * HTTP client for communicating with the Python OCR service.
 */

import { config } from '../config'
import { getApiKeyHeader } from '../middleware/service-auth'

export interface OCRJobRequest {
  image_url: string
  user_id: string
  message_id: string
  webhook_url: string
}

export interface OCRJobResponse {
  job_id: string
  status: string
  estimated_time: number
}

export interface OCRJobStatus {
  job_id: string
  status: string
  progress?: number
  result?: any
  error?: string
}

export class OCRServiceClient {
  private readonly baseUrl: string
  private readonly timeout: number

  constructor() {
    this.baseUrl = process.env.OCR_SERVICE_URL || 'http://localhost:8001'
    this.timeout = parseInt(process.env.OCR_SERVICE_TIMEOUT || '30000')
  }

  /**
   * Submit an invoice processing job to the OCR service
   */
  async processInvoice(
    imageUrl: string,
    userId: string,
    messageId: string
  ): Promise<string> {
    const webhookUrl = `${this.getApiBaseUrl()}/api/webhooks/ocr`

    const requestData: OCRJobRequest = {
      image_url: imageUrl,
      user_id: userId,
      message_id: messageId,
      webhook_url: webhookUrl
    }

    try {
      const response = await this.makeRequest('POST', '/api/v1/jobs/process-invoice', requestData)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(`OCR service error (${response.status}): ${errorData.detail || response.statusText}`)
      }

      const result: OCRJobResponse = await response.json()

      console.log(`OCR job created: ${result.job_id} (estimated ${result.estimated_time}s)`)
      return result.job_id

    } catch (error) {
      console.error('Failed to submit OCR job:', error)
      throw new Error(`Failed to submit OCR job: ${error.message}`)
    }
  }

  /**
   * Get the status of a specific job (optional - mainly for debugging)
   */
  async getJobStatus(jobId: string): Promise<OCRJobStatus> {
    try {
      const response = await this.makeRequest('GET', `/api/v1/jobs/${jobId}/status`)

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Job not found')
        }
        const errorData = await response.json().catch(() => ({}))
        throw new Error(`OCR service error (${response.status}): ${errorData.detail || response.statusText}`)
      }

      return await response.json()

    } catch (error) {
      console.error(`Failed to get job status for ${jobId}:`, error)
      throw new Error(`Failed to get job status: ${error.message}`)
    }
  }

  /**
   * List all jobs (for debugging/monitoring)
   */
  async listJobs(): Promise<any> {
    try {
      const response = await this.makeRequest('GET', '/api/v1/jobs')

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(`OCR service error (${response.status}): ${errorData.detail || response.statusText}`)
      }

      return await response.json()

    } catch (error) {
      console.error('Failed to list jobs:', error)
      throw new Error(`Failed to list jobs: ${error.message}`)
    }
  }

  /**
   * Check if OCR service is healthy
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.makeRequest('GET', '/health')
      return response.ok
    } catch (error) {
      console.error('OCR service health check failed:', error)
      return false
    }
  }

  /**
   * Make HTTP request to OCR service
   */
  private async makeRequest(
    method: string,
    path: string,
    body?: any
  ): Promise<Response> {
    const url = `${this.baseUrl}${path}`

    // Combine headers with API key authentication
    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'Invoice-OCR-API/1.0',
      ...getApiKeyHeader() // Add API key authentication
    }

    const options: RequestInit = {
      method,
      headers,
      signal: AbortSignal.timeout(this.timeout)
    }

    if (body && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(body)
    }

    return fetch(url, options)
  }

  /**
   * Get the base URL for this API service (for webhook callbacks)
   */
  private getApiBaseUrl(): string {
    return process.env.API_BASE_URL ||
           process.env.API_URL ||
           'http://localhost:3000'
  }
}

// Export singleton instance
export const ocrServiceClient = new OCRServiceClient()