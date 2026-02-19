import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
    }
    return Promise.reject(error)
  }
)

// Hardcoded user_id until JWT auth is implemented
const USER_ID = 1

export function getProducts(page = 1, limit = 20) {
  return api.get('/products', { params: { page, limit } })
}

export function getProduct(id) {
  return api.get(`/products/${id}`)
}

export function createOrder(items) {
  return api.post('/orders', {
    items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
  }, {
    params: { user_id: USER_ID },
  })
}

export function getOrders() {
  return api.get('/orders', { params: { user_id: USER_ID } })
}

export function getOrder(id) {
  return api.get(`/orders/${id}`, { params: { user_id: USER_ID } })
}

export default api
