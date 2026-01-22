<script setup>
import { ref, computed } from 'vue'
import { scannerAPI } from '../api/scanner'
import { RefreshCw, Wifi, Activity, Network, GitBranch, X } from 'lucide-vue-next'
import { useScanState } from '../composables/useScanState'
import { useScanProgress } from '../composables/useScanProgress'
import { useToast } from '../composables/useToast'
import { useTheme } from '../composables/useTheme'
import { useIPValidation } from '../composables/useIPValidation'

const { isScanning, startScan, endScan } = useScanState()
const { isDark } = useTheme()
const { cancelCurrentScan } = useScanProgress()
const toast = useToast()
const { isValidCIDR, isValidIP, validateIPRange, getErrorMessage } = useIPValidation()

const hosts = ref('')
const cidr = ref('')
const rangeStart = ref('192.168.0.1')
const rangeEnd = ref('192.168.0.10')
const hostTimeout = ref(2) 
const results = ref([])
const loading = ref(false)
const error = ref('')
const scanType = ref('hosts')
const scanCompleted = ref(false)
const activos = computed(() => results.value.filter((r) => r.status === 'up').length)
const inactivos = computed(() => results.value.filter((r) => r.status !== 'up').length)
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
    console.log('Audio notification not supported')
  }
}

const pingHosts = async () => {
  if (!hosts.value.trim()) {
    error.value = 'Please enter at least one host'
    toast.error('Por favor ingrese al menos una IP', 'Ping Scanner')
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
    toast.error(`IPs inválidas detectadas. Solo se aceptan direcciones IP: ${invalidHosts.slice(0, 3).join(', ')}${invalidHosts.length > 3 ? '...' : ''}`, 'Ping Scanner')
    return
  }

  loading.value = true
  scanCompleted.value = false
  startScan('ping')
  error.value = ''
  results.value = []
  abortController = new AbortController()

  try {
    const data = await scannerAPI.pingHosts(hostList, abortController.signal, hostTimeout.value)
    results.value = data.results || data
    scanCompleted.value = true
    playNotificationSound() 
    toast.success(`Scan completado: ${activos.value} hosts activos encontrados`, 'Ping Scanner')
  } catch (err) {
    if (err.name === 'CancelError' || err.code === 'ERR_CANCELED') {
      error.value = err.response?.data?.detail || 'Scan Canceld'
      toast.warning('Escaneo cancelado por el usuario', 'Ping Scanner')
    } else {
      error.value = err.response?.data?.detail || err.message || 'Error ejecutando ping'
      toast.error(error.value, 'Ping Scanner')
    }
  } finally {
    loading.value = false
    endScan()
    abortController = null
  }
}

