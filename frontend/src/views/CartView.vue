<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-6">Shopping Cart</h1>

    <!-- Empty State -->
    <div v-if="cart.isEmpty" class="text-center py-20">
      <svg class="w-20 h-20 text-gray-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
      </svg>
      <p class="text-gray-500 text-lg mt-4">Your cart is empty</p>
      <router-link
        to="/products"
        class="mt-4 inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Browse Products
      </router-link>
    </div>

    <!-- Cart Items -->
    <div v-else>
      <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div
          v-for="item in cart.items"
          :key="item.product_id"
          class="flex items-center justify-between p-4 border-b border-gray-100 last:border-b-0"
        >
          <!-- Item Info -->
          <div class="flex-1">
            <h3 class="font-semibold text-gray-900">{{ item.name }}</h3>
            <p class="text-gray-500 text-sm">${{ formatPrice(item.price) }} each</p>
          </div>

          <!-- Quantity Controls -->
          <div class="flex items-center gap-4 mx-6">
            <div class="flex items-center border border-gray-300 rounded-lg">
              <button
                @click="cart.updateQuantity(item.product_id, item.quantity - 1)"
                class="px-3 py-1 text-gray-600 hover:bg-gray-100 cursor-pointer rounded-l-lg"
              >
                -
              </button>
              <span class="px-3 py-1 font-medium min-w-[2.5rem] text-center">{{ item.quantity }}</span>
              <button
                @click="cart.updateQuantity(item.product_id, item.quantity + 1)"
                class="px-3 py-1 text-gray-600 hover:bg-gray-100 cursor-pointer rounded-r-lg"
              >
                +
              </button>
            </div>
          </div>

          <!-- Subtotal -->
          <div class="text-right min-w-[5rem]">
            <p class="font-bold text-gray-900">${{ formatPrice(item.price * item.quantity) }}</p>
          </div>

          <!-- Remove -->
          <button
            @click="cart.removeItem(item.product_id)"
            class="ml-4 text-red-400 hover:text-red-600 transition-colors cursor-pointer"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Summary -->
      <div class="mt-6 bg-white rounded-lg shadow-md p-6">
        <div class="flex justify-between items-center text-lg">
          <span class="text-gray-600">Total ({{ cart.itemCount }} items)</span>
          <span class="text-2xl font-bold text-gray-900">${{ formatPrice(cart.totalPrice) }}</span>
        </div>

        <!-- Error -->
        <div v-if="error" class="mt-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
          {{ error }}
        </div>

        <!-- Success -->
        <div v-if="orderSuccess" class="mt-4 p-3 bg-green-50 text-green-600 rounded-lg font-medium">
          Order #{{ orderId }} placed successfully! Redirecting...
        </div>

        <!-- Actions -->
        <div class="mt-4 flex gap-3">
          <router-link
            to="/products"
            class="px-4 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors text-center"
          >
            Continue Shopping
          </router-link>
          <button
            @click="checkout"
            :disabled="loading || orderSuccess"
            class="flex-1 py-3 px-6 rounded-lg text-white font-medium transition-colors cursor-pointer"
            :class="loading || orderSuccess ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'"
          >
            {{ loading ? 'Processing...' : 'Place Order' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '../stores/cart'
import { useNotifications } from '../composables/useNotifications'
import { createOrder } from '../services/api'

const router = useRouter()
const cart = useCartStore()
const { addNotification } = useNotifications()

const loading = ref(false)
const error = ref(null)
const orderSuccess = ref(false)
const orderId = ref(null)

function formatPrice(price) {
  return Number(price).toFixed(2)
}

async function checkout() {
  loading.value = true
  error.value = null

  try {
    const { data } = await createOrder(cart.items)
    orderId.value = data.id
    orderSuccess.value = true
    cart.clearCart()

    setTimeout(() => router.push('/orders'), 2000)
  } catch (err) {
    error.value = err.message || 'Failed to place order. Please try again.'
    addNotification({ type: 'error', title: 'Checkout Failed', message: error.value })
  } finally {
    loading.value = false
  }
}
</script>
