import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    open: false,
    allowedHosts: ['029d0110a58c.ngrok-free.app', 'e9c71196d292.ngrok-free.app'],
    proxy: {
      '/stock-data': {
        target: 'http://localhost:9001',
        changeOrigin: true,
        secure: false
      },
      '/company-metrics': {
        target: 'http://localhost:9001',
        changeOrigin: true,
        secure: false
      },
      '/earnings': {
        target: 'http://localhost:9001',
        changeOrigin: true,
        secure: false
      },
      '/highlights': {
        target: 'http://localhost:9001',
        changeOrigin: true,
        secure: false
      },
      '/qbr': {
        target: 'http://localhost:9001',
        changeOrigin: true,
        secure: false
      },
      '/briefing': {
        target: 'http://localhost:9001',
        changeOrigin: true,
        secure: false
      },
      '/analyze-image': {
        target: 'http://localhost:9001',
        changeOrigin: true,
        secure: false
      },
      '/chatbot': {
        target: 'http://localhost:9001',
        changeOrigin: true,
        secure: false
      },
      '/summary': {
        target: 'http://localhost:9001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
