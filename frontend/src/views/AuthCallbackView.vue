<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center px-4">
    <div class="text-center">
      <!-- Loading -->
      <template v-if="!error">
        <div class="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-gray-500 text-sm">Completing sign-in…</p>
      </template>

      <!-- Error -->
      <template v-else>
        <div class="w-full max-w-sm bg-white rounded-2xl shadow-md p-8">
          <p class="text-red-600 font-medium mb-4">Authentication failed.</p>
          <router-link to="/login" class="text-blue-600 hover:underline text-sm">Back to Login</router-link>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const error = ref(false)

onMounted(async () => {
  const token = route.query.token

  if (!token) {
    error.value = true
    return
  }

  try {
    await authStore.handleGoogleCallback(token)
    router.push('/products')
  } catch {
    error.value = true
  }
})
</script>
