import { Wifi, Server, Monitor, Search, Database } from 'lucide-vue-next'
import { formatDateTime } from './dateTime'

export const getCurrentTimeHHMM = () => {
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

export const getScheduleScanTypeIcon = (type) => ({
  ping: Wifi,
  ports: Server,
  services: Server,
  os: Monitor,
  mac: Search,
  full: Database,
}[type] || Database)

export const getScheduleScanTypeName = (type) => ({
  ping: 'Ping',
  ports: 'Puertos',
  services: 'Servicios',
  os: 'Detección de SO',
  mac: 'Dirección MAC',
  full: 'Escaneo Completo',
}[type] || type)

export const getScheduleScanTypeColor = (type) => ({
  ping: 'bg-cyan-500/20 text-cyan-400',
  ports: 'bg-blue-500/20 text-blue-400',
  services: 'bg-purple-500/20 text-purple-400',
  os: 'bg-green-500/20 text-green-400',
  mac: 'bg-yellow-500/20 text-yellow-400',
  full: 'bg-red-500/20 text-red-400',
}[type] || 'bg-slate-500/20 text-slate-400')

export const getScheduleDayName = (day) => {
  const days = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
  return days[day] || ''
}

export const getScheduleDescription = (schedule) => ({
  hourly: 'Cada hora',
  daily: `Diario a las ${schedule.time}`,
  weekly: `Semanal (${getScheduleDayName(schedule.day_of_week)}) a las ${schedule.time}`,
  monthly: `Mensual (día ${schedule.day_of_month}) a las ${schedule.time}`,
}[schedule.frequency] || schedule.frequency)

export const formatScheduleDateTime = (value) => formatDateTime(value, { locale: 'es-ES', fallback: 'N/A' })
