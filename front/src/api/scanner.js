
import axios from 'axios'
import router from '@/router'


const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.origin.replace(':3000', ':8000')

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, 
})


api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})


let isRefreshing = false
let refreshPromise = null

async function refreshToken() {
  if (isRefreshing) return refreshPromise
  isRefreshing = true
  refreshPromise = (async () => {
    try {
      const token = localStorage.getItem('admin_token')
      const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {}, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000
      })
      const { token: newToken, user } = response.data
      localStorage.setItem('admin_token', newToken)
      localStorage.setItem('admin_user', JSON.stringify(user))
      return newToken
    } catch {
      return null
    } finally {
      isRefreshing = false
      refreshPromise = null
    }
  })()
  return refreshPromise
}

// Auto-refresh: renovar token cuando quede menos de 1 hora
function shouldRefreshToken() {
  const token = localStorage.getItem('admin_token')
  if (!token) return false
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000
    const now = Date.now()
    const oneHour = 60 * 60 * 1000
    return (exp - now) < oneHour && (exp - now) > 0
  } catch {
    return false
  }
}


api.interceptors.response.use(
  (response) => {
    if (shouldRefreshToken()) {
      refreshToken().catch(() => {})
    }
    return response
  },
  async (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
      
      // Emitir evento para que App.vue muestre toast
      window.dispatchEvent(new CustomEvent('session-expired'))
      
      router.push({ name: 'login', query: { redirect: window.location.pathname, expired: '1' } })
    }
    return Promise.reject(error)
  }
)

/**
 * Wrapper centralizado de errores para llamadas API.
 * Extrae el mensaje de error del response de forma consistente.
 */
export function extractErrorMessage(error) {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail
    // Pydantic validation errors
    if (Array.isArray(detail)) {
      return detail.map(d => d.msg || d.message || JSON.stringify(d)).join('. ')
    }
    return String(detail)
  }
  if (error.response?.data?.message) {
    return error.response.data.message
  }
  if (error.message === 'Network Error') {
    return 'Error de conexión con el servidor'
  }
  if (error.code === 'ECONNABORTED') {
    return 'La petición tardó demasiado tiempo'
  }
  return error.message || 'Error desconocido'
}

