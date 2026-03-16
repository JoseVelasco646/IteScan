<script setup>
import { computed } from 'vue'
import {
  Eye,
  Trash2,
  Globe,
  Network,
  Wifi,
  Server,
  Tag,
  Activity,
  Clock,
  Settings,
  Search,
  ArrowUp,
  ArrowDown,
  ChevronsUpDown,
  Pencil,
  Check,
  Monitor,
  X,
} from 'lucide-vue-next'
import SkeletonLoader from './SkeletonLoader.vue'
import { useTheme } from '../composables/useTheme'

const props = defineProps({
  loading: { type: Boolean, default: false },
  hosts: { type: Array, default: () => [] },
  paginatedHosts: { type: Array, default: () => [] },
  filteredHostsLength: { type: Number, default: 0 },
  totalFiltered: { type: Number, default: 0 },
  currentPage: { type: Number, required: true },
  pageSize: { type: Number, required: true },
  pageSizeOptions: { type: Array, required: true },
  totalPages: { type: Number, required: true },
  visiblePages: { type: Array, required: true },
  selectedHosts: { type: Array, required: true },
  sortField: { type: String, default: 'ip' },
  sortDirection: { type: String, default: 'asc' },
  editingNickname: { type: String, default: null },
  nicknameInput: { type: String, default: '' },
  savingNickname: { type: Boolean, default: false },
  canEditResources: { type: Boolean, default: false },
  canDeleteResources: { type: Boolean, default: false },
  isSelected: { type: Function, required: true },
  formatLocal: { type: Function, required: true },
})

const emit = defineEmits([
  'select-all',
  'toggle-selection',
  'toggle-sort',
  'start-edit-nickname',
  'cancel-edit-nickname',
  'save-nickname',
  'show-details',
  'delete-host-confirm',
  'go-to-page',
  'change-page-size',
  'update:nicknameInput',
])

const { isDark } = useTheme()

const nicknameModel = computed({
  get: () => props.nicknameInput,
  set: (value) => emit('update:nicknameInput', value),
})

const allSelected = computed(() => props.selectedHosts.length === props.hosts.length && props.hosts.length > 0)
</script>

