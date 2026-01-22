<script setup>
import { ref } from 'vue'
import { scannerAPI } from '../api/scanner'
import { Cpu, RefreshCw, Network, Server, X, AlertCircle, Activity } from 'lucide-vue-next'
import { useScanState } from '../composables/useScanState'
import { useTheme } from '../composables/useTheme'

const { isScanning, startScan, endScan } = useScanState()
const { isDark } = useTheme()

const hosts = ref('') 
const ports = ref('1-1024')
const timeout = ref(120)
const results = ref(null)
const loading = ref(false)
const error = ref('')
let abortController = null


const scanServicesSegment = async () => {
  if (!hosts.value.trim()) {
    error.value = 'Please enter at least one host'
    return
  }

  const hostsArray = hosts.value
    .split(',')
    .map((h) => h.trim())
    .filter(Boolean)

  if (hostsArray.length === 0) {
    error.value = 'Please enter at least one valid host'
    return
  }

  loading.value = true
  startScan('service-scan')
  error.value = ''
  results.value = null
  abortController = new AbortController()

  try {
    const data = await scannerAPI.scanServicesSegment(hostsArray, ports.value, abortController.signal, timeout.value)
    results.value = data.results || data
  } catch (err) {
    if (err.name === 'CancelError' || err.code === 'ERR_CANCELED') {
      error.value = 'Escaneo cancelado'
    } else {
      error.value = err.response?.data?.detail || 'Error scanning services'
    }
  } finally {
    abortController = null
    loading.value = false
    endScan()
    setTimeout(() => {
      progress.value = 0
    }, 2000)
  }
}

const cancelScan = () => {
  if (abortController) {
    abortController.abort()
    error.value = 'Escaneo cancelado'
    loading.value = false
    endScan()
  }
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
  progress.value = 0
  timeRemaining.value = 0
}
</script>

