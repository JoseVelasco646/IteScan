<script setup>
import { useTheme } from '../composables/useTheme'
import { Users, Wifi, WifiOff, HelpCircle } from 'lucide-vue-next'
import SkeletonLoader from './SkeletonLoader.vue'

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  hostsLength: {
    type: Number,
    default: 0,
  },
  statistics: {
    type: Object,
    default: null,
  },
})

const { isDark } = useTheme()
</script>

<template>
  <SkeletonLoader v-if="loading && hostsLength === 0" type="stats" class="mb-6" />

  <div v-else-if="statistics" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mb-6">
    <div
      class="bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 group"
    >
      <div class="flex items-center justify-between mb-3">
        <div class="p-3 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 rounded-xl border border-cyan-500/30">
          <Users class="w-6 h-6 text-cyan-400" />
        </div>
        <div class="text-right">
          <p class="text-slate-400 text-xs uppercase tracking-wider font-semibold">Total Hosts</p>
        </div>
      </div>
      <p class="text-5xl font-extrabold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">{{ statistics.total }}</p>
      <div class="mt-3 h-1 bg-slate-700/50 rounded-full overflow-hidden">
        <div class="h-full bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full" style="width: 100%"></div>
      </div>
    </div>

    <div
      class="bg-gradient-to-br from-green-900/20 to-emerald-900/20 backdrop-blur-sm rounded-2xl p-6 border border-green-700/50 shadow-xl hover:shadow-2xl hover:shadow-green-500/20 hover:scale-105 transition-all duration-300 group"
    >
      <div class="flex items-center justify-between mb-3">
        <div class="p-3 bg-gradient-to-br from-green-500/20 to-emerald-600/20 rounded-xl border border-green-500/30">
          <Wifi class="w-6 h-6 text-green-400" />
        </div>
        <div class="flex items-center gap-2">
          <span class="relative flex h-3 w-3">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          <p class="text-green-300 text-xs uppercase tracking-wider font-semibold">Online</p>
        </div>
      </div>
      <p class="text-5xl font-extrabold bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">{{ statistics.online }}</p>
      <div class="mt-3 h-1 bg-slate-700/50 rounded-full overflow-hidden">
        <div class="h-full bg-gradient-to-r from-green-500 to-emerald-600 rounded-full transition-all duration-500" :style="`width: ${statistics.total > 0 ? (statistics.online / statistics.total * 100) : 0}%`"></div>
      </div>
    </div>

    <div
      class="bg-gradient-to-br from-red-900/20 to-orange-900/20 backdrop-blur-sm rounded-2xl p-6 border border-red-700/50 shadow-xl hover:shadow-2xl hover:shadow-red-500/20 hover:scale-105 transition-all duration-300 group"
    >
      <div class="flex items-center justify-between mb-3">
        <div class="p-3 bg-gradient-to-br from-red-500/20 to-orange-600/20 rounded-xl border border-red-500/30">
          <WifiOff class="w-6 h-6 text-red-400" />
        </div>
        <div class="flex items-center gap-2">
          <span class="relative flex h-3 w-3">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
          <p class="text-red-300 text-xs uppercase tracking-wider font-semibold">Offline</p>
        </div>
      </div>
      <p class="text-5xl font-extrabold bg-gradient-to-r from-red-400 to-orange-500 bg-clip-text text-transparent">{{ statistics.offline }}</p>
      <div class="mt-3 h-1 bg-slate-700/50 rounded-full overflow-hidden">
        <div class="h-full bg-gradient-to-r from-red-500 to-orange-600 rounded-full transition-all duration-500" :style="`width: ${statistics.total > 0 ? (statistics.offline / statistics.total * 100) : 0}%`"></div>
      </div>
    </div>

    <div
      class="bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-sm rounded-2xl p-6 border border-slate-600/50 shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 group"
    >
      <div class="flex items-center justify-between mb-3">
        <div class="p-3 bg-gradient-to-br from-slate-500/20 to-slate-600/20 rounded-xl border border-slate-500/30">
          <HelpCircle class="w-6 h-6 text-slate-400" />
        </div>
        <div class="text-right">
          <p class="text-slate-400 text-xs uppercase tracking-wider font-semibold">Desconocidos</p>
        </div>
      </div>
      <p class="text-5xl font-extrabold" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">{{ statistics.unknown }}</p>
      <div class="mt-3 h-1 bg-slate-700/50 rounded-full overflow-hidden">
        <div class="h-full bg-gradient-to-r from-slate-500 to-slate-600 rounded-full transition-all duration-500" :style="`width: ${statistics.total > 0 ? (statistics.unknown / statistics.total * 100) : 0}%`"></div>
      </div>
    </div>
  </div>
</template>
