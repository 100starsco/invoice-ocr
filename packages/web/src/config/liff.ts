import type { LiffConfig } from './types'

export const liffConfig: LiffConfig = {
  liffId: import.meta.env.VITE_LIFF_ID || '',
  channelId: import.meta.env.VITE_LINE_CHANNEL_ID || ''
}