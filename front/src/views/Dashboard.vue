<script setup>
import { ref, onMounted, computed } from 'vue'
import { FishingHook, Wifi, EthernetPort, Monitor, Search, Database, Calendar, Radar, Terminal } from 'lucide-vue-next'
import PingScanner from '../components/PingScanner.vue'
import PortScanner from '../components/PortScanner.vue'
import ServiceScanner from '../components/ServiceScanner.vue'
import OSDetection from '../components/OSDetection.vue'
import MacScanner from '../components/MacScanner.vue'
import HostsTable from '../components/HostsTable.vue'
import FullScan from '@/components/FullScan.vue'
import ScanProgress from '../components/ScanProgress.vue'
import { useScanState } from '../composables/useScanState'
import { useScanProgress } from '../composables/useScanProgress'
import ScanScheduler from '../components/ScanScheduler.vue'
import SSHTerminal from '../components/SSHTerminal.vue'
import { useTheme } from '../composables/useTheme'

const activeTab = ref('database')
const { isScanning, currentScanType } = useScanState()
const { scanProgress, setupProgressListener } = useScanProgress()
const { isDark } = useTheme()

onMounted(() => {
  setupProgressListener()
})

const tabs = [
  { id: 'database', name: 'Database', icon: Database },
  { id: 'fullscan', name: 'Full Scan', icon: Radar },
  { id: 'ping', name: 'Ping', icon: Wifi },
  { id: 'ports', name: 'Ports', icon: FishingHook },
  { id: 'services', name: 'Services', icon: EthernetPort },
  { id: 'os', name: 'OS Detection', icon: Monitor },
  { id: 'mac', name: 'MAC Scan', icon: Search },
  { id: 'scheduler', name: 'Scheduler', icon: Calendar },
  { id: 'terminal', name: 'Terminal', icon: Terminal }
]

const containerClasses = computed(() => {
  return isDark()
    ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50'
    : 'bg-gradient-to-br from-white via-slate-50 to-white border-slate-200 shadow-lg'
})

const getTabClasses = (tabId) => {
  const isActive = activeTab.value === tabId
  const dark = isDark()
  if (dark) {
    return isActive
      ? 'bg-gradient-to-br from-cyan-500/20 to-blue-600/20 text-cyan-400 shadow-lg border-2 border-cyan-500/50'
      : 'text-slate-400 hover:text-cyan-300 hover:bg-slate-800/50 border-2 border-transparent'
  } else {
    return isActive
      ? 'bg-gradient-to-br from-cyan-100 to-blue-100 text-cyan-700 shadow-md border-2 border-cyan-400/50'
      : 'text-slate-500 hover:text-cyan-600 hover:bg-slate-100 border-2 border-transparent'
  }
}

const getGlowClasses = (tabId) => {
  const isActive = activeTab.value === tabId
  const dark = isDark()
  if (isActive) {
    return dark 
      ? 'bg-gradient-to-br from-cyan-400/10 via-transparent to-blue-500/10'
      : 'bg-gradient-to-br from-cyan-200/30 via-transparent to-blue-200/30'
  } else {
    return dark
      ? 'bg-gradient-to-br from-slate-600/10 via-transparent to-slate-700/10'
      : 'bg-gradient-to-br from-slate-200/50 via-transparent to-slate-300/50'
  }
}

const getIconClasses = (tabId) => {
  const isActive = activeTab.value === tabId
  const dark = isDark()
  if (isActive) {
    return dark 
      ? 'scale-110 drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]'
      : 'scale-110 drop-shadow-[0_0_6px_rgba(8,145,178,0.4)]'
  }
  return 'group-hover:scale-110'
}

const getTextClasses = (tabId) => {
  const isActive = activeTab.value === tabId
  const dark = isDark()
  if (isActive) {
    return dark
      ? 'bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent'
      : 'bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent'
  }
  return ''
}
</script>

