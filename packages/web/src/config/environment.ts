import type { EnvironmentConfig } from './types'

const nodeEnv = (import.meta.env.VITE_ENV || 'development') as EnvironmentConfig['nodeEnv']

export const environmentConfig: EnvironmentConfig = {
  nodeEnv,
  isProduction: nodeEnv === 'production',
  isDevelopment: nodeEnv === 'development'
}