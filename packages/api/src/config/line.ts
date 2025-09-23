import type { LineConfig } from './types'

export const lineConfig: LineConfig = {
  channelSecret: process.env.LINE_CHANNEL_SECRET || '',
  channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN || '',
  webhookPath: '/api/webhook'
}