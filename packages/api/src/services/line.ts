import type {
  LineProfile,
  LineMessageSend,
  LineReplyMessageRequest,
  LinePushMessageRequest,
  LineMulticastMessageRequest,
  LineBroadcastMessageRequest,
  LineApiResponse
} from '@invoice-ocr/shared'

export class LineMessagingService {
  private readonly baseUrl = 'https://api.line.me/v2/bot'
  private readonly channelAccessToken: string

  constructor(channelAccessToken: string) {
    this.channelAccessToken = channelAccessToken
  }

  private async makeRequest<T = LineApiResponse>(
    endpoint: string,
    method: 'GET' | 'POST' = 'POST',
    body?: object
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`

    const response = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${this.channelAccessToken}`,
        'Content-Type': 'application/json'
      },
      body: body ? JSON.stringify(body) : undefined
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`LINE API Error: ${response.status} ${response.statusText} - ${errorText}`)
    }

    if (response.status === 204) {
      return {} as T
    }

    return response.json() as Promise<T>
  }

  /**
   * Get user profile information
   */
  async getProfile(userId: string): Promise<LineProfile> {
    return this.makeRequest<LineProfile>(`/profile/${userId}`, 'GET')
  }

  /**
   * Reply to a user message using reply token
   */
  async replyMessage(replyToken: string, messages: LineMessageSend[], notificationDisabled = false): Promise<void> {
    if (messages.length === 0 || messages.length > 5) {
      throw new Error('Messages array must contain 1-5 messages')
    }

    const request: LineReplyMessageRequest = {
      replyToken,
      messages,
      notificationDisabled
    }

    await this.makeRequest('/message/reply', 'POST', request)
  }

  /**
   * Send push message to a user
   */
  async pushMessage(to: string, messages: LineMessageSend[], notificationDisabled = false): Promise<void> {
    if (messages.length === 0 || messages.length > 5) {
      throw new Error('Messages array must contain 1-5 messages')
    }

    const request: LinePushMessageRequest = {
      to,
      messages,
      notificationDisabled
    }

    await this.makeRequest('/message/push', 'POST', request)
  }

  /**
   * Send multicast message to multiple users
   */
  async multicastMessage(to: string[], messages: LineMessageSend[], notificationDisabled = false): Promise<void> {
    if (to.length === 0 || to.length > 500) {
      throw new Error('Recipients array must contain 1-500 user IDs')
    }

    if (messages.length === 0 || messages.length > 5) {
      throw new Error('Messages array must contain 1-5 messages')
    }

    const request: LineMulticastMessageRequest = {
      to,
      messages,
      notificationDisabled
    }

    await this.makeRequest('/message/multicast', 'POST', request)
  }

  /**
   * Send broadcast message to all followers
   */
  async broadcastMessage(messages: LineMessageSend[], notificationDisabled = false): Promise<void> {
    if (messages.length === 0 || messages.length > 5) {
      throw new Error('Messages array must contain 1-5 messages')
    }

    const request: LineBroadcastMessageRequest = {
      messages,
      notificationDisabled
    }

    await this.makeRequest('/message/broadcast', 'POST', request)
  }

  /**
   * Get content of a message (for images, videos, audio files)
   */
  async getMessageContent(messageId: string): Promise<Buffer> {
    const url = `${this.baseUrl}/message/${messageId}/content`

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${this.channelAccessToken}`
      }
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`LINE API Error: ${response.status} ${response.statusText} - ${errorText}`)
    }

    return Buffer.from(await response.arrayBuffer())
  }

  /**
   * Create text message
   */
  static createTextMessage(text: string): LineMessageSend {
    return {
      type: 'text',
      text
    }
  }

  /**
   * Create image message
   */
  static createImageMessage(originalContentUrl: string, previewImageUrl?: string): LineMessageSend {
    return {
      type: 'image',
      originalContentUrl,
      previewImageUrl: previewImageUrl || originalContentUrl
    }
  }

  /**
   * Create sticker message
   */
  static createStickerMessage(packageId: string, stickerId: string): LineMessageSend {
    return {
      type: 'sticker',
      packageId,
      stickerId
    }
  }

  /**
   * Create simple flex message with text
   */
  static createSimpleFlexMessage(title: string, body: string, altText?: string): LineMessageSend {
    return {
      type: 'flex',
      altText: altText || title,
      contents: {
        type: 'bubble',
        body: {
          type: 'box',
          layout: 'vertical',
          contents: [
            {
              type: 'text',
              text: title,
              weight: 'bold',
              size: 'xl'
            },
            {
              type: 'text',
              text: body,
              wrap: true,
              margin: 'md'
            }
          ]
        }
      }
    }
  }

  /**
   * Create quick reply with text options
   */
  static createQuickReplyTextOptions(options: { label: string; text: string }[]) {
    return {
      items: options.map(option => ({
        type: 'action' as const,
        action: {
          type: 'message' as const,
          label: option.label,
          text: option.text
        }
      }))
    }
  }

  /**
   * Validate webhook signature
   */
  static async validateSignature(body: string, signature: string, channelSecret: string): Promise<boolean> {
    const crypto = await import('crypto')
    const hash = crypto.default
      .createHmac('SHA256', channelSecret)
      .update(body)
      .digest('base64')

    return hash === signature
  }

  /**
   * Check if user ID is valid LINE user ID format
   */
  static isValidUserId(userId: string): boolean {
    return /^U[0-9a-f]{32}$/.test(userId)
  }

  /**
   * Check if group ID is valid LINE group ID format
   */
  static isValidGroupId(groupId: string): boolean {
    return /^C[0-9a-f]{32}$/.test(groupId)
  }

  /**
   * Check if room ID is valid LINE room ID format
   */
  static isValidRoomId(roomId: string): boolean {
    return /^R[0-9a-f]{32}$/.test(roomId)
  }
}