export const scannerAPI = {
  // Ping múltiples hosts
  pingHosts: async (hosts, signal, host_timeout = 2, concurrency = 50) => {
    const response = await api.post('/ping', { hosts, host_timeout, concurrency }, { signal, timeout: 120000 }) // 2 minutos
    return response.data
  },

  // Escanear red completa
  scanNetwork: async (cidr, signal, host_timeout = 2, concurrency = 50) => {
    const response = await api.post('/scan/network', { cidr, host_timeout, concurrency }, { signal, timeout: 300000 }) // 5 minutos
    return response.data
  },

  // Escanear puertos
  scanPorts: async (host, ports = '1-1024', signal) => {
    const response = await api.post('/scan/ports', { host, ports }, { signal })
    return response.data
  },

  scanPortsSegment: async (hosts, ports = '1-1024', signal, host_timeout = 45, concurrency = 50) => {
    const response = await api.post('/scan/ports/segment', { hosts, ports, host_timeout, concurrency }, { signal })
    return response.data
  },

  // Escanear servicios
  scanServices: async (host, ports = '1-1024', signal) => {
    const response = await api.post('/scan/services', { host, ports }, { signal })
    return response.data
  },
  scanServicesSegment: async (hosts, ports = '1-1024', signal, host_timeout = 120, concurrency = 50) => {
    const response = await api.post('/scan/services/segment', { hosts, ports, host_timeout, concurrency }, { signal, timeout: 600000 }) // 10 minutos
    return response.data
  },

  // Escanear vulnerabilidades
  scanVulnerabilities: async (host, signal) => {
    const response = await api.post('/scan/vulnerabilities', { host }, { signal })
    return response.data
  },
  scanVulnerabilitiesSegment: async (hosts, signal) => {
    const response = await api.post('/scan/vulnerabilities/segment', { hosts }, { signal, timeout: 1800000 })
    return response.data
  },

  // Detectar OS
  detectOS: async (host, signal) => {
    const response = await api.post('/scan/os', { host }, { signal })
    return response.data
  },

  // Detectar OS para múltiples hosts
  detectOSSegment: async (hosts, signal, host_timeout = 60, concurrency = 50) => {
    const response = await api.post('/scan/os/segment', { hosts, host_timeout, concurrency }, { signal, timeout: 360000 }) // 6 minutos
    return response.data
  },

  // Escanear MAC addresses
  scanMAC: async (cidr, signal, host_timeout = 8, concurrency = 30) => {
    const response = await api.post('/scan/mac', { cidr, host_timeout, concurrency }, { signal })
    return response.data
  },

  // scan completo
  fullScan: async (host, saveToDd = true, signal, host_timeout = 120) => {
    const response = await api.post('/scan/full', { host, save_to_db: saveToDd, host_timeout }, { signal, timeout: 600000 }) // 10 minutos para full scan
    return response.data
  },

  // scan completo de rango (ping primero, luego full scan solo activos)
  fullScanRange: async (hosts, saveToDd = true, signal, host_timeout = 120, concurrency = 20) => {
    const response = await api.post('/scan/full/range', { hosts, save_to_db: saveToDd, host_timeout, concurrency }, { signal, timeout: 1800000 }) // 30 minutos máximo
    return response.data
  },

  // Guardar resultados de ping scan (solo IPs activas)
  savePingResults: async (results) => {
    const response = await api.post('/ping/save', { results })
    return response.data
  },

  // Base de datos.
  getAllHosts: async (skip = 0, limit = 100) => {
    const response = await api.get('/hosts', { params: { skip, limit } })
    return response.data
  },

  getHost: async (ip) => {
    const response = await api.get(`/hosts/${ip}`)
    return response.data
  },

  filterByRange: async (startIp, endIp) => {
    const response = await api.get(`/hosts/filter/range`, {
      params: { start_ip: startIp, end_ip: endIp },
    })
    return response.data
  },

  filterSubnet: async (subnet) => {
    const response = await api.get('/hosts/filter/subnet', {
      params: { subnet },
    })
    return response.data
  },
  searchHosts: async (query) => {
    const response = await api.get(`/hosts/search/${query}`)
    return response.data
  },

  deleteHost: async (ip) => {
    const response = await api.post('/hosts/delete', { ip })
    return response.data
  },

  deleteHostsBatch: async (ips) => {
    const response = await api.post('/hosts/delete-batch', { ips })
    return response.data
  },

  updateHostNickname: async (ip, nickname) => {
    const response = await api.post('/hosts/nickname', { ip, nickname })
    return response.data
  },

  getStatistics: async () => {
    const response = await api.get('/statistics')
    return response.data
  },

 
  shutdownHost: async (host, username, password, sudoPassword = null) => {
    const response = await api.post('/ssh/shutdown', {
      host,
      username,
      password,
      sudo_password: sudoPassword,
    })
    return response.data
  },

  shutdownRange: async (startIp, endIp, username, password, sudoPassword = null) => {
    const response = await api.post('/ssh/shutdown/range', {
      start_ip: startIp,
      end_ip: endIp,
      username,
      password,
      sudo_password: sudoPassword,
    })
    return response.data
  },

  testSSH: async (host, username, password) => {
    const response = await api.post('/ssh/test', {
      host,
      username,
      password,
    })
    return response.data
  },

  rebootHost: async (host, username, password, sudoPassword = null) => {
    const response = await api.post('/ssh/reboot', {
      host,
      username,
      password,
      sudo_password: sudoPassword,
    })
    return response.data
  },

  
  executeSSHCommand: async (host, command, username, password) => {
    const response = await api.post('/ssh/execute', {
      host,
      command,
      username,
      password,
    })
    return response.data
  },

  
  executeSSHCommandMultiple: async (hosts, command, username, password) => {
    const response = await api.post('/ssh/execute/multiple', {
      hosts,
      command,
      username,
      password,
    })
    return response.data
  },

  // SSH Credentials (saved)
  getSSHCredentials: async () => {
    const response = await api.get('/ssh/credentials')
    return response.data
  },

  getSSHCredential: async (id) => {
    const response = await api.get(`/ssh/credentials/${id}`)
    return response.data
  },

  createSSHCredential: async (name, username, password) => {
    const response = await api.post('/ssh/credentials', { name, username, password })
    return response.data
  },

  updateSSHCredential: async (id, data) => {
    const response = await api.put(`/ssh/credentials/${id}`, data)
    return response.data
  },

  deleteSSHCredential: async (id) => {
    const response = await api.delete(`/ssh/credentials/${id}`)
    return response.data
  },

  
  exportCSV: async () => {
    const response = await api.get('/export/csv', { responseType: 'blob' })
    return response.data
  },


  createSchedule: async (scheduleData) => {
    const response = await api.post('/api/schedules', scheduleData)
    return response.data
  },

  getSchedules: async () => {
    const response = await api.get('/api/schedules')
    return response.data
  },

  getSchedule: async (id) => {
    const response = await api.get(`/api/schedules/${id}`)
    return response.data
  },

  updateSchedule: async (id, scheduleData) => {
    const response = await api.put(`/api/schedules/${id}`, scheduleData)
    return response.data
  },

  deleteSchedule: async (id) => {
    const response = await api.delete(`/api/schedules/${id}`)
    return response.data
  },

  toggleSchedule: async (id) => {
    const response = await api.post(`/api/schedules/${id}/toggle`)
    return response.data
  },

  runScheduleNow: async (id) => {
    const response = await api.post(`/api/schedules/${id}/run-now`)
    return response.data
  },

  getScheduleResults: async (id) => {
    const response = await api.get(`/api/schedules/${id}/results`)
    return response.data
  },

  getScheduleHistory: async (id, skip = 0, limit = 50) => {
    const response = await api.get(`/api/schedules/${id}/history`, { params: { skip, limit } })
    return response.data
  },

  getAllScanHistory: async (skip = 0, limit = 100) => {
    const response = await api.get('/api/schedules/history/all', { params: { skip, limit } })
    return response.data
  },

  getHistoryDetail: async (historyId) => {
    const response = await api.get(`/api/schedules/history/${historyId}/detail`)
    return response.data
  },

  deleteHistoryEntry: async (historyId) => {
    const response = await api.delete(`/api/schedules/history/${historyId}`)
    return response.data
  },

  // FullScan History
  saveFullScanHistory: async (data) => {
    const response = await api.post('/api/fullscan-history', data)
    return response.data
  },

  getFullScanHistory: async (skip = 0, limit = 50) => {
    const response = await api.get('/api/fullscan-history', { params: { skip, limit } })
    return response.data
  },

  getFullScanHistoryDetail: async (id) => {
    const response = await api.get(`/api/fullscan-history/${id}`)
    return response.data
  },

  deleteFullScanHistory: async (id) => {
    const response = await api.delete(`/api/fullscan-history/${id}`)
    return response.data
  },

  clearFullScanHistory: async () => {
    const response = await api.delete('/api/fullscan-history')
    return response.data
  },

  shutdownNetworkSegment: async (subnet, username, password) => {
    const response = await api.post('/api/schedules/shutdown/segment', {
      target_subnet: subnet,
      ssh_username: username,
      ssh_password: password
    })
    return response.data
  },

  // Audit Log
  getAuditLogs: async (queryString = '') => {
    const response = await api.get(`/api/audit?${queryString}`)
    return response.data
  },

  getAuditStats: async () => {
    const response = await api.get('/api/audit/stats')
    return response.data
  },

  // Dashboard Summary
  getDashboardSummary: async () => {
    const response = await api.get('/api/dashboard/summary')
    return response.data
  },

  // ─── Subnet Lab Management ──────────────────────────────
  getSubnets: async () => {
    const response = await api.get('/api/subnets')
    return response.data
  },

  createSubnet: async (name, startIp, endIp) => {
    const response = await api.post('/api/subnets', { name, start_ip: startIp, end_ip: endIp })
    return response.data
  },

  getSubnet: async (id) => {
    const response = await api.get(`/api/subnets/${id}`)
    return response.data
  },

  updateSubnet: async (id, data) => {
    const response = await api.put(`/api/subnets/${id}`, data)
    return response.data
  },

  deleteSubnet: async (id) => {
    const response = await api.delete(`/api/subnets/${id}`)
    return response.data
  },

  scanSubnet: async (id, signal) => {
    const response = await api.post(`/api/subnets/${id}/scan`, {}, { signal, timeout: 300000 })
    return response.data
  },

  updateDeviceType: async (subnetId, deviceId, deviceType) => {
    const response = await api.put(`/api/subnets/${subnetId}/devices/${deviceId}/type`, { device_type: deviceType })
    return response.data
  },

  updateDeviceLabel: async (subnetId, deviceId, label) => {
    const response = await api.put(`/api/subnets/${subnetId}/devices/${deviceId}/label`, { label })
    return response.data
  },

  getDeviceInfo: async (subnetId, deviceId) => {
    const response = await api.get(`/api/subnets/${subnetId}/devices/${deviceId}/info`)
    return response.data
  },

  scanDevice: async (subnetId, deviceId, signal) => {
    const response = await api.post(`/api/subnets/${subnetId}/devices/${deviceId}/scan`, {}, { signal, timeout: 600000 })
    return response.data
  },

  shutdownDevice: async (subnetId, deviceId, username, password, sudoPassword = null) => {
    const response = await api.post(`/api/subnets/${subnetId}/devices/${deviceId}/shutdown`, {
      username, password, sudo_password: sudoPassword
    })
    return response.data
  },

  shutdownLab: async (subnetId, username, password) => {
    const response = await api.post(`/api/subnets/${subnetId}/shutdown`, {
      username, password
    }, { timeout: 300000 })
    return response.data
  },

  // Token Refresh
  refreshToken: async () => {
    const response = await api.post('/api/auth/refresh')
    return response.data
  },
}

export default api
