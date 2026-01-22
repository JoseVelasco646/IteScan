<template>
  <div
    class="animate-pulse"
    :class="containerClass"
    role="status"
    :aria-label="ariaLabel || 'Cargando contenido'"
  >
    <template v-if="type === 'table'">
      <div class="space-y-4">
        <div class="flex gap-4 pb-4 border-b border-slate-700/50">
          <div v-for="i in columns" :key="i" class="flex-1">
            <div class="h-4 bg-gradient-to-r from-slate-700/50 via-slate-600/30 to-slate-700/50 rounded relative overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-500/20 to-transparent animate-shimmer"></div>
            </div>
          </div>
        </div>
        <div v-for="row in rows" :key="row" class="flex gap-4 py-3 hover:bg-slate-800/20 transition-colors rounded-lg px-2">
          <div v-for="col in columns" :key="col" class="flex-1">
            <div class="h-3 bg-gradient-to-r from-slate-800/50 via-slate-700/30 to-slate-800/50 rounded relative overflow-hidden" :style="{ width: `${Math.random() * 30 + 70}%` }">
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-600/20 to-transparent animate-shimmer" :style="{ animationDelay: `${row * 100}ms` }"></div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="type === 'card'">
      <div class="bg-gradient-to-br from-slate-900/50 to-slate-800/50 rounded-2xl p-6 border border-slate-700/50 relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-600/10 to-transparent animate-shimmer"></div>
        <div class="relative z-10">
          <div class="flex items-center gap-4 mb-4">
            <div class="w-12 h-12 bg-gradient-to-br from-slate-700/50 to-slate-600/50 rounded-xl relative overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 animate-pulse"></div>
            </div>
            <div class="flex-1 space-y-2">
              <div class="h-4 bg-gradient-to-r from-slate-700/50 to-slate-600/50 rounded w-1/2 relative overflow-hidden">
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-500/20 to-transparent animate-shimmer"></div>
              </div>
              <div class="h-3 bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded w-3/4 relative overflow-hidden">
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-500/20 to-transparent animate-shimmer" style="animation-delay: 200ms"></div>
              </div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="h-3 bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded relative overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-500/20 to-transparent animate-shimmer" style="animation-delay: 400ms"></div>
            </div>
            <div class="h-3 bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded w-5/6 relative overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-500/20 to-transparent animate-shimmer" style="animation-delay: 600ms"></div>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template v-else-if="type === 'stats'">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div v-for="i in 3" :key="i" class="bg-gradient-to-br from-slate-900/50 to-slate-800/50 rounded-2xl p-6 border border-slate-700/50 relative overflow-hidden group">
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-600/10 to-transparent animate-shimmer" :style="{ animationDelay: `${i * 200}ms` }"></div>
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-4">
              <div class="w-10 h-10 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 rounded-xl relative overflow-hidden">
                <div class="absolute inset-0 bg-gradient-to-br from-cyan-400/20 to-blue-500/20 animate-pulse"></div>
              </div>
              <div class="h-8 w-16 bg-gradient-to-r from-slate-700/50 to-slate-600/50 rounded relative overflow-hidden">
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/10 to-transparent animate-shimmer"></div>
              </div>
            </div>
            <div class="h-3 bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded w-2/3 mb-2 relative overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-500/20 to-transparent animate-shimmer"></div>
            </div>
            <div class="h-2 bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded w-full relative overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-500/20 to-transparent animate-shimmer" style="animation-delay: 300ms"></div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="type === 'text'">
      <div class="space-y-2">
        <div v-for="i in lines" :key="i" class="h-3 bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded" :style="{ width: i === lines ? '70%' : '100%' }"></div>
      </div>
    </template>

    <template v-else>
      <div class="h-full bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded" :style="customStyle"></div>
    </template>

    <span class="sr-only">Cargando...</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'default', 
    validator: (value) => ['table', 'card', 'stats', 'text', 'default'].includes(value)
  },
  rows: {
    type: Number,
    default: 5
  },
  columns: {
    type: Number,
    default: 4
  },
  lines: {
    type: Number,
    default: 3
  },
  height: {
    type: String,
    default: 'auto'
  },
  width: {
    type: String,
    default: '100%'
  },
  containerClass: {
    type: String,
    default: ''
  },
  ariaLabel: {
    type: String,
    default: ''
  }
})

const customStyle = computed(() => ({
  height: props.height,
  width: props.width
}))
</script>

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
</style>
