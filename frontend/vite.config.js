import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8001',
      '/agente': {
        target: 'http://localhost:8000',
        rewrite: (p) => p.replace(/^\/agente/, '/api'),
      },
    },
  },
})
