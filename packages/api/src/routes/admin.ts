import { Hono } from 'hono'
import { bearerAuth } from 'hono/bearer-auth'
import { AdminAuthService } from '../services/admin-auth'
import type { LoginCredentials } from '../services/admin-auth'

const admin = new Hono()

// Bearer auth middleware for protected routes
const authMiddleware = bearerAuth({
  verifyToken: async (token, c) => {
    try {
      const user = await AdminAuthService.verifyToken(token)
      c.set('adminUser', user)
      return true
    } catch (error) {
      return false
    }
  }
})

// Public routes
admin.post('/login', async (c) => {
  try {
    const body = await c.req.json<LoginCredentials>()

    if (!body.email || !body.password) {
      return c.json({ error: 'Email and password are required' }, 400)
    }

    const loginResponse = await AdminAuthService.login(body)

    return c.json({
      success: true,
      data: loginResponse
    })
  } catch (error) {
    console.error('Admin login error:', error)
    return c.json({
      error: error instanceof Error ? error.message : 'Login failed'
    }, 401)
  }
})

// Protected routes (require bearer token)
admin.use('/logout', authMiddleware)
admin.post('/logout', async (c) => {
  // For JWT tokens, logout is handled client-side by removing the token
  // Here we can add token blacklisting if needed in the future
  return c.json({
    success: true,
    message: 'Logged out successfully'
  })
})

admin.use('/me', authMiddleware)
admin.get('/me', async (c) => {
  const adminUser = c.get('adminUser')

  return c.json({
    success: true,
    data: {
      user: adminUser
    }
  })
})

export { admin }