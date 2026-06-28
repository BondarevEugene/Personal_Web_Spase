import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5177,
    proxy: {
      '/api': {
        target: 'http://localhost:8088', // ИСПРАВЛЕНО НА ТВОЙ БОЕВОЙ ПОРТ
        changeOrigin: true,
        secure: false,
      }
    }
  }
});