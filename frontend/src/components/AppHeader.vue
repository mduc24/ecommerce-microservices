<script setup>
import { useCartStore } from '../stores/cart'
import { storeToRefs } from 'pinia'

const cart = useCartStore()
const { itemCount } = storeToRefs(cart)
</script>

<template>
  <header class="bg-white shadow-md sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
      <router-link to="/products" class="text-2xl font-bold text-blue-600 hover:text-blue-700">
        E-Commerce
      </router-link>

      <nav class="flex items-center space-x-6 text-gray-600">
        <router-link
          to="/products"
          class="hover:text-blue-600 transition-colors"
          active-class="text-blue-600 font-semibold"
        >
          Products
        </router-link>

        <router-link
          to="/cart"
          class="relative hover:text-blue-600 transition-colors"
          active-class="text-blue-600 font-semibold"
        >
          Cart
          <span
            v-if="itemCount > 0"
            class="absolute -top-2 -right-4 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
          >
            {{ itemCount > 99 ? '99+' : itemCount }}
          </span>
        </router-link>

        <router-link
          to="/orders"
          class="hover:text-blue-600 transition-colors"
          active-class="text-blue-600 font-semibold"
        >
          Orders
        </router-link>
      </nav>
    </div>
  </header>
</template>
