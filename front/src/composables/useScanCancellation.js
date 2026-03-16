import { ref, watch } from 'vue'

export const useScanCancellation = ({
  loading,
  error,
  endScan,
  externalCancelFlag,
  isMyOwnScan,
  onCancel,
}) => {
  const abortController = ref(null)

  const createAbortController = () => {
    abortController.value = new AbortController()
    return abortController.value
  }

  const clearAbortController = () => {
    abortController.value = null
  }

  const finalizeScan = () => {
    loading.value = false
    endScan()
    clearAbortController()
  }

  const cancelScan = (message = 'Escaneo cancelado') => {
    if (!loading.value) return

    if (abortController.value) {
      abortController.value.abort()
    }

    if (typeof onCancel === 'function') {
      onCancel()
    }

    error.value = message
    finalizeScan()
  }

  if (externalCancelFlag && isMyOwnScan) {
    watch(externalCancelFlag, (cancelled) => {
      if (cancelled && isMyOwnScan.value && loading.value) {
        cancelScan()
      }
    })
  }

  return {
    abortController,
    createAbortController,
    finalizeScan,
    cancelScan,
  }
}
