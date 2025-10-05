import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Provide a single place to adjust backend target when using the dev proxy.
const BACKEND_TARGET = process.env.VITE_BACKEND_TARGET || 'http://172.20.10.5:8080';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Browser calls /api/...; Vite proxies to backend (avoids CORS issues with X-API-Key header)
      '/api': {
        target: BACKEND_TARGET,
        changeOrigin: true,
        secure: false,
        rewrite: p => p.replace(/^\/api/, '')
      }
    }
  }
})
