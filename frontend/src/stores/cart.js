import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'ecommerce_cart'

function loadCart() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

function saveCart(items) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // localStorage full or unavailable
  }
}

export const useCartStore = defineStore('cart', () => {
  const items = ref(loadCart())

  // Persist on every change
  watch(items, (val) => saveCart(val), { deep: true })

  // Getters
  const itemCount = computed(() =>
    items.value.reduce((sum, item) => sum + item.quantity, 0)
  )

  const totalPrice = computed(() =>
    items.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
  )

  const isEmpty = computed(() => items.value.length === 0)

  // Helper
  function findItem(productId) {
    return items.value.find((item) => item.product_id === productId)
  }

  // Actions
  function addItem(product, quantity = 1) {
    const existing = findItem(product.product_id ?? product.id)
    if (existing) {
      existing.quantity += quantity
    } else {
      items.value.push({
        product_id: product.product_id ?? product.id,
        name: product.name,
        price: Number(product.price),
        quantity,
        image: product.image || null,
      })
    }
  }

  function removeItem(productId) {
    items.value = items.value.filter((item) => item.product_id !== productId)
  }

  function updateQuantity(productId, quantity) {
    if (quantity <= 0) {
      removeItem(productId)
      return
    }
    const item = findItem(productId)
    if (item) {
      item.quantity = quantity
    }
  }

  function clearCart() {
    items.value = []
  }

  return { items, itemCount, totalPrice, isEmpty, addItem, removeItem, updateQuantity, clearCart }
})
