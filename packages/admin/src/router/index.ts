import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Check if route requires authentication
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)

  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login if not authenticated
    next({
      name: 'Login',
      query: { redirect: to.fullPath }
    })
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    // Redirect to dashboard if already authenticated
    next({ name: 'Dashboard' })
  } else {
    // If authenticated but no user data, fetch it
    if (authStore.isAuthenticated && !authStore.user) {
      await authStore.fetchCurrentUser()
    }
    next()
  }
})

export default router