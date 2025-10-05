/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_ENV: string
  readonly VITE_DEFAULT_THEME: string
  readonly VITE_ENABLE_THEME_SWITCHER: string
  readonly VITE_ENABLE_QUEUE_MONITORING: string
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_DEV_TOOLS: string
  readonly VITE_LOG_LEVEL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Global app environment variables
declare const __APP_ENV__: string
declare const __APP_TITLE__: string
declare const __DEFAULT_THEME__: string