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
  build: {
    rollupOptions: {
      output: {
        // Fixed entry filename — no content hash on the main bundle.
        // This means www/marketing.html never needs updating between builds,
        // and bench build simply overwrites index.js in-place rather than
        // adding a new file that the old HTML doesn't know about.
        // Chunks keep hashes for proper cache-busting.
        entryFileNames: 'assets/index.js',
        assetFileNames: (info) =>
          info.name === 'index.css' ? 'assets/index.css' : 'assets/[name]-[hash][extname]',
      },
    },
  },
})
