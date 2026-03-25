import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite' // <-- INI MESIN BARUNYA

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(), // <-- WAJIB DIPANGGIL DI SINI
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})