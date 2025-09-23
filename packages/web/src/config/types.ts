export interface LiffConfig {
  liffId: string
  channelId: string
}

export interface ApiConfig {
  baseUrl: string
  timeout: number
}

export interface EnvironmentConfig {
  nodeEnv: 'development' | 'staging' | 'production' | 'test'
  isProduction: boolean
  isDevelopment: boolean
}

export interface WebConfig {
  environment: EnvironmentConfig
  liff: LiffConfig
  api: ApiConfig
}