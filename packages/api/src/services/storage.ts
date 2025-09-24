import { S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand, GetObjectCommandOutput } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'
import { lookup } from 'mime-types'
import { promises as fs } from 'fs'
import { join, dirname } from 'path'
import { config } from '../config'
import type { StorageConfig } from '../config/types'

export interface UploadOptions {
  folder?: string
  filename?: string
  contentType?: string
  metadata?: Record<string, string>
}

export interface UploadResult {
  url: string
  key: string
  cdnUrl?: string
}

export interface PresignedUrlOptions {
  expiresIn?: number // seconds
  contentType?: string
  metadata?: Record<string, string>
}

export class StorageService {
  private s3Client?: S3Client
  private storageConfig: StorageConfig

  constructor() {
    this.storageConfig = config.storage
    this.initializeClient()

    // Log storage provider initialization
    console.log(`Storage service initialized with provider: ${this.storageConfig.provider}`)
  }

  private initializeClient() {
    if (this.storageConfig.provider === 'spaces') {
      const spacesConfig = this.storageConfig.spaces!
      this.s3Client = new S3Client({
        endpoint: spacesConfig.endpoint,
        region: spacesConfig.region,
        credentials: {
          accessKeyId: spacesConfig.accessKeyId,
          secretAccessKey: spacesConfig.secretAccessKey
        },
        forcePathStyle: false // DigitalOcean Spaces uses virtual-hosted-style URLs
      })
    } else if (this.storageConfig.provider === 's3') {
      const s3Config = this.storageConfig.s3!
      this.s3Client = new S3Client({
        endpoint: s3Config.endpoint,
        region: s3Config.region,
        credentials: {
          accessKeyId: s3Config.accessKeyId,
          secretAccessKey: s3Config.secretAccessKey
        }
      })

      console.log(`S3 client initialized with endpoint: ${s3Config.endpoint || 'default'}, region: ${s3Config.region}, bucket: ${s3Config.bucket}`)
    }
  }

  /**
   * Upload a file buffer to storage
   */
  async uploadBuffer(
    buffer: Buffer,
    originalFilename: string,
    options: UploadOptions = {}
  ): Promise<UploadResult> {
    // Validate file size
    if (buffer.length > this.storageConfig.limits.maxFileSize) {
      throw new Error(`File size exceeds maximum allowed size of ${this.storageConfig.limits.maxFileSize} bytes`)
    }

    // Determine content type
    const contentType = options.contentType || lookup(originalFilename) || 'application/octet-stream'

    // Validate content type
    if (!this.storageConfig.limits.allowedMimeTypes.includes(contentType)) {
      throw new Error(`File type ${contentType} is not allowed`)
    }

    // Generate unique filename
    const timestamp = Date.now()
    const randomString = Math.random().toString(36).substring(2, 8)
    const extension = originalFilename.split('.').pop() || ''
    const filename = options.filename || `${timestamp}_${randomString}.${extension}`

    // Create storage key
    const folder = options.folder || 'uploads'
    const key = `${folder}/${filename}`

    switch (this.storageConfig.provider) {
      case 'spaces':
      case 's3':
        return this.uploadToS3(buffer, key, contentType, options.metadata)

      case 'local':
        return this.uploadToLocal(buffer, key, contentType)

      default:
        throw new Error(`Unsupported storage provider: ${this.storageConfig.provider}`)
    }
  }

  /**
   * Upload file stream to S3-compatible storage
   */
  private async uploadToS3(
    buffer: Buffer,
    key: string,
    contentType: string,
    metadata?: Record<string, string>
  ): Promise<UploadResult> {
    if (!this.s3Client) {
      throw new Error('S3 client not initialized')
    }

    const bucket = this.storageConfig.provider === 'spaces'
      ? this.storageConfig.spaces!.bucket
      : this.storageConfig.s3!.bucket

    console.log(`Uploading to S3: bucket=${bucket}, key=${key}, contentType=${contentType}`)

    const command = new PutObjectCommand({
      Bucket: bucket,
      Key: key,
      Body: buffer,
      ContentType: contentType,
      Metadata: metadata,
      ACL: 'public-read' // Make files publicly accessible
    })

    try {
      await this.s3Client.send(command)
      console.log(`Successfully uploaded to S3: ${key}`)
    } catch (error) {
      console.error(`Failed to upload to S3: ${key}`, error)
      throw error
    }

    // Generate public URL
    let url: string
    let cdnUrl: string | undefined

    if (this.storageConfig.provider === 'spaces') {
      const { endpoint, region } = this.storageConfig.spaces!
      url = `${endpoint}/${bucket}/${key}`
      cdnUrl = this.storageConfig.spaces!.cdnUrl
        ? `${this.storageConfig.spaces!.cdnUrl}/${key}`
        : undefined
    } else {
      const { region } = this.storageConfig.s3!
      url = `https://${bucket}.s3.${region}.amazonaws.com/${key}`
    }

    return { url, key, cdnUrl }
  }

  /**
   * Upload to local storage
   */
  private async uploadToLocal(
    buffer: Buffer,
    key: string,
    contentType: string
  ): Promise<UploadResult> {
    const { uploadPath, baseUrl } = this.storageConfig.local!
    const filePath = join(uploadPath, key)

    // Ensure directory exists
    await fs.mkdir(dirname(filePath), { recursive: true })

    // Write file
    await fs.writeFile(filePath, buffer)

    const url = `${baseUrl}/${key}`
    return { url, key }
  }

