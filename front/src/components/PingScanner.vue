<script setup>
import { ref, computed, watch } from 'vue'
import { scannerAPI } from '../api/scanner'
import { RefreshCw, Wifi, Activity, Network, GitBranch, X } from 'lucide-vue-next'
import { useScanState } from '../composables/useScanState'
import { useScanProgress } from '../composables/useScanProgress'
import { useToast } from '../composables/useToast'
import { useTheme } from '../composables/useTheme'
import { usePermissions } from '../composables/usePermissions'
import { useIPValidation } from '../composables/useIPValidation'
import ActiveScanBanner from './ActiveScanBanner.vue'
import NumberStepper from './NumberStepper.vue'

const { isScanning, currentScanType, startScan, endScan, externalCancelFlag } = useScanState()
const { isDark } = useTheme()
const { canExecuteScans } = usePermissions()
const { cancelCurrentScan } = useScanProgress()
const toast = useToast()
const { isValidCIDR, isValidIP, validateIPRange, getErrorMessage } = useIPValidation()

// Este componente es dueño de escaneos tipo 'ping'
const isMyOwnScan = computed(() => currentScanType.value === 'ping')
const otherScanActive = computed(() => isScanning.value && !isMyOwnScan.value)

const hosts = ref('')
const cidr = ref('')
const rangeStart = ref('192.168.0.1')
const rangeEnd = ref('192.168.0.10')
const hostTimeout = ref(2) 
const concurrency = ref(50)
const results = ref([])
const loading = ref(false)
const error = ref('')
const scanType = ref('hosts')
const scanCompleted = ref(false)
const filterMode = ref('all') // 'active' = solo activas, 'all' = activas e inactivas
const saving = ref(false)
const activos = computed(() => results.value.filter((r) => r.status === 'up').length)
const inactivos = computed(() => results.value.filter((r) => r.status !== 'up').length)
const filteredResults = computed(() => {
  if (filterMode.value === 'active') {
    return results.value.filter((r) => r.status === 'up')
  }
  return results.value
})
let abortController = null

// noti
const playNotificationSound = () => {
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)

    // Configurar el sonido
    oscillator.frequency.value = 800
    oscillator.type = 'sine'

    gainNode.gain.setValueAtTime(0, audioContext.currentTime)
    gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.05)
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)

    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + 0.5)
  } catch (err) {
    // audio not supported
  }
}

const pingHosts = async () => {
  if (!hosts.value.trim()) {
    error.value = 'Por favor ingresa al menos un host'
    toast.error('Por favor ingrese al menos una IP', 'Escáner Ping')
    return
  }

//validar ip
  const hostList = hosts.value
    .split('\n')
    .map((h) => h.trim())
    .filter(Boolean)
  
  const invalidHosts = hostList.filter(host => !isValidIP(host))
  if (invalidHosts.length > 0) {
    error.value = `IPs inválidas: ${invalidHosts.join(', ')}`
    toast.error(`IPs inválidas detectadas. Solo se aceptan direcciones IP: ${invalidHosts.slice(0, 3).join(', ')}${invalidHosts.length > 3 ? '...' : ''}`, 'Escáner Ping')
    return
  }

  loading.value = true
  scanCompleted.value = false
  error.value = ''
  results.value = []
  abortController = new AbortController()
  startScan('ping', abortController)

  try {
    const data = await scannerAPI.pingHosts(hostList, abortController.signal, hostTimeout.value, concurrency.value)
    results.value = data.results || data
    scanCompleted.value = true
    playNotificationSound() 
    toast.success(`Scan completado: ${activos.value} hosts activos encontrados`, 'Escáner Ping')
  } catch (err) {
    if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
      error.value = err.response?.data?.detail || 'Escaneo cancelado'
      toast.warning('Escaneo cancelado por el usuario', 'Escáner Ping')
    } else {
      error.value = err.response?.data?.detail || err.message || 'Error ejecutando ping'
      toast.error(error.value, 'Escáner Ping')
    }
  } finally {
    loading.value = false
    endScan()
    abortController = null
  }
}

