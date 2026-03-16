import { Shield, Zap, Pencil, Eye } from 'lucide-vue-next'
import { formatDateTime } from './dateTime'

export const getPasswordRules = (password) => {
  if (!password) return []
  return [
    { label: 'Al menos 8 caracteres', ok: password.length >= 8 },
    { label: 'Una letra mayúscula', ok: /[A-Z]/.test(password) },
    { label: 'Una letra minúscula', ok: /[a-z]/.test(password) },
    { label: 'Un número', ok: /\d/.test(password) },
  ]
}

export const getPasswordStrength = (password) => {
  if (!password) return 0
  return getPasswordRules(password).filter((rule) => rule.ok).length
}

export const ROLE_OPTIONS = [
  { value: 'viewer', label: 'Visor', desc: 'Solo lectura', icon: Eye, hex: '#64748b', rgba: 'rgba(100,116,139,0.15)', borderActive: 'slate-400' },
  { value: 'op', label: 'Operador', desc: 'Ejecutar escaneos', icon: Zap, hex: '#f59e0b', rgba: 'rgba(245,158,11,0.15)', borderActive: 'amber-400' },
  { value: 'mod', label: 'Moderador', desc: 'Editar y administrar', icon: Pencil, hex: '#3b82f6', rgba: 'rgba(59,130,246,0.15)', borderActive: 'blue-400' },
  { value: 'admin', label: 'Admin', desc: 'Acceso completo', icon: Shield, hex: '#a855f7', rgba: 'rgba(168,85,247,0.15)', borderActive: 'purple-400' },
]

export const getRoleLabel = (role) => ({ admin: 'Admin', mod: 'Moderador', op: 'Operador', viewer: 'Visor' }[role] || 'Visor')

export const getRoleIcon = (role) => ({ admin: Shield, mod: Pencil, op: Zap, viewer: Eye }[role] || Eye)

export const getRoleBadgeClass = (role, isDark) => ({
  admin: isDark ? 'bg-purple-500/15 text-purple-400' : 'bg-purple-50 text-purple-700',
  mod: isDark ? 'bg-blue-500/15 text-blue-400' : 'bg-blue-50 text-blue-700',
  op: isDark ? 'bg-amber-500/15 text-amber-400' : 'bg-amber-50 text-amber-700',
  viewer: isDark ? 'bg-slate-700/60 text-slate-400' : 'bg-slate-100 text-slate-600',
}[role] || (isDark ? 'bg-slate-700/60 text-slate-400' : 'bg-slate-100 text-slate-600'))

export const getRoleSelectClass = (role, isDark) => ({
  admin: isDark ? 'bg-purple-500/15 text-purple-300 border-purple-500/30' : 'bg-purple-50 text-purple-700 border-purple-200',
  mod: isDark ? 'bg-blue-500/15 text-blue-300 border-blue-500/30' : 'bg-blue-50 text-blue-700 border-blue-200',
  op: isDark ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' : 'bg-amber-50 text-amber-700 border-amber-200',
  viewer: isDark ? 'bg-slate-700/60 text-slate-300 border-slate-600' : 'bg-slate-100 text-slate-700 border-slate-200',
}[role] || (isDark ? 'bg-slate-700/60 text-slate-300 border-slate-600' : 'bg-slate-100 text-slate-700 border-slate-200'))

export const formatAdminDate = (dateValue) => formatDateTime(dateValue, { locale: 'es-ES', fallback: 'N/A' })
