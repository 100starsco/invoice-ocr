import type { StorageConfig } from './types'

export const storageConfig: StorageConfig = {
  provider: (process.env.STORAGE_PROVIDER as 'spaces' | 's3' | 'local') || 'local',

  spaces: {
    endpoint: process.env.DO_SPACES_ENDPOINT || '',
    region: process.env.DO_SPACES_REGION || 'sgp1',
    accessKeyId: process.env.DO_SPACES_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.DO_SPACES_SECRET_ACCESS_KEY || '',
    bucket: process.env.DO_SPACES_BUCKET || '',
    cdnUrl: process.env.DO_SPACES_CDN_URL
  },

  s3: {
    endpoint: process.env.S3_ENDPOINT,
    region: process.env.S3_REGION || 'auto', // Default to 'auto' for R2 compatibility
    accessKeyId: process.env.S3_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.S3_SECRET_ACCESS_KEY || '',
    bucket: process.env.S3_BUCKET || ''
  },

  local: {
    uploadPath: process.env.LOCAL_UPLOAD_PATH || './uploads',
    baseUrl: process.env.LOCAL_BASE_URL || 'http://localhost:3000/uploads'
  },

  limits: {
    maxFileSize: parseInt(process.env.MAX_FILE_SIZE || '52428800'), // 50MB default (increased for invoice images)
    allowedMimeTypes: process.env.ALLOWED_MIME_TYPES
      ? process.env.ALLOWED_MIME_TYPES.split(',').map(type => type.trim())
      : ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
  }
}