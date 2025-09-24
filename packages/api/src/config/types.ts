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

export interface QueueConfig {
  redis: {
    host: string
    port: number
    password?: string
    db: number
  }
  queues: {
    imageProcessing: string
    ocrRequest: string
    notification: string
  }
  defaultJobOptions: {
    removeOnComplete: number
    removeOnFail: number
    attempts: number
    backoff: {
      type: 'exponential'
      delay: number
    }
  }
  concurrency: {
    imageProcessing: number
    ocrRequest: number
    notification: number
  }
  dashboard: {
    enabled: boolean
    path: string
  }
}

export interface StorageConfig {
  provider: 'spaces' | 's3' | 'local'
  spaces?: {
    endpoint: string
    region: string
    accessKeyId: string
    secretAccessKey: string
    bucket: string
    cdnUrl?: string
  }
  s3?: {
    endpoint?: string
    region: string
    accessKeyId: string
    secretAccessKey: string
    bucket: string
  }
  local?: {
    uploadPath: string
    baseUrl: string
  }
  limits: {
    maxFileSize: number // in bytes
    allowedMimeTypes: string[]
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
  queue: QueueConfig
  services: ServiceConfig
  storage: StorageConfig
}