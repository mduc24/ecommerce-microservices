<template>
  <div class="fixed top-4 right-4 z-50 space-y-2">
    <TransitionGroup name="toast">
      <div
        v-for="notif in notifications"
        :key="notif.id"
        class="bg-white rounded-lg shadow-lg p-4 min-w-[320px] max-w-[400px] border-l-4"
        :class="{
          'border-green-500': notif.type === 'success',
          'border-red-500': notif.type === 'error',
          'border-blue-500': notif.type === 'info',
        }"
      >
        <div class="flex justify-between items-start gap-3">
          <div class="flex-1">
            <h4 class="font-semibold text-gray-900 text-sm">{{ notif.title }}</h4>
            <p class="text-sm text-gray-600 mt-1">{{ notif.message }}</p>
          </div>
          <button
            @click="removeNotification(notif.id)"
            class="text-gray-400 hover:text-gray-600 text-lg leading-none cursor-pointer"
          >
            &times;
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useNotifications } from '../composables/useNotifications'

const { notifications, removeNotification } = useNotifications()
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
