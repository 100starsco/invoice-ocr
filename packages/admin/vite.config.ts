import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    server: {
      port: 5174, // Changed from 5148 to avoid conflicts
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:3000',
          changeOrigin: true,
          secure: false
        }
      }
    },
    define: {
      __APP_ENV__: JSON.stringify(env.VITE_ENV || 'development'),
      __APP_TITLE__: JSON.stringify(env.VITE_APP_TITLE || 'Invoice OCR Admin'),
      __DEFAULT_THEME__: JSON.stringify(env.VITE_DEFAULT_THEME || 'business')
    },
    build: {
      sourcemap: env.VITE_ENV !== 'production',
      minify: env.VITE_ENV === 'production'
    }
  }
})