<script setup>
import { computed } from 'vue'
import { Search, Globe, Network, GitBranch, Clock } from 'lucide-vue-next'
import { useTheme } from '../composables/useTheme'
import { useButtonClasses } from '../composables/useButtonClasses'

const props = defineProps({
  filterType: { type: String, required: true },
  filterStartIp: { type: String, required: true },
  filterEndIp: { type: String, required: true },
  filterSubnet: { type: String, required: true },
  searchQuery: { type: String, required: true },
  filterStartDate: { type: String, required: true },
  filterEndDate: { type: String, required: true },
})

const emit = defineEmits([
  'set-filter',
  'reload-all',
  'apply-filter',
  'search-hosts',
  'apply-date-filter',
  'clear-date-filter',
  'update:filterStartIp',
  'update:filterEndIp',
  'update:filterSubnet',
  'update:searchQuery',
  'update:filterStartDate',
  'update:filterEndDate',
])

const { isDark } = useTheme()
const { btnPrimaryClass, btnSecondaryClass } = useButtonClasses()

const startIp = computed({
  get: () => props.filterStartIp,
  set: (value) => emit('update:filterStartIp', value),
})

const endIp = computed({
  get: () => props.filterEndIp,
  set: (value) => emit('update:filterEndIp', value),
})

const subnet = computed({
  get: () => props.filterSubnet,
  set: (value) => emit('update:filterSubnet', value),
})

const query = computed({
  get: () => props.searchQuery,
  set: (value) => emit('update:searchQuery', value),
})

const startDate = computed({
  get: () => props.filterStartDate,
  set: (value) => emit('update:filterStartDate', value),
})

const endDate = computed({
  get: () => props.filterEndDate,
  set: (value) => emit('update:filterEndDate', value),
})
</script>

<template>
  <div
    class="border rounded-3xl p-8 mb-6 shadow-2xl"
    :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border-slate-200'"
  >
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg"
        :class="isDark() ? 'bg-gradient-to-br from-cyan-500 to-blue-600 shadow-cyan-500/30' : 'bg-gradient-to-br from-cyan-400 to-blue-500 shadow-cyan-400/30'"
      >
        <Search class="w-5 h-5 text-white" />
      </div>
      <h3 class="text-2xl font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">Filtros y Búsqueda</h3>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
      <button
        @click="emit('set-filter', 'all'); emit('reload-all')"
        :class="[
          filterType === 'all' ? btnPrimaryClass : btnSecondaryClass,
          'w-full justify-center py-3'
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-2">
          <Globe class="w-5 h-5" />
          <span>Todos</span>
        </div>
      </button>

      <button
        @click="emit('set-filter', 'range')"
        :class="[
          filterType === 'range' ? btnPrimaryClass : btnSecondaryClass,
          'w-full justify-center py-3'
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-2">
          <Network class="w-5 h-5" />
          <span>Rango IP</span>
        </div>
      </button>

      <button
        @click="emit('set-filter', 'subnet')"
        :class="[
          filterType === 'subnet' ? btnPrimaryClass : btnSecondaryClass,
          'w-full justify-center py-3'
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-2">
          <GitBranch class="w-5 h-5" />
          <span>Subred</span>
        </div>
      </button>

      <button
        @click="emit('set-filter', 'search')"
        :class="[
          filterType === 'search' ? btnPrimaryClass : btnSecondaryClass,
          'w-full justify-center py-3'
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-2">
          <Search class="w-5 h-5" />
          <span>Buscar</span>
        </div>
      </button>

      <button
        @click="emit('set-filter', 'date')"
        :class="[
          filterType === 'date' ? btnPrimaryClass : btnSecondaryClass,
          'w-full justify-center py-3'
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-2">
          <Clock class="w-5 h-5" />
          <span>Fecha</span>
        </div>
      </button>
    </div>

    <Transition name="fade-slide" mode="out-in">
      <div
        v-if="filterType === 'range'"
        class="rounded-2xl p-6 border"
        :class="isDark() ? 'bg-slate-800/30 border-slate-700/50' : 'bg-slate-50 border-slate-200'"
      >
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="text-xs font-semibold mb-2 block uppercase" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">IP Inicial</label>
            <input
              v-model="startIp"
              class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
              :class="isDark()
                ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
              placeholder="192.168.0.1"
            />
          </div>
          <div>
            <label class="text-xs font-semibold mb-2 block uppercase" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">IP Final</label>
            <input
              v-model="endIp"
              class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
              :class="isDark()
                ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
              placeholder="192.168.0.254"
            />
          </div>
          <div class="flex items-end">
            <button
              @click="emit('apply-filter')"
              :class="[btnPrimaryClass, 'w-full justify-center py-3']"
            >
              Aplicar Filtro
            </button>
          </div>
        </div>
      </div>

      <div
        v-else-if="filterType === 'subnet'"
        class="rounded-2xl p-6 border"
        :class="isDark() ? 'bg-slate-800/30 border-slate-700/50' : 'bg-slate-50 border-slate-200'"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="text-xs font-semibold mb-2 block uppercase" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Subred CIDR</label>
            <input
              v-model="subnet"
              class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
              :class="isDark()
                ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
              placeholder="192.168.0.0/24"
            />
          </div>
          <div class="flex items-end">
            <button
              @click="emit('apply-filter')"
              :class="[btnPrimaryClass, 'w-full justify-center py-3']"
            >
              Aplicar Filtro
            </button>
          </div>
        </div>
      </div>

      <div
        v-else-if="filterType === 'search'"
        class="rounded-2xl p-6 border"
        :class="isDark() ? 'bg-slate-800/30 border-slate-700/50' : 'bg-slate-50 border-slate-200'"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="text-xs font-semibold mb-2 block uppercase" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Término de Búsqueda</label>
            <input
              v-model="query"
              @keyup.enter="emit('search-hosts')"
              class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
              :class="isDark()
                ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
              placeholder="IP, Hostname o Vendor..."
            />
          </div>
          <div class="flex items-end">
            <button
              @click="emit('search-hosts')"
              :class="[btnPrimaryClass, 'w-full justify-center py-3']"
            >
              <Search class="w-5 h-5" />
              <span>Buscar</span>
            </button>
          </div>
        </div>
      </div>

      <div
        v-else-if="filterType === 'date'"
        class="rounded-2xl p-6 border"
        :class="isDark() ? 'bg-slate-800/30 border-slate-700/50' : 'bg-slate-50 border-slate-200'"
      >
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="text-xs font-semibold mb-2 block uppercase" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Desde</label>
            <input
              v-model="startDate"
              type="date"
              class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
              :class="isDark()
                ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
            />
          </div>
          <div>
            <label class="text-xs font-semibold mb-2 block uppercase" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Hasta</label>
            <input
              v-model="endDate"
              type="date"
              class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
              :class="isDark()
                ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
            />
          </div>
          <div class="flex items-end gap-2">
            <button
              @click="emit('apply-date-filter')"
              :class="[btnPrimaryClass, 'flex-1 justify-center py-3']"
            >
              Filtrar
            </button>
            <button
              @click="emit('clear-date-filter')"
              :class="[btnSecondaryClass, 'justify-center py-3']"
            >
              Limpiar
            </button>
          </div>
        </div>
        <p class="text-xs mt-3 flex items-center gap-2" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
          <Clock class="w-3 h-3" />
          Filtra hosts por fecha de última conexión
        </p>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
