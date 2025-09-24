import { db } from '../db'
import { lineMessages, lineUsers } from '../db/schema'
import { eq, desc, asc, and, gte, lte, count, sql } from 'drizzle-orm'

export interface MessageListOptions {
  limit?: number
  offset?: number
  userId?: string
  messageType?: string
  dateFrom?: Date
  dateTo?: Date
  sortBy?: 'sentAt' | 'receivedAt' | 'createdAt'
  sortOrder?: 'asc' | 'desc'
}

export interface PaginatedMessages {
  messages: Array<typeof lineMessages.$inferSelect & {
    user?: Pick<typeof lineUsers.$inferSelect, 'displayName' | 'pictureUrl'>
  }>
  total: number
  limit: number
  offset: number
  hasMore: boolean
}

export class MessageService {
  static async listMessages(options: MessageListOptions = {}): Promise<PaginatedMessages> {
    const {
      limit = 20,
      offset = 0,
      userId,
      messageType,
      dateFrom,
      dateTo,
      sortBy = 'sentAt',
      sortOrder = 'desc'
    } = options

    // Build WHERE conditions
    const conditions = []

    if (userId) {
      conditions.push(eq(lineMessages.userId, userId))
    }

    if (messageType) {
      conditions.push(eq(lineMessages.messageType, messageType))
    }

    if (dateFrom) {
      conditions.push(gte(lineMessages.sentAt, dateFrom))
    }

    if (dateTo) {
      conditions.push(lte(lineMessages.sentAt, dateTo))
    }

    const whereClause = conditions.length > 0 ? and(...conditions) : undefined

    // Build ORDER BY clause
    const orderBy = sortOrder === 'desc'
      ? desc(lineMessages[sortBy])
      : asc(lineMessages[sortBy])

    // Get total count
    const [{ total }] = await db
      .select({ total: count() })
      .from(lineMessages)
      .where(whereClause)

    // Get messages with user information
    const messages = await db
      .select({
        id: lineMessages.id,
        messageId: lineMessages.messageId,
        messageType: lineMessages.messageType,
        content: lineMessages.content,
        userId: lineMessages.userId,
        eventId: lineMessages.eventId,
        replyToken: lineMessages.replyToken,
        responded: lineMessages.responded,
        responseType: lineMessages.responseType,
        responseJobId: lineMessages.responseJobId,
        sentAt: lineMessages.sentAt,
        receivedAt: lineMessages.receivedAt,
        createdAt: lineMessages.createdAt,
        updatedAt: lineMessages.updatedAt,
        user: {
          displayName: lineUsers.displayName,
          pictureUrl: lineUsers.pictureUrl
        }
      })
      .from(lineMessages)
      .leftJoin(lineUsers, eq(lineMessages.userId, lineUsers.userId))
      .where(whereClause)
      .orderBy(orderBy)
      .limit(limit)
      .offset(offset)

    return {
      messages,
      total,
      limit,
      offset,
      hasMore: offset + limit < total
    }
  }

  static async getMessageById(messageId: string): Promise<(typeof lineMessages.$inferSelect & {
    user?: Pick<typeof lineUsers.$inferSelect, 'displayName' | 'pictureUrl' | 'userId'>
  }) | null> {
    const [message] = await db
      .select({
        id: lineMessages.id,
        messageId: lineMessages.messageId,
        messageType: lineMessages.messageType,
        content: lineMessages.content,
        userId: lineMessages.userId,
        eventId: lineMessages.eventId,
        replyToken: lineMessages.replyToken,
        responded: lineMessages.responded,
        responseType: lineMessages.responseType,
        responseJobId: lineMessages.responseJobId,
        sentAt: lineMessages.sentAt,
        receivedAt: lineMessages.receivedAt,
        createdAt: lineMessages.createdAt,
        updatedAt: lineMessages.updatedAt,
        user: {
          userId: lineUsers.userId,
          displayName: lineUsers.displayName,
          pictureUrl: lineUsers.pictureUrl
        }
      })
      .from(lineMessages)
      .leftJoin(lineUsers, eq(lineMessages.userId, lineUsers.userId))
      .where(eq(lineMessages.messageId, messageId))
      .limit(1)

    return message || null
  }

  static async getMessagesByUser(userId: string, options: Omit<MessageListOptions, 'userId'> = {}): Promise<PaginatedMessages> {
    return this.listMessages({ ...options, userId })
  }

  static async getMessageStats() {
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

    const [
      totalMessages,
      todayMessages,
      monthlyMessages,
      messagesByType
    ] = await Promise.all([
      // Total messages
      db.select({ count: count() }).from(lineMessages),

      // Today's messages
      db
        .select({ count: count() })
        .from(lineMessages)
        .where(gte(lineMessages.sentAt, today)),

      // Last 30 days messages
      db
        .select({ count: count() })
        .from(lineMessages)
        .where(gte(lineMessages.sentAt, thirtyDaysAgo)),

      // Messages by type
      db
        .select({
          messageType: lineMessages.messageType,
          count: count()
        })
        .from(lineMessages)
        .groupBy(lineMessages.messageType)
        .orderBy(desc(count()))
    ])

    return {
      total: totalMessages[0].count,
      today: todayMessages[0].count,
      lastMonth: monthlyMessages[0].count,
      byType: messagesByType
    }
  }

  static async getRecentActivity(limit = 10) {
    return await db
      .select({
        messageId: lineMessages.messageId,
        messageType: lineMessages.messageType,
        content: lineMessages.content,
        sentAt: lineMessages.sentAt,
        user: {
          userId: lineUsers.userId,
          displayName: lineUsers.displayName,
          pictureUrl: lineUsers.pictureUrl
        }
      })
      .from(lineMessages)
      .leftJoin(lineUsers, eq(lineMessages.userId, lineUsers.userId))
      .orderBy(desc(lineMessages.sentAt))
      .limit(limit)
  }
}