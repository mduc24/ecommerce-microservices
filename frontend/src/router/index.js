import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const PROTECTED = ['/cart', '/orders', '/products/:id']
const GUEST_ONLY = ['/login', '/register']

const routes = [
  { path: '/', redirect: '/products' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: () => import('../views/AuthCallbackView.vue'),
  },
  {
    path: '/products',
    name: 'Products',
    component: () => import('../views/ProductsView.vue'),
  },
  {
    path: '/products/:id',
    name: 'ProductDetail',
    component: () => import('../views/ProductDetailView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/cart',
    name: 'Cart',
    component: () => import('../views/CartView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('../views/OrdersView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  // Protected route — must be logged in
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { path: '/login' }
  }

  // Guest-only routes — redirect away if already logged in
  if (GUEST_ONLY.includes(to.path) && authStore.isAuthenticated) {
    return { path: '/products' }
  }
})

export default router
