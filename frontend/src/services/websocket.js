let ws = null
let reconnectTimer = null
let pingTimer = null
let messageCallback = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5

function startPing() {
  stopPing()
  pingTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 30000)
}

function stopPing() {
  if (pingTimer) {
    clearInterval(pingTimer)
    pingTimer = null
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.warn('[WS] Max reconnect attempts reached. Giving up.')
    return
  }
  reconnectAttempts++
  console.log(`[WS] Reconnecting (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`)
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    if (messageCallback) {
      connect(messageCallback)
    }
  }, 3000)
}

export function connect(onMessage) {
  messageCallback = onMessage
  if (ws && ws.readyState === WebSocket.OPEN) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${window.location.host}/ws/notifications`

  ws = new WebSocket(url)

  ws.onopen = () => {
    console.log('[WS] Connected')
    reconnectAttempts = 0
    startPing()
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'pong') return
      if (messageCallback) messageCallback(data)
    } catch {
      // ignore non-JSON messages
    }
  }

  ws.onclose = () => {
    console.log('[WS] Disconnected')
    stopPing()
    scheduleReconnect()
  }

  ws.onerror = () => {
    ws.close()
  }
}

export function disconnect() {
  messageCallback = null
  reconnectAttempts = MAX_RECONNECT_ATTEMPTS
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  stopPing()
  if (ws) {
    ws.close()
    ws = null
  }
}
