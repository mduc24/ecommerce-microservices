<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '../stores/cart'

const props = defineProps({
  product: { type: Object, required: true },
})

const router = useRouter()
const cart = useCartStore()
const added = ref(false)

function viewDetails() {
  router.push(`/products/${props.product.id}`)
}

function addToCart() {
  cart.addItem(props.product)
  added.value = true
  setTimeout(() => (added.value = false), 1500)
}

function formatPrice(price) {
  return Number(price).toFixed(2)
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow overflow-hidden flex flex-col">
    <!-- Image placeholder -->
    <div class="h-48 bg-gray-200 flex items-center justify-center">
      <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>
    </div>

    <!-- Content -->
    <div class="p-4 flex flex-col flex-1">
      <div class="flex-1">
        <span v-if="product.category" class="text-xs text-blue-600 font-medium uppercase tracking-wide">
          {{ product.category }}
        </span>
        <h3 class="text-lg font-semibold text-gray-900 mt-1 line-clamp-2">{{ product.name }}</h3>
        <p class="text-sm text-gray-500 mt-1 line-clamp-2">{{ product.description || 'No description' }}</p>
      </div>

      <!-- Price & Stock -->
      <div class="mt-3 flex items-center justify-between">
        <span class="text-xl font-bold text-gray-900">${{ formatPrice(product.price) }}</span>
        <span
          :class="product.stock_quantity > 0 ? 'text-green-600' : 'text-red-500'"
          class="text-sm font-medium"
        >
          {{ product.stock_quantity > 0 ? `In Stock (${product.stock_quantity})` : 'Out of Stock' }}
        </span>
      </div>

      <!-- Actions -->
      <div class="mt-4 flex gap-2">
        <button
          @click="viewDetails"
          class="flex-1 py-2 px-3 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer"
        >
          View Details
        </button>
        <button
          @click="addToCart"
          :disabled="product.stock_quantity === 0"
          class="flex-1 py-2 px-3 rounded-lg text-sm font-medium text-white transition-colors cursor-pointer"
          :class="[
            product.stock_quantity === 0
              ? 'bg-gray-300 cursor-not-allowed'
              : added
                ? 'bg-green-500'
                : 'bg-blue-600 hover:bg-blue-700'
          ]"
        >
          {{ added ? 'Added!' : 'Add to Cart' }}
        </button>
      </div>
    </div>
  </div>
</template>
