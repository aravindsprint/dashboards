import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ command }) => ({
  base: command === 'serve' ? '/' : '/assets/dashboards/dashboard_app/',

  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') }
  },

  server: {
    port: 3000,
    // Dev-server only — vite build never reads this (production always talks
    // to erp.pranera.in directly since it's served from that same origin).
    // Same proxy setup as pranera_knit/frontend/vite.config.js: needed so
    // `npm run dev` (localhost:3000) can reach the live backend; without it
    // every /api/* call 404s against Vite's own dev server.
    proxy: command === 'serve' ? {
      '/api': {
        target: 'https://erp.pranera.in',
        changeOrigin: true,
        secure: false,
        ws: true,
        cookieDomainRewrite: 'localhost',
        headers: {
          'Origin': 'https://erp.pranera.in',
          'Referer': 'https://erp.pranera.in'
        },
        // See pranera_knit/frontend/vite.config.js for why both of these
        // are needed: node-http-proxy forwarding a stray Expect header
        // trips nginx into a flat 417, and the session cookie is marked
        // Secure by erp.pranera.in (HTTPS) so it silently never lands on
        // this plain-HTTP dev server unless stripped.
        configure(proxy) {
          proxy.on('proxyReq', (proxyReq) => {
            proxyReq.removeHeader('expect')
          })
          proxy.on('proxyRes', (proxyRes) => {
            const setCookie = proxyRes.headers['set-cookie']
            if (setCookie) {
              proxyRes.headers['set-cookie'] = setCookie.map(c =>
                c.replace(/;\s*Secure/gi, '').replace(/;\s*SameSite=None/gi, '; SameSite=Lax')
              )
            }
          })
        }
      },
      '/assets': {
        target: 'https://erp.pranera.in',
        changeOrigin: true,
        secure: false
      },
      '/files': {
        target: 'https://erp.pranera.in',
        changeOrigin: true,
        secure: false
      }
    } : undefined
  },

  build: {
    outDir: path.resolve(__dirname, '../dashboards/public/dashboard_app'),
    emptyOutDir: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'),
      output: {
        entryFileNames: 'index.js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: (info) => {
          if (info.name?.endsWith('.css')) return 'index.css'
          return 'assets/[name]-[hash][extname]'
        }
      }
    }
  },

  plugins: [vue()]
}))
