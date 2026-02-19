import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCartStore = defineStore('cart', () => {
  const items = ref([])

  const totalItems = computed(() =>
    items.value.reduce((sum, item) => sum + item.quantity, 0)
  )

  const totalPrice = computed(() =>
    items.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
  )

  function addItem(product, quantity = 1) {
    const existing = items.value.find((item) => item.product_id === product.id)
    if (existing) {
      existing.quantity += quantity
    } else {
      items.value.push({
        product_id: product.id,
        name: product.name,
        price: Number(product.price),
        quantity,
      })
    }
  }

  function removeItem(productId) {
    items.value = items.value.filter((item) => item.product_id !== productId)
  }

  function updateQuantity(productId, quantity) {
    const item = items.value.find((item) => item.product_id === productId)
    if (item) {
      item.quantity = Math.max(1, quantity)
    }
  }

  function clearCart() {
    items.value = []
  }

  return { items, totalItems, totalPrice, addItem, removeItem, updateQuantity, clearCart }
})
