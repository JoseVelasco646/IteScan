<template>
  <div class="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-purple-600 to-purple-900">
    <div class="bg-white rounded-3xl p-16 max-w-2xl text-center shadow-2xl animate-fade-in">
      <div class="flex justify-center mb-6 animate-shake">
        <ShieldX :size="80" class="text-red-600" />
      </div>
      
      <h1 class="text-5xl font-bold text-red-600 mb-6">
        Acceso Denegado
      </h1>
      
      <p class="text-xl text-gray-600 mb-8">
        Tu dirección IP no está autorizada para acceder a este servicio.
      </p>
      
      <div class="bg-gray-100 border-l-4 border-red-600 p-6 rounded-lg text-left mb-8">
        <p class="font-semibold text-gray-900 mb-2">Tu IP:</p>
        <code class="bg-gray-200 px-3 py-1 rounded text-red-600 font-mono">
          {{ clientIp || 'Detectando...' }}
        </code>
        <p class="font-semibold text-gray-900 mt-4 mb-2">Razón:</p>
        <p class="text-gray-700">
          Esta aplicación utiliza whitelist. 
          Tu dirección IP no se encuentra en la lista de dispositivos permitidos.
        </p>
      </div>

      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div class="flex items-center justify-center gap-2">
          <div class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          <p class="text-blue-700 text-sm font-medium">
            Verificando acceso automáticamente cada 3 segundos...
          </p>
        </div>
        <p class="text-blue-600 text-xs mt-2">
          Si el administrador te agrega a la whitelist, serás redirigido automáticamente
        </p>
      </div>

      <p class="text-gray-500 text-sm">
        Si crees que deberías tener acceso, contacta al administrador del sistema.
      </p>
      <div class="mt-6 text-gray-400 text-xs">
        Network Scanner © 2026 - Acceso Protegido
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldX } from 'lucide-vue-next'

const router = useRouter()
const clientIp = ref('')
let checkInterval = null

const checkWhitelistStatus = async () => {
  try {
    const response = await fetch('http://192.168.0.10:8000/api/check-whitelist-status', {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      console.log('Estado de whitelist:', data)
      
      if (data.is_whitelisted) {
        localStorage.removeItem('blocked_ip')
        window.location.href = '/'
      } else {
        console.log('Aún no está en la whitelist')
      }
    }
  } catch (error) {
    console.log('Error verificando whitelist:', error)
  }
}

onMounted(async () => {
  const savedIp = localStorage.getItem('blocked_ip')
  if (savedIp) {
    clientIp.value = savedIp
  } else {
    try {
      console.log('Intentando obtener IP desde backend...')
      const response = await fetch('http://192.168.0.10:8000/api/get-client-ip', {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      })
      
      console.log('Respuesta recibida:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('Datos:', data)
        clientIp.value = data.ip
        localStorage.setItem('blocked_ip', data.ip)
      } else {
        console.error('Error en respuesta:', response.status)
        clientIp.value = 'No disponible'
      }
    } catch (error) {
      console.error('Error obteniendo IP:', error)
      clientIp.value = 'No disponible'
    }
  }

  checkInterval = setInterval(checkWhitelistStatus, 3000)
  
  checkWhitelistStatus()
})

onUnmounted(() => {
  if (checkInterval) {
    clearInterval(checkInterval)
  }
})
</script>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shake {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-10deg); }
  75% { transform: rotate(10deg); }
}

.animate-fade-in {
  animation: fade-in 0.5s ease-out;
}

.animate-shake {
  animation: shake 0.5s ease-out;
}

.bg-gradient-to-br {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
