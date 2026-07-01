import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    frappeui({
      frontendRoute: '/marketing',
    }),
    vue(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  optimizeDeps: {
    include: ['feather-icons', 'showdown', 'tailwind.config.js'],
  },
})
