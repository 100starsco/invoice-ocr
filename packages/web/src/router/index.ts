import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Home from '@/views/Home.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: {
      title: 'Home',
      requiresAuth: false
    }
  },
  {
    path: '/camera',
    name: 'camera',
    component: () => import('@/views/CameraCapture.vue'),
    meta: {
      title: 'Capture Invoice',
      requiresAuth: false,
      requiresLiff: false
    }
  },
  {
    path: '/preview',
    name: 'preview',
    component: () => import('@/views/ImagePreview.vue'),
    meta: {
      title: 'Preview Image',
      requiresAuth: false,
      requiresLiff: false
    }
  },
  {
    path: '/review/:id',
    name: 'review',
    component: () => import('@/views/ReviewCorrection.vue'),
    props: true,
    meta: {
      title: 'Review OCR Results',
      requiresAuth: true
    }
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('@/views/History.vue'),
    meta: {
      title: 'Invoice History',
      requiresAuth: true
    }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/Settings.vue'),
    meta: {
      title: 'Settings',
      requiresAuth: true
    }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: 'Login',
      requiresAuth: false,
      hideNavbar: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '404 - Not Found',
      requiresAuth: false
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    } else {
      return { top: 0 }
    }
  }
})

router.beforeEach(async (to, _from, next) => {
  document.title = `${to.meta.title || 'Invoice OCR'} - Invoice OCR`

  next()
})

export default router