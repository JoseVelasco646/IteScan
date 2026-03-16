export const formatDateTime = (
  dateValue,
  {
    locale = 'es-ES',
    fallback = 'N/A',
    withSeconds = false,
    shortMonth = false,
  } = {},
) => {
  if (!dateValue) return fallback

  try {
    const date = new Date(dateValue)
    if (Number.isNaN(date.getTime())) return String(dateValue)

    return date.toLocaleString(locale, {
      year: 'numeric',
      month: shortMonth ? 'short' : '2-digit',
      day: shortMonth ? 'numeric' : '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      ...(withSeconds ? { second: '2-digit' } : {}),
    })
  } catch {
    return String(dateValue)
  }
}

export const formatDurationCompact = (seconds, fallback = '—') => {
  if (seconds === null || seconds === undefined || Number.isNaN(Number(seconds))) return fallback

  const totalSeconds = Number(seconds)
  if (totalSeconds < 60) return `${Math.round(totalSeconds)}s`

  const minutes = Math.floor(totalSeconds / 60)
  const remainSeconds = Math.round(totalSeconds % 60)

  if (minutes < 60) return `${minutes}m ${remainSeconds}s`

  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  return `${hours}h ${remainMinutes}m`
}

export const formatRelativeTime = (dateValue, fallback = '') => {
  if (!dateValue) return fallback

  const date = new Date(dateValue)
  if (Number.isNaN(date.getTime())) return fallback

  const diff = Math.floor((Date.now() - date.getTime()) / 1000)
  if (diff < 60) return 'hace unos segundos'
  if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)}h`
  return `hace ${Math.floor(diff / 86400)}d`
}
