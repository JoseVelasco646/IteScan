import { ref } from 'vue'

const toasts = ref([])
let toastId = 0

export function useToast() {
  const show = (type, message, title = '', duration = 4000) => {
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
        toasts.value.splice(index, 1)
      }, 300)
    }
  }

  return {
    toasts,
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

