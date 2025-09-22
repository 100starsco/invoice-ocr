import type { ApiConfig } from './types'

export const apiConfig: ApiConfig = {
  baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:3000'
}