export interface LiffConfig {
  liffId: string
  channelId: string
}

export interface ApiConfig {
  baseUrl: string
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