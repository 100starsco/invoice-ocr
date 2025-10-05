import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { StorageService } from '../services/storage'

const images = new Hono()

// Enable CORS for image requests
images.use('/*', cors())

// Image proxy endpoint for OCR service to access DigitalOcean Spaces images
images.get('/proxy/*', async (c) => {
  try {
    // Extract the full key path from the URL - remove /api/images/proxy/ prefix
    const urlPath = c.req.path
    console.log(`Image proxy full URL path: ${urlPath}`)

    // Remove the /api/images/proxy/ prefix to get the actual file key
    const proxyPrefix = '/api/images/proxy/'
    let fullPath = urlPath
    if (urlPath.startsWith(proxyPrefix)) {
      fullPath = urlPath.substring(proxyPrefix.length)
    }

    console.log(`Image proxy request for key: ${fullPath}`)

    // Initialize storage service
    const storage = new StorageService()

    // Get image stream from DigitalOcean Spaces
    const imageStream = await storage.getImageStream(fullPath)

    // Get content type based on file extension
    const extension = fullPath.toLowerCase().split('.').pop()
    let contentType = 'application/octet-stream'

    switch (extension) {
      case 'jpg':
      case 'jpeg':
        contentType = 'image/jpeg'
        break
      case 'png':
        contentType = 'image/png'
        break
      case 'gif':
        contentType = 'image/gif'
        break
      case 'webp':
        contentType = 'image/webp'
        break
    }

    // Set appropriate headers
    c.header('Content-Type', contentType)
    c.header('Cache-Control', 'public, max-age=3600') // Cache for 1 hour
    c.header('Access-Control-Allow-Origin', '*')

    // Return the image stream
    return new Response(imageStream, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=3600',
        'Access-Control-Allow-Origin': '*'
      }
    })

  } catch (error) {
    console.error('Image proxy error:', error)
    return c.json({ error: 'Image not found or access denied' }, 404)
  }
})

// Health check for image service
images.get('/health', (c) => {
  return c.json({ status: 'ok', service: 'image-proxy' })
})

export { images }