<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { scannerAPI } from '../api/scanner'
import { useToast } from '../composables/useToast'
import { useGlobalWebSocket } from '../composables/useWebSocket'
import { exportHostsToExcel, exportHostsToPNG, exportHostsToPDF } from '../utils/hostExportUtils'
import {
  RotateCcw,
  Trash2,
  Monitor,
  Globe,
  Network,
  Power,
  Server,
  Tag,
  Activity,
  Settings,
  X,
  Info,
  Shield,
  Pencil,
} from 'lucide-vue-next'
import HostsStatsCards from './HostsStatsCards.vue'
import HostsFiltersPanel from './HostsFiltersPanel.vue'
import HostsDataTable from './HostsDataTable.vue'
import OSIcon from './OSIcon.vue'
import { useTheme } from '../composables/useTheme'
import { usePermissions } from '../composables/usePermissions'
import { useButtonClasses } from '../composables/useButtonClasses'

const toast = useToast()
const ws = useGlobalWebSocket()
const { isDark } = useTheme()
const { canEditResources, canDeleteResources, canUseSSH } = usePermissions()
const { btnDangerClass } = useButtonClasses()

const hosts = ref([])
const loading = ref(false)
const error = ref('')
const selectedHosts = ref([])
const filterStartIp = ref('192.168.0.1')
const filterEndIp = ref('192.168.0.254')
const filterSubnet = ref('192.168.0.0/24')
const searchQuery = ref('')
const statistics = ref(null)
const filterStartDate = ref('')
const filterEndDate = ref('')
const filterType = ref('all') 
const sortField = ref('ip') 
const sortDirection = ref('asc') 

const showSSHModal = ref(false)
const sshUsername = ref('')
const sshPassword = ref('')
const sshSudoPassword = ref('')
const sshTarget = ref(null)
const sshTestResult = ref(null)
const testingSSH = ref(false)
const sshOSType = ref('linux')

const showDetailModal = ref(false)
const selectedHost = ref(null)

const editingNickname = ref(null)
const nicknameInput = ref('')
const savingNickname = ref(false)

// Paginación
const currentPage = ref(1)
const pageSize = ref(50)
const pageSizeOptions = [25, 50, 100, 200]

const showConfirmModal = ref(false)
const confirmModalData = ref({
  title: '',
  message: '',
  confirmText: 'Confirmar',
  cancelText: 'Cancelar',
  type: 'danger', 
  onConfirm: null
})

const showResultModal = ref(false)
const resultModalData = ref({
  title: '',
  message: '',
  type: 'success' 
})

const wsCleanup = []

onMounted(() => {
  loadHosts()
  loadStatistics()
  
  
  const removeHostUpdate = ws.on('host_update', (data) => {
    if (data.action === 'created') {
      const exists = hosts.value.some(h => h.ip === data.host.ip)
      if (!exists) {
        hosts.value.push(data.host)
      }
    } else if (data.action === 'updated') {
      const index = hosts.value.findIndex(h => h.ip === data.host.ip)
      if (index !== -1) {
        hosts.value[index] = data.host
      }
    }
    loadStatistics()
  })
  
  const removeScanProgress = ws.on('scan_progress', (data) => {
    if (data.scan_type !== 'full') return
    
    if (data.result && data.result.status === 'up') {
      const existingIndex = hosts.value.findIndex(h => h.ip === data.result.host)
      if (existingIndex === -1) {
        hosts.value.push({
          id: null,
          ip: data.result.host,
          hostname: data.result.hostname,
          status: data.result.status,
          latency_ms: data.result.latency_ms,
          last_seen: new Date().toISOString(),
          mac: null,
          vendor: null,
          os_name: null,
          os_accuracy: null
        })
      }
    }
    
    if (data.status === 'completed') {
      setTimeout(() => {
        loadHosts()
        if (data.results && Array.isArray(data.results)) {
          const upHosts = data.results.filter(r => r.status === 'up').length
          toast.success(`Escaneo completado: ${upHosts} hosts encontrados`)
        }
      }, 1000)
    }
  })

  // Store removers for cleanup
  wsCleanup.push(removeHostUpdate, removeScanProgress)
})

onUnmounted(() => {
  wsCleanup.forEach(fn => fn && fn())
})

