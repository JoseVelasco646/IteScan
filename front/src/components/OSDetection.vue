<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { scannerAPI } from '../api/scanner'
import { Monitor, Info, Target, XCircle } from 'lucide-vue-next'
import { useScanState } from '../composables/useScanState'
import { useScanProgress } from '../composables/useScanProgress'
import { useTheme } from '../composables/useTheme'
import { usePermissions } from '../composables/usePermissions'
import NumberStepper from './NumberStepper.vue'
import OSIcon from './OSIcon.vue'

const { isScanning, currentScanType, startScan, endScan, externalCancelFlag } = useScanState()
const isMyOwnScan = computed(() => currentScanType.value === 'os-detection')
const { isDark } = useTheme()
const { canExecuteScans } = usePermissions()
const { scanProgress, setupProgressListener } = useScanProgress()

const hosts = ref('') 
const hostTimeout = ref(60)
const concurrency = ref(50)
const results = ref([])
const loading = ref(false)
const error = ref('')
let abortController = null

const activeResults = computed(() => {
  if (!results.value || results.value.length === 0) return []
  return results.value.filter(r => r.os)
})

const inactiveCount = computed(() => {
  if (!results.value || results.value.length === 0) return 0
  return results.value.filter(r => !r.os).length
})

onMounted(() => {
  setupProgressListener()
})

