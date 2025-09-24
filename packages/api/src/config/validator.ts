import type { ApiConfig } from './types'

export function validateEnvVar(name: string, value: string | undefined, required = true): string {
  if (required && !value) {
    throw new Error(`Environment variable ${name} is required but not set`)
  }
  return value || ''
}

export function validatePort(value: string | undefined, defaultPort: number): number {
  if (!value) return defaultPort

  const port = parseInt(value, 10)
  if (isNaN(port) || port < 1 || port > 65535) {
    throw new Error(`Invalid port number: ${value}`)
  }
  return port
}

export function validateUrl(name: string, value: string | undefined, required = true): string {
  const url = validateEnvVar(name, value, required)

  if (url && required) {
    try {
      new URL(url)
    } catch {
      throw new Error(`Invalid URL for ${name}: ${url}`)
    }
  }

  return url
}

export function validateConfig(config: ApiConfig): void {
  // Validate LINE configuration
  if (!config.line.channelSecret) {
    throw new Error('LINE_CHANNEL_SECRET is required')
  }
  if (!config.line.channelAccessToken) {
    throw new Error('LINE_CHANNEL_ACCESS_TOKEN is required')
  }

  // Validate database URLs
  validateUrl('DATABASE_URL', config.database.postgresql.url)
  validateUrl('MONGODB_URI', config.database.mongodb.uri)
  validateUrl('REDIS_URL', config.database.redis.url)

  // Validate queue configuration
  if (!config.queue.redis.host) {
    throw new Error('Queue Redis host is required')
  }
  if (config.queue.redis.port < 1 || config.queue.redis.port > 65535) {
    throw new Error(`Invalid queue Redis port: ${config.queue.redis.port}`)
  }
  if (config.queue.redis.db < 0) {
    throw new Error(`Invalid queue Redis DB: ${config.queue.redis.db}`)
  }

  // Validate queue names
  if (!config.queue.queues.imageProcessing) {
    throw new Error('Image processing queue name is required')
  }
  if (!config.queue.queues.ocrRequest) {
    throw new Error('OCR request queue name is required')
  }
  if (!config.queue.queues.notification) {
    throw new Error('Notification queue name is required')
  }

  // Validate concurrency settings
  if (config.queue.concurrency.imageProcessing < 1) {
    throw new Error('Image processing concurrency must be positive')
  }
  if (config.queue.concurrency.ocrRequest < 1) {
    throw new Error('OCR request concurrency must be positive')
  }
  if (config.queue.concurrency.notification < 1) {
    throw new Error('Notification concurrency must be positive')
  }

  // Validate service URLs
  validateUrl('OCR_SERVICE_URL', config.services.ocrServiceUrl)

  // Validate storage configuration
  validateStorageConfig(config.storage)

  // Validate server config
  if (config.server.port < 1 || config.server.port > 65535) {
    throw new Error(`Invalid server port: ${config.server.port}`)
  }
}

function validateStorageConfig(storage: any): void {
  if (!storage.provider) {
    throw new Error('STORAGE_PROVIDER is required')
  }

  if (!['spaces', 's3', 'local'].includes(storage.provider)) {
    throw new Error(`Invalid storage provider: ${storage.provider}. Must be 'spaces', 's3', or 'local'`)
  }

  switch (storage.provider) {
    case 'spaces':
      if (!storage.spaces?.endpoint) {
        throw new Error('DO_SPACES_ENDPOINT is required when using spaces storage')
      }
      if (!storage.spaces?.accessKeyId) {
        throw new Error('DO_SPACES_ACCESS_KEY_ID is required when using spaces storage')
      }
      if (!storage.spaces?.secretAccessKey) {
        throw new Error('DO_SPACES_SECRET_ACCESS_KEY is required when using spaces storage')
      }
      if (!storage.spaces?.bucket) {
        throw new Error('DO_SPACES_BUCKET is required when using spaces storage')
      }
      break

    case 's3':
      if (!storage.s3?.accessKeyId) {
        throw new Error('S3_ACCESS_KEY_ID is required when using S3 storage')
      }
      if (!storage.s3?.secretAccessKey) {
        throw new Error('S3_SECRET_ACCESS_KEY is required when using S3 storage')
      }
      if (!storage.s3?.bucket) {
        throw new Error('S3_BUCKET is required when using S3 storage')
      }
      if (storage.s3?.endpoint) {
        try {
          new URL(storage.s3.endpoint)
        } catch {
          throw new Error(`Invalid S3 endpoint URL: ${storage.s3.endpoint}`)
        }
      }
      break

    case 'local':
      if (!storage.local?.uploadPath) {
        throw new Error('LOCAL_UPLOAD_PATH is required when using local storage')
      }
      if (!storage.local?.baseUrl) {
        throw new Error('LOCAL_BASE_URL is required when using local storage')
      }
      break
  }

  // Validate storage limits
  if (storage.limits?.maxFileSize && storage.limits.maxFileSize < 1) {
    throw new Error('MAX_FILE_SIZE must be positive')
  }

  if (storage.limits?.allowedMimeTypes && !Array.isArray(storage.limits.allowedMimeTypes)) {
    throw new Error('ALLOWED_MIME_TYPES must be a comma-separated list')
  }
}