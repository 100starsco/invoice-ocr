import { pgTable, uuid, varchar, jsonb, timestamp, integer, boolean, text } from 'drizzle-orm/pg-core'

export const jobs = pgTable('jobs', {
  id: uuid('id').primaryKey().defaultRandom(),

  // Job identification
  jobId: varchar('job_id', { length: 255 }).notNull().unique(), // BullMQ job ID
  queueName: varchar('queue_name', { length: 100 }).notNull(),
  jobName: varchar('job_name', { length: 255 }).notNull(),

  // Job status and timing
  status: varchar('status', { length: 50 }).notNull().default('pending'), // pending, active, completed, failed, delayed
  priority: integer('priority').default(0),
  attempts: integer('attempts').default(0),
  maxAttempts: integer('max_attempts').default(3),

  // Job data and results
  data: jsonb('data'), // Input data for the job
  result: jsonb('result'), // Job result data
  error: jsonb('error'), // Error information if job failed

  // Timing information
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
  startedAt: timestamp('started_at'),
  completedAt: timestamp('completed_at'),
  failedAt: timestamp('failed_at'),

  // Processing metadata
  processingTimeMs: integer('processing_time_ms'),
  workerInstance: varchar('worker_instance', { length: 255 }),

  // Relations
  parentJobId: uuid('parent_job_id').references(() => jobs.id),

  // Additional metadata
  metadata: jsonb('metadata'), // Additional job-specific metadata
})

export const lineEvents = pgTable('line_events', {
  id: uuid('id').primaryKey().defaultRandom(),

  // LINE event identification
  eventType: varchar('event_type', { length: 50 }).notNull(),
  eventId: varchar('event_id', { length: 255 }),
  replyToken: varchar('reply_token', { length: 255 }),

  // Source information
  userId: varchar('user_id', { length: 100 }),
  groupId: varchar('group_id', { length: 100 }),
  roomId: varchar('room_id', { length: 100 }),

  // Event data
  eventData: jsonb('event_data').notNull(), // Full LINE event payload
  webhookId: varchar('webhook_id', { length: 255 }),

  // Processing status
  processed: boolean('processed').default(false),
  processingStartedAt: timestamp('processing_started_at'),
  processingCompletedAt: timestamp('processing_completed_at'),
  processingError: text('processing_error'),

  // Related job
  jobId: uuid('job_id').references(() => jobs.id),

  // Timestamps
  receivedAt: timestamp('received_at').defaultNow().notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export const lineUsers = pgTable('line_users', {
  id: uuid('id').primaryKey().defaultRandom(),

  // LINE user information
  userId: varchar('user_id', { length: 100 }).notNull().unique(),
  displayName: varchar('display_name', { length: 255 }),
  pictureUrl: varchar('picture_url', { length: 500 }),
  statusMessage: text('status_message'),
  language: varchar('language', { length: 10 }),

  // User status
  isFollowing: boolean('is_following').default(true),
  isBlocked: boolean('is_blocked').default(false),

  // Profile information
  profileLastUpdated: timestamp('profile_last_updated'),

  // Activity tracking
  firstSeenAt: timestamp('first_seen_at').defaultNow().notNull(),
  lastSeenAt: timestamp('last_seen_at').defaultNow().notNull(),
  lastMessageAt: timestamp('last_message_at'),

  // Timestamps
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export const lineMessages = pgTable('line_messages', {
  id: uuid('id').primaryKey().defaultRandom(),

  // Message identification
  messageId: varchar('message_id', { length: 255 }).notNull().unique(),
  messageType: varchar('message_type', { length: 50 }).notNull(), // text, image, video, audio, file, location, sticker

  // Message content
  content: jsonb('content').notNull(), // Message content (text, image URL, etc.)

  // User and event information
  userId: varchar('user_id', { length: 100 }).notNull(),
  eventId: uuid('event_id').references(() => lineEvents.id),

  // Reply information
  replyToken: varchar('reply_token', { length: 255 }),

  // Response tracking
  responded: boolean('responded').default(false),
  responseType: varchar('response_type', { length: 50 }), // reply, push, broadcast
  responseJobId: uuid('response_job_id').references(() => jobs.id),

  // Timestamps
  sentAt: timestamp('sent_at').notNull(),
  receivedAt: timestamp('received_at').defaultNow().notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})