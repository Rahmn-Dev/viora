import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite' // <-- INI MESIN BARUNYA
import obfuscatorPlugin from 'rollup-plugin-obfuscator'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(), // <-- WAJIB DIPANGGIL DI SINI
    obfuscatorPlugin({
      compact: true,
      controlFlowFlattening: false,
      deadCodeInjection: false,
      debugProtection: false,
      disableConsoleOutput: true,
      identifierNamesGenerator: 'hexadecimal',
      log: false,
      stringArray: true,
      stringArrayEncoding: ['base64'],
      stringArrayThreshold: 0.75
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0',
    proxy: {
      '/xendit-api': {
        target: 'https://api.xendit.co',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/xendit-api/, '')
      }
    },
    headers: {
      // Permissions-Policy: allow payment for embedded checkout
      'Permissions-Policy': [
        'geolocation=()',
        'camera=()',
        'microphone=()',
        'usb=()',
      ].join(', '),
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
    }
  },
  build: {
    target: 'esnext',
    cssCodeSplit: true,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('vue')) return 'vendor-vue';
            if (id.includes('axios')) return 'vendor-axios';
            if (id.includes('lucide')) return 'vendor-icons';
            return 'vendor-core';
          }
        }
      }
    }
  },
  esbuild: {
    drop: ['console', 'debugger'],
  }
})