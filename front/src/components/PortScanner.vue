<script setup>
import { ref } from 'vue'
import { scannerAPI } from '../api/scanner'
import { Shield, RefreshCw, Network, Server, X } from 'lucide-vue-next'
import { useScanState } from '../composables/useScanState'
import { useTheme } from '../composables/useTheme'

const { isScanning, startScan, endScan } = useScanState()
const { isDark } = useTheme()

const hosts = ref('') 
const ports = ref('1-1024')
const hostTimeout = ref(45)
const results = ref(null)
const loading = ref(false)
const error = ref('')
let abortController = null

const scanPortsSegment = async () => {
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
  startScan('port-scan')
  error.value = ''
  results.value = null
  abortController = new AbortController()

  try {
    const data = await scannerAPI.scanPortsSegment(hostsArray, ports.value, abortController.signal, hostTimeout.value)
    results.value = data.results || data
  } catch (err) {
    if (err.name === 'CancelError' || err.code === 'ERR_CANCELED') {
      error.value = 'Escaneo cancelado'
    } else {
      error.value = err.response?.data?.detail || 'Error scanning ports'
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

const presetPorts = [
  { label: 'Common (1-1024)', value: '1-1024' },
  { label: 'All (1-65535)', value: '1-65535' },
  { label: 'Web (80,443,8080,8443)', value: '80,443,8080,8443' },
  { label: 'SSH/FTP (21,22)', value: '21,22' },
  { label: 'Database (3306,5432,27017)', value: '3306,5432,27017' },
]
</script>

<template>
  <div class="space-y-8">
    <div 
      class="relative rounded-3xl p-8 shadow-2xl overflow-hidden"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <div class="absolute inset-0 opacity-5">
        <div class="absolute top-0 left-0 w-96 h-96 bg-purple-500 rounded-full blur-3xl"></div>
        <div class="absolute bottom-0 right-0 w-96 h-96 bg-blue-500 rounded-full blur-3xl"></div>
      </div>
      
      <div class="relative z-10">
        <div class="flex items-center gap-4 mb-3">
          <div class="w-14 h-14 bg-gradient-to-br from-purple-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/30">
            <Shield class="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 
              class="text-3xl font-extrabold mb-2 tracking-tight"
              :class="isDark() ? 'text-white' : 'text-slate-800'"
            >
              Port <span class="text-cyan-400">Scan</span>
            </h2>
            <p 
              class="font-tagesschrift text-lg font-semibold mb-2 tracking-wide text-s"
              :class="isDark() ? 'text-gray-200' : 'text-slate-600'"
            >Descubrimiento rápido de puertos TCP</p>
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
          <Network class="w-5 h-5 text-purple-400" />
          <label 
            class="text-sm font-semibold uppercase tracking-wide"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >Hosts Objetivos</label>
        </div>
        <input
          v-model="hosts"
          class="w-full rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-purple-500/60 focus:border-purple-500/50 transition-all font-mono"
          :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          placeholder="192.168.1.1, 192.168.1.0/24"
        />
        <p 
          class="text-xs flex items-center gap-2 mt-2"
          :class="isDark() ? 'text-slate-500' : 'text-slate-600'"
        >
          <span class="inline-block w-2 h-2 bg-purple-500 rounded-full"></span>
          Separa múltiples hosts/subredes con comas (acepta IPs y CIDR)
        </p>
      </div>

      <div>
        <div class="flex items-center gap-2 mb-3">
          <Server class="w-5 h-5 text-purple-400" />
          <label 
            class="text-sm font-semibold uppercase tracking-wide"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >Selección de Puertos</label>
        </div>
        <input
          v-model="ports"
          class="w-full rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-purple-500/60 focus:border-purple-500/50 transition-all font-mono text-lg mb-4"
          :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          placeholder="1-1024 o 80,443,8080"
        />

        <div 
          class="rounded-xl p-4"
          :class="isDark() ? 'bg-slate-800/30 border border-slate-700/50' : 'bg-slate-50 border border-slate-200'"
        >
          <p 
            class="text-xs font-semibold mb-3 uppercase"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
          >Rangos Predefinidos</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="preset in presetPorts"
              :key="preset.value"
              @click="ports = preset.value"
              class="px-4 py-2 rounded-xl text-xs transition-all"
              :class="isDark() ? 'bg-slate-900/50 border border-slate-700 text-slate-300 hover:border-purple-500/50 hover:bg-slate-800/50' : 'bg-white border border-slate-300 text-slate-700 hover:border-purple-500/50 hover:bg-slate-50'"
            >
              {{ preset.label }}
            </button>
          </div>
        </div>
      </div>

      <div class="mt-6">
        <div class="flex items-center gap-2 mb-3">
          <svg
            class="w-5 h-5 text-purple-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <label 
            class="text-sm font-semibold uppercase tracking-wide"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >Timeout por host (segundos)</label>
        </div>
        <div class="flex items-center gap-4">
          <input
            v-model.number="hostTimeout"
            type="number"
            min="10"
            max="180"
            class="w-28 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500/60 font-mono text-lg"
            :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white' : 'bg-white border border-slate-300 text-slate-800'"
          />
          <span 
            class="text-sm"
            :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
          >
            Recomendado: 30-60s para escaneo de puertos
          </span>
        </div>
      </div>

      <button
        @click="scanPortsSegment"
        :disabled="loading || isScanning"
        class="w-full group relative overflow-hidden py-6 rounded-2xl font-bold text-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl"
        :class="loading 
          ? 'bg-slate-800 border-2 border-slate-600' 
          : 'bg-gradient-to-r from-purple-600 via-blue-600 to-purple-600 hover:from-purple-500 hover:via-blue-500 hover:to-purple-500 border-2 border-purple-400/50 hover:border-purple-300 shadow-purple-500/20 hover:shadow-purple-400/30'"
      >
        <div v-if="!loading && !isScanning" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
        
        <div class="relative z-10 flex items-center justify-center gap-3 text-white">
          <RefreshCw :class="['w-6 h-6', loading && 'animate-spin']" />
          <span class="tracking-wide">
            {{ loading ? 'Escaneando Puertos...' : isScanning ? 'Otro escaneo en curso...' : 'Iniciar Escaneo de Puertos' }}
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
          <span class="text-xl">.</span>
        </div>
        <div class="flex-1">
          <p class="font-semibold text-red-300 mb-1">Error en el Escaneo</p>
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
                <div class="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-600 rounded-xl flex items-center justify-center">
                  <Network class="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 class="text-xl font-semibold text-white font-mono">
                    {{ hostData.host }}
                  </h3>
                  <p class="text-xs text-slate-400">Resultados del escaneo</p>
                </div>
              </div>

              <span
                :class="[
                  'px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider shadow-md',
                  hostData.ports.length
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                ]"
              >
                {{ hostData.ports.length }} puertos abiertos
              </span>
            </div>
          </div>

          <div v-if="hostData.ports.length === 0" class="p-8 text-center">
            <div class="w-16 h-16 bg-slate-800/50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <X class="w-8 h-8 text-slate-500" />
            </div>
            <p class="text-slate-400 text-sm italic">No se detectaron puertos abiertos</p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="min-w-full">
              <thead>
                <tr class="bg-slate-900/80">
                  <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                    Puerto
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                    Protocolo
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50">
                    Servicio
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/50">
                <tr
                  v-for="port in hostData.ports"
                  :key="port.port"
                  class="hover:bg-slate-800/30 transition-colors duration-200"
                >
                  <td class="px-6 py-4 text-sm font-mono text-white whitespace-nowrap font-bold">
                    {{ port.port }}
                  </td>
                  <td class="px-6 py-4 text-sm text-slate-300 whitespace-nowrap">
                    <span class="px-3 py-1 bg-slate-800/50 rounded-lg font-mono text-xs">
                      {{ port.protocol }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-slate-300 whitespace-nowrap">
                    {{ port.service || 'Desconocido' }}
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
