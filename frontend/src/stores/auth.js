// src/stores/auth.js
// Trimmed version of pranera_knit's auth store — the dashboards app has no
// Employee/designation concept, it just needs to know if there's a real
// (non-Guest) Frappe session.
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, refreshSession } from '@/api/frappe'

export const useAuthStore = defineStore('auth', () => {
  const frappeUser = ref(window.__FRAPPE_SESSION__?.user || '')
  const isLoggedIn = ref(!!frappeUser.value && frappeUser.value !== 'Guest')
  const loading = ref(false)
  const error = ref('')

  // Re-sync from the user_id cookie. Call after anything that just changed
  // the session (login success), or on app boot.
  function refresh() {
    const u = refreshSession()
    frappeUser.value = u
    isLoggedIn.value = !!u && u !== 'Guest'
  }

  async function login(email, password) {
    loading.value = true
    error.value = ''
    try {
      await apiLogin(email, password)
      return true
    } catch (err) {
      error.value = err.message || 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  return { frappeUser, isLoggedIn, loading, error, refresh, login }
})