const loadHosts = async () => {
  loading.value = true
  error.value = ''
  try {
    const data = await scannerAPI.getAllHosts(0, 5000)
    hosts.value = Array.isArray(data) ? data : (data.items || [])
    const total = data.total || hosts.value.length
    toast.success(`${total} hosts cargados exitosamente`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error Cargando Host de la base de datos'
    hosts.value = []
    toast.error('Error cargando hosts de la base de datos')
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    statistics.value = await scannerAPI.getStatistics()
  } catch (err) {
  }
}

const filteredHosts = computed(() => {
  let result = hosts.value
  
  if (filterStartDate.value || filterEndDate.value) {
    result = result.filter(host => {
      if (!host.last_seen) return false
      
      const hostDate = new Date(host.last_seen)
      const startDate = filterStartDate.value ? new Date(filterStartDate.value) : null
      const endDate = filterEndDate.value ? new Date(filterEndDate.value + 'T23:59:59') : null
      
      if (startDate && hostDate < startDate) return false
      if (endDate && hostDate > endDate) return false
      
      return true
    })
  }
  
  if (sortField.value) {
    result = [...result].sort((a, b) => {
      let aVal = a[sortField.value]
      let bVal = b[sortField.value]
      
      if (sortField.value === 'ip') {
        const aOctets = aVal.split('.').map(Number)
        const bOctets = bVal.split('.').map(Number)
        for (let i = 0; i < 4; i++) {
          if (aOctets[i] !== bOctets[i]) {
            return sortDirection.value === 'asc' 
              ? aOctets[i] - bOctets[i] 
              : bOctets[i] - aOctets[i]
          }
        }
        return 0
      }
      
      if (aVal === null || aVal === undefined) aVal = ''
      if (bVal === null || bVal === undefined) bVal = ''
      
      if (aVal < bVal) return sortDirection.value === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection.value === 'asc' ? 1 : -1
      return 0
    })
  }
  
  return result
})

const totalFiltered = computed(() => filteredHosts.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalFiltered.value / pageSize.value)))

const paginatedHosts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredHosts.value.slice(start, start + pageSize.value)
})

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const changePageSize = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const pages = []
  const start = Math.max(1, current - 2)
  const end = Math.min(total, current + 2)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

const applyDateFilter = () => {
  filterType.value = 'date'
  currentPage.value = 1
}

const clearDateFilter = () => {
  filterStartDate.value = ''
  filterEndDate.value = ''
  filterType.value = 'all'
  currentPage.value = 1
}

const toggleSort = (field) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
}

const applyFilter = async () => {
  loading.value = true
  error.value = ''
  currentPage.value = 1
  try {
    if (filterType.value === 'range') {
      hosts.value = await scannerAPI.filterByRange(filterStartIp.value, filterEndIp.value)
    } else if (filterType.value === 'subnet') {
      hosts.value = await scannerAPI.filterSubnet(filterSubnet.value)
    } else {
      const data = await scannerAPI.getAllHosts(0, 5000)
      hosts.value = Array.isArray(data) ? data : (data.items || [])
    }
  } catch (err) {
    error.value = 'Error aplicando filtro'
  } finally {
    loading.value = false
  }
}

const searchHosts = async () => {
  if (!searchQuery.value) {
    loadHosts()
    return
  }
  loading.value = true
  currentPage.value = 1
  try {
    hosts.value = await scannerAPI.searchHosts(searchQuery.value)
  } catch (err) {
    error.value = 'Error buscando hosts'
  } finally {
    loading.value = false
  }
}

const toggleSelection = (host) => {
  const index = selectedHosts.value.findIndex((h) => h.ip === host.ip)
  if (index > -1) {
    selectedHosts.value.splice(index, 1)
  } else {
    selectedHosts.value.push(host)
  }
}

const selectAll = () => {
  if (selectedHosts.value.length === hosts.value.length) {
    selectedHosts.value = []
  } else {
    selectedHosts.value = [...hosts.value]
  }
}

const isSelected = (host) => {
  return selectedHosts.value.some((h) => h.ip === host.ip)
}

const startEditNickname = (host) => {
  editingNickname.value = host.ip
  nicknameInput.value = host.nickname || ''
}

const cancelEditNickname = () => {
  editingNickname.value = null
  nicknameInput.value = ''
}

const saveNickname = async (host) => {
  savingNickname.value = true
  try {
    const result = await scannerAPI.updateHostNickname(host.ip, nicknameInput.value.trim())
    const idx = hosts.value.findIndex(h => h.ip === host.ip)
    if (idx !== -1) {
      hosts.value[idx].nickname = nicknameInput.value.trim() || null
    }
    editingNickname.value = null
    nicknameInput.value = ''
    toast.success('Apodo actualizado')
  } catch (err) {
    toast.error('Error al actualizar apodo')
  } finally {
    savingNickname.value = false
  }
}


