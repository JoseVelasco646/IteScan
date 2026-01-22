<template>
  <div class="min-h-screen p-6" :class="isDark() ? 'bg-gray-900' : 'bg-gray-50'">
    <div class="max-w-6xl mx-auto">
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold mb-2 flex items-center gap-3" :class="isDark() ? 'text-white' : 'text-gray-900'">
            <Lock :size="32" />
            Gestión de Whitelist
          </h1>
          <p :class="isDark() ? 'text-gray-400' : 'text-gray-600'">
            Administra las direcciones IP autorizadas para usar el escáner de red
          </p>
        </div>
        <button
          @click="$router.push('/')"
          class="px-6 py-3 rounded-lg font-medium transition-all flex items-center gap-2"
          :class="isDark() ? 
            'bg-gray-800 hover:bg-gray-700 text-white border border-gray-700' : 
            'bg-white hover:bg-gray-50 text-gray-900 border border-gray-300 shadow-sm'"
        >
          <ArrowLeft :size="20" />
          Volver al Dashboard
        </button>
      </div>

      <div class="mb-6 p-4 rounded-lg" :class="whitelistInfo.enabled ? 
        (isDark() ? 'bg-green-900/20 border border-green-500' : 'bg-green-50 border border-green-200') :
        (isDark() ? 'bg-yellow-900/20 border border-yellow-500' : 'bg-yellow-50 border border-yellow-200')">
        <div class="flex items-center gap-3">
          <CircleCheck v-if="whitelistInfo.enabled" :size="32" class="text-green-500" />
          <AlertTriangle v-else :size="32" class="text-yellow-500" />
          <div class="flex-1">
            <p class="font-semibold" :class="isDark() ? 'text-white' : 'text-gray-900'">
              {{ whitelistInfo.enabled ? 'Whitelist Activa' : 'Whitelist Desactivada' }}
            </p>
            <p class="text-sm" :class="isDark() ? 'text-gray-400' : 'text-gray-600'">
              {{ whitelistInfo.enabled ? 
                `${whitelistInfo.total} IP(s) autorizada(s)` : 
                'Todas las IPs están permitidas. Configura IP_WHITELIST en .env para activar.' }}
            </p>
          </div>
          <div v-if="whitelistInfo.is_admin" class="px-3 py-1 rounded-full text-sm font-semibold" :class="isDark() ? 'bg-purple-900/50 text-purple-300' : 'bg-purple-100 text-purple-700'">
          Administrador
          </div>
          <div v-else class="px-3 py-1 rounded-full text-sm font-semibold" :class="isDark() ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'">
          Usuario
          </div>
        </div>
      </div>

      <div class="mb-6 p-6 rounded-lg" :class="isDark() ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'">
        <h2 class="text-xl font-semibold mb-4 flex items-center gap-2" :class="isDark() ? 'text-white' : 'text-gray-900'">
          <Plus :size="24" />
          Agregar Nueva IP
        </h2>
        <div v-if="!whitelistInfo.is_admin" class="mb-4 p-3 rounded-lg flex items-center gap-2" :class="isDark() ? 'bg-yellow-900/20 border border-yellow-500' : 'bg-yellow-50 border border-yellow-200'">
          <AlertTriangle :size="20" class="text-yellow-500" />
          <p class="text-sm" :class="isDark() ? 'text-yellow-300' : 'text-yellow-700'">
            Solo los administradores pueden agregar IPs a la whitelist
          </p>
        </div>
        <div class="flex gap-3">
          <input 
            v-model="newIP"
            type="text"
            placeholder="Ej: 192.168.0.100"
            :disabled="!whitelistInfo.is_admin"
            class="flex-1 px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            :class="isDark() ? 'bg-gray-700 text-white border-gray-600' : 'bg-gray-50 text-gray-900 border-gray-300'"
            @keyup.enter="addIP"
          />
          <button 
            @click="addIP"
            :disabled="!newIP || loading || !whitelistInfo.is_admin"
            class="px-6 py-2 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            :class="isDark() ? 
              'bg-blue-600 hover:bg-blue-700 text-white' : 
              'bg-blue-500 hover:bg-blue-600 text-white'"
          >
            <Plus :size="20" />
            {{ loading ? 'Agregando...' : 'Agregar' }}
          </button>
        </div>
      </div>

      <div class="mb-6 rounded-lg overflow-hidden" :class="isDark() ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'">
        <div class="p-6 border-b" :class="isDark() ? 'border-gray-700' : 'border-gray-200'">
          <h2 class="text-xl font-semibold flex items-center gap-2" :class="isDark() ? 'text-white' : 'text-gray-900'">
            <List :size="24" />
            IPs Autorizadas ({{ whitelistInfo.ips_metadata.length }})
          </h2>
        </div>
        
        <div v-if="whitelistInfo.ips_metadata.length === 0" class="p-8 text-center">
          <p class="text-gray-500">No hay IPs en la whitelist</p>
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead :class="isDark() ? 'bg-gray-700' : 'bg-gray-50'">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" :class="isDark() ? 'text-gray-300' : 'text-gray-700'">
                  Dirección IP
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" :class="isDark() ? 'text-gray-300' : 'text-gray-700'">
                  Agregada Por
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" :class="isDark() ? 'text-gray-300' : 'text-gray-700'">
                  Fecha
                </th>
                <th class="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider" :class="isDark() ? 'text-gray-300' : 'text-gray-700'">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody :class="isDark() ? 'divide-y divide-gray-700' : 'divide-y divide-gray-200'">
              <tr v-for="ipData in whitelistInfo.ips_metadata" :key="ipData.ip" :class="isDark() ? 'hover:bg-gray-700' : 'hover:bg-gray-50'">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <Globe :size="24" class="text-blue-500" />
                    <div>
                      <div class="font-mono text-lg" :class="isDark() ? 'text-white' : 'text-gray-900'">
                        {{ ipData.ip }}
                      </div>
                      <div v-if="ipData.is_admin" class="text-xs" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">
                        👑 Administrador
                      </div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-mono" :class="isDark() ? 'text-gray-300' : 'text-gray-700'">
                    {{ ipData.added_by }}
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm" :class="isDark() ? 'text-gray-400' : 'text-gray-600'">
                    {{ formatTimestamp(ipData.added_at) }}
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right">
                  <button
                    @click="openDeleteModal(ipData.ip)"
                    :disabled="loading || !whitelistInfo.is_admin"
                    class="px-4 py-2 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 ml-auto"
                    :class="isDark() ? 
                      'bg-red-600 hover:bg-red-700 text-white' : 
                      'bg-red-500 hover:bg-red-600 text-white'"
                  >
                    <Trash2 :size="18" />
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rounded-lg overflow-hidden" :class="isDark() ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'">
        <div class="p-6 border-b flex justify-between items-center" :class="isDark() ? 'border-gray-700' : 'border-gray-200'">
          <h2 class="text-xl font-semibold flex items-center gap-2" :class="isDark() ? 'text-white' : 'text-gray-900'">
            <ShieldAlert :size="24" />
            Intentos de Acceso Bloqueados
          </h2>
          <button
            @click="loadLogs"
            class="px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2"
            :class="isDark() ? 
              'bg-gray-700 hover:bg-gray-600 text-white' : 
              'bg-gray-100 hover:bg-gray-200 text-gray-900'"
          >
            <RefreshCw :size="18" />
            Recargar
          </button>
        </div>
        
        <div v-if="!logs.attempts || logs.attempts.length === 0" class="p-8 text-center">
          <p class="text-gray-500 mb-2">No hay intentos bloqueados registrados</p>
          <p v-if="logs.message" class="text-sm text-yellow-500">{{ logs.message }}</p>
          <p v-if="logs.error" class="text-sm text-red-500">Error: {{ logs.error }}</p>
          <div v-if="logs.total_lines !== undefined" class="text-xs mt-2" :class="isDark() ? 'text-gray-600' : 'text-gray-400'">
            <p>Total de líneas: {{ logs.total_lines }}</p>
            <p>Intentos bloqueados: {{ logs.total_blocked || 0 }}</p>
            <p v-if="logs.log_file">Archivo: {{ logs.log_file }}</p>
          </div>
        </div>
        
        <div v-else class="p-6">
          <p class="mb-4 text-sm" :class="isDark() ? 'text-gray-400' : 'text-gray-600'">
            Mostrando {{ logs.showing }} de {{ logs.total_blocked }} intentos bloqueados
          </p>
          <div class="space-y-4 max-h-[600px] overflow-y-auto">
            <div 
              v-for="(attempt, index) in logs.attempts" 
              :key="index"
              class="p-4 rounded-lg border-l-4"
              :class="isDark() ? 
                'bg-gray-900 border-red-500' : 
                'bg-red-50 border-red-400'"
            >
              <div v-if="attempt.ip && attempt.ip !== 'N/A'" class="space-y-3">
                <div class="flex items-center justify-between mb-3 pb-3 border-b" :class="isDark() ? 'border-gray-700' : 'border-red-200'">
                  <div class="flex items-center gap-2">
                    <Clock :size="20" class="text-cyan-500" />
                    <div>
                      <p class="text-xs font-semibold mb-0.5" :class="isDark() ? 'text-gray-500' : 'text-gray-600'">
                        Hora del intento
                      </p>
                      <p class="font-mono text-sm font-bold" :class="isDark() ? 'text-cyan-400' : 'text-cyan-700'">
                        {{ formatTimestamp(attempt.timestamp) }}
                      </p>
                    </div>
                  </div>
                  <span class="text-xs px-3 py-1 rounded font-semibold" :class="isDark() ? 'bg-red-900/50 text-red-300' : 'bg-red-200 text-red-800'">
                    {{ attempt.method }}
                  </span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div class="flex items-start gap-2">
                    <Globe :size="20" class="text-blue-500" />
                    <div class="flex-1">
                      <p class="text-xs font-semibold mb-1" :class="isDark() ? 'text-gray-500' : 'text-gray-600'">
                        Dirección IP
                      </p>
                      <p class="font-mono font-bold" :class="isDark() ? 'text-red-400' : 'text-red-700'">
                        {{ attempt.ip }}
                      </p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-2">
                    <Monitor :size="20" class="text-purple-500" />
                    <div class="flex-1">
                      <p class="text-xs font-semibold mb-1" :class="isDark() ? 'text-gray-500' : 'text-gray-600'">
                        MAC Address
                      </p>
                      <p class="font-mono text-sm" :class="isDark() ? 'text-gray-300' : 'text-gray-800'">
                        {{ attempt.mac }}
                      </p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-2">
                    <Factory :size="20" class="text-orange-500" />
                    <div class="flex-1">
                      <p class="text-xs font-semibold mb-1" :class="isDark() ? 'text-gray-500' : 'text-gray-600'">
                        Fabricante
                      </p>
                      <p class="text-sm font-medium" :class="isDark() ? 'text-gray-300' : 'text-gray-800'">
                        {{ attempt.vendor }}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div class="pt-2 flex items-start gap-2">
                  <Route :size="18" class="text-gray-500 mt-0.5" />
                  <div class="flex-1">
                    <p class="text-xs font-semibold mb-1" :class="isDark() ? 'text-gray-500' : 'text-gray-600'">
                      Ruta solicitada
                    </p>
                    <p class="font-mono text-sm" :class="isDark() ? 'text-gray-400' : 'text-gray-700'">
                      {{ attempt.path }}
                    </p>
                  </div>
                </div>
                
                <div class="pt-2 flex items-start gap-2">
                  <User :size="18" class="text-gray-500 mt-0.5" />
                  <div class="flex-1">
                    <p class="text-xs font-semibold mb-1" :class="isDark() ? 'text-gray-500' : 'text-gray-600'">
                      User Agent
                    </p>
                    <p class="text-xs break-all" :class="isDark() ? 'text-gray-500' : 'text-gray-600'">
                      {{ attempt.user_agent }}
                    </p>
                  </div>
                </div>
              </div>
              
              <div v-else class="font-mono text-sm" :class="isDark() ? 'text-red-400' : 'text-red-700'">
                {{ attempt.raw || JSON.stringify(attempt) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <ToastNotification 
      :visible="toast.show"
      :message="toast.message" 
      :type="toast.type"
      :duration="5000"
      @close="toast.show = false"
    />

    <div 
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black bg-opacity-50 z-[9998] flex items-center justify-center"
      @click="closeDeleteModal"
      style="backdrop-filter: blur(4px);"
    >
      <div 
        class="max-w-md w-full mx-4 p-6 rounded-2xl shadow-2xl"
        :class="isDark() ? 'bg-gray-800 border border-gray-700' : 'bg-white'"
        @click.stop
      >
        <div class="text-center">
          <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full mb-4" :class="isDark() ? 'bg-red-900/20' : 'bg-red-100'">
            <AlertCircle :size="32" class="text-red-600" />
          </div>
          <h3 class="text-xl font-bold mb-2" :class="isDark() ? 'text-white' : 'text-gray-900'">
            ¿Eliminar IP de la Whitelist?
          </h3>
          <p class="text-sm mb-1" :class="isDark() ? 'text-gray-400' : 'text-gray-600'">
            Estás a punto de eliminar la siguiente IP:
          </p>
          <p class="font-mono text-lg font-bold mb-4" :class="isDark() ? 'text-red-400' : 'text-red-600'">
            {{ ipToDelete }}
          </p>
          <p class="text-sm mb-6" :class="isDark() ? 'text-gray-400' : 'text-gray-600'">
            Esta acción bloqueará el acceso desde esta dirección IP.
          </p>
          <div class="flex gap-3">
            <button
              @click="closeDeleteModal"
              :disabled="loading"
              class="flex-1 px-4 py-2 rounded-lg font-medium transition-all"
              :class="isDark() ? 
                'bg-gray-700 hover:bg-gray-600 text-white' : 
                'bg-gray-200 hover:bg-gray-300 text-gray-900'"
            >
              Cancelar
            </button>
            <button
              @click="confirmDelete"
              :disabled="loading"
              class="flex-1 px-4 py-2 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              :class="isDark() ? 
                'bg-red-600 hover:bg-red-700 text-white' : 
                'bg-red-500 hover:bg-red-600 text-white'"
            >
              <Trash2 :size="18" />
              {{ loading ? 'Eliminando...' : 'Eliminar' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div 
      v-if="showIntrusionAlert"
      class="fixed inset-0 bg-black bg-opacity-70 z-[9999] flex items-center justify-center"
      @click="showIntrusionAlert = false"
      style="backdrop-filter: blur(4px);"
    >
      <div 
        class="max-w-lg w-full mx-4 p-8 rounded-2xl border-4 border-red-500 shadow-2xl relative"
        :class="isDark() ? 'bg-red-900' : 'bg-red-100'"
        @click.stop
        style="animation: pulse-border 1s infinite;"
      >
        <div class="text-center">
          <div class="flex justify-center mb-4" style="animation: bounce 1s infinite;">
            <ShieldAlert :size="64" class="text-red-600" />
          </div>
          <h2 class="text-3xl font-bold mb-4" :class="isDark() ? 'text-white' : 'text-red-900'">
            ¡ALERTA DE INTRUSO!
          </h2>
          <div v-if="lastBlockedAttempt" class="space-y-2 text-lg" :class="isDark() ? 'text-red-200' : 'text-red-800'">
            <p class="font-bold">IP: {{ lastBlockedAttempt.ip }}</p>
            <p>Fabricante: {{ lastBlockedAttempt.vendor }}</p>
            <p>MAC: {{ lastBlockedAttempt.mac }}</p>
            <p class="text-sm">{{ formatTimestamp(lastBlockedAttempt.timestamp) }}</p>
          </div>
          <button
            @click="showIntrusionAlert = false"
            class="mt-6 px-6 py-3 rounded-lg font-bold transition-all"
            :class="isDark() ? 
              'bg-white text-red-900 hover:bg-red-100' : 
              'bg-red-600 text-white hover:bg-red-700'"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes pulse-border {
  0%, 100% {
    border-color: rgb(239, 68, 68);
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
  }
  50% {
    border-color: rgb(220, 38, 38);
    box-shadow: 0 0 40px rgba(239, 68, 68, 0.8);
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}
.intrusion-alert-enter-active,
.intrusion-alert-leave-active {
  transition: all 0.3s ease;
}

.intrusion-alert-enter-from {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.5);
}

.intrusion-alert-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.5);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useTheme } from '@/composables/useTheme'
import ToastNotification from './ToastNotification.vue'
import { 
  Lock, 
  ArrowLeft, 
  CircleCheck, 
  AlertTriangle, 
  Plus, 
  List, 
  Globe, 
  Trash2, 
  ShieldAlert, 
  RefreshCw,
  Clock,
  Monitor,
  Factory,
  Route,
  User,
  AlertCircle
} from 'lucide-vue-next'

const { isDark } = useTheme()

const API_URL = 'http://192.168.0.10:8000'
const WS_URL = 'ws://192.168.0.10:8000'

let ws = null

const whitelistInfo = ref({
  enabled: false,
  ips: [],
  ips_metadata: [],
  total: 0,
  is_admin: false,
  admin_ips: []
})

const logs = ref({
  total_lines: 0,
  total_blocked: 0,
  showing: 0,
  attempts: []
})

const newIP = ref('')
const loading = ref(false)
const showIntrusionAlert = ref(false)
const lastBlockedAttempt = ref(null)
const showDeleteModal = ref(false)
const ipToDelete = ref('')

const toast = ref({
  show: false,
  message: '',
  type: 'success'
})

const formatTimestamp = (timestamp) => {
  if (!timestamp || timestamp === 'N/A') return 'N/A'
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return timestamp
  }
}

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 5000) 
}

