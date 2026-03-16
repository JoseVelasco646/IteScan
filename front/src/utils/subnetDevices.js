export const getSubnetDeviceStatusRing = (status) => {
  if (status === 'green') return 'ring-2 ring-emerald-400/60 shadow-emerald-500/30'
  if (status === 'red') return 'ring-2 ring-red-400/60 shadow-red-500/30'
  return 'ring-1 ring-slate-500/30'
}

export const getSubnetDeviceStatusLabel = (status) => {
  if (status === 'green') return 'Activo'
  if (status === 'red') return 'Inactivo'
  return 'Sin escanear'
}

export const getSubnetDeviceStatusDot = (status) => {
  if (status === 'green') return 'bg-emerald-400'
  if (status === 'red') return 'bg-red-400'
  return 'bg-slate-400'
}
