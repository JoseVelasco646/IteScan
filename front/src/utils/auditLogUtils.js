import {
  ScrollText,
  Scan,
  Calendar,
  Shield,
  Server,
  Terminal,
  LogIn,
  Plus,
  Pencil,
  Trash2,
} from 'lucide-vue-next'

export const AUDIT_CATEGORIES = [
  { value: '', label: 'Todas' },
  { value: 'scan', label: 'Escaneos' },
  { value: 'scheduler', label: 'Scheduler' },
  { value: 'admin', label: 'Administración' },
  { value: 'host', label: 'Hosts' },
  { value: 'ssh', label: 'SSH' },
  { value: 'auth', label: 'Autenticación' },
]

export const AUDIT_ACTIONS = [
  { value: '', label: 'Todas' },
  { value: 'scan', label: 'Escaneo' },
  { value: 'create', label: 'Crear' },
  { value: 'update', label: 'Modificar' },
  { value: 'delete', label: 'Eliminar' },
  { value: 'login', label: 'Login' },
]

export const getAuditCategoryIcon = (category) => ({
  scan: Scan,
  scheduler: Calendar,
  admin: Shield,
  host: Server,
  ssh: Terminal,
  auth: LogIn,
}[category] || ScrollText)

export const getAuditActionIcon = (action) => ({
  scan: Scan,
  create: Plus,
  update: Pencil,
  delete: Trash2,
  login: LogIn,
  logout: LogIn,
}[action] || ScrollText)

export const getAuditActionLabel = (action) => ({
  scan: 'Escaneo',
  create: 'Crear',
  update: 'Modificar',
  delete: 'Eliminar',
  login: 'Login',
  logout: 'Logout',
}[action] || action)

export const getAuditCategoryLabel = (category) => ({
  scan: 'Escaneo',
  scheduler: 'Scheduler',
  admin: 'Admin',
  host: 'Host',
  ssh: 'SSH',
  auth: 'Auth',
}[category] || category)

export const getAuditCategoryColor = (category, isDark) => ({
  scan: isDark ? 'text-cyan-400 bg-cyan-500/10' : 'text-cyan-600 bg-cyan-100',
  scheduler: isDark ? 'text-purple-400 bg-purple-500/10' : 'text-purple-600 bg-purple-100',
  admin: isDark ? 'text-amber-400 bg-amber-500/10' : 'text-amber-600 bg-amber-100',
  host: isDark ? 'text-green-400 bg-green-500/10' : 'text-green-600 bg-green-100',
  ssh: isDark ? 'text-orange-400 bg-orange-500/10' : 'text-orange-600 bg-orange-100',
  auth: isDark ? 'text-blue-400 bg-blue-500/10' : 'text-blue-600 bg-blue-100',
}[category] || (isDark ? 'text-slate-400 bg-slate-500/10' : 'text-slate-600 bg-slate-100'))

export const getAuditActionBadgeColor = (action, isDark) => ({
  scan: isDark ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' : 'bg-cyan-100 text-cyan-700 border-cyan-300',
  create: isDark ? 'bg-green-500/20 text-green-300 border-green-500/30' : 'bg-green-100 text-green-700 border-green-300',
  update: isDark ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' : 'bg-amber-100 text-amber-700 border-amber-300',
  delete: isDark ? 'bg-red-500/20 text-red-300 border-red-500/30' : 'bg-red-100 text-red-700 border-red-300',
  login: isDark ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' : 'bg-blue-100 text-blue-700 border-blue-300',
  logout: isDark ? 'bg-slate-500/20 text-slate-300 border-slate-500/30' : 'bg-slate-100 text-slate-700 border-slate-300',
}[action] || (isDark ? 'bg-slate-500/20 text-slate-300 border-slate-500/30' : 'bg-slate-100 text-slate-700 border-slate-300'))
