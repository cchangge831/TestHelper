import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // 开发模式下代理 /api 请求到 Flask 后端
    proxy: {
      '/api': {
        target: 'http://localhost:6688',
        changeOrigin: true,
      },
    },
  },
  // 构建输出到 dist 目录，供 Flask 生产模式托管
  build: {
    outDir: 'dist',
  },
})
