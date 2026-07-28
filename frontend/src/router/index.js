import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from '@/api/frappe'

import HubPage from '@/pages/hub/HubPage.vue'
import SalesDashboardPage from '@/pages/sales/SalesDashboardPage.vue'
import InventoryDashboardPage from '@/pages/inventory/InventoryDashboardPage.vue'
import LoginPage from '@/pages/login/LoginPage.vue'

const routes = [
  { path: '/', redirect: '/dashboard-app' },
  { path: '/dashboard-app/login', component: LoginPage },
  { path: '/dashboard-app', component: HubPage },
  { path: '/dashboard-app/sales', component: SalesDashboardPage },
  { path: '/dashboard-app/inventory', component: InventoryDashboardPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Explicit auth guard: anyone without a real (non-Guest) Frappe session gets
// bounced to /dashboard-app/login instead of being allowed to sit on a page
// that will just fail its API calls with 403s. Conversely, someone who is
// already logged in is bounced away from the login page itself.
//
// window.__FRAPPE_SESSION__.user is set synchronously in main.js from the
// user_id cookie before the router is created, so this check is safe to run
// on the very first navigation with no async wait. Same pattern as
// pranera_knit/frontend/src/router/index.js.
router.beforeEach((to) => {
  const loggedIn = isLoggedIn()
  if (to.path !== '/dashboard-app/login' && !loggedIn) {
    return { path: '/dashboard-app/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/dashboard-app/login' && loggedIn) {
    return { path: '/dashboard-app' }
  }
})

export default router
