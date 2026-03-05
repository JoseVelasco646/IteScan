<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { scannerAPI } from '@/api/scanner'
import { useTheme } from '@/composables/useTheme'
import { useGlobalWebSocket } from '@/composables/useWebSocket'
import { 
  Monitor, Wifi, WifiOff, HelpCircle, Shield, Server, 
  AlertTriangle, Activity, Clock, Calendar, RefreshCw,
  TrendingUp, Database, Zap, Globe, Eye
} from 'lucide-vue-next'

const { isDark } = useTheme()
const ws = useGlobalWebSocket()
const summary = ref(null)
const loading = ref(true)
const error = ref('')
let refreshInterval = null
const wsCleanup = []

const loadSummary = async () => {
  loading.value = true
  error.value = ''
  try {
    summary.value = await scannerAPI.getDashboardSummary()
  } catch (err) {
    error.value = 'Error cargando resumen del dashboard'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSummary()
  refreshInterval = setInterval(loadSummary, 60000)
  const removeScanProgress = ws.on('scan_progress', (data) => {
    if (data.status === 'completed') {
      setTimeout(loadSummary, 2000)
    }
  })
  wsCleanup.push(removeScanProgress)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  wsCleanup.forEach(fn => fn && fn())
})

const vulnTotal = computed(() => summary.value?.network?.total_vulnerabilities || 0)
const vulnCritical = computed(() => summary.value?.network?.vulnerabilities_by_severity?.critical || 0)
const vulnHigh = computed(() => summary.value?.network?.vulnerabilities_by_severity?.high || 0)
const vulnMedium = computed(() => summary.value?.network?.vulnerabilities_by_severity?.medium || 0)
const vulnLow = computed(() => summary.value?.network?.vulnerabilities_by_severity?.low || 0)

const hostPercent = computed(() => {
  if (!summary.value?.hosts?.total) return 0
  return Math.round((summary.value.hosts.up / summary.value.hosts.total) * 100)
})

