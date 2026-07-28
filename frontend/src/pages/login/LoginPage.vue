<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <img :src="logoUrl" alt="Dashboards" class="logo-img" />
        <h1>Dashboards</h1>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input
            v-model="email"
            type="email"
            class="form-input"
            placeholder="Enter your email"
            autocomplete="email"
            required
          />
        </div>

        <div class="form-group" style="position:relative">
          <label class="form-label">Password</label>
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            class="form-input"
            placeholder="Enter your password"
            autocomplete="current-password"
            required
          />
          <button type="button" class="eye-toggle" @click="showPassword = !showPassword" :aria-label="showPassword ? 'Hide password' : 'Show password'">
            <svg v-if="!showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a19.66 19.66 0 0 1 5.06-5.94M9.9 4.24A10.4 10.4 0 0 1 12 4c7 0 11 8 11 8a19.7 19.7 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
              <line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
          </button>
        </div>

        <div v-if="errorMsg" class="error-box">
          ⚠️ {{ errorMsg }}
        </div>

        <button type="submit" class="btn btn-primary btn-full" :disabled="loading">
          <span v-if="loading" class="btn-spinner"></span>
          <span>{{ loading ? loadingMsg : 'Login' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

// Served by Frappe at runtime from the app's own public/images/ folder —
// deliberately a plain string, not a static template src=, so Vite doesn't
// try to resolve/bundle it as a frontend build asset (it isn't one).
const logoUrl = '/assets/dashboards/images/logo.svg'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const loadingMsg = ref('Logging in...')
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  loadingMsg.value = 'Logging in...'

  try {
    await auth.login(email.value, password.value)
    loadingMsg.value = 'Redirecting...'
    const dest = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard-app'
    // Full page reload on purpose — re-runs main.js against the fresh
    // session cookie from scratch, same as pranera_knit's LoginPage does
    // (an SPA router.replace() here was the unreliable path there too).
    window.location.href = dest
  } catch (err) {
    errorMsg.value = err.message || 'Login failed'
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1565C0 0%, #0097A7 100%);
  padding: 24px;
}
.login-card {
  background: white;
  border-radius: 16px;
  padding: 32px 24px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}
.login-logo {
  text-align: center;
  margin-bottom: 28px;
}
.logo-img {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  margin: 0 auto 12px;
  display: block;
}
.login-logo h1 { font-size: 22px; font-weight: 700; color: #1e293b; }

.form-group { margin-bottom: 16px; }
.form-label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 5px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.form-input {
  width: 100%;
  padding: 11px 13px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  color: #0f172a;
  background: white;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  -webkit-appearance: none;
  box-sizing: border-box;
}
.form-input:focus {
  border-color: #1565C0;
  box-shadow: 0 0 0 3px rgba(21,101,192,0.1);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 11px 20px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
  white-space: nowrap;
  letter-spacing: 0.01em;
}
.btn:active { transform: scale(0.97); }
.btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
.btn-primary { background: #1565C0; color: white; }
.btn-primary:hover:not(:disabled) { background: #0D47A1; }
.btn-full { width: 100%; }

.btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: btn-spin 0.7s linear infinite;
  margin-right: 6px;
  vertical-align: -2px;
}
@keyframes btn-spin { to { transform: rotate(360deg); } }

.eye-toggle {
  position: absolute;
  right: 12px;
  bottom: 10px;
  background: none;
  border: none;
  cursor: pointer;
  color: #94a3b8;
  display: flex;
  align-items: center;
  padding: 2px;
}
.eye-toggle:hover { color: #64748b; }
.error-box {
  background: #fee2e2;
  color: #991b1b;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
