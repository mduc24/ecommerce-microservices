<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-6">My Orders</h1>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-20">
      <p class="text-red-500 text-lg">{{ error }}</p>
      <button
        @click="$router.go(0)"
        class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
      >
        Retry
      </button>
    </div>

    <!-- Empty -->
    <div v-else-if="orders.length === 0" class="text-center py-20">
      <svg class="w-20 h-20 text-gray-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <p class="text-gray-500 text-lg mt-4">No orders yet</p>
      <router-link
        to="/products"
        class="mt-4 inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Start Shopping
      </router-link>
    </div>

    <!-- Orders List -->
    <div v-else class="space-y-4">
      <div
        v-for="order in orders"
        :key="order.id"
        class="bg-white rounded-lg shadow-md overflow-hidden"
      >
        <!-- Order Header -->
        <div class="p-4">
          <div class="flex justify-between items-start">
            <div>
              <h3 class="font-semibold text-gray-900 text-lg">Order #{{ order.id }}</h3>
              <p class="text-sm text-gray-500 mt-1">{{ formatDate(order.created_at) }}</p>
            </div>
            <span
              :class="statusColors[order.status]"
              class="px-3 py-1 rounded-full text-sm font-medium capitalize"
            >
              {{ order.status }}
            </span>
          </div>

          <!-- Summary -->
          <div class="mt-3 flex items-center justify-between">
            <span class="text-sm text-gray-500">
              {{ order.items.length }} {{ order.items.length === 1 ? 'item' : 'items' }}
            </span>
            <span class="text-xl font-bold text-gray-900">${{ formatPrice(order.total_amount) }}</span>
          </div>

          <!-- Toggle Details -->
          <button
            @click="toggleDetails(order.id)"
            class="mt-3 text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors cursor-pointer"
          >
            {{ expandedOrders.has(order.id) ? 'Hide Details' : 'View Details' }}
          </button>
        </div>

        <!-- Expanded Items -->
        <div v-if="expandedOrders.has(order.id)" class="border-t border-gray-100 bg-gray-50 p-4">
          <div
            v-for="item in order.items"
            :key="item.id"
            class="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0"
          >
            <div>
              <p class="font-medium text-gray-900">{{ item.product_name }}</p>
              <p class="text-sm text-gray-500">
                ${{ formatPrice(item.product_price) }} x {{ item.quantity }}
              </p>
            </div>
            <p class="font-medium text-gray-900">${{ formatPrice(item.subtotal) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getOrders } from '../services/api'

const orders = ref([])
const loading = ref(true)
const error = ref(null)
const expandedOrders = ref(new Set())

const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  shipped: 'bg-purple-100 text-purple-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

onMounted(async () => {
  try {
    const { data } = await getOrders()
    orders.value = data.orders || data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load orders'
  } finally {
    loading.value = false
  }
})

function toggleDetails(orderId) {
  if (expandedOrders.value.has(orderId)) {
    expandedOrders.value.delete(orderId)
  } else {
    expandedOrders.value.add(orderId)
  }
}

function formatPrice(price) {
  return Number(price).toFixed(2)
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>