const loadWhitelist = async () => {
  try {
    const response = await fetch(`${API_URL}/api/whitelist`)
    const data = await response.json()
    console.log('Datos de whitelist recibidos:', data)
    console.log('is_admin:', data.is_admin)
    console.log('admin_ips:', data.admin_ips)
    whitelistInfo.value = data
  } catch (error) {
    console.error('Error loading whitelist:', error)
    showToast('Error al cargar la whitelist', 'error')
  }
}

const loadLogs = async () => {
  try {
    const response = await fetch(`${API_URL}/api/whitelist/logs`)
    const data = await response.json()
    logs.value = data
  } catch (error) {
    console.error('Error loading logs:', error)
    showToast('Error al cargar los logs', 'error')
  }
}

const addIP = async () => {
  if (!newIP.value) return
  
  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/whitelist/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ip: newIP.value })
    })
    
    const data = await response.json()
    
    if (response.ok) {
      showToast(data.message, 'success')
      newIP.value = ''
      await loadWhitelist()
    } else {
      showToast(data.detail || 'Error al agregar IP', 'error')
    }
  } catch (error) {
    console.error('Error adding IP:', error)
    showToast('Error al agregar IP', 'error')
  } finally {
    loading.value = false
  }
}

const openDeleteModal = (ip) => {
  ipToDelete.value = ip
  showDeleteModal.value = true
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  ipToDelete.value = ''
}