const detectOS = async () => {
  if (!hosts.value.trim()) {
    error.value = 'Por favor ingrese al menos un host'
    return
  }

  const hostsArray = hosts.value
    .split(',')
    .map((h) => h.trim())
    .filter(Boolean)

  if (hostsArray.length === 0) {
    error.value = 'Por favor ingrese al menos un host válido'
    return
  }

  loading.value = true
  startScan('os-detection')
  error.value = ''
  results.value = []
  abortController = new AbortController()

  try {
    const data = await scannerAPI.detectOSSegment(hostsArray, abortController.signal, hostTimeout.value, concurrency.value)
    results.value = data.results || data
    
    await new Promise(resolve => setTimeout(resolve, 200))
  } catch (err) {
    if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
      error.value = 'Escaneo cancelado'
    } else {
      error.value = err.response?.data?.detail || 'Error detectando SO'
    }
  } finally {
    loading.value = false
    endScan()
    abortController = null
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

// Detectar cancelación externa (desde ActiveScanBanner u otro componente)
watch(externalCancelFlag, (cancelled) => {
  if (cancelled && isMyOwnScan.value && loading.value) {
    if (abortController) abortController.abort()
    error.value = 'Escaneo cancelado'
    loading.value = false
    endScan()
  }
})


</script>

<template>
  <div class="space-y-8">
    <div 
      class="relative rounded-3xl p-8 shadow-2xl overflow-hidden"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <div class="absolute inset-0 opacity-5">
        <div class="absolute top-0 left-0 w-96 h-96 bg-teal-500 rounded-full blur-3xl"></div>
        <div class="absolute bottom-0 right-0 w-96 h-96 bg-emerald-500 rounded-full blur-3xl"></div>
      </div>
      
      <div class="relative z-10">
        <div class="flex items-center gap-4 mb-3">
          <div class="w-14 h-14 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg shadow-teal-500/30">
            <Monitor class="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 
              class="text-3xl font-extrabold mb-2 tracking-tight"
              :class="isDark() ? 'text-white' : 'text-slate-800'"
            >
              OS <span class="text-cyan-400">Scan</span>
            </h2>
            <p 
              class="font-tagesschrift text-lg font-semibold mb-2 tracking-wide text-s"
              :class="isDark() ? 'text-gray-200' : 'text-slate-600'"
            >Identificación de sistema operativo</p>
          </div>
        </div>
      </div>
    </div>

    <div 
      class="rounded-2xl p-6 shadow-xl"
      :class="isDark() ? 'bg-gradient-to-br from-blue-900/20 to-cyan-900/20 border-2 border-blue-500/50 shadow-blue-500/10' : 'bg-gradient-to-br from-blue-50 to-cyan-50 border-2 border-blue-300 shadow-blue-200/20'"
    >
      <div class="flex items-start gap-4">
        <div 
          class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
          :class="isDark() ? 'bg-blue-500/20' : 'bg-blue-200/50'"
        >
          <Info class="w-6 h-6 text-blue-400" />
        </div>
        <div class="flex-1">
          <p 
            class="font-bold text-lg mb-2"
            :class="isDark() ? 'text-blue-300' : 'text-blue-700'"
          >Información Importante</p>
          <p 
            class="text-sm leading-relaxed mb-2"
            :class="isDark() ? 'text-blue-300/90' : 'text-blue-700/90'"
          >
            La detección de SO requiere <strong :class="isDark() ? 'text-blue-200' : 'text-blue-800'">privilegios de administrador</strong> y puede fallar si:
          </p>
          <ul 
            class="text-xs space-y-1 ml-4 list-disc"
            :class="isDark() ? 'text-blue-400/80' : 'text-blue-600/80'"
          >
            <li>Los firewalls bloquean las sondas de fingerprinting</li>
            <li>El host limita las respuestas ICMP/TCP</li>
            <li>Permisos insuficientes en el sistema</li>
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
          <Target class="w-5 h-5 text-teal-400" />
          <label 
            class="text-sm font-semibold uppercase tracking-wide"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >Hosts (separados por comas)</label>
        </div>
        <textarea
          v-model="hosts"
          :disabled="loading"
          rows="3"
          class="w-full rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-teal-500/60 focus:border-teal-500/50 transition-all font-mono text-lg resize-none"
          :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          placeholder="192.168.1.1, 192.168.1.10, 192.168.1.0/24"
        />
        <p 
          class="text-xs flex items-center gap-2 mt-2"
          :class="isDark() ? 'text-slate-500' : 'text-slate-600'"
        >
          <span class="inline-block w-2 h-2 bg-teal-500 rounded-full"></span>
          Puede ingresar IPs individuales, rangos CIDR o combinación (separados por comas)
        </p>
      </div>

      <div class="mt-6">
        <div class="flex items-center gap-2 mb-3">
          <svg
            class="w-5 h-5 text-teal-400"
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
          >Timeout por host</label>
        </div>
        <NumberStepper v-model="hostTimeout" :min="20" :max="300" :step="5" unit="s"
          hint="Recomendado: 45-90s para detección de SO"
          accent-color="teal" :show-range="true" />
      </div>

      <!-- Concurrencia -->
      <div>
        <div class="flex items-center gap-2 mb-3">
          <svg class="w-5 h-5" :class="isDark() ? 'text-teal-400' : 'text-teal-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <label 
            class="text-sm font-semibold uppercase tracking-wide"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >IPs simultáneas</label>
        </div>
        <NumberStepper v-model="concurrency" :min="1" :max="50" unit="IPs"
          :presets="[5, 10, 25, 50]"
          accent-color="teal" :show-range="true" />
        <p class="text-xs mt-1.5" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Más simultáneas = más rápido pero más carga de red</p>
      </div>

      <div class="flex gap-3">
        <button
          v-if="!loading && canExecuteScans"
          @click="detectOS"
          :disabled="isScanning"
          class="flex-1 group relative overflow-hidden py-6 rounded-2xl font-bold text-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl bg-gradient-to-r from-teal-600 via-emerald-600 to-teal-600 hover:from-teal-500 hover:via-emerald-500 hover:to-teal-500 border-2 border-teal-400/50 hover:border-teal-300 shadow-teal-500/20 hover:shadow-teal-400/30"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
          <span class="relative flex items-center justify-center gap-3 text-white">
            <Monitor class="w-6 h-6" />
            Detectar OS
          </span>
        </button>
        <button
          v-else
          @click="cancelScan"
          class="flex-1 group relative overflow-hidden py-6 rounded-2xl font-bold text-lg transition-all duration-300 shadow-xl bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 border-2 border-red-400/50 hover:border-red-300 shadow-red-500/20 hover:shadow-red-400/30"
        >
          <span class="relative flex items-center justify-center gap-3 text-white">
            Cancelar
          </span>
        </button>
      </div>
    </div>

    <Transition name="fade-slide">
      <div v-if="error" class="bg-red-500/10 border-2 border-red-500/50 rounded-2xl p-5 flex items-start gap-3 shadow-lg shadow-red-500/20">
        <div class="w-10 h-10 bg-red-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <div class="flex-1">
          <p class="font-semibold text-red-300 mb-1">Error en la Detección</p>
          <p class="text-sm text-red-400">{{ error }}</p>
        </div>
      </div>
    </Transition>

    <Transition name="fade-slide">
      <div v-if="results && results.length > 0" class="space-y-6">
        <!-- Resumen -->
        <div 
          class="rounded-2xl p-5 shadow-xl"
          :class="isDark() ? 'bg-gradient-to-br from-teal-900/20 to-emerald-900/20 border border-teal-500/30' : 'bg-gradient-to-br from-teal-50 to-emerald-50 border border-teal-300'"
        >
          <p :class="isDark() ? 'text-teal-300 font-semibold' : 'text-teal-700 font-semibold'">
            {{ activeResults.length }} host(s) con SO detectado
            <span v-if="inactiveCount > 0" :class="isDark() ? 'text-slate-400' : 'text-slate-500'"> · {{ inactiveCount }} host(s) sin detección</span>
          </p>
        </div>

        <!-- Sin resultados activos -->
        <div v-if="activeResults.length === 0" class="text-center py-12">
          <XCircle class="w-12 h-12 mx-auto mb-3" :class="isDark() ? 'text-slate-600' : 'text-slate-400'" />
          <p :class="isDark() ? 'text-slate-400' : 'text-slate-500'" class="font-semibold">No se detectó SO en ningún host escaneado</p>
        </div>

        <div 
          v-for="(result, index) in activeResults" 
          :key="index"
          class="space-y-4 stagger-item-scale"
        >
          <div class="bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50 rounded-3xl p-6 shadow-2xl">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-xl flex items-center justify-center">
                <Target class="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 class="text-xl font-semibold text-white font-mono">
                  {{ result.host }}
                </h3>
                <p class="text-xs text-slate-400">Resultados de la detección</p>
              </div>
            </div>
          </div>

        <div
          class="bg-gradient-to-br from-teal-900/30 to-emerald-900/30 border-2 border-teal-500/40 rounded-3xl p-8 shadow-2xl shadow-teal-500/10"
        >
          <div class="flex items-center gap-8">
            <div class="w-24 h-24 bg-teal-500/10 rounded-3xl flex items-center justify-center border-2 border-teal-500/30 flex-shrink-0">
              <OSIcon :name="result.os.name" :size="56" :stroke-width="1.5" />
            </div>

            <div class="flex-1 space-y-4">
              <div>
                <p class="text-sm text-teal-400 font-semibold uppercase tracking-wide mb-1">Sistema Operativo Detectado</p>
                <h4 class="text-3xl font-bold text-white">
                  {{ result.os.name }}
                </h4>
              </div>

              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-slate-300 font-semibold">Nivel de Confianza</span>
                  <span class="text-sm font-bold"
                    :class="
                      result.os.accuracy > 80
                        ? 'text-emerald-400'
                        : result.os.accuracy > 50
                          ? 'text-yellow-400'
                          : 'text-red-400'
                    "
                  > 
                    {{ result.os.accuracy }}%
                  </span>
                </div>

                <div class="relative h-3 bg-slate-900/50 rounded-full overflow-hidden border border-slate-700/50">
                  <div
                    class="h-3 rounded-full transition-all duration-500 shadow-lg"
                    :class="
                      result.os.accuracy > 80
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-500 shadow-emerald-500/50'
                        : result.os.accuracy > 50
                          ? 'bg-gradient-to-r from-yellow-500 to-orange-500 shadow-yellow-500/50'
                          : 'bg-gradient-to-r from-red-500 to-orange-500 shadow-red-500/50'
                    "
                    :style="{ width: result.os.accuracy + '%' }"
                  >
                    <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
                  </div>
                </div>
              </div>
            </div>
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
