import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  // Load environment variables
  const env = loadEnv(mode, process.cwd(), '')

  return {
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
      },
      proxy: env.VITE_API_URL ? {
        '/api': {
          target: env.VITE_API_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      } : undefined
    },
    define: {
      __APP_ENV__: JSON.stringify(env.VITE_ENV || 'development')
    }
  }
})