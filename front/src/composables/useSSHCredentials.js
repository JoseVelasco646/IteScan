import { ref } from 'vue'
import { scannerAPI } from '../api/scanner'

export function useSSHCredentials(toast) {
  const savedCredentials = ref([])
  const loadingCredentials = ref(false)

  const loadSavedCredentials = async () => {
    loadingCredentials.value = true
    try {
      savedCredentials.value = await scannerAPI.getSSHCredentials()
    } catch {
      savedCredentials.value = []
    } finally {
      loadingCredentials.value = false
    }
  }

  const applySavedCredential = async (id) => {
    try {
      const credential = await scannerAPI.getSSHCredential(id)
      if (toast) toast.success(`Credenciales "${credential.name}" cargadas`)
      return credential
    } catch {
      if (toast) toast.error('Error cargando credencial')
      return null
    }
  }

  const saveCredential = async (name, username, password) => {
    try {
      await scannerAPI.createSSHCredential(name, username, password)
      if (toast) toast.success('Credencial guardada')
      await loadSavedCredentials()
      return true
    } catch {
      if (toast) toast.error('Error guardando credencial')
      return false
    }
  }

  const deleteCredential = async (id) => {
    try {
      await scannerAPI.deleteSSHCredential(id)
      if (toast) toast.success('Credencial eliminada')
      await loadSavedCredentials()
      return true
    } catch {
      if (toast) toast.error('Error eliminando credencial')
      return false
    }
  }

  return {
    savedCredentials,
    loadingCredentials,
    loadSavedCredentials,
    applySavedCredential,
    saveCredential,
    deleteCredential,
  }
}
