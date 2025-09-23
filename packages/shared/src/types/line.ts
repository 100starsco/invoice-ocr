// LINE Messaging API Types

export interface LineUser {
  userId: string
  displayName?: string
  pictureUrl?: string
  statusMessage?: string
}

export interface LineSource {
  type: 'user' | 'group' | 'room'
  userId?: string
  groupId?: string
  roomId?: string
}

export interface LineMessage {
  id: string
  type: 'text' | 'image' | 'video' | 'audio' | 'file' | 'location' | 'sticker' | 'imagemap' | 'template' | 'flex'
  text?: string
  packageId?: string
  stickerId?: string
  contentProvider?: {
    type: 'line' | 'external'
    originalContentUrl?: string
    previewImageUrl?: string
  }
}

export interface LineTextMessage extends LineMessage {
  type: 'text'
  text: string
}

export interface LineImageMessage extends LineMessage {
  type: 'image'
  contentProvider: {
    type: 'line' | 'external'
    originalContentUrl?: string
    previewImageUrl?: string
  }
}

export interface LineStickerMessage extends LineMessage {
  type: 'sticker'
  packageId: string
  stickerId: string
}

export interface LineEvent {
  type: 'message' | 'follow' | 'unfollow' | 'join' | 'leave' | 'memberJoined' | 'memberLeft' | 'postback' | 'videoPlayComplete' | 'beacon' | 'accountLink' | 'things'
  mode: 'active' | 'standby'
  timestamp: number
  source: LineSource
  webhookEventId: string
  deliveryContext: {
    isRedelivery: boolean
  }
  replyToken?: string
  message?: LineMessage
  joined?: {
    members: LineUser[]
  }
  left?: {
    members: LineUser[]
  }
  postback?: {
    data: string
    params?: {
      date?: string
      time?: string
      datetime?: string
    }
  }
}

export interface LineMessageEvent extends LineEvent {
  type: 'message'
  replyToken: string
  message: LineMessage
}

export interface LineFollowEvent extends LineEvent {
  type: 'follow'
  replyToken: string
}

export interface LineUnfollowEvent extends LineEvent {
  type: 'unfollow'
}

export interface LineJoinEvent extends LineEvent {
  type: 'join'
  replyToken: string
  joined: {
    members: LineUser[]
  }
}

export interface LineLeaveEvent extends LineEvent {
  type: 'leave'
  left: {
    members: LineUser[]
  }
}

export interface LinePostbackEvent extends LineEvent {
  type: 'postback'
  replyToken: string
  postback: {
    data: string
    params?: {
      date?: string
      time?: string
      datetime?: string
    }
  }
}

export interface LineWebhookBody {
  destination: string
  events: LineEvent[]
}

// LINE API Response Types
export interface LineApiResponse {
  message?: string
}

export interface LineProfile {
  displayName: string
  userId: string
  language?: string
  pictureUrl?: string
  statusMessage?: string
}

// LINE Message Types for Sending
export interface LineTextMessageSend {
  type: 'text'
  text: string
  quickReply?: LineQuickReply
}

export interface LineImageMessageSend {
  type: 'image'
  originalContentUrl: string
  previewImageUrl: string
  quickReply?: LineQuickReply
}

export interface LineStickerMessageSend {
  type: 'sticker'
  packageId: string
  stickerId: string
  quickReply?: LineQuickReply
}

export interface LineFlexMessageSend {
  type: 'flex'
  altText: string
  contents: LineFlexContainer
  quickReply?: LineQuickReply
}

export interface LineTemplateMessageSend {
  type: 'template'
  altText: string
  template: LineTemplate
  quickReply?: LineQuickReply
}

export type LineMessageSend = LineTextMessageSend | LineImageMessageSend | LineStickerMessageSend | LineFlexMessageSend | LineTemplateMessageSend

// Quick Reply Types
export interface LineQuickReply {
  items: LineQuickReplyItem[]
}

export interface LineQuickReplyItem {
  type: 'action'
  action: LineAction
  imageUrl?: string
}

