export const ipv4ToNumber = (ip) => {
  const parts = String(ip).trim().split('.').map(Number)
  if (parts.length !== 4 || parts.some((part) => Number.isNaN(part) || part < 0 || part > 255)) {
    return null
  }
  return ((parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]) >>> 0
}

export const expandIPv4Range = (startIP, endIP) => {
  const start = String(startIP).trim()
  const end = String(endIP).trim()

  const startNum = ipv4ToNumber(start)
  const endNum = ipv4ToNumber(end)

  if (startNum === null || endNum === null || endNum < startNum) {
    return []
  }

  const startParts = start.split('.').map(Number)
  const endParts = end.split('.').map(Number)

  const hosts = []

  for (let thirdOctet = startParts[2]; thirdOctet <= endParts[2]; thirdOctet++) {
    const rangeStart = thirdOctet === startParts[2] ? startParts[3] : 1
    const rangeEnd = thirdOctet === endParts[2] ? endParts[3] : 254

    for (let lastOctet = rangeStart; lastOctet <= rangeEnd; lastOctet++) {
      hosts.push(`${startParts[0]}.${startParts[1]}.${thirdOctet}.${lastOctet}`)
    }
  }

  return hosts
}

export const parseHostsInput = (input) => {
  if (!input || !String(input).trim()) return []

  const hosts = []
  const parts = String(input)
    .split(/[\n,]+/)
    .map((part) => part.trim())
    .filter(Boolean)

  for (const part of parts) {
    if (part.includes('-') && !part.includes('/')) {
      const [start, end] = part.split('-').map((segment) => segment.trim())
      if (!start || !end) continue
      hosts.push(...expandIPv4Range(start, end))
      continue
    }

    hosts.push(part)
  }

  return hosts
}