const scanNetwork = async () => {
  if (!cidr.value.trim()) {
    error.value = 'Please enter a CIDR network'
    toast.error('Por favor ingrese una red CIDR', 'Ping Scanner')
    return
  }

  // Validar formato CIDR
  if (!isValidCIDR(cidr.value)) {
    error.value = getErrorMessage('cidr')
    toast.error(error.value, 'Ping Scanner')
    return
  }

  loading.value = true
  scanCompleted.value = false
  error.value = ''
  results.value = []
  abortController = new AbortController()

  try {
    const data = await scannerAPI.scanNetwork(cidr.value, abortController.signal, hostTimeout.value)
    results.value = data.results || data
    scanCompleted.value = true
    playNotificationSound() 
  } catch (err) {
    if (err.name === 'CancelError' || err.code === 'ERR_CANCELED') {
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
    error.value = 'Please enter both start and end IPs'
    toast.error('Por favor ingrese ambas IPs (inicial y final)', 'Ping Scanner')
    return
  }

  // Validar el rango de IPs
  const validation = validateIPRange(rangeStart.value, rangeEnd.value)
  if (!validation.valid) {
    error.value = validation.message
    toast.error(error.value, 'Ping Scanner')
    return
  }

  loading.value = true
  scanCompleted.value = false
  error.value = ''
  results.value = []
  abortController = new AbortController()

  try {
    const startParts = rangeStart.value.split('.')
    const endParts = rangeEnd.value.split('.')

    if (startParts.length !== 4 || endParts.length !== 4) {
      error.value = 'Invalid IP format'
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
      toast.info(`Escaneando ${hostList.length} hosts${batchSize}...`, 'Ping Scanner')
      
      for (let i = 0; i < hostList.length; i += batchSize) {
        if (abortController?.signal.aborted) {
          break
        }
        
        const batch = hostList.slice(i, i + batchSize)
        const batchNum = Math.floor(i / batchSize) + 1
        const totalBatches = Math.ceil(hostList.length / batchSize)
        
        toast.info(`Procesando ${batchNum}/${totalBatches} (${batch.length} hosts)`, 'Ping Scanner')
        
        try {
          const data = await scannerAPI.pingHosts(batch, abortController.signal)
          const batchResults = data.results || data
          allResults.push(...batchResults)
          results.value = [...allResults] 
        } catch (batchErr) {
          if (batchErr.name === 'CancelError' || batchErr.code === 'ERR_CANCELED') {
            throw batchErr
          }
          console.error(`Error en lote ${batchNum}:`, batchErr)
        }
      }
      
      results.value = allResults
    } else {
      const data = await scannerAPI.pingHosts(hostList, abortController.signal)
      results.value = data.results || data
    }
    
    scanCompleted.value = true
    playNotificationSound() 
    toast.success(`Escaneo completado: ${results.value.filter(r => r.status === 'up').length} hosts activos de ${hostList.length}`, 'Ping Scanner')
  } catch (err) {
    if (err.name === 'CancelError' || err.code === 'ERR_CANCELED') {
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
  error.value = 'Scan cancelled'
  loading.value = false
  endScan()
}

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
</script>

<template>
  <div class="space-y-8">
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
            Solo direcciones IP válidas (IPv4 o IPv6)
          </p>

          <!-- TIMEOUT CONFIG -->
          <div class="mt-4">
            <label 
              class="text-sm font-semibold mb-2 block"
              :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
            >
              Timeout por host (segundos)
            </label>
            <div class="flex items-center gap-4">
              <input
                v-model.number="hostTimeout"
                type="number"
                min="1"
                max="30"
                class="w-24 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 font-mono"
                :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white' : 'bg-white border border-slate-300 text-slate-800'"
              />
              <span 
                class="text-xs"
                :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
              >
                Recomendado: 2-5s para redes locales
              </span>
            </div>
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
            <label 
              class="text-sm font-semibold mb-2 block"
              :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
            >
              Timeout por host (segundos)
            </label>
            <div class="flex items-center gap-4">
              <input
                v-model.number="hostTimeout"
                type="number"
                min="1"
                max="30"
                class="w-24 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 font-mono"
                :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white' : 'bg-white border border-slate-300 text-slate-800'"
              />
              <span 
                class="text-xs"
                :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
              >
                Recomendado: 2-5s para redes locales
              </span>
            </div>
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
        @click="handleScan"
        :disabled="loading || isScanning"
        class="w-full group relative overflow-hidden py-6 rounded-2xl font-bold text-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl"
        :class="loading 
          ? 'bg-slate-800 border-2 border-slate-600' 
          : 'bg-gradient-to-r from-cyan-600 via-blue-600 to-cyan-600 hover:from-cyan-500 hover:via-blue-500 hover:to-cyan-500 border-2 border-cyan-400/50 hover:border-cyan-300 shadow-cyan-500/20 hover:shadow-cyan-400/30'"
      >
        <div v-if="!loading && !isScanning" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
        
        <div class="relative z-10 flex items-center justify-center gap-3 text-white">
          <RefreshCw :class="['w-6 h-6', loading && 'animate-spin']" />
          <span class="tracking-wide">
            {{ loading ? 'Escaneando Red...' : scanCompleted ? 'Escaneo Completo' : isScanning ? 'Otro escaneo en curso...' : 'Iniciar Escaneo Ping' }}
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
              >{{ results.length }} hosts escaneados</p>
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
                v-for="(r, i) in results"
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
