import { db } from '../db'
import { lineUsers } from '../db/schema'
import { eq, desc, asc, and, ilike, count } from 'drizzle-orm'

export interface UserListOptions {
  limit?: number
  offset?: number
  search?: string
  isFollowing?: boolean
  sortBy?: 'displayName' | 'lastSeenAt' | 'firstSeenAt' | 'lastMessageAt'
  sortOrder?: 'asc' | 'desc'
}

export interface PaginatedUsers {
  users: typeof lineUsers.$inferSelect[]
  total: number
  limit: number
  offset: number
  hasMore: boolean
}

export class UserService {
  static async listUsers(options: UserListOptions = {}): Promise<PaginatedUsers> {
    const {
      limit = 20,
      offset = 0,
      search,
      isFollowing,
      sortBy = 'lastSeenAt',
      sortOrder = 'desc'
    } = options

    // Build WHERE conditions
    const conditions = []

    if (search) {
      conditions.push(
        ilike(lineUsers.displayName, `%${search}%`)
      )
    }

    if (typeof isFollowing === 'boolean') {
      conditions.push(eq(lineUsers.isFollowing, isFollowing))
    }

    const whereClause = conditions.length > 0 ? and(...conditions) : undefined

    // Build ORDER BY clause
    const orderBy = sortOrder === 'desc'
      ? desc(lineUsers[sortBy])
      : asc(lineUsers[sortBy])

    // Get total count
    const [{ total }] = await db
      .select({ total: count() })
      .from(lineUsers)
      .where(whereClause)

    // Get users with pagination
    const users = await db
      .select()
      .from(lineUsers)
      .where(whereClause)
      .orderBy(orderBy)
      .limit(limit)
      .offset(offset)

    return {
      users,
      total,
      limit,
      offset,
      hasMore: offset + limit < total
    }
  }

  static async getUserById(userId: string): Promise<typeof lineUsers.$inferSelect | null> {
    const [user] = await db
      .select()
      .from(lineUsers)
      .where(eq(lineUsers.userId, userId))
      .limit(1)

    return user || null
  }

  static async getUserStats(userId: string) {
    // Get user with message count and other stats
    const [user] = await db
      .select()
      .from(lineUsers)
      .where(eq(lineUsers.userId, userId))
      .limit(1)

    if (!user) {
      return null
    }

    // Get message count for this user
    const { lineMessages } = await import('../db/schema')
    const [{ messageCount }] = await db
      .select({ messageCount: count() })
      .from(lineMessages)
      .where(eq(lineMessages.userId, userId))

    return {
      ...user,
      messageCount
    }
  }

  static async searchUsers(query: string, limit = 10): Promise<typeof lineUsers.$inferSelect[]> {
    return await db
      .select()
      .from(lineUsers)
      .where(
        and(
          ilike(lineUsers.displayName, `%${query}%`),
          eq(lineUsers.isFollowing, true)
        )
      )
      .orderBy(desc(lineUsers.lastSeenAt))
      .limit(limit)
  }
}