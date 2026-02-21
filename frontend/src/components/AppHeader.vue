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

        <!-- Authenticated nav -->
        <template v-if="authStore.isAuthenticated">
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

          <span class="text-sm text-gray-500">{{ authStore.user?.username }}</span>

          <button
            @click="authStore.logout()"
            class="text-sm text-red-500 hover:text-red-700 transition-colors"
          >
            Logout
          </button>
        </template>

        <!-- Guest nav -->
        <template v-else>
          <router-link
            to="/login"
            class="hover:text-blue-600 transition-colors"
            active-class="text-blue-600 font-semibold"
          >
            Login
          </router-link>

          <router-link
            to="/register"
            class="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Register
          </router-link>
        </template>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { useCartStore } from '../stores/cart'
import { useAuthStore } from '../stores/auth'
import { storeToRefs } from 'pinia'

const cart = useCartStore()
const { itemCount } = storeToRefs(cart)
const authStore = useAuthStore()
</script>
