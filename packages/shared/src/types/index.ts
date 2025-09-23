export interface HealthCheck {
  status: 'healthy' | 'unhealthy'
  service: string
  timestamp: string
}

export * from './line'