<template>
  <div class="space-y-8">
    <div 
      class="relative rounded-3xl p-8 shadow-2xl overflow-hidden"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <div class="absolute inset-0 opacity-5">
        <div class="absolute top-0 left-0 w-96 h-96 bg-indigo-500 rounded-full blur-3xl"></div>
        <div class="absolute bottom-0 right-0 w-96 h-96 bg-violet-500 rounded-full blur-3xl"></div>
      </div>
      
      <div class="relative z-10">
        <div class="flex items-center gap-4 mb-3">
          <div class="w-14 h-14 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Cpu class="w-7 h-7 text-white" />
          </div>
          <div>
           <h2 
             class="text-3xl font-extrabold mb-2 tracking-tight"
             :class="isDark() ? 'text-white' : 'text-slate-800'"
           >
              Service <span class="text-cyan-400">Scan</span>
            </h2>
            <p 
              class="font-tagesschrift text-lg font-semibold mb-2 tracking-wide text-s"
              :class="isDark() ? 'text-gray-200' : 'text-slate-600'"
            >Identificación de servicios, productos y versiones</p>
          </div>
        </div>
      </div>
    </div>

    <div 
      class="rounded-3xl p-8 shadow-2xl space-y-8"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <div>
        <div class="flex items-center gap-2 mb-3">
          <Network class="w-5 h-5 text-indigo-400" />
          <label 
            class="text-sm font-semibold uppercase tracking-wide"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >Hosts Objetivos</label>
        </div>
        <input
          v-model="hosts"
          class="w-full rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/60 focus:border-indigo-500/50 transition-all font-mono"
          :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          placeholder="192.168.0.1, 192.168.0.2, 192.168.0.0/30"
        />
        <p 
          class="text-xs flex items-center gap-2 mt-2"
          :class="isDark() ? 'text-slate-500' : 'text-slate-600'"
        >
          <span class="inline-block w-2 h-2 bg-indigo-500 rounded-full"></span>
          Separa múltiples hosts/subredes con comas (acepta IPs y CIDR)
        </p>
      </div>

      <div>
        <div class="flex items-center gap-2 mb-3">
          <Server class="w-5 h-5 text-indigo-400" />
          <label 
            class="text-sm font-semibold uppercase tracking-wide"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >Rango de Puertos</label>
        </div>
        <input
          v-model="ports"
          class="w-full rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/60 focus:border-indigo-500/50 transition-all font-mono text-lg"
          :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          placeholder="1-1024 o 80,443"
        />
        <div 
          class="mt-3 rounded-xl p-4 flex items-start gap-3"
          :class="isDark() ? 'bg-amber-500/10 border border-amber-500/30' : 'bg-amber-50 border border-amber-200'"
        >
          <AlertCircle class="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p class="text-sm font-semibold text-amber-400 mb-1">Proceso Lento</p>
            <p class="text-xs text-amber-300/80">La detección de servicios puede tardar varios minutos dependiendo del número de puertos</p>
          </div>
        </div>
      </div>

      <div>
        <div class="flex items-center gap-2 mb-3">
          <Activity class="w-5 h-5 text-indigo-400" />
          <label 
            class="text-sm font-semibold uppercase tracking-wide"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >Timeout por Host (segundos)</label>
        </div>
        <input
          v-model.number="timeout"
          type="number"
          min="30"
          max="300"
          class="w-full rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/60 focus:border-indigo-500/50 transition-all font-mono text-lg"
          :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          placeholder="120"
        />
        <p 
          class="text-xs flex items-center gap-2 mt-2"
          :class="isDark() ? 'text-slate-500' : 'text-slate-600'"
        >
          <span class="inline-block w-2 h-2 bg-indigo-500 rounded-full"></span>
          Tiempo máximo de espera por host (recomendado: 120s)
        </p>
      </div>

      <button
        @click="scanServicesSegment"
        :disabled="loading || isScanning"
        class="w-full group relative overflow-hidden py-6 rounded-2xl font-bold text-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl"
        :class="loading 
          ? 'bg-slate-800 border-2 border-slate-600' 
          : 'bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-600 hover:from-indigo-500 hover:via-violet-500 hover:to-indigo-500 border-2 border-indigo-400/50 hover:border-indigo-300 shadow-indigo-500/20 hover:shadow-indigo-400/30'"
      >
        <div v-if="!loading && !isScanning" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
        
        <div class="relative z-10 flex items-center justify-center gap-3 text-white">
          <RefreshCw :class="['w-6 h-6', loading && 'animate-spin']" />
          <span class="tracking-wide">
            {{ loading ? 'Detectando Servicios...' : isScanning ? 'Otro escaneo en curso...' : 'Iniciar Detección de Servicios' }}
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
          <p class="font-semibold text-red-300 mb-1">Error en la Detección</p>
          <p class="text-sm text-red-400">{{ error }}</p>
        </div>
      </div>
    </Transition>

    <Transition name="fade-slide">
      <div v-if="results" class="space-y-6">
        <div
          v-for="hostData in results"
          :key="hostData.host"
          class="bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50 rounded-3xl overflow-hidden shadow-2xl stagger-item-scale"
        >
          <div class="p-6 border-b border-slate-700/50 bg-slate-900/50">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-xl flex items-center justify-center">
                  <Network class="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 class="text-xl font-semibold text-white font-mono">
                    {{ hostData.host }}
                  </h3>
                  <p class="text-xs text-slate-400">Servicios detectados</p>
                </div>
              </div>

              <span
                :class="[
                  'px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider shadow-md',
                  hostData.services.length
                    ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                ]"
              >
                {{ hostData.services.length }} servicios
              </span>
            </div>
          </div>

          <div v-if="hostData.services.length === 0" class="p-8 text-center">
            <div class="w-16 h-16 bg-slate-800/50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <X class="w-8 h-8 text-slate-500" />
            </div>
            <p class="text-slate-400 text-sm italic">No se detectaron servicios</p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="min-w-full">
              <thead>
                <tr class="bg-slate-900/80">
                  <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                    Puerto
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                    Servicio
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                    Producto
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                    Versión
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                    Extra
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/50">
                <tr
                  v-for="svc in hostData.services"
                  :key="svc.port"
                  class="hover:bg-slate-800/30 transition-colors duration-200"
                >
                  <td class="px-6 py-4 text-sm font-mono text-white whitespace-nowrap font-bold">
                    {{ svc.port }}/{{ svc.protocol }}
                  </td>
                  <td class="px-6 py-4 text-sm text-slate-300 whitespace-nowrap">
                    <span class="px-3 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded-lg font-semibold text-indigo-300">
                      {{ svc.service || 'Desconocido' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-slate-300">
                    {{ svc.product || 'N/A' }}
                  </td>
                  <td class="px-6 py-4 text-sm text-slate-300 font-mono">
                    {{ svc.version || 'N/A' }}
                  </td>
                  <td class="px-6 py-4 text-sm text-slate-400">
                    {{ svc.extra || 'N/A' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
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