  /**
   * Generate presigned URL for direct upload
   */
  async generatePresignedUploadUrl(
    key: string,
    options: PresignedUrlOptions = {}
  ): Promise<string> {
    if (this.storageConfig.provider === 'local') {
      throw new Error('Presigned URLs not supported for local storage')
    }

    if (!this.s3Client) {
      throw new Error('S3 client not initialized')
    }

    const bucket = this.storageConfig.provider === 'spaces'
      ? this.storageConfig.spaces!.bucket
      : this.storageConfig.s3!.bucket

    const command = new PutObjectCommand({
      Bucket: bucket,
      Key: key,
      ContentType: options.contentType,
      Metadata: options.metadata,
      ACL: 'public-read'
    })

    return getSignedUrl(this.s3Client, command, {
      expiresIn: options.expiresIn || 3600 // 1 hour default
    })
  }

  /**
   * Generate presigned URL for download
   */
  async generatePresignedDownloadUrl(
    key: string,
    expiresIn: number = 3600
  ): Promise<string> {
    if (this.storageConfig.provider === 'local') {
      // For local storage, return direct URL
      const { baseUrl } = this.storageConfig.local!
      return `${baseUrl}/${key}`
    }

    if (!this.s3Client) {
      throw new Error('S3 client not initialized')
    }

    const bucket = this.storageConfig.provider === 'spaces'
      ? this.storageConfig.spaces!.bucket
      : this.storageConfig.s3!.bucket

    const command = new GetObjectCommand({
      Bucket: bucket,
      Key: key
    })

    return getSignedUrl(this.s3Client, command, { expiresIn })
  }

  /**
   * Delete file from storage
   */
  async deleteFile(key: string): Promise<void> {
    switch (this.storageConfig.provider) {
      case 'spaces':
      case 's3':
        await this.deleteFromS3(key)
        break

      case 'local':
        await this.deleteFromLocal(key)
        break

      default:
        throw new Error(`Unsupported storage provider: ${this.storageConfig.provider}`)
    }
  }

  /**
   * Delete file from S3-compatible storage
   */
  private async deleteFromS3(key: string): Promise<void> {
    if (!this.s3Client) {
      throw new Error('S3 client not initialized')
    }

    const bucket = this.storageConfig.provider === 'spaces'
      ? this.storageConfig.spaces!.bucket
      : this.storageConfig.s3!.bucket

    const command = new DeleteObjectCommand({
      Bucket: bucket,
      Key: key
    })

    await this.s3Client.send(command)
  }

  /**
   * Delete file from local storage
   */
  private async deleteFromLocal(key: string): Promise<void> {
    const { uploadPath } = this.storageConfig.local!
    const filePath = join(uploadPath, key)

    try {
      await fs.unlink(filePath)
    } catch (error: any) {
      if (error.code !== 'ENOENT') {
        throw error
      }
      // File doesn't exist, which is fine for delete operation
    }
  }

  /**
   * Get file buffer from storage
   */
  async getFileBuffer(key: string): Promise<Buffer> {
    switch (this.storageConfig.provider) {
      case 'spaces':
      case 's3':
        return this.getBufferFromS3(key)

      case 'local':
        return this.getBufferFromLocal(key)

      default:
        throw new Error(`Unsupported storage provider: ${this.storageConfig.provider}`)
    }
  }

  /**
   * Get file buffer from S3-compatible storage
   */
  private async getBufferFromS3(key: string): Promise<Buffer> {
    if (!this.s3Client) {
      throw new Error('S3 client not initialized')
    }

    const bucket = this.storageConfig.provider === 'spaces'
      ? this.storageConfig.spaces!.bucket
      : this.storageConfig.s3!.bucket

    const command = new GetObjectCommand({
      Bucket: bucket,
      Key: key
    })

    const response: GetObjectCommandOutput = await this.s3Client.send(command)

    if (!response.Body) {
      throw new Error(`File not found: ${key}`)
    }

    // Convert stream to buffer
    const chunks: Uint8Array[] = []
    const reader = response.Body.transformToWebStream().getReader()

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        chunks.push(value)
      }
    } finally {
      reader.releaseLock()
    }

    return Buffer.concat(chunks)
  }

  /**
   * Get file buffer from local storage
   */
  private async getBufferFromLocal(key: string): Promise<Buffer> {
    const { uploadPath } = this.storageConfig.local!
    const filePath = join(uploadPath, key)
    return fs.readFile(filePath)
  }

  /**
   * Check if file exists
   */
  async fileExists(key: string): Promise<boolean> {
    try {
      switch (this.storageConfig.provider) {
        case 'spaces':
        case 's3':
          if (!this.s3Client) return false

          const bucket = this.storageConfig.provider === 'spaces'
            ? this.storageConfig.spaces!.bucket
            : this.storageConfig.s3!.bucket

          const command = new GetObjectCommand({
            Bucket: bucket,
            Key: key
          })

          await this.s3Client.send(command)
          return true

        case 'local':
          const { uploadPath } = this.storageConfig.local!
          const filePath = join(uploadPath, key)
          await fs.access(filePath)
          return true

        default:
          return false
      }
    } catch {
      return false
    }
  }
}

// Export singleton instance
export const storageService = new StorageService()