<template>
  <div class="w-full py-6 px-4">
    <div
      class="rounded-3xl border mb-6 shadow-2xl overflow-hidden transition-all duration-300"
      :class="containerClasses"
    >
      <div class="p-4">
        <nav 
          class="hidden lg:grid lg:grid-cols-5 gap-3" 
          role="tablist" 
          aria-label="Navegación de escáners"
        >
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            role="tab"
            :aria-selected="activeTab === tab.id"
            :aria-controls="`panel-${tab.id}`"
            :aria-label="`Ir a ${tab.name}`"
            class="relative flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group overflow-hidden"
            :class="getTabClasses(tab.id)"
          >
            <div
              class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              :class="
                activeTab === tab.id
                  ? isDark() 
                    ? 'bg-gradient-to-br from-cyan-400/10 via-transparent to-blue-500/10'
                    : 'bg-gradient-to-br from-cyan-200/30 via-transparent to-blue-200/30'
                  : isDark()
                    ? 'bg-gradient-to-br from-slate-600/10 via-transparent to-slate-700/10'
                    : 'bg-gradient-to-br from-slate-200/50 via-transparent to-slate-300/50'
              "
            ></div>

            <component
              :is="tab.icon"
              class="w-5 h-5 transition-all duration-300 relative z-10 flex-shrink-0"
              :class="
                activeTab === tab.id
                  ? isDark() 
                    ? 'scale-110 drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]'
                    : 'scale-110 drop-shadow-[0_0_6px_rgba(8,145,178,0.4)]'
                  : 'group-hover:scale-110'
              "
            />

            <span
              class="text-sm font-bold tracking-wide uppercase relative z-10 truncate"
              :class="
                activeTab === tab.id
                  ? isDark()
                    ? 'bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent'
                    : 'bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent'
                  : ''
              "
            >
              {{ tab.name }}
            </span>

            <span
              v-if="activeTab === tab.id"
              class="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-cyan-400 via-blue-500 to-cyan-400 rounded-r-full"
            ></span>
          </button>
        </nav>

        <nav
          class="lg:hidden flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory scrollbar-hide"
          role="tablist"
          aria-label="Navegación de escáners"
        >
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            role="tab"
            :aria-selected="activeTab === tab.id"
            :aria-controls="`panel-${tab.id}`"
            :aria-label="`Ir a ${tab.name}`"
            class="relative flex flex-col items-center justify-center min-w-[100px] h-24 rounded-2xl transition-all duration-300 group overflow-hidden snap-start flex-shrink-0"
            :class="getTabClasses(tab.id)"
          >
            <div
              class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              :class="
                activeTab === tab.id
                  ? isDark()
                    ? 'bg-gradient-to-br from-cyan-400/10 via-transparent to-blue-500/10'
                    : 'bg-gradient-to-br from-cyan-200/30 via-transparent to-blue-200/30'
                  : isDark()
                    ? 'bg-gradient-to-br from-slate-600/10 via-transparent to-slate-700/10'
                    : 'bg-gradient-to-br from-slate-200/50 via-transparent to-slate-300/50'
              "
            ></div>

            <component
              :is="tab.icon"
              class="w-6 h-6 mb-2 transition-all duration-300 relative z-10"
              :class="
                activeTab === tab.id
                  ? isDark()
                    ? 'scale-110 drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]'
                    : 'scale-110 drop-shadow-[0_0_6px_rgba(8,145,178,0.4)]'
                  : 'group-hover:scale-110'
              "
            />

            <span
              class="text-xs font-bold tracking-wide text-center uppercase relative z-10"
              :class="
                activeTab === tab.id
                  ? isDark()
                    ? 'bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent'
                    : 'bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent'
                  : ''
              "
            >
              {{ tab.name }}
            </span>

            <span
              v-if="activeTab === tab.id"
              class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-400 animate-pulse"
            ></span>
          </button>
        </nav>
      </div>
    </div>

    <div 
      class="rounded-3xl shadow-2xl p-8 border min-h-[420px] transition-all duration-300"
      :class="containerClasses"
    >
      <ScanProgress v-if="activeTab !== 'database' && activeTab !== 'scheduler' && activeTab !== 'fullscan' && activeTab !== 'terminal'" :progress="scanProgress" />
      
      <HostsTable v-if="activeTab === 'database'" />
      <FullScan v-else-if="activeTab === 'fullscan'" />
      <PingScanner v-else-if="activeTab === 'ping'" />
      <PortScanner v-else-if="activeTab === 'ports'" />
      <ServiceScanner v-else-if="activeTab === 'services'" />
      <OSDetection v-else-if="activeTab === 'os'" />
      <MacScanner v-else-if="activeTab === 'mac'" />
      <ScanScheduler v-else-if="activeTab === 'scheduler'" />
      <SSHTerminal v-else-if="activeTab === 'terminal'" />
    </div>
  </div>
</template>

<style>
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