const scanNetwork = async () => {
  if (!cidr.value.trim()) {
    error.value = 'Por favor ingresa una red CIDR'
    toast.error('Por favor ingrese una red CIDR', 'Escáner Ping')
    return
  }

  // Validar formato CIDR
  if (!isValidCIDR(cidr.value)) {
    error.value = getErrorMessage('cidr')
    toast.error(error.value, 'Escáner Ping')
    return
  }

  loading.value = true
  scanCompleted.value = false
  error.value = ''
  results.value = []
  abortController = new AbortController()
  startScan('ping', abortController)

  try {
    const data = await scannerAPI.scanNetwork(cidr.value, abortController.signal, hostTimeout.value, concurrency.value)
    results.value = data.results || data
    scanCompleted.value = true
    playNotificationSound() 
  } catch (err) {
    if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
      error.value = err.response?.data?.detail || 'Error...'
    } else {
      error.value = err.response?.data?.detail || err.message || 'Error escaneando red'
    }
  } finally {
    loading.value = false
    endScan()
    abortController = null
  }
}

const scanRange = async () => {
  if (!rangeStart.value.trim() || !rangeEnd.value.trim()) {
    error.value = 'Por favor ingresa IP de inicio y fin'
    toast.error('Por favor ingrese ambas IPs (inicial y final)', 'Escáner Ping')
    return
  }

  // Validar el rango de IPs
  const validation = validateIPRange(rangeStart.value, rangeEnd.value)
  if (!validation.valid) {
    error.value = validation.message
    toast.error(error.value, 'Escáner Ping')
    return
  }

  loading.value = true
  scanCompleted.value = false
  error.value = ''
  results.value = []
  abortController = new AbortController()
  startScan('ping', abortController)

  try {
    const startParts = rangeStart.value.split('.')
    const endParts = rangeEnd.value.split('.')

    if (startParts.length !== 4 || endParts.length !== 4) {
      error.value = 'Formato de IP inválido'
      loading.value = false
      return
    }

    if (startParts[0] !== endParts[0] || startParts[1] !== endParts[1]) {
      error.value = 'Los dos primeros octetos deben ser iguales (e.g., 192.168.x.x)'
      loading.value = false
      return
    }

    const hostList = []
    const startThird = parseInt(startParts[2])
    const endThird = parseInt(endParts[2])
    const startLast = parseInt(startParts[3])
    const endLast = parseInt(endParts[3])

    for (let third = startThird; third <= endThird; third++) {
      const start = third === startThird ? startLast : 1
      const end = third === endThird ? endLast : 254
      for (let last = start; last <= end; last++) {
        hostList.push(`${startParts[0]}.${startParts[1]}.${third}.${last}`)
      }
    }

    const batchSize = 100
    const allResults = []
    
    if (hostList.length > batchSize) {
      toast.info(`Escaneando ${hostList.length} hosts${batchSize}...`, 'Escáner Ping')
      
      for (let i = 0; i < hostList.length; i += batchSize) {
        if (abortController?.signal.aborted) {
          break
        }
        
        const batch = hostList.slice(i, i + batchSize)
        const batchNum = Math.floor(i / batchSize) + 1
        const totalBatches = Math.ceil(hostList.length / batchSize)
        
        toast.info(`Procesando ${batchNum}/${totalBatches} (${batch.length} hosts)`, 'Escáner Ping')
        
        try {
          const data = await scannerAPI.pingHosts(batch, abortController.signal, hostTimeout.value, concurrency.value)
          const batchResults = data.results || data
          allResults.push(...batchResults)
          results.value = [...allResults] 
        } catch (batchErr) {
          if (batchErr.name === 'CanceledError' || batchErr.code === 'ERR_CANCELED') {
            throw batchErr
          }
          // batch error, continue with next
        }
      }
      
      results.value = allResults
    } else {
      const data = await scannerAPI.pingHosts(hostList, abortController.signal, hostTimeout.value, concurrency.value)
      results.value = data.results || data
    }
    
    scanCompleted.value = true
    playNotificationSound() 
    toast.success(`Escaneo completado: ${results.value.filter(r => r.status === 'up').length} hosts activos de ${hostList.length}`, 'Escáner Ping')
  } catch (err) {
    if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
      error.value = err.response?.data?.detail || 'Error...'
    } else {
      error.value = err.response?.data?.detail || err.message || 'Error escaneando rango'
    }
  } finally {
    loading.value = false
    endScan()
    abortController = null
  }
}