const exportToCSV = async () => {
  try {
    const blob = await scannerAPI.exportCSV()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `network_scan_${Date.now()}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    toast.success('Exportado a CSV exitosamente')
  } catch (err) {
    error.value = 'Error exportando a CSV'
    toast.error('Error exportando a CSV')
  }
}

const exportToExcel = async () => {
  const hostsToExport = selectedHosts.value.length > 0 ? selectedHosts.value : filteredHosts.value

  try {
    await exportHostsToExcel(hostsToExport)
    toast.success('Exportado a Excel exitosamente')
  } catch (err) {
    toast.error('Error exportando a Excel')
  }
}

const exportToPDF = async () => {
  const hostsToExport = selectedHosts.value.length > 0 ? selectedHosts.value : filteredHosts.value

  try {
    await exportHostsToPDF(hostsToExport)
    toast.success('Exportado a PDF exitosamente')
  } catch (err) {
    toast.error('Error exportando a PDF')
  }
}

const exportToPNG = async () => {
  const hostsToExport = selectedHosts.value.length > 0 ? selectedHosts.value : filteredHosts.value

  try {
    await exportHostsToPNG(hostsToExport)
    toast.success('Exportado a PNG exitosamente')
  } catch (err) {
    toast.error('Error exportando a PNG')
  }
}


const openSSHModal = (target) => {
  sshTarget.value = target
  showSSHModal.value = true
  sshTestResult.value = null
}

const testSSHConnection = async () => {
  if (!sshUsername.value || !sshPassword.value) {
    error.value = 'Por favor proporciona credenciales SSH'
    return
  }

  testingSSH.value = true
  sshTestResult.value = null

  try {
    let testHost = ''
    if (sshTarget.value === 'selected' && selectedHosts.value.length > 0) {
      testHost = selectedHosts.value[0].ip
    } else if (sshTarget.value === 'range') {
      testHost = filterStartIp.value
    }

    if (!testHost) {
      sshTestResult.value = { success: false, message: 'No hay host para probar' }
      return
    }

    const result = await scannerAPI.testSSH(testHost, sshUsername.value, sshPassword.value)
    sshTestResult.value = result
  } catch (err) {
    sshTestResult.value = {
      success: false,
      message: err.response?.data?.detail || 'Connection test failed',
    }
  } finally {
    testingSSH.value = false
  }
}

const shutdownHosts = async () => {
  if (!sshUsername.value || !sshPassword.value) {
    error.value = 'Por favor proporciona credenciales SSH'
    return
  }

  loading.value = true
  const results = []

  try {
    if (sshTarget.value === 'selected') {
      for (const host of selectedHosts.value) {
        const result = await scannerAPI.shutdownHost(
          host.ip,
          sshUsername.value,
          sshPassword.value,
          sshSudoPassword.value,
          sshOSType.value,
        )
        results.push(result)
      }
    } else if (sshTarget.value === 'range') {
      const response = await scannerAPI.shutdownRange(
        filterStartIp.value,
        filterEndIp.value,
        sshUsername.value,
        sshPassword.value,
        sshSudoPassword.value,
        sshOSType.value,
      )
      results.push(...response.results)
    }

    showSSHModal.value = false

    const successful = results.filter((r) => r.success).length
    const failed = results.filter((r) => !r.success).length

    if (failed === 0) {
      showResultModal.value = true
      resultModalData.value = {
        title: 'Operación Exitosa',
        message: `Se enviaron comandos de apagado exitosamente a ${successful} host(s).\n\nLos hosts se marcaron como inactivos en la base de datos.`,
        type: 'success'
      }
    } else {
      showResultModal.value = true
      resultModalData.value = {
        title: 'Operación Completada con Errores',
        message: `Exitosos: ${successful}\nFallidos: ${failed}\n\nLos hosts exitosos se marcaron como inactivos.\n\nRevisa la consola para más detalles.`,
        type: 'warning'
      }
    }

    await loadHosts()
    await loadStatistics()
    selectedHosts.value = []
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error enviando comandos de apagado'
  } finally {
    loading.value = false
  }
}

const showDetails = async (host) => {
  selectedHost.value = host
  showDetailModal.value = true
}

const deleteHostConfirm = async (ip) => {
  confirmModalData.value = {
    title: 'Confirmar Eliminación',
    message: `¿Estás seguro de que deseas eliminar el host ${ip}?\n\nEsta acción no se puede deshacer.`,
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    type: 'danger',
    onConfirm: async () => {
      try {
        await scannerAPI.deleteHost(ip)
        await loadHosts()
        await loadStatistics()
        showResultModal.value = true
        resultModalData.value = {
          title: '✓ Host Eliminado',
          message: `El host ${ip} ha sido eliminado exitosamente.`,
          type: 'success'
        }
      } catch (err) {
        error.value = 'Error eliminando el host'
        showResultModal.value = true
        resultModalData.value = {
          title: '✕ Error',
          message: 'No se pudo eliminar el host. Intenta nuevamente.',
          type: 'error'
        }
      }
    }
  }
  showConfirmModal.value = true
}

const deleteSelectedHosts = async () => {
  if (selectedHosts.value.length === 0) return
  
  const count = selectedHosts.value.length
  confirmModalData.value = {
    title: 'Confirmar Eliminación Múltiple',
    message: `¿Estás seguro de que deseas eliminar ${count} host(s) seleccionado(s)?\n\nEsta acción no se puede deshacer.`,
    confirmText: 'Eliminar Todos',
    cancelText: 'Cancelar',
    type: 'danger',
    onConfirm: async () => {
      loading.value = true
      error.value = ''
      
      try {
        const ips = selectedHosts.value.map(h => h.ip)
        const result = await scannerAPI.deleteHostsBatch(ips)
        
        selectedHosts.value = []
        await loadHosts()
        await loadStatistics()
        
        if (result.failed === 0) {
          showResultModal.value = true
          resultModalData.value = {
            title: 'Eliminación Exitosa',
            message: `Se eliminaron exitosamente ${result.deleted} host(s).`,
            type: 'success'
          }
        } else {
          showResultModal.value = true
          resultModalData.value = {
            title: 'Eliminación Completada',
            message: `Eliminados: ${result.deleted}\nFallidos: ${result.failed}\n\nAlgunos hosts no pudieron ser eliminados.`,
            type: 'warning'
          }
        }
      } catch (err) {
        error.value = 'Error eliminando hosts seleccionados'
        showResultModal.value = true
        resultModalData.value = {
          title: '✕ Error',
          message: 'Ocurrió un error durante la eliminación.',
          type: 'error'
        }
      } finally {
        loading.value = false
      }
    }
  }
  showConfirmModal.value = true
}

const setFilter = (type) => {
  filterType.value = type
  if (type === 'all') {
    loadHosts()
  }
}

const updateFilterStartIp = (value) => {
  filterStartIp.value = value
}

const updateFilterEndIp = (value) => {
  filterEndIp.value = value
}

const updateFilterSubnet = (value) => {
  filterSubnet.value = value
}

const updateSearchQuery = (value) => {
  searchQuery.value = value
}

const updateFilterStartDate = (value) => {
  filterStartDate.value = value
}

const updateFilterEndDate = (value) => {
  filterEndDate.value = value
}

const updateNicknameInput = (value) => {
  nicknameInput.value = value
}

const formatLocal = (iso) => {
  if (!iso) return ''
  try {
    let cleanedIso = iso.split('.')[0]
    if (!cleanedIso.endsWith('Z')) {
      cleanedIso += 'Z'
    }
    return new Date(cleanedIso).toLocaleString('es-MX', {
      timeZone: 'America/Tijuana',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  } catch {
    return iso
  }
}
</script>

<template>
  
  <div>
    <!-- Titulo -->
    <h2 class="text-3xl font-extrabold text-white mb-6 tracking-tight">
      Host <span class="text-cyan-400">Database</span>
    </h2>

    <HostsStatsCards
      :loading="loading"
      :hosts-length="hosts.length"
      :statistics="statistics"
    />

    <HostsFiltersPanel
      :filter-type="filterType"
      :filter-start-ip="filterStartIp"
      :filter-end-ip="filterEndIp"
      :filter-subnet="filterSubnet"
      :search-query="searchQuery"
      :filter-start-date="filterStartDate"
      :filter-end-date="filterEndDate"
      @set-filter="setFilter"
      @reload-all="loadHosts"
      @apply-filter="applyFilter"
      @search-hosts="searchHosts"
      @apply-date-filter="applyDateFilter"
      @clear-date-filter="clearDateFilter"
      @update:filter-start-ip="updateFilterStartIp"
      @update:filter-end-ip="updateFilterEndIp"
      @update:filter-subnet="updateFilterSubnet"
      @update:search-query="updateSearchQuery"
      @update:filter-start-date="updateFilterStartDate"
      @update:filter-end-date="updateFilterEndDate"
    />

    <div class="flex flex-wrap gap-3 mb-6">
      <button
        @click="loadHosts"
        class="group relative px-5 py-3 bg-slate-800/80 hover:bg-slate-700 border border-slate-600 hover:border-slate-500 rounded-xl text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden"
      >
        <div class="relative z-10 flex items-center gap-2">
          <RotateCcw class="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
          <span>Actualizar</span>
        </div>
        <div class="absolute inset-0 bg-gradient-to-r from-slate-600/0 via-slate-500/20 to-slate-600/0 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
      </button>

      <button
        @click="exportToCSV"
        class="group relative px-5 py-3 bg-slate-800/80 hover:bg-slate-700 border border-slate-600 hover:border-blue-500/50 rounded-xl text-white font-semibold shadow-lg hover:shadow-xl hover:shadow-blue-500/20 transition-all duration-300 overflow-hidden"
      >
        <div class="relative z-10 flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>CSV</span>
        </div>
        <div class="absolute inset-0 bg-gradient-to-r from-blue-600/0 via-blue-500/10 to-blue-600/0 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
      </button>

      <button
        @click="exportToExcel"
        class="group relative px-5 py-3 bg-slate-800/80 hover:bg-slate-700 border border-slate-600 hover:border-emerald-500/50 rounded-xl text-white font-semibold shadow-lg hover:shadow-xl hover:shadow-emerald-500/20 transition-all duration-300 overflow-hidden"
      >
        <div class="relative z-10 flex items-center gap-2">
          <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>Excel</span>
        </div>
        <div class="absolute inset-0 bg-gradient-to-r from-emerald-600/0 via-emerald-500/10 to-emerald-600/0 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
      </button>

      <button
        @click="exportToPDF"
        class="group relative px-5 py-3 bg-slate-800/80 hover:bg-slate-700 border border-slate-600 hover:border-red-500/50 rounded-xl text-white font-semibold shadow-lg hover:shadow-xl hover:shadow-red-500/20 transition-all duration-300 overflow-hidden"
      >
        <div class="relative z-10 flex items-center gap-2">
          <svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <span>PDF</span>
        </div>
        <div class="absolute inset-0 bg-gradient-to-r from-red-600/0 via-red-500/10 to-red-600/0 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
      </button>

      <button
        @click="exportToPNG"
        class="group relative px-5 py-3 bg-slate-800/80 hover:bg-slate-700 border border-slate-600 hover:border-purple-500/50 rounded-xl text-white font-semibold shadow-lg hover:shadow-xl hover:shadow-purple-500/20 transition-all duration-300 overflow-hidden"
      >
        <div class="relative z-10 flex items-center gap-2">
          <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>PNG</span>
        </div>
        <div class="absolute inset-0 bg-gradient-to-r from-purple-600/0 via-purple-500/10 to-purple-600/0 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
      </button>

      <button
        v-if="selectedHosts.length > 0 && canUseSSH"
        @click="openSSHModal('selected')"
        :class="btnDangerClass"
      >
        <Power class="w-4 h-4" />
        <span>Apagar Seleccionados ({{ selectedHosts.length }})</span>
      </button>

      <button
        v-if="selectedHosts.length > 0 && canDeleteResources"
        @click="deleteSelectedHosts"
        :class="btnDangerClass"
      >
        <Trash2 class="w-4 h-4" />
        Borrar Seleccionados ({{ selectedHosts.length }})
      </button>

      <button
        v-if="filterType === 'range' && canUseSSH"
        @click="openSSHModal('range')"
        :class="btnDangerClass"
      >
        <Power class="w-4 h-4" />
        <span>Apagar Rango</span>
      </button>
    </div>

    <div v-if="error" class="mb-4 p-4 bg-red-900/50 border border-red-700 rounded text-red-300">
      {{ error }}
    </div>

    <HostsDataTable
      :loading="loading"
      :hosts="hosts"
      :paginated-hosts="paginatedHosts"
      :filtered-hosts-length="filteredHosts.length"
      :total-filtered="totalFiltered"
      :current-page="currentPage"
      :page-size="pageSize"
      :page-size-options="pageSizeOptions"
      :total-pages="totalPages"
      :visible-pages="visiblePages"
      :selected-hosts="selectedHosts"
      :sort-field="sortField"
      :sort-direction="sortDirection"
      :editing-nickname="editingNickname"
      :nickname-input="nicknameInput"
      :saving-nickname="savingNickname"
      :can-edit-resources="canEditResources"
      :can-delete-resources="canDeleteResources"
      :is-selected="isSelected"
      :format-local="formatLocal"
      @select-all="selectAll"
      @toggle-selection="toggleSelection"
      @toggle-sort="toggleSort"
      @start-edit-nickname="startEditNickname"
      @cancel-edit-nickname="cancelEditNickname"
      @save-nickname="saveNickname"
      @show-details="showDetails"
      @delete-host-confirm="deleteHostConfirm"
      @go-to-page="goToPage"
      @change-page-size="changePageSize"
      @update:nickname-input="updateNicknameInput"
    />

    <div
      v-if="showSSHModal"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      @click.self="showSSHModal = false"
    >
      <div class="bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700 rounded-3xl shadow-2xl p-8 max-w-2xl w-full">
        <div class="flex items-center gap-4 mb-6">
          <div class="w-14 h-14 bg-gradient-to-br from-red-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-lg shadow-red-500/30">
            <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div class="flex-1">
            <h3 class="text-2xl font-bold text-white">Credenciales SSH</h3>
            <p class="text-slate-400 text-sm">Apagado remoto de hosts</p>
          </div>
          <button
            @click="showSSHModal = false"
            class="text-slate-400 hover:text-white transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="mb-6 p-4 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-2xl">
          <div class="flex items-start gap-3">
            <svg class="w-6 h-6 text-yellow-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            <div>
              <p class="text-yellow-300 font-semibold mb-1">¡Advertencia! Acción Irreversible</p>
              <p class="text-yellow-200 text-sm">
                Esto apagará los hosts seleccionados inmediatamente.
              </p>
              <p class="text-yellow-200 text-sm mt-2">
                <strong>Objetivo:</strong>
                {{
                  sshTarget === 'selected'
                    ? `${selectedHosts.length} host(s) seleccionado(s)`
                    : `Rango ${filterStartIp} - ${filterEndIp}`
                }}
              </p>
            </div>
          </div>
        </div>

        <div class="space-y-5">
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-3">Sistema Operativo</label>
            <div class="grid grid-cols-2 gap-3">
              <label class="relative flex items-center cursor-pointer">
                <input type="radio" v-model="sshOSType" value="linux" class="peer sr-only" />
                <div class="w-full px-4 py-3 bg-slate-800/50 border-2 border-slate-700 peer-checked:border-cyan-500 peer-checked:bg-cyan-500/10 rounded-xl transition-all flex items-center gap-2">
                  <OSIcon name="linux" :size="28" :stroke-width="1.5" />
                  <span class="text-white font-medium">Linux / Unix</span>
                </div>
              </label>
              <label class="relative flex items-center cursor-pointer">
                <input type="radio" v-model="sshOSType" value="windows" class="peer sr-only" />
                <div class="w-full px-4 py-3 bg-slate-800/50 border-2 border-slate-700 peer-checked:border-cyan-500 peer-checked:bg-cyan-500/10 rounded-xl transition-all flex items-center gap-2">
                  <OSIcon name="windows" :size="28" :stroke-width="1.5" />
                  <span class="text-white font-medium">Windows</span>
                </div>
              </label>
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Usuario SSH</label>
            <input
              v-model="sshUsername"
              type="text"
              placeholder="usuario"
              class="w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 focus:border-cyan-500/50 transition-all"
            />
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Contraseña SSH</label>
            <input
              v-model="sshPassword"
              type="password"
              placeholder="••••••••"
              class="w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 focus:border-cyan-500/50 transition-all"
            />
          </div>
          
          <div v-if="sshOSType === 'linux'">
            <label class="block text-sm font-semibold text-slate-300 mb-2">Contraseña Sudo (Opcional)</label>
            <input
              v-model="sshSudoPassword"
              type="password"
              placeholder="••••••••"
              class="w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 focus:border-cyan-500/50 transition-all"
            />
            <p class="text-xs text-slate-400 mt-2">
              Dejar vacío si el usuario tiene NOPASSWD en sudoers
            </p>
          </div>

          <p v-if="sshOSType === 'windows'" class="text-xs text-slate-400 bg-slate-800/30 rounded-lg p-3 border border-slate-700/50">
            Los usuarios de Windows necesitan privilegios de Administrador para apagar remotamente
          </p>
        </div>

        <button
          @click="testSSHConnection"
          :disabled="testingSSH"
          class="w-full mt-6 px-6 py-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-white rounded-xl font-semibold transition-all duration-200 flex items-center justify-center gap-2"
        >
          <svg v-if="!testingSSH" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>{{ testingSSH ? 'Probando...' : 'Probar Conexión' }}</span>
        </button>

        <div
          v-if="sshTestResult"
          :class="[
            'mt-4 p-4 rounded-xl border text-sm flex items-start gap-3',
            sshTestResult.success
              ? 'bg-emerald-500/10 border-emerald-500/30'
              : 'bg-red-500/10 border-red-500/30',
          ]"
        >
          <svg 
            v-if="sshTestResult.success" 
            class="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <svg 
            v-else
            class="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <p :class="sshTestResult.success ? 'text-emerald-300' : 'text-red-300'">
            {{ sshTestResult.message }}
          </p>
        </div>

        <div class="flex gap-3 mt-6">
          <button
            @click="showSSHModal = false"
            class="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-semibold transition-all duration-200"
          >
            Cancelar
          </button>
          <button
            @click="shutdownHosts"
            :disabled="!sshTestResult?.success"
            class="group relative overflow-hidden flex-1 px-6 py-3 bg-gradient-to-r from-red-600 via-rose-600 to-red-600 hover:from-red-500 hover:via-rose-500 hover:to-red-500 disabled:from-slate-700 disabled:to-slate-800 disabled:cursor-not-allowed text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:shadow-red-500/40 disabled:shadow-none transition-all duration-200 flex items-center justify-center gap-2"
          >
            <div v-if="sshTestResult?.success" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
            <Power class="w-5 h-5 relative z-10" />
            <span class="relative z-10">Apagar Hosts</span>
          </button>
        </div>
      </div>
    </div>

    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="showDetailModal && selectedHost"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 overflow-y-auto p-4"
        @click.self="showDetailModal = false"
      >
        <div
          class="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 rounded-3xl shadow-2xl border border-slate-700/50 p-8 max-w-5xl w-full max-h-[90vh] overflow-y-auto"
        >
          <div class="flex justify-between items-start mb-8">
            <div class="flex items-center gap-4">
              <div class="p-3 bg-cyan-500/10 rounded-2xl border border-cyan-500/30">
                <Info class="w-8 h-8 text-cyan-400" />
              </div>
              <div>
                <h3 class="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                  Detalles del Host
                </h3>
                <p class="text-cyan-400 font-mono text-lg mt-1">{{ selectedHost.ip }}</p>
              </div>
            </div>
            <button
              @click="showDetailModal = false"
              class="p-2 hover:bg-slate-800 rounded-xl transition-all duration-300 group"
              title="Cerrar"
            >
              <X class="w-6 h-6 text-slate-400 group-hover:text-white transition-colors" />
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div class="bg-slate-800/30 rounded-2xl p-5 border border-slate-700/50">
              <div class="flex items-center gap-2 mb-2">
                <Globe class="w-4 h-4 text-cyan-400" />
                <p class="text-slate-400 text-xs uppercase tracking-wider font-semibold">Hostname</p>
              </div>
              <p class="text-white font-medium text-lg">{{ selectedHost.hostname || 'N/A' }}</p>
            </div>

            <div class="bg-slate-800/30 rounded-2xl p-5 border border-slate-700/50">
              <div class="flex items-center gap-2 mb-2">
                <Pencil class="w-4 h-4 text-amber-300" />
                <p class="text-slate-400 text-xs uppercase tracking-wider font-semibold">Apodo</p>
              </div>
              <p class="text-white font-medium text-lg">{{ selectedHost.nickname || 'Sin apodo' }}</p>
            </div>
            
            <div class="bg-slate-800/30 rounded-2xl p-5 border border-slate-700/50">
              <div class="flex items-center gap-2 mb-2">
                <Network class="w-4 h-4 text-purple-400" />
                <p class="text-slate-400 text-xs uppercase tracking-wider font-semibold">Dirección MAC</p>
              </div>
              <p class="text-white font-mono text-lg">{{ selectedHost.mac || 'N/A' }}</p>
            </div>
            
            <div class="bg-slate-800/30 rounded-2xl p-5 border border-slate-700/50">
              <div class="flex items-center gap-2 mb-2">
                <Tag class="w-4 h-4 text-amber-400" />
                <p class="text-slate-400 text-xs uppercase tracking-wider font-semibold">Vendor</p>
              </div>
              <p class="text-white font-medium text-lg">{{ selectedHost.vendor || 'N/A' }}</p>
            </div>
            
            <div class="bg-slate-800/30 rounded-2xl p-5 border border-slate-700/50">
              <div class="flex items-center gap-2 mb-2">
                <Activity class="w-4 h-4 text-green-400" />
                <p class="text-slate-400 text-xs uppercase tracking-wider font-semibold">Estado</p>
              </div>
              <span
                :class="[
                  'inline-flex items-center gap-2 px-4 py-2 text-sm font-bold rounded-xl uppercase tracking-wider border-2 transition-all duration-200',
                  selectedHost.status === 'up'
                    ? 'bg-green-500/20 text-green-400 border-green-500/50 shadow-lg shadow-green-500/20'
                    : 'bg-red-500/20 text-red-400 border-red-500/50 shadow-lg shadow-red-500/20',
                ]"
              >
                <span class="relative flex h-2 w-2">
                  <span
                    :class="[
                      'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                      selectedHost.status === 'up' ? 'bg-green-400' : 'bg-red-400',
                    ]"
                  ></span>
                  <span
                    :class="[
                      'relative inline-flex rounded-full h-2 w-2',
                      selectedHost.status === 'up' ? 'bg-green-500' : 'bg-red-500',
                    ]"
                  ></span>
                </span>
                {{ selectedHost.status }}
              </span>
            </div>
          </div>

          <div class="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/50 mb-8">
            <div class="flex items-center gap-2 mb-4">
              <Monitor class="w-5 h-5 text-blue-400" />
              <h4 class="text-xl font-semibold text-white">Sistema Operativo</h4>
            </div>
            <div class="flex items-center gap-3">
              <div class="p-3 bg-slate-700/50 rounded-xl">
                <OSIcon :name="selectedHost.os_name || ''" :size="32" :stroke-width="1.5" />
              </div>
              
              <div>
                <p class="text-white text-xl font-medium">{{ selectedHost.os_name || 'Desconocido' }}</p>
                <p class="text-slate-400 text-sm">Operating System</p>
              </div>
            </div>
          </div>

          <div v-if="selectedHost.ports?.length > 0" class="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/50 mb-8">
            <div class="flex items-center gap-2 mb-4">
              <Server class="w-5 h-5 text-purple-400" />
              <h4 class="text-xl font-semibold text-white">Puertos Abiertos</h4>
              <span class="ml-auto px-3 py-1 bg-purple-500/20 text-purple-400 border border-purple-500/50 rounded-xl text-sm font-bold">
                {{ selectedHost.ports?.length || 0 }}
              </span>
            </div>
            <div class="bg-slate-900/50 rounded-xl p-4 max-h-64 overflow-y-auto space-y-2">
              <div
                v-for="port in selectedHost.ports"
                :key="port.port"
                class="flex justify-between items-center px-4 py-3 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/30 hover:border-purple-500/30 transition-all duration-200"
              >
                <span class="font-mono text-cyan-400 font-semibold">{{ port.port }}/{{ port.protocol }}</span>
                <span class="text-white font-medium">{{ port.service || 'unknown' }}</span>
              </div>
            </div>
          </div>

          <div v-if="selectedHost.services?.length > 0" class="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/50 mb-8">
            <div class="flex items-center gap-2 mb-4">
              <Settings class="w-5 h-5 text-indigo-400" />
              <h4 class="text-xl font-semibold text-white">Servicios Detectados</h4>
              <span class="ml-auto px-3 py-1 bg-indigo-500/20 text-indigo-400 border border-indigo-500/50 rounded-xl text-sm font-bold">
                {{ selectedHost.services?.length || 0 }}
              </span>
            </div>
            <div class="bg-slate-900/50 rounded-xl p-4 max-h-64 overflow-y-auto space-y-2">
              <div
                v-for="service in selectedHost.services"
                :key="service.port"
                class="flex flex-col gap-2 px-4 py-3 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/30 hover:border-indigo-500/30 transition-all duration-200"
              >
                <div class="flex items-center gap-3">
                  <span class="px-3 py-1 bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 rounded-lg font-mono text-sm font-semibold">
                    {{ service.port }}
                  </span>
                  <span class="text-white font-semibold">{{ service.service }}</span>
                </div>
                <div v-if="service.product" class="flex items-center gap-2 text-sm text-slate-400 ml-1">
                  <Shield class="w-4 h-4" />
                  <span>{{ service.product }} {{ service.version }}</span>
                </div>
              </div>
            </div>
          </div>

          <button
            @click="showDetailModal = false"
            class="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white px-6 py-4 rounded-xl font-bold text-lg shadow-lg shadow-cyan-500/30 hover:shadow-xl hover:shadow-cyan-500/40 transition-all duration-300 flex items-center justify-center gap-2"
          >
            <X class="w-5 h-5" />
            Cerrar
          </button>
        </div>
      </div>
    </Transition>

    <div
      v-if="showConfirmModal"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      @click.self="showConfirmModal = false"
    >
      <div class="bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 p-6 max-w-md w-full transform transition-all">
        <div class="flex items-start gap-4 mb-6">
          <div 
            :class="[
              'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0',
              confirmModalData.type === 'danger' ? 'bg-red-500/20' : 'bg-yellow-500/20'
            ]"
          >
            <svg 
              v-if="confirmModalData.type === 'danger'"
              class="w-6 h-6 text-red-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <svg 
              v-else
              class="w-6 h-6 text-yellow-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div class="flex-1">
            <h3 class="text-xl font-bold text-white mb-2">{{ confirmModalData.title }}</h3>
            <p class="text-gray-300 text-sm whitespace-pre-line leading-relaxed">{{ confirmModalData.message }}</p>
          </div>
        </div>

        <div class="flex gap-3">
          <button
            @click="showConfirmModal = false"
            class="flex-1 px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-semibold transition-colors duration-200"
          >
            {{ confirmModalData.cancelText }}
          </button>
          <button
            @click="() => { confirmModalData.onConfirm?.(); showConfirmModal = false }"
            :class="[
              'flex-1 px-4 py-3 rounded-xl font-semibold transition-all duration-200',
              confirmModalData.type === 'danger' 
                ? 'bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-500/30' 
                : 'bg-yellow-600 hover:bg-yellow-700 text-white shadow-lg shadow-yellow-500/30'
            ]"
          >
            {{ confirmModalData.confirmText }}
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showResultModal"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      @click.self="showResultModal = false"
    >
      <div class="bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 p-6 max-w-md w-full transform transition-all">
        <div class="flex items-start gap-4 mb-6">
          <div 
            :class="[
              'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0',
              resultModalData.type === 'success' ? 'bg-emerald-500/20' : 
              resultModalData.type === 'error' ? 'bg-red-500/20' : 'bg-yellow-500/20'
            ]"
          >
            <svg 
              v-if="resultModalData.type === 'success'"
              class="w-6 h-6 text-emerald-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg 
              v-else-if="resultModalData.type === 'error'"
              class="w-6 h-6 text-red-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <svg 
              v-else
              class="w-6 h-6 text-yellow-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div class="flex-1">
            <h3 class="text-xl font-bold text-white mb-2">{{ resultModalData.title }}</h3>
            <p class="text-gray-300 text-sm whitespace-pre-line leading-relaxed">{{ resultModalData.message }}</p>
          </div>
        </div>

        <button
          @click="showResultModal = false"
          class="w-full px-4 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-xl font-semibold transition-colors duration-200"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>
</template>
<style scoped>
.active-dot {
  position: absolute;
  bottom: -0.5rem;
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 9999px;
  background-color: rgb(34 211 238);
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Animación */
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


* {
  scrollbar-width: none; 
  -ms-overflow-style: none; 
}
*::-webkit-scrollbar {
  display: none; 
}
</style>
