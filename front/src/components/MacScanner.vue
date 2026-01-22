<script setup>
import { ref, onMounted } from 'vue'
import { scannerAPI } from '../api/scanner'
import { Radio, RefreshCw, AlertCircle, Network, HardDrive, XCircle, X } from 'lucide-vue-next'
import { useScanState } from '../composables/useScanState'
import { useScanProgress } from '../composables/useScanProgress'
import { useTheme } from '../composables/useTheme'

const { isScanning, startScan, endScan } = useScanState()
const { isDark } = useTheme()
const { scanProgress, setupProgressListener } = useScanProgress()

const cidr = ref('192.168.0.1/24')
const hostTimeout = ref(8)
const results = ref(null)
const loading = ref(false)
const error = ref('')
let abortController = null

onMounted(() => {
  setupProgressListener()
})

const scanMAC = async () => {
  if (!cidr.value.trim()) {
    error.value = 'Please enter a CIDR network'
    return
  }

  loading.value = true
  startScan('mac-scan')
  error.value = ''
  results.value = null
  abortController = new AbortController()

  try {
    const data = await scannerAPI.scanMAC(cidr.value, abortController.signal, hostTimeout.value)
    results.value = data.results || data
  } catch (err) {
    if (err.name === 'CancelError' || err.code === 'ERR_CANCELED') {
      error.value = 'Escaneo cancelado'
    } else {
      error.value = err.response?.data?.detail || 'Error scanning MAC addresses'
    }
  } finally {
    abortController = null
    loading.value = false
    endScan()
  }
}

const cancelScan = () => {
  if (abortController) {
    abortController.abort()
    error.value = 'Escaneo cancelado'
    loading.value = false
    endScan()
  }
}

const getVendorColor = (vendor) => {
  if (!vendor) return 'bg-gray-700 text-gray-400'
  return 'bg-blue-900/50 text-blue-300'
}
</script>

