<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ScrollText, Filter, RefreshCw, ChevronLeft, ChevronRight, User, Shield, Server, Calendar, Terminal, LogIn, Trash2, Pencil, Plus, Scan, ToggleLeft, Play, Download } from 'lucide-vue-next'
import { scannerAPI } from '../api/scanner.js'
import { useTheme } from '../composables/useTheme'
import { useButtonClasses } from '../composables/useButtonClasses'
import { formatDateTime, formatRelativeTime } from '../utils/dateTime'
import {
  AUDIT_CATEGORIES,
  AUDIT_ACTIONS,
  getAuditCategoryIcon,
  getAuditActionIcon,
  getAuditActionLabel,
  getAuditCategoryLabel,
  getAuditCategoryColor,
  getAuditActionBadgeColor,
} from '../utils/auditLogUtils'

const { isDark } = useTheme()
const { btnPrimaryClass, btnSecondaryClass, getPaginationButtonClass } = useButtonClasses()

const logs = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const limit = 20
const stats = ref(null)


const filterCategory = ref('')
const filterAction = ref('')
const filterUsername = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')
const showFilters = ref(false)

const categories = AUDIT_CATEGORIES
const actions = AUDIT_ACTIONS

const totalPages = computed(() => Math.ceil(total.value / limit))
const skip = computed(() => (page.value - 1) * limit)

async function fetchLogs() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', skip.value)
    params.append('limit', limit)
    if (filterCategory.value) params.append('category', filterCategory.value)
    if (filterAction.value) params.append('action', filterAction.value)
    if (filterUsername.value) params.append('username', filterUsername.value)
    if (filterDateFrom.value) params.append('date_from', filterDateFrom.value)
    if (filterDateTo.value) params.append('date_to', filterDateTo.value)
    
    const response = await scannerAPI.getAuditLogs(params.toString())
    logs.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('Error al obtener auditoría:', error)
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const response = await scannerAPI.getAuditStats()
    stats.value = response
  } catch (error) {
    console.error('Error al obtener estadísticas:', error)
  }
}

function applyFilters() {
  page.value = 1
  fetchLogs()
}

function clearFilters() {
  filterCategory.value = ''
  filterAction.value = ''
  filterUsername.value = ''
  filterDateFrom.value = ''
  filterDateTo.value = ''
  page.value = 1
  fetchLogs()
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    fetchLogs()
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
    fetchLogs()
  }
}

function getCategoryIcon(category) {
  return getAuditCategoryIcon(category)
}

function getCategoryColor(category) {
  return getAuditCategoryColor(category, isDark())
}

function getActionIcon(action) {
  return getAuditActionIcon(action)
}

function getActionBadgeColor(action) {
  return getAuditActionBadgeColor(action, isDark())
}

function getActionLabel(action) {
  return getAuditActionLabel(action)
}

function getCategoryLabel(category) {
  return getAuditCategoryLabel(category)
}

function formatDate(isoString) {
  return formatDateTime(isoString, { locale: 'es-MX', fallback: '-', withSeconds: true })
}

