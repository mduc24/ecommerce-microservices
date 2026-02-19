import { ref } from 'vue'

const notifications = ref([])

const eventTypeMap = {
  order_confirmation: 'success',
  order_status_update: 'info',
}

export function useNotifications() {
  function addNotification({ type = 'info', title, message }) {
    const id = Date.now()
    notifications.value.push({ id, type, title, message })

    setTimeout(() => removeNotification(id), 4000)

    // Keep max 3 toasts
    if (notifications.value.length > 3) {
      notifications.value.shift()
    }
  }

  function removeNotification(id) {
    notifications.value = notifications.value.filter((n) => n.id !== id)
  }

  function handleWebSocketMessage(data) {
    if (data.type === 'notification') {
      addNotification({
        type: eventTypeMap[data.data.event_type] || 'info',
        title: data.data.subject,
        message: data.data.message,
      })
    }
  }

  return { notifications, addNotification, removeNotification, handleWebSocketMessage }
}
