<script setup>
import { ref, onMounted, computed } from 'vue'
import { scannerAPI } from '../api/scanner'
import { useToast } from '../composables/useToast'
import { useGlobalWebSocket } from '../composables/useWebSocket'
import ExcelJS from 'exceljs'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import {
  RotateCcw,
  Eye,
  Trash2,
  Apple,
  Monitor,
  Globe,
  Network,
  GitBranch,
  Search,
  Power,
  Wifi,
  Server,
  Tag,
  Activity,
  Clock,
  Settings,
  X,
  Info,
  Shield,
  Users,
  WifiOff,
  HelpCircle,
  ArrowUp,
  ArrowDown,
  ChevronsUpDown,
} from 'lucide-vue-next'
import SkeletonLoader from './SkeletonLoader.vue'
import { useTheme } from '../composables/useTheme'

const toast = useToast()
const ws = useGlobalWebSocket()
const { isDark } = useTheme()

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

const tableRef = ref(null)

onMounted(() => {
  loadHosts()
  loadStatistics()
  
  
  ws.on('host_update', (data) => {
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
  
  ws.on('scan_progress', (data) => {
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
})

const loadHosts = async () => {
  loading.value = true
  error.value = ''
  try {
    const data = await scannerAPI.getAllHosts()
    hosts.value = Array.isArray(data) ? data : []
    toast.success(`${hosts.value.length} hosts cargados exitosamente`)
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

const applyDateFilter = () => {
  filterType.value = 'date'
}

const clearDateFilter = () => {
  filterStartDate.value = ''
  filterEndDate.value = ''
  filterType.value = 'all'
}

const toggleSort = (field) => {
  console.log('toggleSort llamado con campo:', field)
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
  console.log('Nuevo sortField:', sortField.value, 'sortDirection:', sortDirection.value)
}

const applyFilter = async () => {
  loading.value = true
  error.value = ''
  try {
    if (filterType.value === 'range') {
      hosts.value = await scannerAPI.filterByRange(filterStartIp.value, filterEndIp.value)
    } else if (filterType.value === 'subnet') {
      hosts.value = await scannerAPI.filterSubnet(filterSubnet.value)
    } else {
      hosts.value = await scannerAPI.getAllHosts()
    }
  } catch (err) {
    error.value = 'Error applying filter'
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
  try {
    hosts.value = await scannerAPI.searchHosts(searchQuery.value)
  } catch (err) {
    error.value = 'Error searching hosts'
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
    error.value = 'Error exporting to CSV'
    toast.error('Error exportando a CSV')
  }
}

const exportToExcel = async () => {
  const hostsToExport = selectedHosts.value.length > 0 ? selectedHosts.value : filteredHosts.value
  
  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet('Network Scan')

  worksheet.columns = [
    { header: 'IP', key: 'ip', width: 15 },
    { header: 'Hostname', key: 'hostname', width: 20 },
    { header: 'MAC', key: 'mac', width: 18 },
    { header: 'Vendor', key: 'vendor', width: 20 },
    { header: 'OS', key: 'os', width: 15 },
    { header: 'Status', key: 'status', width: 10 },
    { header: 'Latency (ms)', key: 'latency', width: 12 },
    { header: 'Last Seen', key: 'lastSeen', width: 20 },
    { header: 'Ports', key: 'ports', width: 30 },
    { header: 'Services', key: 'services', width: 30 },
  ]

  hostsToExport.forEach((host) => {
    worksheet.addRow({
      ip: host.ip,
      hostname: host.hostname || 'N/A',
      mac: host.mac || 'N/A',
      vendor: host.vendor || 'N/A',
      os: host.os_name || 'N/A',
      status: host.status,
      latency: host.latency_ms || 'N/A',
      lastSeen: host.last_seen ? new Date(host.last_seen).toLocaleString() : 'N/A',
      ports: host.ports.map((p) => `${p.port}/${p.protocol}`).join(', '),
      services: host.services.map((s) => s.service).join(', '),
    })
  })

  worksheet.getRow(1).font = { bold: true }
  worksheet.getRow(1).fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FF4CAF50' },
  }

  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `network_scan_${Date.now()}.xlsx`
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
  toast.success('Exportado a Excel exitosamente')
}

const exportToPDF = async () => {
  const hostsToExport = selectedHosts.value.length > 0 ? selectedHosts.value : filteredHosts.value
  
  const pdf = new jsPDF('l', 'mm', 'a4')
  
  pdf.setFontSize(20)
  pdf.setTextColor(34, 211, 238) 
  pdf.setFont(undefined, 'bold')
  pdf.text('Network Scan Report', 14, 15)
  
  pdf.setDrawColor(34, 211, 238)
  pdf.setLineWidth(0.5)
  pdf.line(14, 18, 280, 18)
  
  pdf.setFontSize(10)
  pdf.setTextColor(100)
  pdf.setFont(undefined, 'normal')
  pdf.text(`Fecha: ${new Date().toLocaleDateString()}`, 14, 25)
  pdf.text(`Hora: ${new Date().toLocaleTimeString()}`, 14, 30)
  pdf.text(`Total de Hosts: ${hostsToExport.length}`, 100, 25)
  pdf.text(`Hosts Activos: ${hostsToExport.filter(h => h.status === 'up').length}`, 100, 30)
  
  const tableData = hostsToExport.map(host => [
    host.ip,
    host.hostname || 'N/A',
    host.mac || 'N/A',
    host.vendor || 'N/A',
    host.os_name || 'N/A',
    host.status.toUpperCase(),
    (host.ports?.length || 0).toString(),
    host.last_seen ? new Date(host.last_seen).toLocaleDateString() : 'N/A'
  ])
  
  autoTable(pdf, {
    startY: 38,
    head: [['IP Address', 'Hostname', 'MAC Address', 'Vendor', 'OS', 'Status', 'Ports', 'Last Seen']],
    body: tableData,
    theme: 'striped',
    headStyles: {
      fillColor: [34, 211, 238], 
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      fontSize: 10,
      halign: 'center',
      cellPadding: 4
    },
    bodyStyles: {
      fontSize: 9,
      cellPadding: 3,
      textColor: [50, 50, 50]
    },
    alternateRowStyles: {
      fillColor: [245, 250, 252]
    },
    columnStyles: {
      0: { cellWidth: 30, fontStyle: 'bold', textColor: [34, 211, 238] }, // IP
      1: { cellWidth: 35 }, 
      2: { cellWidth: 35, font: 'courier' }, 
      3: { cellWidth: 35 }, 
      4: { cellWidth: 30 }, 
      5: { 
        cellWidth: 20,
        halign: 'center',
        fontStyle: 'bold'
      },
      6: { cellWidth: 18, halign: 'center' }, 
      7: { cellWidth: 28 } 
    },
    didParseCell: function(data) {
      if (data.column.index === 5 && data.section === 'body') {
        if (data.cell.raw === 'UP') {
          data.cell.styles.textColor = [34, 197, 94] 
          data.cell.styles.fillColor = [220, 252, 231]
        } else {
          data.cell.styles.textColor = [239, 68, 68] 
          data.cell.styles.fillColor = [254, 226, 226]
        }
      }
    },
    margin: { top: 38, left: 14, right: 14 },
    didDrawPage: function(data) {
      const pageCount = pdf.internal.getNumberOfPages()
      const pageSize = pdf.internal.pageSize
      const pageHeight = pageSize.height || pageSize.getHeight()
      
      pdf.setFontSize(8)
      pdf.setTextColor(150)
      pdf.text(
        `Página ${data.pageNumber} de ${pageCount}`,
        pageSize.width / 2,
        pageHeight - 10,
        { align: 'center' }
      )
      
      pdf.text(
        `Generado con Network Scanner`,
        14,
        pageHeight - 10
      )
    }
  })
  
  pdf.save(`network_scan_${Date.now()}.pdf`)
  toast.success('Exportado a PDF exitosamente')
}

const exportToPNG = async () => {
  const hostsToExport = selectedHosts.value.length > 0 ? selectedHosts.value : filteredHosts.value
  
  const container = document.createElement('div')
  container.style.position = 'absolute'
  container.style.left = '-9999px'
  container.style.width = '1200px'
  container.style.padding = '40px'
  container.style.backgroundColor = '#0f172a'
  container.style.fontFamily = 'Arial, sans-serif'
  
  const header = document.createElement('div')
  header.style.marginBottom = '30px'
  header.innerHTML = `
    <h1 style="color: #67e8f9; font-size: 32px; margin: 0 0 10px 0;">Network Scanner Report</h1>
    <p style="color: #94a3b8; font-size: 14px; margin: 0;">Generated: ${new Date().toLocaleString()}</p>
    <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0 0;">Total Hosts: ${hostsToExport.length}</p>
  `
  container.appendChild(header)
  
  const table = document.createElement('table')
  table.style.width = '100%'
  table.style.borderCollapse = 'collapse'
  table.style.fontSize = '12px'
  
  const thead = document.createElement('thead')
  thead.innerHTML = `
    <tr style="background: #1e293b;">
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">IP Address</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">Hostname</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">MAC</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">Vendor</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">OS</th>
      <th style="padding: 12px; text-align: center; color: #67e8f9; border: 1px solid #475569;">Status</th>
      <th style="padding: 12px; text-align: center; color: #67e8f9; border: 1px solid #475569;">Ports</th>
      <th style="padding: 12px; text-align: left; color: #67e8f9; border: 1px solid #475569;">Last Seen</th>
    </tr>
  `
  table.appendChild(thead)
  
  const tbody = document.createElement('tbody')
  hostsToExport.forEach((host, index) => {
    const row = document.createElement('tr')
    row.style.background = index % 2 === 0 ? '#0f172a' : '#1e293b'
    
    const statusColor = host.status === 'up' ? '#22c55e' : '#ef4444'
    const statusText = host.status.toUpperCase()
    
    row.innerHTML = `
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.ip}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.hostname || 'N/A'}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.mac || 'N/A'}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.vendor || 'N/A'}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${host.os_name || 'N/A'}</td>
      <td style="padding: 10px; text-align: center; border: 1px solid #475569;">
        <span style="display: inline-block; padding: 4px 12px; background: ${statusColor}; color: white; border-radius: 4px; font-weight: bold;">${statusText}</span>
      </td>
      <td style="padding: 10px; color: #e2e8f0; text-align: center; border: 1px solid #475569;">${host.ports?.length || 0}</td>
      <td style="padding: 10px; color: #e2e8f0; border: 1px solid #475569;">${new Date(host.last_seen).toLocaleString()}</td>
    `
    tbody.appendChild(row)
  })
  table.appendChild(tbody)
  container.appendChild(table)
  
  const footer = document.createElement('div')
  footer.style.marginTop = '30px'
  footer.style.textAlign = 'center'
  footer.innerHTML = `<p style="color: #94a3b8; font-size: 12px; margin: 0;">Network Scanner Dashboard - Professional Report</p>`
  container.appendChild(footer)
  
  document.body.appendChild(container)
  
  try {
    const canvas = await html2canvas(container, {
      scale: 2,
      backgroundColor: '#0f172a',
      logging: false,
      width: 1200,
      windowWidth: 1200
    })
    
    canvas.toBlob((blob) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `network_scan_${Date.now()}.png`
      a.click()
      URL.revokeObjectURL(url)
      document.body.removeChild(container)
      toast.success('Exportado a PNG exitosamente')
    })
  } catch (err) {
    document.body.removeChild(container)
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
    error.value = 'Please provide SSH credentials'
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
      sshTestResult.value = { success: false, message: 'No host to test' }
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
    error.value = 'Please provide SSH credentials'
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
    error.value = err.response?.data?.detail || 'Error sending shutdown commands'
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
        let successful = 0
        let failed = 0
        
        for (const host of selectedHosts.value) {
          try {
            await scannerAPI.deleteHost(host.ip)
            successful++
          } catch (err) {
            failed++
          }
        }
        
        selectedHosts.value = []
        await loadHosts()
        await loadStatistics()
        
        if (failed === 0) {
          showResultModal.value = true
          resultModalData.value = {
            title: 'Eliminación Exitosa',
            message: `Se eliminaron exitosamente ${successful} host(s).`,
            type: 'success'
          }
        } else {
          showResultModal.value = true
          resultModalData.value = {
            title: 'Eliminación Completada',
            message: `Eliminados: ${successful}\nFallidos: ${failed}\n\nAlgunos hosts no pudieron ser eliminados.`,
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
const baseBtn =
  'relative flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold tracking-wide transition-all duration-300'

const activeBtn = 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/40 ring-1 ring-cyan-400/50'

const inactiveBtn = 'bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-white'

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

    <SkeletonLoader v-if="loading && hosts.length === 0" type="stats" class="mb-6" />

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
        <p class="text-5xl font-extrabold text-slate-200">{{ statistics.unknown }}</p>
        <div class="mt-3 h-1 bg-slate-700/50 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-slate-500 to-slate-600 rounded-full transition-all duration-500" :style="`width: ${statistics.total > 0 ? (statistics.unknown / statistics.total * 100) : 0}%`"></div>
        </div>
      </div>
    </div>

    <div 
      class="border rounded-3xl p-8 mb-6 shadow-2xl"
      :class="isDark() 
        ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50' 
        : 'bg-gradient-to-br from-white via-slate-50 to-white border-slate-200'"
    >
      <div class="flex items-center gap-3 mb-6">
        <div 
          class="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg"
          :class="isDark() ? 'bg-gradient-to-br from-cyan-500 to-blue-600 shadow-cyan-500/30' : 'bg-gradient-to-br from-cyan-400 to-blue-500 shadow-cyan-400/30'"
        >
          <Search class="w-5 h-5 text-white" />
        </div>
        <h3 
          class="text-2xl font-bold"
          :class="isDark() ? 'text-white' : 'text-slate-800'"
        >Filtros y Búsqueda</h3>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <button
          @click="setFilter('all'); loadHosts()"
          :class="[
            'group relative px-4 py-3 rounded-xl font-semibold transition-all duration-300 overflow-hidden',
            filterType === 'all'
              ? isDark() 
                ? 'bg-slate-700 border-2 border-slate-500 text-white shadow-lg'
                : 'bg-cyan-100 border-2 border-cyan-400 text-cyan-700 shadow-md'
              : isDark()
                ? 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50'
                : 'bg-white border border-slate-300 text-slate-600 hover:border-cyan-300 hover:bg-slate-50'
          ]"
        >
          <div class="relative z-10 flex items-center justify-center gap-2">
            <Globe class="w-5 h-5" />
            <span>Todos</span>
          </div>
        </button>

        <button
          @click="setFilter('range')"
          :class="[
            'group relative px-4 py-3 rounded-xl font-semibold transition-all duration-300 overflow-hidden',
            filterType === 'range'
              ? isDark() 
                ? 'bg-slate-700 border-2 border-slate-500 text-white shadow-lg'
                : 'bg-cyan-100 border-2 border-cyan-400 text-cyan-700 shadow-md'
              : isDark()
                ? 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50'
                : 'bg-white border border-slate-300 text-slate-600 hover:border-cyan-300 hover:bg-slate-50'
          ]"
        >
          <div class="relative z-10 flex items-center justify-center gap-2">
            <Network class="w-5 h-5" />
            <span>Rango IP</span>
          </div>
        </button>

        <button
          @click="setFilter('subnet')"
          :class="[
            'group relative px-4 py-3 rounded-xl font-semibold transition-all duration-300 overflow-hidden',
            filterType === 'subnet'
              ? isDark() 
                ? 'bg-slate-700 border-2 border-slate-500 text-white shadow-lg'
                : 'bg-cyan-100 border-2 border-cyan-400 text-cyan-700 shadow-md'
              : isDark()
                ? 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50'
                : 'bg-white border border-slate-300 text-slate-600 hover:border-cyan-300 hover:bg-slate-50'
          ]"
        >
          <div class="relative z-10 flex items-center justify-center gap-2">
            <GitBranch class="w-5 h-5" />
            <span>Subred</span>
          </div>
        </button>

        <button
          @click="setFilter('search')"
          :class="[
            'group relative px-4 py-3 rounded-xl font-semibold transition-all duration-300 overflow-hidden',
            filterType === 'search'
              ? isDark() 
                ? 'bg-slate-700 border-2 border-slate-500 text-white shadow-lg'
                : 'bg-cyan-100 border-2 border-cyan-400 text-cyan-700 shadow-md'
              : isDark()
                ? 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50'
                : 'bg-white border border-slate-300 text-slate-600 hover:border-cyan-300 hover:bg-slate-50'
          ]"
        >
          <div class="relative z-10 flex items-center justify-center gap-2">
            <Search class="w-5 h-5" />
            <span>Buscar</span>
          </div>
        </button>

        <button
          @click="setFilter('date')"
          :class="[
            'group relative px-4 py-3 rounded-xl font-semibold transition-all duration-300 overflow-hidden',
            filterType === 'date'
              ? isDark() 
                ? 'bg-slate-700 border-2 border-slate-500 text-white shadow-lg'
                : 'bg-cyan-100 border-2 border-cyan-400 text-cyan-700 shadow-md'
              : isDark()
                ? 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50'
                : 'bg-white border border-slate-300 text-slate-600 hover:border-cyan-300 hover:bg-slate-50'
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
              <label 
                class="text-xs font-semibold mb-2 block uppercase"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
              >IP Inicial</label>
              <input
                v-model="filterStartIp"
                class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                :class="isDark() 
                  ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                  : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
                placeholder="192.168.0.1"
              />
            </div>
            <div>
              <label 
                class="text-xs font-semibold mb-2 block uppercase"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
              >IP Final</label>
              <input
                v-model="filterEndIp"
                class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                :class="isDark() 
                  ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                  : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
                placeholder="192.168.0.254"
              />
            </div>
            <div class="flex items-end">
              <button
                @click="applyFilter"
                class="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-xl px-6 py-3 font-bold shadow-lg shadow-cyan-500/30 hover:shadow-xl hover:shadow-cyan-500/40 transition-all duration-300"
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
              <label 
                class="text-xs font-semibold mb-2 block uppercase"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
              >Subred CIDR</label>
              <input
                v-model="filterSubnet"
                class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                :class="isDark() 
                  ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                  : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
                placeholder="192.168.0.0/24"
              />
            </div>
            <div class="flex items-end">
              <button
                @click="applyFilter"
                class="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-xl px-6 py-3 font-bold shadow-lg shadow-cyan-500/30 hover:shadow-xl hover:shadow-cyan-500/40 transition-all duration-300"
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
              <label 
                class="text-xs font-semibold mb-2 block uppercase"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
              >Término de Búsqueda</label>
              <input
                v-model="searchQuery"
                @keyup.enter="searchHosts"
                class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                :class="isDark() 
                  ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                  : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
                placeholder="IP, Hostname o Vendor..."
              />
            </div>
            <div class="flex items-end">
              <button
                @click="searchHosts"
                class="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-xl px-6 py-3 font-bold shadow-lg shadow-cyan-500/30 hover:shadow-xl hover:shadow-cyan-500/40 transition-all duration-300 flex items-center justify-center gap-2"
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
              <label 
                class="text-xs font-semibold mb-2 block uppercase"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
              >Desde</label>
              <input
                v-model="filterStartDate"
                type="date"
                class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                :class="isDark() 
                  ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                  : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
              />
            </div>
            <div>
              <label 
                class="text-xs font-semibold mb-2 block uppercase"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
              >Hasta</label>
              <input
                v-model="filterEndDate"
                type="date"
                class="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                :class="isDark() 
                  ? 'bg-slate-900/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                  : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
              />
            </div>
            <div class="flex items-end gap-2">
              <button
                @click="applyDateFilter"
                class="flex-1 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-xl px-6 py-3 font-bold shadow-lg shadow-cyan-500/30 hover:shadow-xl hover:shadow-cyan-500/40 transition-all duration-300"
              >
                Filtrar
              </button>
              <button
                @click="clearDateFilter"
                class="px-4 py-3 rounded-xl font-semibold transition-all duration-300"
                :class="isDark() 
                  ? 'bg-slate-700 hover:bg-slate-600 text-white'
                  : 'bg-slate-200 hover:bg-slate-300 text-slate-700'"
              >
                Limpiar
              </button>
            </div>
          </div>
          <p 
            class="text-xs mt-3 flex items-center gap-2"
            :class="isDark() ? 'text-slate-500' : 'text-slate-400'"
          >
            <Clock class="w-3 h-3" />
            Filtra hosts por fecha de última conexión
          </p>
        </div>
      </Transition>
    </div>

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
        v-if="selectedHosts.length > 0"
        @click="openSSHModal('selected')"
        class="group relative overflow-hidden flex items-center justify-center gap-2 px-6 py-3 text-sm font-bold rounded-xl bg-gradient-to-r from-red-600 via-rose-600 to-red-600 hover:from-red-500 hover:via-rose-500 hover:to-red-500 text-white shadow-lg shadow-red-600/40 hover:shadow-red-500/50 transition-all duration-300 transform hover:scale-105 active:scale-95"
      >
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
        <Power class="w-4 h-4 relative z-10" />
        <span class="relative z-10">Shutdown Selected ({{ selectedHosts.length }})</span>
      </button>

      <button
        v-if="selectedHosts.length > 0"
        @click="deleteSelectedHosts"
        class="flex items-center justify-center gap-2 px-5 py-2 text-sm font-bold rounded-lg bg-rose-700 hover:bg-rose-800 text-white shadow-lg shadow-rose-600/50 transition-all duration-300 transform hover:scale-105 active:scale-95"
      >
        <Trash2 class="w-4 h-4" />
        Borrar Seleccionados ({{ selectedHosts.length }})
      </button>

      <button
        v-if="filterType === 'range'"
        @click="openSSHModal('range')"
        class="group relative overflow-hidden flex items-center justify-center gap-2 px-6 py-3 text-sm font-bold rounded-xl bg-gradient-to-r from-orange-600 via-amber-600 to-orange-600 hover:from-orange-500 hover:via-amber-500 hover:to-orange-500 text-white shadow-lg shadow-orange-600/40 hover:shadow-orange-500/50 transition-all duration-300 transform hover:scale-105 active:scale-95"
      >
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
        <Power class="w-4 h-4 relative z-10" />
        <span class="relative z-10">Shutdown Range</span>
      </button>
    </div>

    <div v-if="error" class="mb-4 p-4 bg-red-900/50 border border-red-700 rounded text-red-300">
      {{ error }}
    </div>

    <div 
      ref="tableRef" 
      class="overflow-x-auto rounded-2xl shadow-2xl border"
      :class="isDark() 
        ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50'
        : 'bg-gradient-to-br from-white via-slate-50 to-white border-slate-200'"
    >
      <table class="min-w-full divide-y" :class="isDark() ? 'divide-slate-700/50' : 'divide-slate-200'">
        <thead 
          class="backdrop-blur-sm"
          :class="isDark() 
            ? 'bg-gradient-to-r from-slate-800/80 via-slate-900/80 to-slate-800/80'
            : 'bg-gradient-to-r from-slate-100 via-slate-50 to-slate-100'"
        >
          <tr>
            <th class="px-4 py-4">
              <div class="flex items-center justify-center">
                <input
                  type="checkbox"
                  @change="selectAll"
                  :checked="selectedHosts.length === hosts.length && hosts.length > 0"
                  class="w-5 h-5 appearance-none border-2 rounded-md transition-all duration-200 cursor-pointer relative
                  before:content-['✓'] before:absolute before:inset-0 before:flex before:items-center before:justify-center before:text-white before:text-sm before:font-bold before:opacity-0 checked:before:opacity-100 before:transition-opacity"
                  :class="isDark()
                    ? 'bg-slate-700 border-slate-500 checked:bg-gradient-to-br checked:from-cyan-500 checked:to-blue-600 checked:border-cyan-400 hover:border-cyan-400'
                    : 'bg-white border-slate-300 checked:bg-gradient-to-br checked:from-cyan-400 checked:to-blue-500 checked:border-cyan-400 hover:border-cyan-400'"
                />
              </div>
            </th>
            <th class="px-6 py-4 text-left">
              <button 
                type="button"
                @click.stop="toggleSort('ip')"
                class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer"
              >
                <Wifi 
                  class="w-4 h-4"
                  :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
                />
                <span 
                  class="text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-200' : 'text-slate-700'"
                >IP</span>
                <ArrowUp v-if="sortField === 'ip' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
                <ArrowDown v-else-if="sortField === 'ip' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
                <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
              </button>
            </th>
            <th class="px-6 py-4 text-left">
              <button 
                type="button"
                @click.stop="toggleSort('hostname')"
                class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer"
              >
                <Globe 
                  class="w-4 h-4"
                  :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
                />
                <span 
                  class="text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-200' : 'text-slate-700'"
                >Hostname</span>
                <ArrowUp v-if="sortField === 'hostname' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
                <ArrowDown v-else-if="sortField === 'hostname' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
                <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
              </button>
            </th>
            <th class="px-6 py-4 text-left">
              <button 
                type="button"
                @click.stop="toggleSort('mac')"
                class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer"
              >
                <Network 
                  class="w-4 h-4"
                  :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
                />
                <span 
                  class="text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-200' : 'text-slate-700'"
                >MAC</span>
                <ArrowUp v-if="sortField === 'mac' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
                <ArrowDown v-else-if="sortField === 'mac' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
                <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
              </button>
            </th>
            <th class="px-6 py-4 text-left">
              <button 
                type="button"
                @click.stop="toggleSort('vendor')"
                class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer"
              >
                <Tag 
                  class="w-4 h-4"
                  :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
                />
                <span 
                  class="text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-200' : 'text-slate-700'"
                >Vendor</span>
                <ArrowUp v-if="sortField === 'vendor' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
                <ArrowDown v-else-if="sortField === 'vendor' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
                <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
              </button>
            </th>
            <th class="px-6 py-4 text-left">
              <button 
                type="button"
                @click.stop="toggleSort('os_name')"
                class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer"
              >
                <Monitor 
                  class="w-4 h-4"
                  :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
                />
                <span 
                  class="text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-200' : 'text-slate-700'"
                >Sistema Operativo</span>
                <ArrowUp v-if="sortField === 'os_name' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
                <ArrowDown v-else-if="sortField === 'os_name' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
                <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
              </button>
            </th>
            <th class="px-6 py-4 text-left">
              <button 
                type="button"
                @click.stop="toggleSort('status')"
                class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer"
              >
                <Activity 
                  class="w-4 h-4"
                  :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
                />
                <span 
                  class="text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-200' : 'text-slate-700'"
                >Estado</span>
                <ArrowUp v-if="sortField === 'status' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
                <ArrowDown v-else-if="sortField === 'status' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
                <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
              </button>
            </th>
            <th class="px-6 py-4 text-left">
              <div class="flex items-center gap-2">
                <Server 
                  class="w-4 h-4"
                  :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
                />
                <span 
                  class="text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-200' : 'text-slate-700'"
                >Puertos</span>
              </div>
            </th>
            <th class="px-6 py-4 text-left">
              <button 
                type="button"
                @click.stop="toggleSort('last_seen')"
                class="flex items-center gap-2 hover:opacity-80 transition-opacity group cursor-pointer"
              >
                <Clock 
                  class="w-4 h-4"
                  :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
                />
                <span 
                  class="text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-200' : 'text-slate-700'"
                >Última Conexión</span>
                <ArrowUp v-if="sortField === 'last_seen' && sortDirection === 'asc'" class="w-3 h-3 text-cyan-400" />
                <ArrowDown v-else-if="sortField === 'last_seen' && sortDirection === 'desc'" class="w-3 h-3 text-cyan-400" />
                <ChevronsUpDown v-else class="w-3 h-3 opacity-30 group-hover:opacity-60" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
              </button>
            </th>
            <th class="px-6 py-4 text-left">
              <div class="flex items-center gap-2">
                <Settings 
                  class="w-4 h-4"
                  :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
                />
                <span 
                  class="text-xs font-bold uppercase tracking-wider"
                  :class="isDark() ? 'text-slate-200' : 'text-slate-700'"
                >Acciones</span>
              </div>
            </th>
          </tr>
        </thead>

        <tbody 
          class="divide-y"
          :class="isDark() 
            ? 'divide-slate-700/30 bg-slate-900/50'
            : 'divide-slate-200 bg-white'"
        >
          <tr v-if="loading && hosts.length === 0">
            <td colspan="10" class="px-6 py-8">
              <SkeletonLoader type="table" :rows="5" :columns="9" />
            </td>
          </tr>
          
          <tr v-else-if="hosts.length === 0">
            <td colspan="10" class="px-6 py-8 text-center">
              <div class="flex flex-col items-center gap-2">
                <Search class="w-12 h-12 text-slate-600" />
                <span class="text-slate-400 font-medium">No se encontraron hosts</span>
              </div>
            </td>
          </tr>
          
          <tr
            v-for="host in filteredHosts"
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
                  @change="toggleSelection(host)"
                  class="w-5 h-5 appearance-none bg-slate-700 border-2 border-slate-500 rounded-md checked:bg-gradient-to-br checked:from-cyan-500 checked:to-blue-600 checked:border-cyan-400 hover:border-cyan-400 transition-all duration-200 cursor-pointer relative
                  before:content-['✓'] before:absolute before:inset-0 before:flex before:items-center before:justify-center before:text-white before:text-sm before:font-bold before:opacity-0 checked:before:opacity-100 before:transition-opacity"
                />
              </div>
            </td>

            <td class="px-6 py-4 text-sm font-mono font-semibold text-cyan-300">{{ host.ip }}</td>
            <td class="px-6 py-4 text-sm text-slate-300">{{ host.hostname || 'N/A' }}</td>
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
            <td class="px-6 py-4 text-sm text-slate-400">
              {{ formatLocal(host.last_seen) || 'N/A' }}
            </td>
            <td class="px-6 py-4 text-sm">
              <div class="flex gap-2">
                <!-- Ver detalles -->
                <button
                  @click="showDetails(host)"
                  class="flex items-center justify-center w-9 h-9 rounded-lg text-blue-400 hover:text-blue-300 bg-blue-900/20 hover:bg-blue-900/40 border border-blue-700/30 hover:border-blue-600/50 shadow-md shadow-blue-400/10 hover:shadow-blue-400/20 transition-all duration-200 transform hover:scale-110 active:scale-95"
                  title="Ver detalles"
                >
                  <Eye class="w-4 h-4" />
                </button>

                <button
                  @click="deleteHostConfirm(host.ip)"
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
                  <span class="text-2xl">🐧</span>
                  <span class="text-white font-medium">Linux / Unix</span>
                </div>
              </label>
              <label class="relative flex items-center cursor-pointer">
                <input type="radio" v-model="sshOSType" value="windows" class="peer sr-only" />
                <div class="w-full px-4 py-3 bg-slate-800/50 border-2 border-slate-700 peer-checked:border-cyan-500 peer-checked:bg-cyan-500/10 rounded-xl transition-all flex items-center gap-2">
                  <span class="text-2xl">🪟</span>
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
                <Network class="w-4 h-4 text-purple-400" />
                <p class="text-slate-400 text-xs uppercase tracking-wider font-semibold">MAC Address</p>
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
                <span
                  v-if="
                    selectedHost.os_name && selectedHost.os_name.toLowerCase().includes('windows')
                  "
                  class="text-3xl"
                >
                  🪟
                </span>
                <span
                  v-else-if="
                    selectedHost.os_name && selectedHost.os_name.toLowerCase().includes('linux')
                  "
                  class="text-3xl"
                >
                  🐧
                </span>
                <span
                  v-else-if="
                    selectedHost.os_name && selectedHost.os_name.toLowerCase().includes('android')
                  "
                  class="text-3xl"
                >
                  🤖
                </span>
                <span
                  v-else-if="
                    selectedHost.os_name &&
                    (selectedHost.os_name.toLowerCase().includes('ios') ||
                      selectedHost.os_name.toLowerCase().includes('mac'))
                  "
                >
                  <Apple class="w-8 h-8 text-slate-300" />
                </span>
                <Monitor v-else class="w-8 h-8 text-slate-500" />
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