const confirmDelete = async () => {
  if (!ipToDelete.value) return
  
  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/whitelist/remove/${ipToDelete.value}`, {
      method: 'DELETE'
    })
    
    const data = await response.json()
    
    if (response.ok) {
      showToast(data.message, 'success')
      await loadWhitelist()
      closeDeleteModal()
    } else {
      showToast(data.detail || 'Error al eliminar IP', 'error')
    }
  } catch (error) {
    console.error('Error removing IP:', error)
    showToast('Error al eliminar IP', 'error')
  } finally {
    loading.value = false
  }
}

const connectWebSocket = () => {
  try {
    ws = new WebSocket(`${WS_URL}/ws/whitelist`)
    
    ws.onopen = () => {
      console.log('WebSocket conectado para monitoreo de whitelist')
    }
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        
        if (message.type === 'blocked_access') {
          const attempt = message.data?.attempt
          
          
          if (!attempt) {
            console.warn('Mensaje sin datos de intento:', message)
            return
          }
          
          if (!logs.value.attempts) {
            logs.value.attempts = []
          }
          logs.value.attempts.unshift(attempt)
          logs.value.total_blocked = (logs.value.total_blocked || 0) + 1
          logs.value.showing = Math.min((logs.value.showing || 0) + 1, 50)
          
          if (logs.value.attempts.length > 50) {
            logs.value.attempts.pop()
          }
          
          
          lastBlockedAttempt.value = attempt
          showIntrusionAlert.value = true
          
          
          setTimeout(() => {
            showIntrusionAlert.value = false
          }, 10000)
          
          try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)()
            const oscillator = audioContext.createOscillator()
            const gainNode = audioContext.createGain()
            
            oscillator.connect(gainNode)
            gainNode.connect(audioContext.destination)
            
            oscillator.frequency.value = 800
            oscillator.type = 'square'
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)
            
            oscillator.start(audioContext.currentTime)
            oscillator.stop(audioContext.currentTime + 0.5)
          } catch (e) {
            console.log('Audio no disponible')
          }
          
          showToast(
            `¡ALERTA DE INTRUSO! IP: ${attempt.ip} - ${attempt.vendor || 'Desconocido'}`,
            'error'
          )
        }
      } catch (error) {
        console.error('Error procesando mensaje WebSocket:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.error('Error en WebSocket:', error)
    }
    
    ws.onclose = () => {
      console.log('WebSocket desconectado, reconectando en 5s...')
      setTimeout(connectWebSocket, 5000)
    }
  } catch (error) {
    console.error('Error conectando WebSocket:', error)
    setTimeout(connectWebSocket, 5000)
  }
}

onMounted(() => {
  loadWhitelist()
  loadLogs()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>
