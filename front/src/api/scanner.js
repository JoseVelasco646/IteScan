// src/api/scanner.js
import axios from 'axios'

// Para desarrollo local con Docker
// Si accedes desde otra IP, usa la IP del servidor en lugar de localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.origin.replace(':3000', ':8000')

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutos timeout
})

export const scannerAPI = {
  // Ping múltiples hosts
  pingHosts: async (hosts, signal, host_timeout = 2) => {
    const response = await api.post('/ping', { hosts, host_timeout }, { signal, timeout: 120000 }) // 2 minutos
    return response.data
  },

  // Escanear red completa
  scanNetwork: async (cidr, signal, host_timeout = 2) => {
    const response = await api.post('/scan/network', { cidr, host_timeout }, { signal, timeout: 300000 }) // 5 minutos
    return response.data
  },

  // Escanear puertos
  scanPorts: async (host, ports = '1-1024', signal) => {
    const response = await api.post('/scan/ports', { host, ports }, { signal })
    return response.data
  },

  scanPortsSegment: async (hosts, ports = '1-1024', signal, host_timeout = 45) => {
    const response = await api.post('/scan/ports/segment', { hosts, ports, host_timeout }, { signal })
    return response.data
  },

  // Escanear servicios
  scanServices: async (host, ports = '1-1024', signal) => {
    const response = await api.post('/scan/services', { host, ports }, { signal })
    return response.data
  },
  scanServicesSegment: async (hosts, ports = '1-1024', signal, host_timeout = 120) => {
    const response = await api.post('/scan/services/segment', { hosts, ports, host_timeout }, { signal, timeout: 600000 }) // 10 minutos
    return response.data
  },

  // Escanear vulnerabilidades
  scanVulnerabilities: async (host, signal) => {
    const response = await api.post('/scan/vulnerabilities', { host }, { signal })
    return response.data
  },

  // Detectar OS
  detectOS: async (host, signal) => {
    const response = await api.post('/scan/os', { host }, { signal })
    return response.data
  },

  // Detectar OS para múltiples hosts
  detectOSSegment: async (hosts, signal, host_timeout = 60) => {
    const response = await api.post('/scan/os/segment', { hosts, host_timeout }, { signal, timeout: 360000 }) // 6 minutos
    return response.data
  },

  // Escanear MAC addresses
  scanMAC: async (cidr, signal, host_timeout = 8) => {
    const response = await api.post('/scan/mac', { cidr, host_timeout }, { signal })
    return response.data
  },

  // scan completo
  fullScan: async (host, saveToDd = true, signal, host_timeout = 120) => {
    const response = await api.post('/scan/full', { host, save_to_db: saveToDd, host_timeout }, { signal, timeout: 600000 }) // 10 minutos para full scan
    return response.data
  },
  // Base de datos.
  getAllHosts: async () => {
    const response = await api.get('/hosts')
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
    const response = await api.delete(`/hosts/${ip}`)
    return response.data
  },

  getStatistics: async () => {
    const response = await api.get('/statistics')
    return response.data
  },

  // ==================== SSH ====================
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

  // Ejecutar comando SSH en un host
  executeSSHCommand: async (host, command, username, password) => {
    const response = await api.post('/ssh/execute', {
      host,
      command,
      username,
      password,
    })
    return response.data
  },

  // Ejecutar comando en múltiples hosts en paralelo
  executeSSHCommandMultiple: async (hosts, command, username, password) => {
    const response = await api.post('/ssh/execute/multiple', {
      hosts,
      command,
      username,
      password,
    })
    return response.data
  },

  // ==================== EXPORTACIÓN ====================
  exportCSV: async () => {
    const response = await api.get('/export/csv', { responseType: 'blob' })
    return response.data
  },

  // ==================== SCHEDULES ====================
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

  shutdownNetworkSegment: async (subnet, username, password) => {
    const response = await api.post('/api/schedules/shutdown/segment', {
      target_subnet: subnet,
      ssh_username: username,
      ssh_password: password
    })
    return response.data
  },
}

export default api
