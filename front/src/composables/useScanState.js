import { ref } from 'vue'

// Estado compartido a nivel de módulo (singleton)
const isScanning = ref(false)
const currentScanType = ref('')

export function useScanState() {
  const startScan = (scanType) => {
    isScanning.value = true
    currentScanType.value = scanType
  }

  const endScan = () => {
    isScanning.value = false
    currentScanType.value = ''
  }

  return {
    isScanning,
    currentScanType,
    startScan,
    endScan
  }
}