const handleScan = () => {
  if (scanType.value === 'hosts') {
    pingHosts()
  } else if (scanType.value === 'network') {
    scanNetwork()
  } else {
    scanRange()
  }
}

const cancelScan = () => {
  if (abortController) {
    abortController.abort()
  }
  cancelCurrentScan()
  error.value = 'Escaneo cancelado'
  loading.value = false
  endScan()
}

// Detectar cancelación externa (desde ActiveScanBanner u otro componente)
watch(externalCancelFlag, (cancelled) => {
  if (cancelled && isMyOwnScan.value && loading.value) {
    if (abortController) abortController.abort()
    cancelCurrentScan()
    error.value = 'Escaneo cancelado'
    loading.value = false
    endScan()
  }
})

const quickFillRange = (preset) => {
  const baseIP = '192.168.0'
  if (preset === 'small') {
    rangeStart.value = `${baseIP}.1`
    rangeEnd.value = `${baseIP}.10`
  } else if (preset === 'medium') {
    rangeStart.value = `${baseIP}.1`
    rangeEnd.value = `${baseIP}.50`
  } else if (preset === 'full') {
    rangeStart.value = `${baseIP}.1`
    rangeEnd.value = `${baseIP}.254`
  } else if (preset === 'large') {
    rangeStart.value = '192.168.0.1'
    rangeEnd.value = '192.168.7.254'
  }
}

