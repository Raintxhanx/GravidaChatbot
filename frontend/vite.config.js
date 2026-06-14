import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],
  build: {
    outDir: '../dist',       // Build dilempar ke folder dist di root proyek
    emptyOutDir: true,       // Bersihkan folder dist sebelum build baru
  }
})