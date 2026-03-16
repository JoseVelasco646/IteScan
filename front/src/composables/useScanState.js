import { ref, computed } from 'vue'
import { useGlobalWebSocket } from './useWebSocket'
import { suppressProgressAfterCancellation } from './useScanProgress'

const isScanning = ref(false)
const currentScanType = ref('')
const currentAbortController = ref(null)
const currentScanId = ref(null)


const externalCancelFlag = ref(false)
let scanProgressListenerInitialized = false


const scanTypeLabels = {
  'ping': 'Ping Scan',
  'port-scan': 'Port Scan',
  'service-scan': 'Service Scan',
  'full-scan-single': 'Full Scan (Individual)',
  'full-scan-range': 'Full Scan (Rango)',
}

export function useScanState() {
  const ws = useGlobalWebSocket()

  if (!scanProgressListenerInitialized) {
    ws.on('scan_progress', (data) => {
      if (!isScanning.value || currentScanId.value) return
      if (!data || !data.scan_id) return

      currentScanId.value = data.scan_id
    })

    scanProgressListenerInitialized = true
  }

  const scanDisplayName = computed(() => {
    return scanTypeLabels[currentScanType.value] || currentScanType.value || ''
  })

  const startScan = (scanType, abortController = null) => {
    isScanning.value = true
    currentScanType.value = scanType
    currentAbortController.value = abortController
    externalCancelFlag.value = false
  }

  const setScanId = (scanId) => {
    currentScanId.value = scanId
  }

  const endScan = () => {
    isScanning.value = false
    currentScanType.value = ''
    currentAbortController.value = null
    currentScanId.value = null
    externalCancelFlag.value = false
  }


  const cancelActiveScan = () => {
    if (currentScanId.value) {
      suppressProgressAfterCancellation([currentScanId.value])
    } else {
      suppressProgressAfterCancellation()
    }

    if (ws.connected.value) {
      if (currentScanId.value) {
        ws.send(JSON.stringify({
          type: 'cancel_scan',
          scan_id: currentScanId.value
        }))
      } else {
        ws.send(JSON.stringify({
          type: 'cancel_active_scans'
        }))
      }
    }

    if (currentAbortController.value) {
      currentAbortController.value.abort()
    }

    externalCancelFlag.value = true
  }

  return {
    isScanning,
    currentScanType,
    currentScanId,
    scanDisplayName,
    currentAbortController,
    externalCancelFlag,
    startScan,
    setScanId,
    endScan,
    cancelActiveScan
  }
}
