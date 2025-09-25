import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  },
  server: {
    port: 5176,
    host: '0.0.0.0', // Allow all hosts
    allowedHosts: ['fn.100s.dev', 'localhost'],
    hmr: {
      port: 5176,
      host: 'fn.100s.dev'
    }
  }
})