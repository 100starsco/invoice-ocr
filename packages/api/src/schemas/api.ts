import { z } from 'zod'

// Common schemas
export const PaginationQuerySchema = z.object({
  limit: z.string().optional(),
  offset: z.string().optional()
})

export const ErrorResponseSchema = z.object({
  error: z.string()
})

export const SuccessResponseSchema = z.object({
  success: z.literal(true),
  data: z.any()
})

// User schemas
export const LineUserSchema = z.object({
  id: z.string(),
  userId: z.string(),
  displayName: z.string().nullable(),
  pictureUrl: z.string().nullable(),
  statusMessage: z.string().nullable(),
  language: z.string().nullable(),
  isFollowing: z.boolean(),
  isBlocked: z.boolean(),
  profileLastUpdated: z.string().nullable(),
  firstSeenAt: z.string(),
  lastSeenAt: z.string(),
  lastMessageAt: z.string().nullable(),
  createdAt: z.string(),
  updatedAt: z.string()
})

export const UserWithStatsSchema = LineUserSchema.extend({
  messageCount: z.number()
})

export const UserListQuerySchema = PaginationQuerySchema.extend({
  search: z.string().optional(),
  isFollowing: z.string().optional(),
  sortBy: z.enum(['displayName', 'lastSeenAt', 'firstSeenAt', 'lastMessageAt']).optional(),
  sortOrder: z.enum(['asc', 'desc']).optional()
})

export const PaginatedUsersSchema = z.object({
  users: z.array(LineUserSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
  hasMore: z.boolean()
})

// Message schemas
export const MessageContentSchema = z.record(z.string(), z.any())

export const LineMessageSchema = z.object({
  id: z.string(),
  messageId: z.string(),
  messageType: z.string(),
  content: MessageContentSchema,
  userId: z.string(),
  eventId: z.string().nullable(),
  replyToken: z.string().nullable(),
  responded: z.boolean(),
  responseType: z.string().nullable(),
  responseJobId: z.string().nullable(),
  sentAt: z.string(),
  receivedAt: z.string(),
  createdAt: z.string(),
  updatedAt: z.string()
})

export const MessageWithUserSchema = LineMessageSchema.extend({
  user: z.object({
    displayName: z.string().nullable(),
    pictureUrl: z.string().nullable()
  }).nullable()
})

export const MessageListQuerySchema = PaginationQuerySchema.extend({
  userId: z.string().optional(),
  messageType: z.string().optional(),
  dateFrom: z.string().optional(),
  dateTo: z.string().optional(),
  sortBy: z.enum(['sentAt', 'receivedAt', 'createdAt']).optional(),
  sortOrder: z.enum(['asc', 'desc']).optional()
})

export const PaginatedMessagesSchema = z.object({
  messages: z.array(MessageWithUserSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
  hasMore: z.boolean()
})

export const MessageStatsSchema = z.object({
  total: z.number(),
  today: z.number(),
  lastMonth: z.number(),
  byType: z.array(z.object({
    messageType: z.string(),
    count: z.number()
  }))
})

export const RecentActivitySchema = z.array(z.object({
  messageId: z.string(),
  messageType: z.string(),
  content: MessageContentSchema,
  sentAt: z.string(),
  user: z.object({
    userId: z.string(),
    displayName: z.string().nullable(),
    pictureUrl: z.string().nullable()
  }).nullable()
}))

// Auth schemas
export const LoginCredentialsSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
})

export const AdminUserSchema = z.object({
  id: z.string(),
  email: z.string(),
  name: z.string(),
  isActive: z.boolean(),
  createdAt: z.string(),
  updatedAt: z.string()
})

export const LoginResponseSchema = z.object({
  user: AdminUserSchema,
  token: z.string()
})

// Path parameter schemas
export const UserIdParamSchema = z.object({
  userId: z.string().min(1)
})

export const MessageIdParamSchema = z.object({
  messageId: z.string().min(1)
})

export const SearchQueryParamSchema = z.object({
  query: z.string().min(1)
})

export const SearchQuerySchema = z.object({
  limit: z.string().optional()
})