<template>
  <div
    class="overflow-x-auto rounded-2xl shadow-2xl border"
    :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border-slate-200'"
  >
    <table class="min-w-full divide-y" :class="isDark() ? 'divide-slate-700/50' : 'divide-slate-200'" role="table" aria-label="Tabla de hosts descubiertos">
      <thead
        class="backdrop-blur-sm"
        :class="isDark() ? 'bg-gradient-to-r from-slate-800/80 via-slate-900/80 to-slate-800/80' : 'bg-gradient-to-r from-slate-100 via-slate-50 to-slate-100'"
      >
        <tr>
          <th class="px-4 py-4">
            <div class="flex items-center justify-center">
              <input
                type="checkbox"
                @change="emit('select-all')"
                :checked="allSelected"
                class="w-5 h-5 appearance-none border-2 rounded-md transition-all duration-200 cursor-pointer relative before:content-['✓'] before:absolute before:inset-0 before:flex before:items-center before:justify-center before:text-white before:text-sm before:font-bold before:opacity-0 checked:before:opacity-100 before:transition-opacity"
                :class="isDark()
                  ? 'bg-slate-700 border-slate-500 checked:bg-gradient-to-br checked:from-cyan-500 checked:to-blue-600 checked:border-cyan-400 hover:border-cyan-400'
                  : 'bg-white border-slate-300 checked:bg-gradient-to-br checked:from-cyan-400 checked:to-blue-500 checked:border-cyan-400 hover:border-cyan-400'"
              />
            </div>
          </th>
          <th class="px-6 py-4 text-left">
            <button type="button" @click.stop="emit('toggle-sort', 'ip')" class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer">
              <Wifi class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">IP</span>
              <ArrowUp v-if="sortField === 'ip' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
              <ArrowDown v-else-if="sortField === 'ip' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
              <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
            </button>
          </th>
          <th class="px-6 py-4 text-left">
            <button type="button" @click.stop="emit('toggle-sort', 'hostname')" class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer">
              <Globe class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">Hostname</span>
              <ArrowUp v-if="sortField === 'hostname' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
              <ArrowDown v-else-if="sortField === 'hostname' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
              <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
            </button>
          </th>
          <th class="px-6 py-4 text-left">
            <button type="button" @click.stop="emit('toggle-sort', 'nickname')" class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer">
              <Pencil class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">Apodo</span>
              <ArrowUp v-if="sortField === 'nickname' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
              <ArrowDown v-else-if="sortField === 'nickname' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
              <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
            </button>
          </th>
          <th class="px-6 py-4 text-left">
            <button type="button" @click.stop="emit('toggle-sort', 'mac')" class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer">
              <Network class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">MAC</span>
              <ArrowUp v-if="sortField === 'mac' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
              <ArrowDown v-else-if="sortField === 'mac' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
              <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
            </button>
          </th>
          <th class="px-6 py-4 text-left">
            <button type="button" @click.stop="emit('toggle-sort', 'vendor')" class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer">
              <Tag class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">Vendor</span>
              <ArrowUp v-if="sortField === 'vendor' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
              <ArrowDown v-else-if="sortField === 'vendor' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
              <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
            </button>
          </th>
          <th class="px-6 py-4 text-left">
            <button type="button" @click.stop="emit('toggle-sort', 'os_name')" class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer">
              <Monitor class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">Sistema Operativo</span>
              <ArrowUp v-if="sortField === 'os_name' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
              <ArrowDown v-else-if="sortField === 'os_name' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
              <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
            </button>
          </th>
          <th class="px-6 py-4 text-left">
            <button type="button" @click.stop="emit('toggle-sort', 'status')" class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer">
              <Activity class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">Estado</span>
              <ArrowUp v-if="sortField === 'status' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
              <ArrowDown v-else-if="sortField === 'status' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
              <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
            </button>
          </th>
          <th class="px-6 py-4 text-left">
            <div class="flex items-center gap-2">
              <Server class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">Puertos</span>
            </div>
          </th>
          <th class="px-6 py-4 text-left">
            <button type="button" @click.stop="emit('toggle-sort', 'last_seen')" class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer">
              <Clock class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">Última Conexión</span>
              <ArrowUp v-if="sortField === 'last_seen' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
              <ArrowDown v-else-if="sortField === 'last_seen' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
              <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
            </button>
          </th>
          <th class="px-6 py-4 text-left">
            <div class="flex items-center gap-2">
              <Settings class="w-4 h-4" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
              <span class="text-xs font-bold uppercase tracking-wider" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">Acciones</span>
            </div>
          </th>
        </tr>
      </thead>

      <tbody class="divide-y" :class="isDark() ? 'divide-slate-700/30 bg-slate-900/50' : 'divide-slate-200 bg-white'">
        <tr v-if="loading && hosts.length === 0">
          <td colspan="11" class="px-6 py-8">
            <SkeletonLoader type="table" :rows="5" :columns="9" />
          </td>
        </tr>

        <tr v-else-if="hosts.length === 0">
          <td colspan="11" class="px-6 py-8 text-center">
            <div class="flex flex-col items-center gap-2">
              <Search class="w-12 h-12 text-slate-600" />
              <span class="text-slate-400 font-medium">No se encontraron hosts</span>
            </div>
          </td>
        </tr>

        <tr
          v-for="host in paginatedHosts"
          :key="host.id"
          :class="[
            'transition-all duration-200 border-l-4',
            isSelected(host)
              ? 'bg-cyan-900/20 hover:bg-cyan-800/30 border-cyan-400'
              : 'hover:bg-slate-800/40 border-transparent hover:border-slate-600'
          ]"
        >
          <td class="px-4 py-4">
            <div class="flex items-center justify-center">
              <input
                type="checkbox"
                :checked="isSelected(host)"
                @change="emit('toggle-selection', host)"
                class="w-5 h-5 appearance-none bg-slate-700 border-2 border-slate-500 rounded-md checked:bg-gradient-to-br checked:from-cyan-500 checked:to-blue-600 checked:border-cyan-400 hover:border-cyan-400 transition-all duration-200 cursor-pointer relative before:content-['✓'] before:absolute before:inset-0 before:flex before:items-center before:justify-center before:text-white before:text-sm before:font-bold before:opacity-0 checked:before:opacity-100 before:transition-opacity"
              />
            </div>
          </td>

          <td class="px-6 py-4 text-sm font-mono font-semibold text-cyan-300">{{ host.ip }}</td>
          <td class="px-6 py-4 text-sm text-slate-300">{{ host.hostname || 'N/A' }}</td>
          <td class="px-6 py-4 text-sm">
            <div v-if="editingNickname === host.ip" class="flex items-center gap-1">
              <input
                v-model="nicknameModel"
                @keyup.enter="emit('save-nickname', host)"
                @keyup.escape="emit('cancel-edit-nickname')"
                class="w-32 px-2 py-1 text-sm rounded-lg border focus:outline-none focus:ring-2 focus:ring-cyan-400"
                :class="isDark() ? 'bg-slate-800 border-slate-600 text-slate-200' : 'bg-white border-slate-300 text-slate-800'"
                placeholder="Apodo..."
                :disabled="savingNickname"
              />
              <button
                @click="emit('save-nickname', host)"
                :disabled="savingNickname"
                class="flex items-center justify-center w-7 h-7 rounded-lg text-green-400 hover:text-green-300 bg-green-900/20 hover:bg-green-900/40 border border-green-700/30 transition-all duration-200"
                title="Guardar"
              >
                <Check class="w-3.5 h-3.5" />
              </button>
              <button
                @click="emit('cancel-edit-nickname')"
                class="flex items-center justify-center w-7 h-7 rounded-lg text-red-400 hover:text-red-300 bg-red-900/20 hover:bg-red-900/40 border border-red-700/30 transition-all duration-200"
                title="Cancelar"
              >
                <X class="w-3.5 h-3.5" />
              </button>
            </div>
            <div v-else class="flex items-center gap-1 group/nick">
              <span :class="host.nickname ? (isDark() ? 'text-amber-300' : 'text-amber-600') : 'text-slate-500'">{{ host.nickname || '—' }}</span>
              <button
                v-if="canEditResources"
                @click="emit('start-edit-nickname', host)"
                class="opacity-0 group-hover/nick:opacity-100 flex items-center justify-center w-6 h-6 rounded-md transition-all duration-200"
                :class="isDark() ? 'text-slate-400 hover:text-cyan-400 hover:bg-slate-700' : 'text-slate-400 hover:text-cyan-600 hover:bg-slate-100'"
                title="Editar apodo"
              >
                <Pencil class="w-3 h-3" />
              </button>
            </div>
          </td>
          <td class="px-6 py-4 text-sm font-mono text-slate-400">{{ host.mac || 'N/A' }}</td>
          <td class="px-6 py-4">
            <span v-if="host.vendor && host.vendor !== 'N/A'" class="inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
              {{ host.vendor }}
            </span>
            <span v-else class="text-sm text-slate-500">N/A</span>
          </td>
          <td class="px-6 py-4">
            <span v-if="host.os_name && host.os_name !== 'N/A'" class="inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold bg-blue-900/30 text-blue-300 border border-blue-700/50">
              {{ host.os_name }}
            </span>
            <span v-else class="text-sm text-slate-500">N/A</span>
          </td>

          <td class="px-6 py-4">
            <span
              :class="[
                'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg uppercase tracking-wide transition-all duration-200',
                host.status === 'up'
                  ? 'bg-gradient-to-r from-green-900/50 to-emerald-900/50 text-green-300 border border-green-700/50 shadow-lg shadow-green-500/20'
                  : 'bg-gradient-to-r from-red-900/50 to-rose-900/50 text-red-300 border border-red-700/50 shadow-lg shadow-red-500/20',
              ]"
            >
              <div :class="['w-2 h-2 rounded-full', host.status === 'up' ? 'bg-green-400 animate-pulse' : 'bg-red-400']"></div>
              {{ host.status }}
            </span>
          </td>
          <td class="px-6 py-4">
            <span class="inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold bg-purple-900/30 text-purple-300 border border-purple-700/50">
              {{ host.ports?.length || 0 }} open
            </span>
          </td>
          <td class="px-6 py-4 text-sm text-slate-400">{{ formatLocal(host.last_seen) || 'N/A' }}</td>
          <td class="px-6 py-4 text-sm">
            <div class="flex gap-2">
              <button
                @click="emit('show-details', host)"
                class="flex items-center justify-center w-9 h-9 rounded-lg text-blue-400 hover:text-blue-300 bg-blue-900/20 hover:bg-blue-900/40 border border-blue-700/30 hover:border-blue-600/50 shadow-md shadow-blue-400/10 hover:shadow-blue-400/20 transition-all duration-200 transform hover:scale-110 active:scale-95"
                title="Ver detalles"
              >
                <Eye class="w-4 h-4" />
              </button>

              <button
                v-if="canDeleteResources"
                @click="emit('delete-host-confirm', host.ip)"
                class="flex items-center justify-center w-9 h-9 rounded-lg text-red-400 hover:text-red-300 bg-red-900/20 hover:bg-red-900/40 border border-red-700/30 hover:border-red-600/50 shadow-md shadow-red-400/10 hover:shadow-red-400/20 transition-all duration-200 transform hover:scale-110 active:scale-95"
                title="Eliminar host"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div v-if="filteredHostsLength > 0" class="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 px-2">
    <div class="flex items-center gap-3">
      <span class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
        Mostrando {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, totalFiltered) }} de {{ totalFiltered }} hosts
      </span>
      <select
        :value="pageSize"
        @change="emit('change-page-size', Number($event.target.value))"
        class="px-2 py-1 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
        :class="isDark() ? 'bg-slate-800 border border-slate-600 text-white' : 'bg-white border border-slate-300 text-slate-800'"
      >
        <option v-for="opt in pageSizeOptions" :key="opt" :value="opt">{{ opt }} por página</option>
      </select>
    </div>
    <div class="flex items-center gap-1">
      <button
        @click="emit('go-to-page', 1)"
        :disabled="currentPage === 1"
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all disabled:opacity-30"
        :class="isDark() ? 'bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:hover:bg-slate-800' : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-300 disabled:hover:bg-white'"
      >«</button>
      <button
        @click="emit('go-to-page', currentPage - 1)"
        :disabled="currentPage === 1"
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all disabled:opacity-30"
        :class="isDark() ? 'bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:hover:bg-slate-800' : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-300 disabled:hover:bg-white'"
      >‹</button>
      <button
        v-for="page in visiblePages"
        :key="page"
        @click="emit('go-to-page', page)"
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
        :class="page === currentPage
          ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30'
          : isDark()
            ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-300'"
      >{{ page }}</button>
      <button
        @click="emit('go-to-page', currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all disabled:opacity-30"
        :class="isDark() ? 'bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:hover:bg-slate-800' : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-300 disabled:hover:bg-white'"
      >›</button>
      <button
        @click="emit('go-to-page', totalPages)"
        :disabled="currentPage === totalPages"
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all disabled:opacity-30"
        :class="isDark() ? 'bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:hover:bg-slate-800' : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-300 disabled:hover:bg-white'"
      >»</button>
    </div>
  </div>
</template>
