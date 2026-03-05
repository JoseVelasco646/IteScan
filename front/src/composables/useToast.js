import { ref } from 'vue'

const toasts = ref([])
let toastId = 0

// Persistir preferencia de silenciar notificaciones informativas
const muted = ref(localStorage.getItem('toast_muted') === 'true')

function setMuted(value) {
  muted.value = value
  localStorage.setItem('toast_muted', String(value))
}

export function useToast() {
  const show = (type, message, title = '', duration = 4000) => {
    // Si está silenciado, solo mostrar errores y warnings
    if (muted.value && (type === 'success' || type === 'info')) return

    const id = toastId++
    toasts.value.push({
      id,
      type,
      title,
      message,
      duration,
      visible: true
    })

    // Auto-remove después de la duración + tiempo de animación
    setTimeout(() => {
      remove(id)
    }, duration + 200)
  }

  const remove = (id) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value[index].visible = false
      setTimeout(() => {
        const currentIndex = toasts.value.findIndex(t => t.id === id)
        if (currentIndex !== -1) {
          toasts.value.splice(currentIndex, 1)
        }
      }, 300)
    }
  }

  return {
    toasts,
    muted,
    setMuted,
    success: (message, title = '¡Éxito!') => {
      show('success', message, title, 3000)
    },
    error: (message, title = 'Error') => {
      show('error', message, title, 4000)
    },
    warning: (message, title = 'Advertencia') => {
      show('warning', message, title, 3500)
    },
    info: (message, title = 'Información') => {
      show('info', message, title, 3000)
    },
    remove,
    clear: () => {
      toasts.value = []
    }
  }
}