<template>
  <div class="space-y-8">
    <div 
      class="relative rounded-3xl p-8 shadow-2xl overflow-hidden"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <div class="absolute inset-0 opacity-5">
        <div class="absolute top-0 left-0 w-96 h-96 bg-amber-500 rounded-full blur-3xl"></div>
        <div class="absolute bottom-0 right-0 w-96 h-96 bg-yellow-500 rounded-full blur-3xl"></div>
      </div>
      
      <div class="relative z-10">
        <div class="flex items-center gap-4 mb-3">
          <div class="w-14 h-14 bg-gradient-to-br from-amber-500 to-yellow-600 rounded-2xl flex items-center justify-center shadow-lg shadow-amber-500/30">
            <Radio class="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 
              class="text-3xl font-extrabold mb-2 tracking-tight"
              :class="isDark() ? 'text-white' : 'text-slate-800'"
            >
              Mac <span class="text-cyan-400">Scan</span>
            </h2>
            <p 
              class="font-tagesschrift text-lg font-semibold mb-2 tracking-wide text-s"
              :class="isDark() ? 'text-gray-200' : 'text-slate-600'"
            >Descubrimiento de dispositivos mediante ARP</p>
          </div>
        </div>
      </div>
    </div>

    <div 
      class="rounded-2xl p-6 shadow-xl"
      :class="isDark() ? 'bg-gradient-to-br from-orange-900/20 to-amber-900/20 border-2 border-orange-500/50 shadow-orange-500/10' : 'bg-gradient-to-br from-orange-50 to-amber-50 border-2 border-orange-300 shadow-orange-200/20'"
    >
      <div class="flex items-start gap-4">
        <div 
          class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
          :class="isDark() ? 'bg-orange-500/20' : 'bg-orange-200/50'"
        >
          <AlertCircle class="w-6 h-6 text-orange-400" />
        </div>
        <div class="flex-1">
          <p 
            class="font-bold text-lg mb-2"
            :class="isDark() ? 'text-orange-300' : 'text-orange-700'"
          >Requisitos</p>
          <ul 
            class="text-sm space-y-2"
            :class="isDark() ? 'text-orange-300/90' : 'text-orange-700/90'"
          >
            <li class="flex items-center gap-2">
              <span class="inline-block w-1.5 h-1.5 bg-orange-400 rounded-full"></span>
              Privilegios de administrador / root
            </li>
            <li class="flex items-center gap-2">
              <span class="inline-block w-1.5 h-1.5 bg-orange-400 rounded-full"></span>
              Debe ejecutarse en la misma LAN
            </li>
            <li class="flex items-center gap-2">
              <span class="inline-block w-1.5 h-1.5 bg-orange-400 rounded-full"></span>
              Protocolo ARP (no funciona a través de firewall)
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div 
      class="rounded-3xl p-8 shadow-2xl space-y-6"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <div>
        <div class="flex items-center gap-2 mb-3">
          <Network class="w-5 h-5 text-amber-400" />
          <label 
            class="text-sm font-semibold uppercase tracking-wide"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >Red CIDR</label>
        </div>
        <input
          v-model="cidr"
          class="w-full rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-amber-500/60 focus:border-amber-500/50 transition-all font-mono text-lg"
          :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          placeholder="192.168.1.0/24"
        />
        <div 
          class="mt-3 rounded-xl p-3"
          :class="isDark() ? 'bg-slate-800/30 border border-slate-700/50' : 'bg-slate-50 border border-slate-200'"
        >
          <p 
            class="text-xs font-semibold mb-2"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
          >Redes LAN comunes:</p>
          <div class="flex flex-wrap gap-2">
            <span class="px-2 py-1 bg-slate-900/50 border border-slate-700 rounded text-xs text-amber-400 font-mono">192.168.1.0/24</span>
            <span class="px-2 py-1 bg-slate-900/50 border border-slate-700 rounded text-xs text-amber-400 font-mono">192.168.0.0/24</span>
            <span class="px-2 py-1 bg-slate-900/50 border border-slate-700 rounded text-xs text-amber-400 font-mono">10.0.0.0/24</span>
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
            min="3"
            max="20"
            class="w-24 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500/60 font-mono"
            :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white' : 'bg-white border border-slate-300 text-slate-800'"
          />
          <span 
            class="text-xs"
            :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
          >
            Recomendado: 5-10s para detección MAC
          </span>
        </div>
      </div>

      <button
        @click="scanMAC"
        :disabled="loading || isScanning"
        class="w-full group relative overflow-hidden py-6 rounded-2xl font-bold text-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl"
        :class="loading 
          ? 'bg-slate-800 border-2 border-slate-600' 
          : 'bg-gradient-to-r from-amber-600 via-yellow-600 to-amber-600 hover:from-amber-500 hover:via-yellow-500 hover:to-amber-500 border-2 border-amber-400/50 hover:border-amber-300 shadow-amber-500/20 hover:shadow-amber-400/30'"
      >
        <div v-if="!loading && !isScanning" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
        
        <div class="relative z-10 flex items-center justify-center gap-3 text-white">
          <RefreshCw :class="['w-6 h-6', loading && 'animate-spin']" />
          <span class="tracking-wide">
            {{ loading ? 'Escaneando Red...' : isScanning ? 'Otro escaneo en curso...' : 'Escanear Dispositivos' }}
          </span>
        </div>
      </button>

      <button
        v-if="loading"
        @click="cancelScan"
        class="w-full mt-3 group relative py-4 rounded-2xl font-bold text-lg transition-all duration-300 bg-red-900/50 hover:bg-red-800/60 border-2 border-red-700 hover:border-red-600 text-white shadow-lg"
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
      <div v-if="results" class="space-y-6">
        <div class="bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50 rounded-3xl p-6 shadow-2xl">
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gradient-to-br from-amber-500 to-yellow-600 rounded-xl flex items-center justify-center">
                <Network class="w-5 h-5 text-white" />
              </div>
              <div>
                <p class="text-sm text-slate-400">Red Escaneada</p>
                <h3 class="text-xl font-semibold text-white font-mono text-amber-400">
                  {{ results.network }}
                </h3>
              </div>
            </div>

            <div class="flex gap-6">
              <div class="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50">
                <p class="text-xs text-slate-400 uppercase mb-1">Total Dispositivos</p>
                <p class="text-3xl font-bold text-white">
                  {{ results.devices.length }}
                </p>
              </div>
              <div class="bg-amber-500/10 rounded-xl p-4 border border-amber-500/30">
                <p class="text-xs text-amber-400 uppercase mb-1">Con MAC</p>
                <p class="text-3xl font-bold text-amber-400">
                  {{ results.devices.filter((d) => d.mac).length }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="results.devices.length === 0"
          class="bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-2 border-slate-700 rounded-2xl p-8 shadow-xl"
        >
          <div class="flex items-start gap-4">
            <div class="w-12 h-12 bg-slate-800/50 rounded-xl flex items-center justify-center flex-shrink-0">
              <XCircle class="w-7 h-7 text-slate-500" />
            </div>
            <div>
              <p class="text-slate-300 font-bold text-lg mb-2">No se encontraron dispositivos</p>
              <p class="text-sm text-slate-400">
                Asegúrate de tener privilegios de root/admin y que la red objetivo sea local.
              </p>
            </div>
          </div>
        </div>

        <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="(device, index) in results.devices"
            :key="index"
            class="bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50 rounded-2xl p-6 hover:border-amber-500/60 hover:shadow-xl hover:shadow-amber-500/10 transition-all duration-300 stagger-item-scale"
          >
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 bg-amber-500/10 rounded-xl flex items-center justify-center border border-amber-500/30">
                <HardDrive class="w-6 h-6 text-amber-400" />
              </div>

              <span
                :class="[
                  'px-3 py-1 text-xs font-bold rounded-xl uppercase tracking-wider',
                  device.mac 
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                ]"
              >
                {{ device.mac ? 'MAC Detectada' : 'Sin MAC' }}
              </span>
            </div>

            <div class="space-y-3">
              <div>
                <p class="text-xs text-slate-500 uppercase font-semibold mb-1">Dirección IP</p>
                <p class="font-mono text-white text-base font-bold">
                  {{ device.ip }}
                </p>
              </div>

              <div v-if="device.mac">
                <p class="text-xs text-slate-500 uppercase font-semibold mb-1">Dirección MAC</p>
                <p class="font-mono text-amber-400 text-sm">
                  {{ device.mac }}
                </p>
              </div>

              <div v-if="device.vendor">
                <p class="text-xs text-slate-500 uppercase font-semibold mb-1">Fabricante</p>
                <span class="inline-block mt-1 px-3 py-1 text-xs rounded-lg bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  {{ device.vendor }}
                </span>
              </div>

              <p v-else-if="device.mac" class="text-xs text-slate-500 italic">Fabricante desconocido</p>
            </div>
          </div>
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
