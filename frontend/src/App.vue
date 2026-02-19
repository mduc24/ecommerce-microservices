<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    <router-view />
    <NotificationToast />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import AppHeader from './components/AppHeader.vue'
import NotificationToast from './components/NotificationToast.vue'
import { connect, disconnect } from './services/websocket'
import { useNotifications } from './composables/useNotifications'

const { handleWebSocketMessage } = useNotifications()

onMounted(() => {
  connect(handleWebSocketMessage)
})

onUnmounted(() => {
  disconnect()
})
</script>
