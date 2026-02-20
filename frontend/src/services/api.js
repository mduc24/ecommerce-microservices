import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach JWT token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle errors with clear messages
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!error.response) {
      error.message = 'Network error. Check your connection.'
    } else if (error.code === 'ECONNABORTED') {
      error.message = 'Request timeout. Please try again.'
    } else if (error.response.status === 401) {
      // Dynamic import avoids circular dependency (auth store imports api)
      const { useAuthStore } = await import('../stores/auth')
      const authStore = useAuthStore()
      authStore.logout()
      error.message = 'Session expired. Please log in again.'
    } else if (error.response.status === 404) {
      error.message = 'Not found.'
    } else if (error.response.status >= 500) {
      error.message = 'Server error. Please try again later.'
    }
    return Promise.reject(error)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────

export function loginUser(email, password) {
  return api.post('/users/login', { email, password })
}

export function registerUser(email, username, password) {
  return api.post('/users/register', { email, username, password })
}

export function getMe() {
  return api.get('/users/me')
}

// ── Products ──────────────────────────────────────────────────────────────────

export function getProducts(page = 1, limit = 20) {
  return api.get('/products', { params: { page, limit } })
}

export function getProduct(id) {
  return api.get(`/products/${id}`)
}

// ── Orders ────────────────────────────────────────────────────────────────────
// user_id is read from the JWT token by the backend

export function createOrder(items) {
  return api.post('/orders', {
    items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
  })
}

export function getOrders() {
  return api.get('/orders')
}

export function getOrder(id) {
  return api.get(`/orders/${id}`)
}

export default api
