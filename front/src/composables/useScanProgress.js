import { ref } from 'vue'
import { useGlobalWebSocket } from './useWebSocket'

const scanProgress = ref({
  active: false,
  scan_id: null,
  scan_type: null,
  status: 'idle',
  total: 0,
  completed: 0,
  progress: 0,
  current_host: null,
  stage: null,
  network: null,
  result: null,
  results: [],
  host_timeout: null
})

let progressListener = null
let hideTimeout = null
let currentScanId = null
let cancelledScanIds = new Set()

export function useScanProgress() {
  const ws = useGlobalWebSocket()

  const setupProgressListener = () => {
    if (!progressListener) {
      progressListener = ws.on('scan_progress', (data) => {
        // Ignorar mensajes de scans cancelados
        if (data.scan_id && cancelledScanIds.has(data.scan_id)) {
          return
        }

        // Limpiar timeout anterior si existe
        if (hideTimeout) {
          clearTimeout(hideTimeout)
          hideTimeout = null
        }

        // Guardar el scan_id actual
        if (data.scan_id) {
          currentScanId = data.scan_id
        }

        scanProgress.value = {
          active: data.status !== 'completed' && data.status !== 'cancelled',
          scan_id: data.scan_id,
          scan_type: data.scan_type || null,
          status: data.status,
          total: data.total || 0,
          completed: data.completed || 0,
          progress: data.progress || 0,
          current_host: data.current_host || null,
          stage: data.stage || null,
          network: data.network || null,
          result: data.result || null,
          results: data.results || [],
          host_timeout: data.host_timeout || null
        }

        // Si está completado o cancelado, ocultar después de 3 segundos
        if (data.status === 'completed' || data.status === 'cancelled') {
          hideTimeout = setTimeout(() => {
            scanProgress.value.active = false
            scanProgress.value.status = 'idle'
            currentScanId = null
            // Limpiar de la lista de cancelados después de un tiempo
            if (data.scan_id) {
              setTimeout(() => cancelledScanIds.delete(data.scan_id), 5000)
            }
          }, 3000)
        }
      })
    }
  }

  const cancelCurrentScan = () => {
    if (currentScanId && ws.connected.value) {
      // Marcar como cancelado localmente
      cancelledScanIds.add(currentScanId)
      
      // Enviar mensaje de cancelación al backend
      ws.send({
        type: 'cancel_scan',
        scan_id: currentScanId
      })
      
      // Ocultar la barra de progreso inmediatamente
      scanProgress.value.active = false
      scanProgress.value.status = 'cancelled'
    }
  }

  const resetProgress = () => {
    scanProgress.value = {
      active: false,
      scan_id: null,
      scan_type: null,
      status: 'idle',
      total: 0,
      completed: 0,
      progress: 0,
      current_host: null,
      stage: null,
      network: null,
      result: null,
      results: [],
      host_timeout: null
    }
    currentScanId = null
  }

  return {
    scanProgress,
    setupProgressListener,
    resetProgress,
    cancelCurrentScan,
    currentScanId: () => currentScanId
  }
}
