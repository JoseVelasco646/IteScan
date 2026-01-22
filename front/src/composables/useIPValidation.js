/**
 * Composable para validación de direcciones IP y redes
 */
export function useIPValidation() {
  /**
   * Valida si una cadena es una dirección IPv4 válida
   * @param {string} ip - Dirección IP a validar
   * @returns {boolean}
   */
  const isValidIPv4 = (ip) => {
    if (!ip || typeof ip !== 'string') return false
    
    const ipv4Regex = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
    return ipv4Regex.test(ip.trim())
  }

  /**
   * Valida si una cadena es una dirección IPv6 válida
   * @param {string} ip - Dirección IP a validar
   * @returns {boolean}
   */
  const isValidIPv6 = (ip) => {
    if (!ip || typeof ip !== 'string') return false
    
    const ipv6Regex = /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/
    return ipv6Regex.test(ip.trim())
  }

  /**
   * Valida si una cadena es una IP válida (IPv4 o IPv6)
   * @param {string} ip - Dirección IP a validar
   * @returns {boolean}
   */
  const isValidIP = (ip) => {
    return isValidIPv4(ip) || isValidIPv6(ip)
  }

  /**
   * Valida si una cadena es un CIDR válido
   * @param {string} cidr - Red CIDR a validar (ej: 192.168.0.0/24)
   * @returns {boolean}
   */
  const isValidCIDR = (cidr) => {
    if (!cidr || typeof cidr !== 'string') return false
    
    const parts = cidr.trim().split('/')
    if (parts.length !== 2) return false
    
    const [ip, prefix] = parts
    const prefixNum = parseInt(prefix, 10)
    
    // Validar IP
    if (!isValidIPv4(ip)) return false
    
    // Validar prefijo (0-32 para IPv4)
    if (isNaN(prefixNum) || prefixNum < 0 || prefixNum > 32) return false
    
    return true
  }

  /**
   * Valida si un rango de IPs es válido
   * @param {string} startIP - IP inicial
   * @param {string} endIP - IP final
   * @returns {object} { valid: boolean, message: string }
   */
  const validateIPRange = (startIP, endIP) => {
    if (!isValidIPv4(startIP)) {
      return { valid: false, message: 'IP inicial inválida' }
    }
    
    if (!isValidIPv4(endIP)) {
      return { valid: false, message: 'IP final inválida' }
    }
    
    // Convertir IPs a números para comparar
    const startParts = startIP.split('.').map(Number)
    const endParts = endIP.split('.').map(Number)
    
    const startNum = (startParts[0] << 24) + (startParts[1] << 16) + (startParts[2] << 8) + startParts[3]
    const endNum = (endParts[0] << 24) + (endParts[1] << 16) + (endParts[2] << 8) + endParts[3]
    
    if (startNum > endNum) {
      return { valid: false, message: 'La IP inicial debe ser menor o igual a la IP final' }
    }
    
    return { valid: true, message: 'Rango válido' }
  }

  /**
   * Valida si una dirección MAC es válida
   * @param {string} mac - Dirección MAC a validar
   * @returns {boolean}
   */
  const isValidMAC = (mac) => {
    if (!mac || typeof mac !== 'string') return false
    
    const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/
    return macRegex.test(mac.trim())
  }

  /**
   * Valida un puerto o rango de puertos
   * @param {string} ports - Puerto o rango (ej: "80" o "1-1024" o "80,443,8080")
   * @returns {boolean}
   */
  const isValidPortRange = (ports) => {
    if (!ports || typeof ports !== 'string') return false
    
    const portStr = ports.trim()
    
    // Validar rango (ej: "1-1024")
    if (portStr.includes('-')) {
      const [start, end] = portStr.split('-').map(p => parseInt(p.trim(), 10))
      if (isNaN(start) || isNaN(end)) return false
      if (start < 1 || start > 65535) return false
      if (end < 1 || end > 65535) return false
      if (start > end) return false
      return true
    }
    
    // Validar lista (ej: "80,443,8080")
    if (portStr.includes(',')) {
      const portList = portStr.split(',').map(p => parseInt(p.trim(), 10))
      return portList.every(p => !isNaN(p) && p >= 1 && p <= 65535)
    }
    
    // Validar puerto único
    const port = parseInt(portStr, 10)
    return !isNaN(port) && port >= 1 && port <= 65535
  }

  /**
   * Sanitiza una IP eliminando espacios
   * @param {string} ip - IP a sanitizar
   * @returns {string}
   */
  const sanitizeIP = (ip) => {
    if (!ip || typeof ip !== 'string') return ''
    return ip.trim()
  }

  /**
   * Obtiene el mensaje de error apropiado para una validación
   * @param {string} type - Tipo de validación ('ip', 'cidr', 'mac', 'port')
   * @returns {string}
   */
  const getErrorMessage = (type) => {
    const messages = {
      ip: 'Dirección IP inválida. Formato esperado: 192.168.0.1',
      ipv4: 'Dirección IPv4 inválida. Formato esperado: 192.168.0.1',
      ipv6: 'Dirección IPv6 inválida',
      cidr: 'Red CIDR inválida. Formato esperado: 192.168.0.0/24',
      mac: 'Dirección MAC inválida. Formato esperado: aa:bb:cc:dd:ee:ff',
      port: 'Puerto inválido. Debe estar entre 1 y 65535',
      portRange: 'Rango de puertos inválido. Ejemplos: "80", "1-1024", "80,443,8080"'
    }
    return messages[type] || 'Valor inválido'
  }

  return {
    isValidIPv4,
    isValidIPv6,
    isValidIP,
    isValidCIDR,
    isValidMAC,
    isValidPortRange,
    validateIPRange,
    sanitizeIP,
    getErrorMessage
  }
}
