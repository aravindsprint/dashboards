// Shared API helper for the dashboards SPA.
//
// All current dashboards pages only need GET-based whitelisted method calls
// (report/summary data) — no writes, so `call()` below stays CSRF-free, same
// assumption the original pre-SPA pages made. If a page ever needs a POST
// (create/update), extend this with a CSRF-aware call like pranera_knit's
// src/api/frappe.js does (ensureCSRF/resetCSRF/initCSRF).

export function call(fullMethod, args = {}) {
  // Desk context: frappe object is available (e.g. if this SPA is ever
  // embedded in a Desk page)
  if (window.frappe && window.frappe.call) {
    return new Promise((resolve, reject) => {
      window.frappe.call({
        method: fullMethod,
        args: args || {},
        callback: (r) => (r && r.message !== undefined ? resolve(r.message) : reject(r)),
        error: reject,
      })
    })
  }

  // www / PWA context: plain fetch GET
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(args || {})) {
    if (v !== null && v !== undefined && v !== '') params.set(k, String(v))
  }
  const url = '/api/method/' + fullMethod + (params.toString() ? '?' + params.toString() : '')
  return fetch(url, {
    method: 'GET',
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  })
    .then((r) => r.json())
    .then((r) => {
      if (r.message !== undefined) return r.message
      throw new Error(r.exc || r._server_messages || 'API error')
    })
}

export function todayStr() {
  if (window.frappe && window.frappe.datetime) return window.frappe.datetime.get_today()
  return new Date().toISOString().split('T')[0]
}

// ── Session / login (mirrors pranera_knit's src/api/frappe.js) ────────────
// Frappe sets a plain, JS-readable `user_id` cookie alongside the HttpOnly
// `sid` session cookie on login — that's what we read client-side to know
// whether we're logged in, since we can't read `sid` itself from JS.

function getCookieValue(name) {
  return document.cookie
    .split('; ')
    .find((r) => r.startsWith(name + '='))
    ?.split('=')[1] || ''
}

export function isLoggedIn() {
  const user = window.__FRAPPE_SESSION__?.user
  return !!user && user !== 'Guest'
}

// Re-sync window.__FRAPPE_SESSION__.user from the user_id cookie. Call after
// anything that just changed the session (login success), or on app boot.
export function refreshSession() {
  const user = decodeURIComponent(getCookieValue('user_id') || 'Guest')
  window.__FRAPPE_SESSION__ = { ...(window.__FRAPPE_SESSION__ || {}), user }
  return user
}

// Explicit email/password login against Frappe's own login endpoint.
// credentials:'include' + this app's dev-server proxy (vite.config.js) is
// what makes the resulting session cookie land on localhost during
// `npm run dev` — see cookieDomainRewrite there.
export async function login(email, password) {
  const res = await fetch('/api/method/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ usr: email, pwd: password }).toString(),
    credentials: 'include',
  })
  const data = await res.json().catch(() => ({}))

  if (!res.ok || data.message !== 'Logged In') {
    let msg = 'Incorrect email or password'
    try {
      const msgs = JSON.parse(data._server_messages || '[]')
      if (msgs.length) msg = JSON.parse(msgs[msgs.length - 1]).message || msg
    } catch { /* keep default */ }
    throw new Error(msg)
  }
  return true
}