export interface LineAction {
  type: 'message' | 'postback' | 'uri' | 'datetimepicker' | 'camera' | 'cameraRoll' | 'location'
  label?: string
  text?: string
  data?: string
  uri?: string
  mode?: 'date' | 'time' | 'datetime'
  initial?: string
  max?: string
  min?: string
}

// Flex Message Types
export interface LineFlexContainer {
  type: 'bubble' | 'carousel'
  header?: LineFlexComponent
  hero?: LineFlexComponent
  body?: LineFlexComponent
  footer?: LineFlexComponent
  styles?: LineFlexBubbleStyle
  contents?: LineFlexContainer[]
}

export interface LineFlexComponent {
  type: 'box' | 'button' | 'filler' | 'icon' | 'image' | 'separator' | 'spacer' | 'text'
  layout?: 'horizontal' | 'vertical' | 'baseline'
  contents?: LineFlexComponent[]
  text?: string
  url?: string
  action?: LineAction
  flex?: number
  margin?: string
  spacing?: string
  size?: string
  align?: string
  gravity?: string
  wrap?: boolean
  weight?: string
  color?: string
  style?: string
}

export interface LineFlexBubbleStyle {
  header?: LineFlexBlockStyle
  hero?: LineFlexBlockStyle
  body?: LineFlexBlockStyle
  footer?: LineFlexBlockStyle
}

export interface LineFlexBlockStyle {
  backgroundColor?: string
  separator?: boolean
  separatorColor?: string
}

// Template Types
export interface LineTemplate {
  type: 'buttons' | 'confirm' | 'carousel' | 'image_carousel'
  text?: string
  title?: string
  thumbnailImageUrl?: string
  imageAspectRatio?: 'rectangle' | 'square'
  imageSize?: 'cover' | 'contain'
  actions?: LineAction[]
  columns?: LineTemplateColumn[]
}

export interface LineTemplateColumn {
  thumbnailImageUrl?: string
  imageBackgroundColor?: string
  title?: string
  text: string
  actions: LineAction[]
}

// Push Message Request
export interface LinePushMessageRequest {
  to: string
  messages: LineMessageSend[]
  notificationDisabled?: boolean
}

// Reply Message Request
export interface LineReplyMessageRequest {
  replyToken: string
  messages: LineMessageSend[]
  notificationDisabled?: boolean
}

// Multicast Message Request
export interface LineMulticastMessageRequest {
  to: string[]
  messages: LineMessageSend[]
  notificationDisabled?: boolean
}

// Broadcast Message Request
export interface LineBroadcastMessageRequest {
  messages: LineMessageSend[]
  notificationDisabled?: boolean
}

// Job Queue Types
export interface LineMessageJobData {
  type: 'reply' | 'push' | 'multicast' | 'broadcast'
  replyToken?: string
  to?: string | string[]
  messages: LineMessageSend[]
  notificationDisabled?: boolean
  userId?: string
  metadata?: Record<string, any>
}

export interface LineMessageJobResult {
  success: boolean
  messageId?: string
  error?: string
  timestamp: number
}

// Database Types
export interface LineUserRecord {
  id: string
  userId: string
  displayName?: string
  pictureUrl?: string
  statusMessage?: string
  language?: string
  isFollowing: boolean
  followedAt?: Date
  unfollowedAt?: Date
  createdAt: Date
  updatedAt: Date
}

export interface LineMessageRecord {
  id: string
  userId: string
  messageId: string
  type: 'incoming' | 'outgoing'
  messageType: LineMessage['type']
  content: string | object
  replyToken?: string
  timestamp: Date
  createdAt: Date
}

export interface LineJobRecord {
  id: string
  jobId: string
  userId?: string
  jobType: LineMessageJobData['type']
  status: 'pending' | 'processing' | 'completed' | 'failed'
  data: LineMessageJobData
  result?: LineMessageJobResult
  attempts: number
  maxAttempts: number
  createdAt: Date
  updatedAt: Date
  completedAt?: Date
  failedAt?: Date
}