const formatDate = (str) => {
  if (!str) return 'N/A'
  try {
    return new Date(str).toLocaleString('es-MX', { 
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
    })
  } catch { return str }
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`
}

const cardClasses = computed(() => {
  return isDark()
    ? 'bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm'
    : 'bg-white border border-slate-200 shadow-sm'
})
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="animate-spin rounded-full h-10 w-10 border-2 border-t-transparent" 
        :class="isDark() ? 'border-cyan-400' : 'border-cyan-600'"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-8">
      <div class="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center"
        :class="isDark() ? 'bg-red-500/10' : 'bg-red-50'">
        <AlertTriangle class="w-8 h-8" :class="isDark() ? 'text-red-400' : 'text-red-500'" />
      </div>
      <p class="font-medium mb-1" :class="isDark() ? 'text-red-400' : 'text-red-600'">{{ error }}</p>
      <button @click="loadSummary" class="mt-3 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200"
        :class="isDark() ? 'bg-cyan-600 hover:bg-cyan-700 text-white shadow-lg shadow-cyan-500/20' : 'bg-cyan-500 hover:bg-cyan-600 text-white shadow-lg shadow-cyan-500/20'">
        Reintentar
      </button>
    </div>

    <!-- Summary -->
    <div v-else-if="summary" class="space-y-6">
      <!-- Header with refresh -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-xl" :class="isDark() ? 'bg-cyan-500/10' : 'bg-cyan-50'">
            <TrendingUp class="w-5 h-5" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
          </div>
          <div>
            <h2 class="text-lg font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">Resumen de Red</h2>
            <p class="text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Vista general del estado actual</p>
          </div>
        </div>
        <button @click="loadSummary"
          class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
          :class="isDark() ? 'bg-slate-700/50 hover:bg-slate-700 text-slate-300 border border-slate-600' : 'bg-white hover:bg-slate-50 text-slate-600 border border-slate-300 shadow-sm'">
          <RefreshCw class="w-4 h-4" />
          Actualizar
        </button>
      </div>

      <!-- Main host status - prominent card with ring gauge -->
      <div class="rounded-2xl p-6 transition-all duration-300 relative overflow-hidden" :class="cardClasses">
        <div class="absolute top-0 right-0 w-40 h-40 opacity-5"
          :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">
          <Globe class="w-full h-full" />
        </div>
        
        <div class="relative grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <!-- Left: Total hosts + ring indicator -->
          <div class="flex items-center gap-5">
            <div class="relative w-20 h-20 flex-shrink-0">
              <svg class="w-20 h-20 transform -rotate-90" viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="34" stroke-width="6" fill="none" 
                  :stroke="isDark() ? '#1e293b' : '#e2e8f0'" />
                <circle cx="40" cy="40" r="34" stroke-width="6" fill="none"
                  stroke-linecap="round"
                  :stroke="isDark() ? '#22d3ee' : '#0891b2'"
                  :stroke-dasharray="`${hostPercent * 2.136} 213.6`" />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <span class="text-lg font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">{{ hostPercent }}%</span>
              </div>
            </div>
            <div>
              <p class="text-3xl font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">{{ summary.hosts.total }}</p>
              <p class="text-sm font-medium" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Hosts totales</p>
            </div>
          </div>

          <!-- Center: Online / Offline split -->
          <div class="grid grid-cols-2 gap-4">
            <div class="text-center p-3 rounded-xl" :class="isDark() ? 'bg-emerald-500/10' : 'bg-emerald-50'">
              <div class="flex items-center justify-center gap-2 mb-1">
                <Wifi class="w-4 h-4" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'" />
                <span class="text-xs font-semibold uppercase tracking-wider" :class="isDark() ? 'text-emerald-400/70' : 'text-emerald-600/70'">Online</span>
              </div>
              <p class="text-2xl font-bold" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">{{ summary.hosts.up }}</p>
            </div>
            <div class="text-center p-3 rounded-xl" :class="isDark() ? 'bg-red-500/10' : 'bg-red-50'">
              <div class="flex items-center justify-center gap-2 mb-1">
                <WifiOff class="w-4 h-4" :class="isDark() ? 'text-red-400' : 'text-red-500'" />
                <span class="text-xs font-semibold uppercase tracking-wider" :class="isDark() ? 'text-red-400/70' : 'text-red-500/70'">Offline</span>
              </div>
              <p class="text-2xl font-bold" :class="isDark() ? 'text-red-400' : 'text-red-500'">{{ summary.hosts.down }}</p>
            </div>
          </div>

          <!-- Right: Quick network stats -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Database class="w-4 h-4" :class="isDark() ? 'text-blue-400' : 'text-blue-600'" />
                <span class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puertos</span>
              </div>
              <span class="text-sm font-bold" :class="isDark() ? 'text-blue-400' : 'text-blue-600'">{{ summary.network.total_ports }}</span>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Server class="w-4 h-4" :class="isDark() ? 'text-purple-400' : 'text-purple-600'" />
                <span class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicios</span>
              </div>
              <span class="text-sm font-bold" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">{{ summary.network.total_services }}</span>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Calendar class="w-4 h-4" :class="isDark() ? 'text-indigo-400' : 'text-indigo-600'" />
                <span class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Schedulers</span>
              </div>
              <span class="text-sm font-bold" :class="isDark() ? 'text-indigo-400' : 'text-indigo-600'">
                {{ summary.schedules.active }}<span class="font-normal" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">/{{ summary.schedules.total }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Vulnerability summary card with severity bars -->
      <div class="rounded-2xl p-5 transition-all duration-300" :class="cardClasses">
        <div class="flex items-center gap-2 mb-4">
          <Shield class="w-5 h-5" :class="isDark() ? 'text-amber-400' : 'text-amber-600'" />
          <h3 class="text-sm font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">Vulnerabilidades</h3>
          <span class="ml-auto text-2xl font-bold" :class="isDark() ? 'text-amber-400' : 'text-amber-600'">{{ vulnTotal }}</span>
        </div>
        <div v-if="vulnTotal > 0" class="space-y-2.5">
          <div v-if="vulnCritical" class="flex items-center gap-3">
            <span class="text-xs font-semibold w-16 text-right" :class="isDark() ? 'text-red-400' : 'text-red-600'">Crítica</span>
            <div class="flex-1 h-2.5 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-700' : 'bg-slate-200'">
              <div class="h-full rounded-full bg-gradient-to-r from-red-500 to-red-400 transition-all duration-500"
                :style="{ width: `${Math.max((vulnCritical / vulnTotal) * 100, 8)}%` }"></div>
            </div>
            <span class="text-xs font-bold w-8" :class="isDark() ? 'text-red-400' : 'text-red-600'">{{ vulnCritical }}</span>
          </div>
          <div v-if="vulnHigh" class="flex items-center gap-3">
            <span class="text-xs font-semibold w-16 text-right" :class="isDark() ? 'text-orange-400' : 'text-orange-600'">Alta</span>
            <div class="flex-1 h-2.5 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-700' : 'bg-slate-200'">
              <div class="h-full rounded-full bg-gradient-to-r from-orange-500 to-orange-400 transition-all duration-500"
                :style="{ width: `${Math.max((vulnHigh / vulnTotal) * 100, 8)}%` }"></div>
            </div>
            <span class="text-xs font-bold w-8" :class="isDark() ? 'text-orange-400' : 'text-orange-600'">{{ vulnHigh }}</span>
          </div>
          <div v-if="vulnMedium" class="flex items-center gap-3">
            <span class="text-xs font-semibold w-16 text-right" :class="isDark() ? 'text-yellow-400' : 'text-yellow-600'">Media</span>
            <div class="flex-1 h-2.5 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-700' : 'bg-slate-200'">
              <div class="h-full rounded-full bg-gradient-to-r from-yellow-500 to-yellow-400 transition-all duration-500"
                :style="{ width: `${Math.max((vulnMedium / vulnTotal) * 100, 8)}%` }"></div>
            </div>
            <span class="text-xs font-bold w-8" :class="isDark() ? 'text-yellow-400' : 'text-yellow-600'">{{ vulnMedium }}</span>
          </div>
          <div v-if="vulnLow" class="flex items-center gap-3">
            <span class="text-xs font-semibold w-16 text-right" :class="isDark() ? 'text-blue-400' : 'text-blue-600'">Baja</span>
            <div class="flex-1 h-2.5 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-700' : 'bg-slate-200'">
              <div class="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-500"
                :style="{ width: `${Math.max((vulnLow / vulnTotal) * 100, 8)}%` }"></div>
            </div>
            <span class="text-xs font-bold w-8" :class="isDark() ? 'text-blue-400' : 'text-blue-600'">{{ vulnLow }}</span>
          </div>
        </div>
        <div v-else class="text-center py-3">
          <p class="text-sm" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Sin vulnerabilidades detectadas</p>
        </div>
      </div>

      <!-- Bottom row: Recent Scans + Recent Hosts -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Recent Scans -->
        <div class="rounded-2xl p-5 transition-all duration-300" :class="cardClasses">
          <div class="flex items-center gap-2 mb-4">
            <Activity class="w-5 h-5" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
            <h3 class="text-sm font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">Escaneos Recientes</h3>
          </div>
          <div v-if="summary.recent_scans.length === 0" class="text-center py-6">
            <Eye class="w-10 h-10 mx-auto mb-2" :class="isDark() ? 'text-slate-600' : 'text-slate-300'" />
            <p class="text-sm" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Sin escaneos recientes</p>
          </div>
          <div v-else class="space-y-2">
            <div v-for="scan in summary.recent_scans" :key="scan.id" 
              class="flex items-center justify-between p-3 rounded-xl transition-all duration-200 group"
              :class="isDark() ? 'bg-slate-700/30 hover:bg-slate-700/50' : 'bg-slate-50 hover:bg-slate-100'">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <p class="text-sm font-semibold truncate" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                    {{ scan.target }}
                  </p>
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold flex-shrink-0"
                    :class="scan.status === 'success' 
                      ? (isDark() ? 'bg-emerald-500/20 text-emerald-400' : 'bg-emerald-100 text-emerald-700')
                      : (isDark() ? 'bg-red-500/20 text-red-400' : 'bg-red-100 text-red-700')">
                    <svg v-if="scan.status === 'success'" class="w-3 h-3 inline -mt-px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    <svg v-else class="w-3 h-3 inline -mt-px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </span>
                </div>
                <div class="flex items-center gap-2 mt-1">
                  <span class="text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                    {{ scan.scan_type }}
                  </span>
                  <span class="text-xs" :class="isDark() ? 'text-slate-600' : 'text-slate-300'">|</span>
                  <span class="text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                    {{ scan.hosts_active }}/{{ scan.hosts_scanned }} activos
                  </span>
                  <span v-if="scan.username" class="text-xs" :class="isDark() ? 'text-slate-600' : 'text-slate-300'">|</span>
                  <span v-if="scan.username" class="text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                    {{ scan.username }}
                  </span>
                </div>
              </div>
              <div class="text-right flex-shrink-0 ml-3">
                <p class="text-[10px]" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                  {{ formatDate(scan.created_at) }}
                </p>
                <p class="text-[10px] font-mono" :class="isDark() ? 'text-slate-600' : 'text-slate-300'">
                  {{ formatDuration(scan.duration_seconds) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Hosts -->
        <div class="rounded-2xl p-5 transition-all duration-300" :class="cardClasses">
          <div class="flex items-center gap-2 mb-4">
            <Clock class="w-5 h-5" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
            <h3 class="text-sm font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">Últimos Hosts</h3>
          </div>
          <div v-if="summary.recent_hosts.length === 0" class="text-center py-6">
            <Monitor class="w-10 h-10 mx-auto mb-2" :class="isDark() ? 'text-slate-600' : 'text-slate-300'" />
            <p class="text-sm" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Sin hosts</p>
          </div>
          <div v-else class="space-y-1.5">
            <div v-for="host in summary.recent_hosts" :key="host.ip"
              class="flex items-center justify-between p-2.5 rounded-xl transition-all duration-200"
              :class="isDark() ? 'bg-slate-700/20 hover:bg-slate-700/40' : 'bg-slate-50 hover:bg-slate-100'">
              <div class="flex items-center gap-2.5 min-w-0">
                <div class="relative flex-shrink-0">
                  <div class="w-2.5 h-2.5 rounded-full"
                    :class="host.status === 'up' ? 'bg-emerald-500' : 'bg-red-500'"></div>
                  <div v-if="host.status === 'up'" class="absolute inset-0 w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping opacity-40"></div>
                </div>
                <span class="text-sm font-mono font-medium truncate" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                  {{ host.ip }}
                </span>
                <span v-if="host.nickname" class="text-xs truncate" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                  {{ host.nickname }}
                </span>
              </div>
              <span class="text-[10px] flex-shrink-0 ml-2" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                {{ formatDate(host.last_seen) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
