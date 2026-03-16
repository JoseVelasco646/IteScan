export const normalizeFullScanResultsForHistory = (resultsList) => {
  return resultsList.map((result) => {
    if (result.data) {
      return { ...result.data, _status: result.status, _message: result.message }
    }
    return result
  })
}

export const summarizeFullScanResults = (resultsList) => {
  const hostsActive = resultsList.filter((result) => result.status === 'up' || result.status === 'success').length
  const totalPorts = resultsList.reduce((sum, result) => sum + (result.ports?.length || result.data?.ports?.length || 0), 0)
  const totalServices = resultsList.reduce((sum, result) => sum + (result.services?.length || result.data?.services?.length || 0), 0)

  return {
    hostsScanned: resultsList.length,
    hostsActive,
    totalPorts,
    totalServices,
  }
}
