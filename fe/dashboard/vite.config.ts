import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// @ts-ignore
import fs from 'fs';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    https: {
      key: fs.readFileSync('key.pem'),
      cert: fs.readFileSync('cert.pem'),
    },
    proxy: {
      // Proxy API to backend to avoid CORS/mixed-content on mobile HTTPS
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
      }
    }
  }
});
