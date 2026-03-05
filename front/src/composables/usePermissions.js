import { computed, ref } from 'vue'

const ROLE_HIERARCHY = {
  admin: 4,
  mod: 3,
  op: 2,
  viewer: 1
}

const ROLE_LABELS = {
  admin: 'Admin',
  mod: 'Moderador',
  op: 'Operador',
  viewer: 'Visor'
}

// Global reactive trigger — bump this to force all permission computeds to re-evaluate
const authVersion = ref(0)

export function refreshPermissions() {
  authVersion.value++
}

export function usePermissions() {
  const userRole = computed(() => {
    authVersion.value // reactive dependency
    try {
      const user = JSON.parse(localStorage.getItem('admin_user') || '{}')
      return user.role || 'viewer'
    } catch {
      return 'viewer'
    }
  })

  const isSuperAdmin = computed(() => {
    authVersion.value // reactive dependency
    try {
      const user = JSON.parse(localStorage.getItem('admin_user') || '{}')
      return user.is_super_admin === true
    } catch {
      return false
    }
  })

  const roleLevel = computed(() => ROLE_HIERARCHY[userRole.value] || 1)

  const hasRole = (minimumRole) => {
    const required = ROLE_HIERARCHY[minimumRole] || 0
    return roleLevel.value >= required
  }

  const isAdmin = computed(() => hasRole('admin'))
  const isMod = computed(() => hasRole('mod'))
  const isOp = computed(() => hasRole('op'))
  const isViewer = computed(() => hasRole('viewer'))

  // Permisos específicos
  const canExecuteScans = computed(() => hasRole('op'))
  const canEditResources = computed(() => hasRole('mod'))
  const canDeleteResources = computed(() => hasRole('mod'))
  const canManageUsers = computed(() => hasRole('admin'))
  const canCreateDeleteUsers = computed(() => isSuperAdmin.value)
  const canViewAudit = computed(() => hasRole('admin'))
  const canManageSchedulers = computed(() => hasRole('mod'))
  const canRunSchedulers = computed(() => hasRole('op'))
  const canUseSSH = computed(() => hasRole('op'))

  return {
    userRole,
    roleLevel,
    hasRole,
    isAdmin,
    isMod,
    isOp,
    isViewer,
    isSuperAdmin,
    canExecuteScans,
    canEditResources,
    canDeleteResources,
    canManageUsers,
    canCreateDeleteUsers,
    canViewAudit,
    canManageSchedulers,
    canRunSchedulers,
    canUseSSH,
    refreshPermissions,
    ROLE_HIERARCHY,
    ROLE_LABELS
  }
}