async function exportCSV() {
  try {
    const params = new URLSearchParams()
    params.append('skip', 0)
    params.append('limit', 10000)
    if (filterCategory.value) params.append('category', filterCategory.value)
    if (filterAction.value) params.append('action', filterAction.value)
    if (filterUsername.value) params.append('username', filterUsername.value)
    if (filterDateFrom.value) params.append('date_from', filterDateFrom.value)
    if (filterDateTo.value) params.append('date_to', filterDateTo.value)
    
    const response = await scannerAPI.getAuditLogs(params.toString())
    const items = response.items
    
    const csv = [
      ['Fecha', 'Usuario', 'Acción', 'Categoría', 'Descripción', 'IP'].join(','),
      ...items.map(i => [
        `"${formatDate(i.created_at)}"`,
        `"${i.username || 'Sistema'}"`,
        `"${getActionLabel(i.action)}"`,
        `"${getCategoryLabel(i.category)}"`,
        `"${(i.description || '').replace(/"/g, '""')}"`,
        `"${i.ip_address || ''}"`,
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_log_${new Date().toISOString().slice(0,10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error al exportar:', error)
  }
}

onMounted(() => {
  fetchLogs()
  fetchStats()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="p-2.5 rounded-xl" :class="isDark() ? 'bg-indigo-500/10 border border-indigo-500/20' : 'bg-indigo-50 border border-indigo-200'">
          <ScrollText class="w-6 h-6" :class="isDark() ? 'text-indigo-400' : 'text-indigo-600'" />
        </div>
        <div>
          <h2 class="text-xl font-bold" :class="isDark() ? 'text-white' : 'text-slate-900'">
            Auditoría del Sistema
          </h2>
          <p class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
            {{ total }} registros totales
          </p>
        </div>
      </div>
      
      <div class="flex items-center gap-2">
        <button
          @click="exportCSV"
          :class="btnSecondaryClass"
        >
          <Download class="w-4 h-4" />
          <span class="hidden sm:inline">Exportar</span>
        </button>
        <button
          @click="showFilters = !showFilters"
          class="relative inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-sm font-semibold transition-all duration-200 border"
          :class="showFilters
            ? (isDark() ? 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30' : 'bg-cyan-50 text-cyan-700 border-cyan-300')
            : (isDark() ? 'bg-slate-800 text-slate-200 border-slate-600 hover:bg-slate-700' : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50')"
        >
          <Filter class="w-4 h-4" />
          <span class="hidden sm:inline">Filtros</span>
          <!-- Active filters indicator -->
          <span v-if="filterCategory || filterAction || filterUsername || filterDateFrom || filterDateTo"
            class="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full text-[10px] font-bold flex items-center justify-center"
            :class="isDark() ? 'bg-cyan-500 text-white' : 'bg-cyan-600 text-white'">
            {{ [filterCategory, filterAction, filterUsername, filterDateFrom, filterDateTo].filter(Boolean).length }}
          </span>
        </button>
        <button
          @click="fetchLogs(); fetchStats()"
          :disabled="loading"
          :class="btnSecondaryClass"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
        </button>
      </div>
    </div>

    <!-- Stats Cards - Enhanced with better styling -->
    <div v-if="stats" class="grid grid-cols-3 sm:grid-cols-6 gap-2">
      <button
        v-for="cat in categories.filter(c => c.value)"
        :key="cat.value"
        class="rounded-xl p-3 border transition-all duration-200 text-center group"
        :class="[
          filterCategory === cat.value 
            ? (isDark() ? 'border-cyan-500/50 bg-cyan-500/10 ring-1 ring-cyan-500/20' : 'border-cyan-400 bg-cyan-50 ring-1 ring-cyan-400/20')
            : (isDark() ? 'border-slate-700/50 bg-slate-800/30 hover:border-slate-600 hover:bg-slate-800/60' : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm')
        ]"
        @click="filterCategory = filterCategory === cat.value ? '' : cat.value; applyFilters()"
      >
        <div class="flex items-center justify-center mb-1.5">
          <div class="p-1.5 rounded-lg" :class="getCategoryColor(cat.value)">
            <component :is="getCategoryIcon(cat.value)" class="w-3.5 h-3.5" />
          </div>
        </div>
        <p class="text-lg font-bold leading-none mb-0.5" :class="isDark() ? 'text-white' : 'text-slate-900'">
          {{ stats.by_category[cat.value] || 0 }}
        </p>
        <span class="text-[10px] font-medium uppercase tracking-wider" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">{{ cat.label }}</span>
      </button>
    </div>

    <!-- Filters Panel - Improved with smooth transition -->
    <transition 
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 -translate-y-2 max-h-0"
      enter-to-class="opacity-100 translate-y-0 max-h-96"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0 max-h-96"
      leave-to-class="opacity-0 -translate-y-2 max-h-0"
    >
      <div
        v-if="showFilters"
        class="rounded-xl border p-4 space-y-4 overflow-hidden"
        :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'"
      >
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div>
            <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Categoría</label>
            <select
              v-model="filterCategory"
              class="w-full rounded-lg px-3 py-2 text-sm border outline-none transition-all focus:ring-2"
              :class="isDark() 
                ? 'bg-slate-900/50 border-slate-600 text-slate-200 focus:border-cyan-500 focus:ring-cyan-500/20' 
                : 'bg-white border-slate-300 text-slate-800 focus:border-cyan-500 focus:ring-cyan-500/20'"
            >
              <option v-for="c in categories" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Acción</label>
            <select
              v-model="filterAction"
              class="w-full rounded-lg px-3 py-2 text-sm border outline-none transition-all focus:ring-2"
              :class="isDark() 
                ? 'bg-slate-900/50 border-slate-600 text-slate-200 focus:border-cyan-500 focus:ring-cyan-500/20' 
                : 'bg-white border-slate-300 text-slate-800 focus:border-cyan-500 focus:ring-cyan-500/20'"
            >
              <option v-for="a in actions" :key="a.value" :value="a.value">{{ a.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Usuario</label>
            <input
              v-model="filterUsername"
              type="text"
              placeholder="Buscar usuario..."
              class="w-full rounded-lg px-3 py-2 text-sm border outline-none transition-all focus:ring-2"
              :class="isDark() 
                ? 'bg-slate-900/50 border-slate-600 text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:ring-cyan-500/20' 
                : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500/20'"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Desde</label>
            <input
              v-model="filterDateFrom"
              type="date"
              class="w-full rounded-lg px-3 py-2 text-sm border outline-none transition-all focus:ring-2"
              :class="isDark() 
                ? 'bg-slate-900/50 border-slate-600 text-slate-200 focus:border-cyan-500 focus:ring-cyan-500/20' 
                : 'bg-white border-slate-300 text-slate-800 focus:border-cyan-500 focus:ring-cyan-500/20'"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Hasta</label>
            <input
              v-model="filterDateTo"
              type="date"
              class="w-full rounded-lg px-3 py-2 text-sm border outline-none transition-all focus:ring-2"
              :class="isDark() 
                ? 'bg-slate-900/50 border-slate-600 text-slate-200 focus:border-cyan-500 focus:ring-cyan-500/20' 
                : 'bg-white border-slate-300 text-slate-800 focus:border-cyan-500 focus:ring-cyan-500/20'"
            />
          </div>
        </div>
        <div class="flex items-center justify-between">
          <!-- Active filter chips -->
          <div class="flex items-center gap-1.5 flex-wrap">
            <span v-if="filterCategory" 
              class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium cursor-pointer"
              :class="isDark() ? 'bg-cyan-500/15 text-cyan-400' : 'bg-cyan-100 text-cyan-700'"
              @click="filterCategory = ''; applyFilters()">
              {{ categories.find(c => c.value === filterCategory)?.label }}
              <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </span>
            <span v-if="filterAction"
              class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium cursor-pointer"
              :class="isDark() ? 'bg-cyan-500/15 text-cyan-400' : 'bg-cyan-100 text-cyan-700'"
              @click="filterAction = ''; applyFilters()">
              {{ actions.find(a => a.value === filterAction)?.label }}
              <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </span>
          </div>
          <div class="flex gap-2">
            <button
              @click="clearFilters"
              :class="btnSecondaryClass"
            >
              Limpiar todo
            </button>
            <button
              @click="applyFilters"
              :class="btnPrimaryClass"
            >
              Aplicar filtros
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <RefreshCw class="w-8 h-8 animate-spin" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
    </div>

    <!-- Timeline-style Logs -->
    <div v-else-if="logs.length > 0" class="relative">
      <!-- Timeline line -->
      <div class="absolute left-6 top-0 bottom-0 w-px hidden sm:block" :class="isDark() ? 'bg-slate-700/50' : 'bg-slate-200'"></div>
      
      <div class="space-y-3">
        <div
          v-for="log in logs"
          :key="log.id"
          class="relative rounded-xl border p-4 pl-4 sm:pl-14 transition-all duration-200 hover:shadow-md group"
          :class="isDark() 
            ? 'bg-slate-800/30 border-slate-700/50 hover:border-slate-600' 
            : 'bg-white border-slate-200 hover:border-slate-300'"
        >
          <!-- Timeline dot -->
          <div class="hidden sm:flex absolute left-3.5 top-5 w-5 h-5 rounded-full items-center justify-center ring-4"
            :class="[
              getCategoryColor(log.category),
              isDark() ? 'ring-slate-900' : 'ring-white'
            ]">
            <component :is="getCategoryIcon(log.category)" class="w-2.5 h-2.5" />
          </div>

          <div class="flex items-start gap-3">
            <!-- Category Icon (visible on mobile) -->
            <div class="p-2 rounded-lg flex-shrink-0 sm:hidden" :class="getCategoryColor(log.category)">
              <component :is="getCategoryIcon(log.category)" class="w-4 h-4" />
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-2 mb-1.5">
                <div class="flex items-center gap-2 flex-wrap">
                  <!-- Action Badge -->
                  <span 
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold border"
                    :class="getActionBadgeColor(log.action)"
                  >
                    <component :is="getActionIcon(log.action)" class="w-3 h-3" />
                    {{ getActionLabel(log.action) }}
                  </span>
                  
                  <!-- Category Badge -->
                  <span 
                    class="px-2 py-0.5 rounded-md text-xs font-medium"
                    :class="isDark() ? 'bg-slate-700/50 text-slate-400' : 'bg-slate-100 text-slate-500'"
                  >
                    {{ getCategoryLabel(log.category) }}
                  </span>
                </div>
                
                <!-- Time (right-aligned) -->
                <div class="flex items-center gap-1.5 text-[11px] flex-shrink-0" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                  <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  {{ formatRelativeTime(log.created_at) }}
                </div>
              </div>

              <!-- Description -->
              <p class="text-sm leading-relaxed" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">
                {{ log.description }}
              </p>

              <!-- Meta row -->
              <div class="flex items-center gap-3 mt-2 text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md"
                  :class="isDark() ? 'bg-slate-700/40' : 'bg-slate-100'">
                  <User class="w-3 h-3" />
                  {{ log.username || 'Sistema' }}
                </span>
                <span>{{ formatDate(log.created_at) }}</span>
                <span v-if="log.ip_address" class="font-mono opacity-70">{{ log.ip_address }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="text-center py-16 rounded-2xl border"
      :class="isDark() ? 'bg-slate-800/20 border-slate-700/30' : 'bg-slate-50 border-slate-200'"
    >
      <div class="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center"
        :class="isDark() ? 'bg-slate-700/30' : 'bg-slate-100'">
        <ScrollText class="w-8 h-8" :class="isDark() ? 'text-slate-500' : 'text-slate-400'" />
      </div>
      <p class="text-lg font-medium" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">No hay registros de auditoría</p>
      <p class="text-sm mt-1" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Las acciones de los usuarios aparecerán aquí</p>
    </div>

    <!-- Pagination - Enhanced -->
    <div v-if="totalPages > 1" class="flex items-center justify-between pt-4">
      <p class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
        <span class="font-semibold">{{ skip + 1 }}-{{ Math.min(skip + limit, total) }}</span> de {{ total }}
      </p>
      <div class="flex items-center gap-1">
        <button
          @click="prevPage"
          :disabled="page <= 1"
          :class="getPaginationButtonClass(page <= 1)"
        >
          <ChevronLeft class="w-4 h-4" />
        </button>
        <div class="flex items-center gap-0.5">
          <button v-for="p in Math.min(totalPages, 5)" :key="p"
            @click="page = p; fetchLogs()"
            class="w-8 h-8 rounded-lg text-xs font-semibold transition-all duration-200"
            :class="page === p
              ? (isDark() ? 'bg-cyan-500/20 text-cyan-400 ring-1 ring-cyan-500/30' : 'bg-cyan-100 text-cyan-700 ring-1 ring-cyan-300')
              : (isDark() ? 'text-slate-400 hover:bg-slate-700' : 'text-slate-600 hover:bg-slate-100')">
            {{ p }}
          </button>
          <span v-if="totalPages > 5" class="px-1 text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">...</span>
        </div>
        <button
          @click="nextPage"
          :disabled="page >= totalPages"
          :class="getPaginationButtonClass(page >= totalPages)"
        >
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>
