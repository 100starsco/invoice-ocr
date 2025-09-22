export interface LineConfig {
  channelSecret: string
  channelAccessToken: string
  webhookPath: string
}

export interface DatabaseConfig {
  postgresql: {
    url: string
  }
  mongodb: {
    uri: string
  }
  redis: {
    url: string
  }
}

export interface ServiceConfig {
  ocrServiceUrl: string
}

export interface ServerConfig {
  port: number
  host: string
}

export interface EnvironmentConfig {
  nodeEnv: 'development' | 'staging' | 'production' | 'test'
  isProduction: boolean
  isDevelopment: boolean
}

export interface ApiConfig {
  environment: EnvironmentConfig
  server: ServerConfig
  line: LineConfig
  database: DatabaseConfig
  services: ServiceConfig
}