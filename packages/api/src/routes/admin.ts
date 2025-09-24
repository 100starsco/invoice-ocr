import { Hono } from 'hono'
import { bearerAuth } from 'hono/bearer-auth'
import { AdminAuthService } from '../services/admin-auth'
import { UserService } from '../services/user'
import { MessageService } from '../services/message'
import type { LoginCredentials, AdminUser } from '../services/admin-auth'

type AdminVariables = {
  adminUser: AdminUser
}

const admin = new Hono<{ Variables: AdminVariables }>()

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

// User management endpoints
admin.use('/users*', authMiddleware)

admin.get('/users', async (c) => {
  try {
    const limit = parseInt(c.req.query('limit') || '20')
    const offset = parseInt(c.req.query('offset') || '0')
    const search = c.req.query('search')
    const isFollowing = c.req.query('isFollowing')
    const sortBy = c.req.query('sortBy') as 'displayName' | 'lastSeenAt' | 'firstSeenAt' | 'lastMessageAt' || 'lastSeenAt'
    const sortOrder = c.req.query('sortOrder') as 'asc' | 'desc' || 'desc'

    const options = {
      limit: Math.min(limit, 100), // Max 100 per request
      offset,
      search,
      isFollowing: isFollowing ? isFollowing === 'true' : undefined,
      sortBy,
      sortOrder
    }

    const result = await UserService.listUsers(options)

    return c.json({
      success: true,
      data: result
    })
  } catch (error) {
    console.error('Error listing users:', error)
    return c.json({
      error: error instanceof Error ? error.message : 'Failed to list users'
    }, 500)
  }
})

admin.get('/users/:userId', async (c) => {
  try {
    const userId = c.req.param('userId')

    if (!userId) {
      return c.json({ error: 'User ID is required' }, 400)
    }

    const user = await UserService.getUserStats(userId)

    if (!user) {
      return c.json({ error: 'User not found' }, 404)
    }

    return c.json({
      success: true,
      data: { user }
    })
  } catch (error) {
    console.error('Error getting user:', error)
    return c.json({
      error: error instanceof Error ? error.message : 'Failed to get user'
    }, 500)
  }
})

admin.get('/users/search/:query', async (c) => {
  try {
    const query = c.req.param('query')
    const limit = parseInt(c.req.query('limit') || '10')

    if (!query) {
      return c.json({ error: 'Search query is required' }, 400)
    }

    const users = await UserService.searchUsers(query, Math.min(limit, 50))

    return c.json({
      success: true,
      data: { users }
    })
  } catch (error) {
    console.error('Error searching users:', error)
    return c.json({
      error: error instanceof Error ? error.message : 'Failed to search users'
    }, 500)
  }
})

// Message management endpoints
admin.use('/messages*', authMiddleware)

admin.get('/messages', async (c) => {
  try {
    const limit = parseInt(c.req.query('limit') || '20')
    const offset = parseInt(c.req.query('offset') || '0')
    const userId = c.req.query('userId')
    const messageType = c.req.query('messageType')
    const dateFrom = c.req.query('dateFrom') ? new Date(c.req.query('dateFrom')!) : undefined
    const dateTo = c.req.query('dateTo') ? new Date(c.req.query('dateTo')!) : undefined
    const sortBy = c.req.query('sortBy') as 'sentAt' | 'receivedAt' | 'createdAt' || 'sentAt'
    const sortOrder = c.req.query('sortOrder') as 'asc' | 'desc' || 'desc'

    const options = {
      limit: Math.min(limit, 100), // Max 100 per request
      offset,
      userId,
      messageType,
      dateFrom,
      dateTo,
      sortBy,
      sortOrder
    }

    const result = await MessageService.listMessages(options)

    return c.json({
      success: true,
      data: result
    })
  } catch (error) {
    console.error('Error listing messages:', error)
    return c.json({
      error: error instanceof Error ? error.message : 'Failed to list messages'
    }, 500)
  }
})

admin.get('/messages/:messageId', async (c) => {
  try {
    const messageId = c.req.param('messageId')

    if (!messageId) {
      return c.json({ error: 'Message ID is required' }, 400)
    }

    const message = await MessageService.getMessageById(messageId)

    if (!message) {
      return c.json({ error: 'Message not found' }, 404)
    }

    return c.json({
      success: true,
      data: { message }
    })
  } catch (error) {
    console.error('Error getting message:', error)
    return c.json({
      error: error instanceof Error ? error.message : 'Failed to get message'
    }, 500)
  }
})

admin.get('/users/:userId/messages', async (c) => {
  try {
    const userId = c.req.param('userId')
    const limit = parseInt(c.req.query('limit') || '20')
    const offset = parseInt(c.req.query('offset') || '0')
    const messageType = c.req.query('messageType')
    const dateFrom = c.req.query('dateFrom') ? new Date(c.req.query('dateFrom')!) : undefined
    const dateTo = c.req.query('dateTo') ? new Date(c.req.query('dateTo')!) : undefined
    const sortBy = c.req.query('sortBy') as 'sentAt' | 'receivedAt' | 'createdAt' || 'sentAt'
    const sortOrder = c.req.query('sortOrder') as 'asc' | 'desc' || 'desc'

    if (!userId) {
      return c.json({ error: 'User ID is required' }, 400)
    }

    const options = {
      limit: Math.min(limit, 100),
      offset,
      messageType,
      dateFrom,
      dateTo,
      sortBy,
      sortOrder
    }

    const result = await MessageService.getMessagesByUser(userId, options)

    return c.json({
      success: true,
      data: result
    })
  } catch (error) {
    console.error('Error getting user messages:', error)
    return c.json({
      error: error instanceof Error ? error.message : 'Failed to get user messages'
    }, 500)
  }
})

// Dashboard stats endpoints
admin.get('/stats/messages', async (c) => {
  try {
    const stats = await MessageService.getMessageStats()

    return c.json({
      success: true,
      data: { stats }
    })
  } catch (error) {
    console.error('Error getting message stats:', error)
    return c.json({
      error: error instanceof Error ? error.message : 'Failed to get message stats'
    }, 500)
  }
})

admin.get('/activity/recent', async (c) => {
  try {
    const limit = parseInt(c.req.query('limit') || '10')
    const activity = await MessageService.getRecentActivity(Math.min(limit, 50))

    return c.json({
      success: true,
      data: { activity }
    })
  } catch (error) {
    console.error('Error getting recent activity:', error)
    return c.json({
      error: error instanceof Error ? error.message : 'Failed to get recent activity'
    }, 500)
  }
})

export { admin }