import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/internship-daily-work/',
  server: {
    host: true,
    allowedHosts: true,
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/candidates': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/jobs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/resumes': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/screening': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/interviews': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/scoring': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/duplicates': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/diversity': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/feedback': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/privacy': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
    },
  },
})
