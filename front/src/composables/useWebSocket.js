import { ref, onMounted, onUnmounted } from 'vue'

const WS_BASE = 'ws://192.168.0.12:8000/ws'
const RECONNECT_DELAY = 3000 
const MAX_RECONNECT_ATTEMPTS = 5

export function useWebSocket() {
  const ws = ref(null)
  const connected = ref(false)
  const reconnectTimeout = ref(null)
  const reconnectAttempts = ref(0)
  const listeners = new Map()
  const pingInterval = ref(null)

  const connect = () => {
    if (reconnectAttempts.value >= MAX_RECONNECT_ATTEMPTS) {
      return
    }

    const token = localStorage.getItem('admin_token')
    if (!token) {
      // Sin token no intentar conectar, reintentar después
      reconnectTimeout.value = setTimeout(connect, RECONNECT_DELAY)
      return
    }

    try {
      const wsUrl = `${WS_BASE}?token=${token}`
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        connected.value = true
        reconnectAttempts.value = 0
        
        // Enviar ping cada 30 segundos para mantener viva la conexión
        if (pingInterval.value) {
          clearInterval(pingInterval.value)
        }
        
        pingInterval.value = setInterval(() => {
          if (ws.value?.readyState === WebSocket.OPEN) {
            try {
              ws.value.send('ping')
            } catch (err) {
            }
          } else {
            clearInterval(pingInterval.value)
          }
        }, 30000)
      }

      ws.value.onmessage = (event) => {
        // Ignorar respuesta pong
        if (event.data === 'pong') return
        
        try {
          const message = JSON.parse(event.data)
          const { type, data } = message

          // Llamar a todos los listeners registrados para este tipo de evento
          if (listeners.has(type)) {
            listeners.get(type).forEach(callback => callback(data))
          }

          // También llamar a listeners globales
          if (listeners.has('*')) {
            listeners.get('*').forEach(callback => callback({ type, data }))
          }
        } catch (err) {
        }
      }

      ws.value.onerror = () => {
        // Error de WebSocket - se manejará en onclose
      }

      ws.value.onclose = (event) => {
        connected.value = false
        
        if (pingInterval.value) {
          clearInterval(pingInterval.value)
        }
        
        // Intentar reconectar solo si no fue un cierre limpio por el cliente
        if (event.code !== 1000) {
          reconnectAttempts.value++
          
          reconnectTimeout.value = setTimeout(() => {
            connect()
          }, RECONNECT_DELAY)
        }
      }
    } catch (err) {
      reconnectAttempts.value++
      
      // Intentar reconectar
      if (reconnectAttempts.value < MAX_RECONNECT_ATTEMPTS) {
        reconnectTimeout.value = setTimeout(() => {
          connect()
        }, RECONNECT_DELAY)
      }
    }
  }
  
  const disconnect = () => {
    if (reconnectTimeout.value) {
      clearTimeout(reconnectTimeout.value)
    }
    
    if (pingInterval.value) {
      clearInterval(pingInterval.value)
    }
    
    if (ws.value) {
      ws.value.close(1000, 'Client disconnect')
      ws.value = null
    }
    
    connected.value = false
    reconnectAttempts.value = 0
    listeners.clear()
  }

  const on = (eventType, callback) => {
    if (!listeners.has(eventType)) {
      listeners.set(eventType, new Set())
    }
    listeners.get(eventType).add(callback)

    // Retornar función para remover el listener
    return () => {
      if (listeners.has(eventType)) {
        listeners.get(eventType).delete(callback)
      }
    }
  }

  const off = (eventType, callback) => {
    if (listeners.has(eventType)) {
      listeners.get(eventType).delete(callback)
    }
  }

  const send = (message) => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(typeof message === 'string' ? message : JSON.stringify(message))
    }
  }

  return {
    connected,
    connect,
    disconnect,
    on,
    off,
    send
  }
}

// Instancia global compartida del WebSocket
let globalWS = null

export function useGlobalWebSocket() {
  if (!globalWS) {
    globalWS = useWebSocket()
    globalWS.connect()
  }
  
  return globalWS
}

export function reconnectGlobalWebSocket() {
  if (!globalWS) {
    globalWS = useWebSocket()
  }

  globalWS.disconnect()
  globalWS.connect()

  return globalWS
}

export function disconnectGlobalWebSocket() {
  if (!globalWS) return
  globalWS.disconnect()
}
