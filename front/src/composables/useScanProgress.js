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
let cancelListener = null
let hideTimeout = null
let currentScanId = null
let cancelledScanIds = new Set()
let suppressProgressUntil = 0

const markCancelledScans = (scanIds = []) => {
  scanIds.filter(Boolean).forEach((scanId) => cancelledScanIds.add(scanId))
}

export const suppressProgressAfterCancellation = (scanIds = []) => {
  markCancelledScans(scanIds)
  suppressProgressUntil = Date.now() + 1500
  scanProgress.value.active = false
  scanProgress.value.status = 'cancelled'
}

export function useScanProgress() {
  const ws = useGlobalWebSocket()

  const setupProgressListener = () => {
    if (!progressListener) {
      progressListener = ws.on('scan_progress', (data) => {
        if (Date.now() < suppressProgressUntil) {
          return
        }

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

    if (!cancelListener) {
      cancelListener = ws.on('scan_cancelled', (data) => {
        const cancelledIds = []

        if (data?.scan_id) {
          cancelledIds.push(data.scan_id)
        }

        if (Array.isArray(data?.scan_ids)) {
          cancelledIds.push(...data.scan_ids)
        }

        suppressProgressAfterCancellation(cancelledIds)
      })
    }
  }

  const cancelCurrentScan = () => {
    if (currentScanId && ws.connected.value) {
      suppressProgressAfterCancellation([currentScanId])
      
      // Enviar mensaje de cancelación al backend
      ws.send({
        type: 'cancel_scan',
        scan_id: currentScanId
      })
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
