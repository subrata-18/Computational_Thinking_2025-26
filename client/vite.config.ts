import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // This tells Vite to securely tunnel our WebSocket to Flask
      '/VoiceTutor': {
        target: 'ws://127.0.0.1:5000',
        ws: true,
      }
    }
  }
})