const saveActiveResults = async () => {
  if (!results.value.length) return
  saving.value = true
  try {
    const activeResults = results.value.filter(r => r.status === 'up')
    if (activeResults.length === 0) {
      toast.warning('No hay hosts activos para guardar', 'Escáner Ping')
      return
    }
    const data = await scannerAPI.savePingResults(activeResults)
    toast.success(`Guardados: ${data.saved} nuevos, ${data.updated} actualizados (${data.total} total)`, 'Escáner Ping')
  } catch (err) {
    toast.error('Error al guardar resultados: ' + (err.message || 'desconocido'), 'Escáner Ping')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-8">
    <!-- Banner de escaneo activo de otro tipo -->
    <ActiveScanBanner myScanType="ping" />

    <div 
      class="relative rounded-3xl p-8 shadow-2xl overflow-hidden"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <div class="absolute inset-0 opacity-5">
        <div class="absolute top-0 left-0 w-96 h-96 bg-cyan-500 rounded-full blur-3xl"></div>
        <div class="absolute bottom-0 right-0 w-96 h-96 bg-blue-500 rounded-full blur-3xl"></div>
      </div>
      
      <div class="relative z-10">
        <div class="flex items-center gap-4 mb-3">
          <div class="w-14 h-14 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-cyan-500/30">
            <Wifi class="w-7 h-7 text-white" />
          </div>
          <div>
           <h2 
             class="text-3xl font-extrabold mb-2 tracking-tight"
             :class="isDark() ? 'text-white' : 'text-slate-800'"
           >
              Ping <span class="text-cyan-400">Scan</span>
            </h2>
            <p 
              class="font-tagesschrift text-lg font-semibold mb-2 tracking-wide text-s"
              :class="isDark() ? 'text-gray-200' : 'text-slate-600'"
            >Descubrimiento rápido mediante ICMP</p>
          </div>
        </div>
      </div>
    </div>

    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <button
        @click="scanType = 'hosts'"
        :class="[
          'relative group py-5 px-6 rounded-2xl font-semibold transition-all duration-300',
          scanType === 'hosts'
            ? isDark() ? 'bg-slate-700 border-2 border-slate-500 text-white shadow-lg' : 'bg-cyan-100 border-2 border-cyan-300 text-cyan-900 shadow-lg'
            : isDark() ? 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50' : 'bg-white border border-slate-300 text-slate-600 hover:border-slate-400 hover:bg-slate-50'
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-3">
          <Activity class="w-5 h-5" />
          <span>IPs Individuales</span>
        </div>
      </button>

      <button
        @click="scanType = 'network'"
        :class="[
          'relative group py-5 px-6 rounded-2xl font-semibold transition-all duration-300',
          scanType === 'network'
            ? isDark() ? 'bg-slate-700 border-2 border-slate-500 text-white shadow-lg' : 'bg-cyan-100 border-2 border-cyan-300 text-cyan-900 shadow-lg'
            : isDark() ? 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50' : 'bg-white border border-slate-300 text-slate-600 hover:border-slate-400 hover:bg-slate-50'
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-3">
          <Network class="w-5 h-5" />
          <span>Red CIDR</span>
        </div>
      </button>

      <button
        @click="scanType = 'range'"
        :class="[
          'relative group py-5 px-6 rounded-2xl font-semibold transition-all duration-300',
          scanType === 'range'
            ? isDark() ? 'bg-slate-700 border-2 border-slate-500 text-white shadow-lg' : 'bg-cyan-100 border-2 border-cyan-300 text-cyan-900 shadow-lg'
            : isDark() ? 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50' : 'bg-white border border-slate-300 text-slate-600 hover:border-slate-400 hover:bg-slate-50'
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-3">
          <GitBranch class="w-5 h-5" />
          <span>Rango de IPs</span>
        </div>
      </button>
    </div>

    <!-- INPUT PANEL -->
    <div 
      class="rounded-3xl p-8 shadow-2xl"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <Transition name="fade-slide" mode="out-in">
        <!-- HOSTS INDIVIDUALES -->
        <div v-if="scanType === 'hosts'" key="hosts" class="space-y-4">
          <div class="flex items-center gap-2 mb-3">
            <Activity class="w-5 h-5 text-cyan-400" />
            <label 
              class="text-sm font-semibold uppercase tracking-wide"
              :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
            >Direcciones IP (una por línea)</label>
          </div>
          <textarea
            v-model="hosts"
            rows="6"
            placeholder="192.168.0.1&#10;192.168.0.2&#10;192.168.0.3"
            class="w-full rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 focus:border-cyan-500/50 transition-all resize-none font-mono"
            :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          />
          <p 
            class="text-xs flex items-center gap-2"
            :class="isDark() ? 'text-slate-500' : 'text-slate-600'"
          >
            <span class="inline-block w-2 h-2 bg-cyan-500 rounded-full"></span>
            Solo direcciones IP válidas
          </p>

          <!-- TIMEOUT CONFIG -->
          <div class="mt-4">
            <NumberStepper v-model="hostTimeout" :min="1" :max="30" unit="s"
              label="Timeout por host" hint="Recomendado: 2-5s para redes locales"
              accent-color="cyan" :show-range="true" />
          </div>

          <!-- CONCURRENCIA -->
          <div class="mt-4">
            <NumberStepper v-model="concurrency" :min="1" :max="100" unit="IPs"
              label="IPs simultáneas" :presets="[10, 25, 50, 100]"
              accent-color="cyan" :show-range="true" />
          </div>
        </div>

        <!-- RED CIDR -->
        <div v-else-if="scanType === 'network'" key="network" class="space-y-4">
          <div class="flex items-center gap-2 mb-3">
            <Network class="w-5 h-5 text-cyan-400" />
            <label 
              class="text-sm font-semibold uppercase tracking-wide"
              :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
            >Red CIDR</label>
          </div>
          <input
            v-model="cidr"
            placeholder="192.168.0.0/24"
            class="w-full rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 focus:border-cyan-500/50 transition-all font-mono text-lg"
            :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          />
          <div 
            class="rounded-xl p-4"
            :class="isDark() ? 'bg-slate-800/30 border border-slate-700/50' : 'bg-slate-50 border border-slate-200'"
          >
            <p 
              class="text-xs mb-2 font-semibold"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
            >Ejemplos de notación CIDR:</p>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="flex items-center gap-2">
                <span class="text-cyan-400 font-mono">/24</span>
                <span :class="isDark() ? 'text-slate-500' : 'text-slate-400'">=</span>
                <span :class="isDark() ? 'text-slate-400' : 'text-slate-600'">254 hosts</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-cyan-400 font-mono">/28</span>
                <span :class="isDark() ? 'text-slate-500' : 'text-slate-400'">=</span>
                <span :class="isDark() ? 'text-slate-400' : 'text-slate-600'">14 hosts</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-cyan-400 font-mono">/21</span>
                <span :class="isDark() ? 'text-slate-500' : 'text-slate-400'">=</span>
                <span :class="isDark() ? 'text-slate-400' : 'text-slate-600'">2048 hosts</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-cyan-400 font-mono">/30</span>
                <span :class="isDark() ? 'text-slate-500' : 'text-slate-400'">=</span>
                <span :class="isDark() ? 'text-slate-400' : 'text-slate-600'">2 hosts</span>
              </div>
            </div>
          </div>
          
          <div class="mt-4">
            <NumberStepper v-model="hostTimeout" :min="1" :max="30" unit="s"
              label="Timeout por host" hint="Recomendado: 2-5s para redes locales"
              accent-color="cyan" :show-range="true" />
          </div>

          <!-- CONCURRENCIA -->
          <div class="mt-4">
            <NumberStepper v-model="concurrency" :min="1" :max="200" unit="IPs"
              label="IPs simultáneas" :presets="[10, 25, 50, 100]"
              accent-color="cyan" :show-range="true" />
          </div>
        </div>

        <!-- RANGO DE IPS -->
        <div v-else key="range" class="space-y-6">
          <div class="flex items-center gap-2 mb-3">
            <GitBranch class="w-5 h-5 text-cyan-400" />
            <label 
              class="text-sm font-semibold uppercase tracking-wide"
              :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
            >Rango de Direcciones IP</label>
          </div>
          
          <div class="grid md:grid-cols-2 gap-4">
            <div>
              <label 
                class="text-xs font-semibold mb-2 block uppercase"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
              >IP Inicial</label>
              <input
                v-model="rangeStart"
                placeholder="192.168.0.1"
                class="w-full rounded-xl px-5 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 focus:border-cyan-500/50 transition-all font-mono"
                :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              />
            </div>
            <div>
              <label 
                class="text-xs font-semibold mb-2 block uppercase"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
              >IP Final</label>
              <input
                v-model="rangeEnd"
                placeholder="192.168.0.254"
                class="w-full rounded-xl px-5 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 focus:border-cyan-500/50 transition-all font-mono"
                :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              />
            </div>
          </div>

          <div>
            <label
              class="text-xs font-semibold text-slate-400 mb-2 block uppercase tracking-wider"
              >Rangos predefinidos</label
            >
            <div class="grid grid-cols-2 gap-2">
              <button
                @click="quickFillRange('small')"
                class="group bg-slate-900/80 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-lg p-2.5 transition-all duration-200 flex items-center gap-2"
              >
                <div
                  class="w-8 h-8 bg-slate-800 group-hover:bg-slate-700 rounded-md flex items-center justify-center transition-colors"
                >
                  <span
                    class="text-lg font-bold text-slate-300 group-hover:text-white"
                    >10</span
                  >
                </div>
                <span
                  class="text-xs text-slate-400 group-hover:text-slate-300 font-medium"
                  >Hosts</span
                >
              </button>
              <button
                @click="quickFillRange('medium')"
                class="group bg-slate-900/80 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-lg p-2.5 transition-all duration-200 flex items-center gap-2"
              >
                <div
                  class="w-8 h-8 bg-slate-800 group-hover:bg-slate-700 rounded-md flex items-center justify-center transition-colors"
                >
                  <span
                    class="text-lg font-bold text-slate-300 group-hover:text-white"
                    >50</span
                  >
                </div>
                <span
                  class="text-xs text-slate-400 group-hover:text-slate-300 font-medium"
                  >Hosts</span
                >
              </button>
              <button
                @click="quickFillRange('full')"
                class="group bg-slate-900/80 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-lg p-2.5 transition-all duration-200 flex items-center gap-2"
              >
                <div
                  class="w-8 h-8 bg-slate-800 group-hover:bg-slate-700 rounded-md flex items-center justify-center transition-colors"
                >
                  <span
                    class="text-sm font-bold text-slate-300 group-hover:text-white"
                    >254</span
                  >
                </div>
                <span
                  class="text-xs text-slate-400 group-hover:text-slate-300 font-medium"
                  >Subred</span
                >
              </button>
              <button
                @click="quickFillRange('large')"
                class="group bg-slate-900/80 hover:bg-slate-800 border border-amber-600/50 hover:border-amber-500 rounded-lg p-2.5 transition-all duration-200 flex items-center gap-2"
              >
                <div
                  class="w-8 h-8 bg-slate-800 group-hover:bg-amber-900/30 rounded-md flex items-center justify-center transition-colors"
                >
                  <span
                    class="text-xs font-bold text-slate-300 group-hover:text-amber-400"
                    >2K</span
                  >
                </div>
                <span
                  class="text-xs text-slate-400 group-hover:text-amber-300 font-medium"
                  >Masivo</span
                >
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <div class="space-y-3">
      <button
        v-if="canExecuteScans"
        @click="handleScan"
        :disabled="loading || otherScanActive"
        class="w-full group relative overflow-hidden py-6 rounded-2xl font-bold text-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl"
        :class="loading 
          ? 'bg-slate-800 border-2 border-slate-600' 
          : 'bg-gradient-to-r from-cyan-600 via-blue-600 to-cyan-600 hover:from-cyan-500 hover:via-blue-500 hover:to-cyan-500 border-2 border-cyan-400/50 hover:border-cyan-300 shadow-cyan-500/20 hover:shadow-cyan-400/30'"
      >
        <div v-if="!loading && !otherScanActive" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
        
        <div class="relative z-10 flex items-center justify-center gap-3 text-white">
          <RefreshCw :class="['w-6 h-6', loading && 'animate-spin']" />
          <span class="tracking-wide">
            {{ loading ? 'Escaneando Red...' : scanCompleted ? 'Escaneo Completo' : otherScanActive ? 'Otro escaneo en curso...' : 'Iniciar Escaneo Ping' }}
          </span>
        </div>
      </button>

      <button
        v-if="loading"
        @click="cancelScan"
        class="w-full group relative py-4 rounded-2xl font-bold text-lg transition-all duration-300 bg-red-900/50 hover:bg-red-800/60 border-2 border-red-700 hover:border-red-600 text-white shadow-lg"
      >
        <div class="relative z-10 flex items-center justify-center gap-3">
          <span>Cancelar Escaneo</span>
        </div>
      </button>
    </div>

    <Transition name="fade-slide">
      <div v-if="error" class="bg-red-500/10 border-2 border-red-500/50 rounded-2xl p-5 flex items-start gap-3 shadow-lg shadow-red-500/20">
        <div class="w-10 h-10 bg-red-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
          <span class="text-xl">⚠️</span>
        </div>
        <div class="flex-1">
          <p class="font-semibold text-red-300 mb-1">Error en el Escaneo</p>
          <p class="text-sm text-red-400">{{ error }}</p>
        </div>
      </div>
    </Transition>

    <Transition name="fade-slide">
      <div v-if="results.length" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-gradient-to-br from-emerald-900/20 to-emerald-950/20 border border-emerald-500/30 rounded-2xl p-6 shadow-xl stagger-item-scale">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-emerald-400 text-sm uppercase tracking-wider font-semibold mb-1">Hosts Activos</p>
              <p class="text-5xl font-bold text-emerald-400">{{ activos }}</p>
            </div>
            <div class="w-16 h-16 bg-emerald-500/20 rounded-2xl flex items-center justify-center">
              <span class="text-4xl">.</span>
            </div>
          </div>
        </div>
        
        <div class="bg-gradient-to-br from-red-900/20 to-red-950/20 border border-red-500/30 rounded-2xl p-6 shadow-xl stagger-item-scale">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-red-400 text-sm uppercase tracking-wider font-semibold mb-1">Hosts Inactivos</p>
              <p class="text-5xl font-bold text-red-400">{{ inactivos }}</p>
            </div>
            <div class="w-16 h-16 bg-red-500/20 rounded-2xl flex items-center justify-center">
              <span class="text-4xl">.</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- FILTRO Y GUARDAR -->
    <Transition name="fade-slide">
      <div v-if="results.length" class="flex flex-wrap items-center gap-3">
        <!-- Filtro -->
        <div class="flex items-center gap-2 flex-1">
          <span 
            class="text-sm font-semibold"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
          >Filtro:</span>
          <button
            @click="filterMode = 'active'"
            :class="[
              'px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200',
              filterMode === 'active'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-md'
                : isDark() 
                  ? 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600' 
                  : 'bg-white text-slate-600 border border-slate-300 hover:border-slate-400'
            ]"
          >
            Solo Activas
          </button>
          <button
            @click="filterMode = 'all'"
            :class="[
              'px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200',
              filterMode === 'all'
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/40 shadow-md'
                : isDark() 
                  ? 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600' 
                  : 'bg-white text-slate-600 border border-slate-300 hover:border-slate-400'
            ]"
          >
            Activas e Inactivas
          </button>
        </div>
        <!-- Guardar -->
        <button
          @click="saveActiveResults"
          :disabled="saving || activos === 0"
          class="px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          :class="isDark() 
            ? 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white border border-cyan-500/50 shadow-lg shadow-cyan-500/20' 
            : 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white shadow-lg'"
        >
          <svg v-if="!saving" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
          <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>{{ saving ? 'Guardando...' : `Guardar Activas (${activos})` }}</span>
        </button>
      </div>
    </Transition>

    <!-- TABLA DE RESULTADOS  -->
    <Transition name="fade-slide">
      <div
        v-if="results.length"
        class="rounded-3xl overflow-hidden shadow-2xl"
        :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
      >
        <div 
          class="p-6"
          :class="isDark() ? 'border-b border-slate-700/50 bg-slate-900/50' : 'border-b border-slate-200 bg-slate-50'"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center">
              <Activity class="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 
                class="text-xl font-bold"
                :class="isDark() ? 'text-white' : 'text-slate-800'"
              >Resultados del Escaneo</h3>
              <p 
                class="text-sm"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
              >{{ filteredResults.length }} hosts {{ filterMode === 'active' ? 'activos ' : '' }}mostrados de {{ results.length }} escaneados</p>
            </div>
          </div>
        </div>
        
        <div class="overflow-x-auto">
          <table class="min-w-full">
            <thead>
              <tr :class="isDark() ? 'bg-slate-900/80' : 'bg-slate-100'">
                <th 
                  class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-400 border-b border-slate-700/50' : 'text-slate-600 border-b border-slate-300'"
                >
                  Host
                </th>
                <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                  Estado
                </th>
                <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                  Latencia
                </th>
                <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                  Método
                </th>
              </tr>
            </thead>
            <tbody :class="isDark() ? 'divide-y divide-slate-800/50' : 'divide-y divide-slate-200'">
              <tr
                v-for="(r, i) in filteredResults"
                :key="i"
                class="transition-colors duration-200 stagger-item"
                :class="isDark() ? 'hover:bg-slate-800/30' : 'hover:bg-slate-50'"
              >
                <td 
                  class="px-6 py-4 text-sm font-mono whitespace-nowrap"
                  :class="isDark() ? 'text-white' : 'text-slate-800'"
                >
                  {{ r.host }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    :class="[
                      'inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider shadow-md transition-all',
                      r.status === 'up'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    ]"
                  >
                    <span :class="['inline-block w-2 h-2 rounded-full', r.status === 'up' ? 'bg-emerald-400' : 'bg-red-400']"></span>
                    {{ r.status }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-slate-300 whitespace-nowrap">
                  <span v-if="r.latency_ms" class="font-mono">{{ r.latency_ms }} ms</span>
                  <span v-else class="text-slate-600">—</span>
                </td>
                <td class="px-6 py-4 text-sm text-slate-400 whitespace-nowrap">
                  <span class="px-3 py-1 bg-slate-800/50 rounded-lg font-mono text-xs">
                    {{ r.method }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Transition>
  </div>
</template>
<style scoped>
@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.animate-shimmer {
  animation: shimmer 2s infinite;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
