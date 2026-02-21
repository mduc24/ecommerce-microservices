<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <!-- Back -->
    <button
      @click="router.back()"
      class="text-gray-600 hover:text-gray-900 mb-6 inline-flex items-center gap-1 cursor-pointer"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      Back to Products
    </button>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 404 -->
    <div v-else-if="error === 404" class="text-center py-20">
      <h2 class="text-2xl font-bold text-gray-900">Product not found</h2>
      <p class="text-gray-500 mt-2">This product doesn't exist or has been removed.</p>
      <router-link
        to="/products"
        class="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Back to Products
      </router-link>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-20">
      <p class="text-red-500 text-lg">{{ error }}</p>
      <button
        @click="fetchProduct"
        class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer"
      >
        Retry
      </button>
    </div>

    <!-- Product -->
    <div v-else-if="product" class="grid md:grid-cols-2 gap-10">
      <!-- Image -->
      <div class="bg-gray-200 rounded-lg flex items-center justify-center h-80 md:h-96">
        <svg class="w-24 h-24 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      </div>

      <!-- Details -->
      <div>
        <span v-if="product.category" class="text-sm text-blue-600 font-medium uppercase tracking-wide">
          {{ product.category }}
        </span>
        <h1 class="text-3xl font-bold text-gray-900 mt-1">{{ product.name }}</h1>
        <p class="text-3xl font-bold text-blue-600 mt-3">${{ formatPrice(product.price) }}</p>
        <p class="text-gray-600 mt-4 leading-relaxed">{{ product.description || 'No description available.' }}</p>

        <!-- Stock -->
        <div class="mt-4">
          <span
            :class="product.stock_quantity > 0 ? 'text-green-600' : 'text-red-500'"
            class="font-medium"
          >
            {{ product.stock_quantity > 0 ? `In Stock (${product.stock_quantity} available)` : 'Out of Stock' }}
          </span>
        </div>

        <!-- SKU -->
        <p class="text-sm text-gray-400 mt-2">SKU: {{ product.sku }}</p>

        <!-- Quantity + Add to Cart -->
        <div v-if="product.stock_quantity > 0" class="mt-6 flex items-center gap-4">
          <div class="flex items-center border border-gray-300 rounded-lg">
            <button
              @click="quantity > 1 && quantity--"
              :disabled="quantity <= 1"
              class="px-3 py-2 text-gray-600 hover:bg-gray-100 disabled:opacity-30 cursor-pointer rounded-l-lg"
            >
              -
            </button>
            <span class="px-4 py-2 font-medium min-w-[3rem] text-center">{{ quantity }}</span>
            <button
              @click="quantity < product.stock_quantity && quantity++"
              :disabled="quantity >= product.stock_quantity"
              class="px-3 py-2 text-gray-600 hover:bg-gray-100 disabled:opacity-30 cursor-pointer rounded-r-lg"
            >
              +
            </button>
          </div>

          <button
            @click="addToCart"
            class="flex-1 py-3 px-6 rounded-lg text-white font-medium transition-colors cursor-pointer"
            :class="showToast ? 'bg-green-500' : 'bg-blue-600 hover:bg-blue-700'"
          >
            {{ showToast ? 'Added to Cart!' : 'Add to Cart' }}
          </button>
        </div>

        <!-- Out of stock button -->
        <div v-else class="mt-6">
          <button disabled class="w-full py-3 px-6 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed font-medium">
            Out of Stock
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProduct } from '../services/api'
import { useCartStore } from '../stores/cart'
import { useNotifications } from '../composables/useNotifications'

const route = useRoute()
const router = useRouter()
const cart = useCartStore()
const { addNotification } = useNotifications()

const product = ref(null)
const loading = ref(true)
const error = ref(null)
const quantity = ref(1)
const showToast = ref(false)

async function fetchProduct() {
  loading.value = true
  error.value = null
  try {
    const { data } = await getProduct(route.params.id)
    product.value = data
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = 404
      addNotification({ type: 'error', title: 'Not Found', message: 'Product not found' })
    } else {
      error.value = err.message || 'Failed to load product'
      addNotification({ type: 'error', title: 'Error', message: error.value })
    }
  } finally {
    loading.value = false
  }
}

onMounted(fetchProduct)

function addToCart() {
  if (!product.value) return
  cart.addItem(product.value, quantity.value)
  showToast.value = true
  setTimeout(() => (showToast.value = false), 1500)
}

function formatPrice(price) {
  return Number(price).toFixed(2)
}
</script>
