import { Hono } from 'hono'
import { streamToBuffer } from 'node:stream/consumers'
import { storageService } from '../services/storage'

export const liff = new Hono()

// Handle CORS preflight requests
liff.options('/*', (c) => {
  return c.text('', 204, {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400'
  })
})

/**
 * Upload image from LIFF app with user-specific storage path
 * POST /api/liff/upload-image
 */
liff.post('/upload-image', async (c) => {
  console.log('=== LIFF Upload Request Received ===')
  console.log('Method:', c.req.method)
  console.log('URL:', c.req.url)
  console.log('Headers:', Object.fromEntries(c.req.header()))
  console.log('Content-Type:', c.req.header('content-type'))

  try {
    // Parse form data
    console.log('Attempting to parse FormData...')
    const formData = await c.req.formData()
    console.log('FormData parsed successfully')

    const imageFile = formData.get('image') as File
    const userId = formData.get('userId') as string

    console.log('FormData contents:', {
      imageFile: imageFile ? {
        name: imageFile.name,
        type: imageFile.type,
        size: imageFile.size
      } : null,
      userId: userId,
      allKeys: Array.from(formData.keys())
    })

    // Validation
    if (!imageFile) {
      console.log('ERROR: No image file provided')
      return c.json({ error: 'No image file provided' }, 400)
    }

    if (!userId) {
      console.log('ERROR: User ID is required')
      return c.json({ error: 'User ID is required' }, 400)
    }

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if (!allowedTypes.includes(imageFile.type)) {
      return c.json({
        error: 'Invalid file type. Only JPEG, PNG, and WebP images are allowed'
      }, 400)
    }

    // Convert file to buffer
    const arrayBuffer = await imageFile.arrayBuffer()
    const buffer = Buffer.from(arrayBuffer)

    // Generate filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const extension = imageFile.name.split('.').pop() || 'jpg'
    const filename = `invoice_${timestamp}.${extension}`

    // Upload with user-specific path: liff/capture/{user_line_id}/filename
    const uploadResult = await storageService.uploadBuffer(buffer, filename, {
      folder: `liff/capture/${userId}`,
      filename: filename,
      contentType: imageFile.type,
      metadata: {
        originalName: imageFile.name,
        userId: userId,
        uploadedAt: new Date().toISOString(),
        source: 'liff_camera_capture'
      }
    })

    console.log(`Image uploaded for user ${userId}:`, {
      key: uploadResult.key,
      url: uploadResult.url,
      size: buffer.length
    })

    return c.json({
      success: true,
      url: uploadResult.cdnUrl || uploadResult.url, // Use CDN URL if available
      key: uploadResult.key,
      filename: filename,
      size: buffer.length
    })

  } catch (error: any) {
    console.error('LIFF image upload error:', error)

    // Handle specific errors
    if (error.message.includes('File size exceeds')) {
      return c.json({ error: 'File size too large' }, 413)
    }

    if (error.message.includes('not allowed')) {
      return c.json({ error: 'File type not allowed' }, 415)
    }

    return c.json({
      error: 'Failed to upload image',
      message: error.message
    }, 500)
  }
})

/**
 * Health check for LIFF endpoints
 * GET /api/liff/health
 */
liff.get('/health', (c) => {
  return c.json({
    status: 'healthy',
    service: 'liff-api',
    timestamp: new Date().toISOString()
  })
})