<script setup>
import { ref, onMounted, computed } from 'vue'
import { scannerAPI } from '../api/scanner'
import { useTheme } from '../composables/useTheme'
import { usePermissions } from '../composables/usePermissions'
import { useToast } from '../composables/useToast'
import { useScanState } from '../composables/useScanState'
import { useScanProgress } from '../composables/useScanProgress'
import { ArrowLeft, Radar, RefreshCw, Settings, Power, Key, FolderOpen, Save, Trash2 } from 'lucide-vue-next'
import DeviceIcon from './DeviceIcon.vue'
import DeviceInfoPanel from './DeviceInfoPanel.vue'

const props = defineProps({
  subnetId: { type: Number, required: true }
})
const emit = defineEmits(['back'])

const { isDark } = useTheme()
const { canExecuteScans } = usePermissions()
const toast = useToast()
const { isScanning, startScan, endScan } = useScanState()
const { scanProgress, setupProgressListener } = useScanProgress()

const subnet = ref(null)
const devices = ref([])
const loading = ref(false)
const scanning = ref(false)
const selectedDevice = ref(null)
const showDevicePanel = ref(false)
const showShutdownForm = ref(false)
const showManualCreds = ref(false)
const shuttingDown = ref(false)
const shutdownUser = ref('')
const shutdownPass = ref('')
const savedCredentials = ref([])
const selectedCredentialId = ref(null)
let abortController = null

onMounted(() => {
  setupProgressListener()
  fetchSubnet()
  loadSavedCredentials()
})

const loadSavedCredentials = async () => {
  try {
    savedCredentials.value = await scannerAPI.getSSHCredentials()
  } catch { /* ignore */ }
}

const fetchSubnet = async () => {
  loading.value = true
  try {
    const data = await scannerAPI.getSubnet(props.subnetId)
    subnet.value = data
    devices.value = data.devices || []
  } catch (e) {
    toast.error('Error cargando subred')
  } finally {
    loading.value = false
  }
}

const scanSubnet = async () => {
  scanning.value = true
  startScan('subnet-scan')
  abortController = new AbortController()
  try {
    const data = await scannerAPI.scanSubnet(props.subnetId, abortController.signal)
    devices.value = data.devices || []
    toast.success(`Scan completado: ${data.active_count}/${data.total} activos`)
  } catch (e) {
    if (e.name !== 'CanceledError' && e.code !== 'ERR_CANCELED') {
      toast.error('Error escaneando subred')
    }
  } finally {
    scanning.value = false
    endScan()
    abortController = null
  }
}

const openDevicePanel = (device) => {
  selectedDevice.value = device
  showDevicePanel.value = true
}

const shutdownWithCredential = async (credId) => {
  selectedCredentialId.value = credId
  shuttingDown.value = true
  try {
    const cred = await scannerAPI.getSSHCredential(credId)
    const data = await scannerAPI.shutdownLab(props.subnetId, cred.username, cred.password)
    if (data.total === 0) {
      toast.warning('No hay dispositivos activos para apagar')
    } else {
      toast.success(`Apagado: ${data.success_count}/${data.total} exitosos`)
    }
    showShutdownForm.value = false
    await fetchSubnet()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Error apagando laboratorio')
  } finally {
    shuttingDown.value = false
    selectedCredentialId.value = null
  }
}

const shutdownLabManual = async () => {
  if (!shutdownUser.value.trim() || !shutdownPass.value.trim()) {
    toast.error('Ingrese usuario y contraseña SSH')
    return
  }
  shuttingDown.value = true
  try {
    const data = await scannerAPI.shutdownLab(props.subnetId, shutdownUser.value.trim(), shutdownPass.value.trim())
    if (data.total === 0) {
      toast.warning('No hay dispositivos activos para apagar')
    } else {
      toast.success(`Apagado: ${data.success_count}/${data.total} exitosos`)
    }
    showShutdownForm.value = false
    shutdownUser.value = ''
    shutdownPass.value = ''
    await fetchSubnet()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Error apagando laboratorio')
  } finally {
    shuttingDown.value = false
  }
}

const closeDevicePanel = () => {
  showDevicePanel.value = false
  selectedDevice.value = null
}

const onDeviceUpdated = (updatedDevice) => {
  const idx = devices.value.findIndex(d => d.id === updatedDevice.id)
  if (idx !== -1) {
    devices.value[idx] = { ...devices.value[idx], ...updatedDevice }
  }
}

const stats = computed(() => {
  const green = devices.value.filter(d => d.status === 'green').length
  const red = devices.value.filter(d => d.status === 'red').length
  const grey = devices.value.filter(d => d.status === 'grey').length
  return { green, red, grey, total: devices.value.length }
})

const DEVICE_TYPES = [
  { value: 'pc', label: 'PC' },
  { value: 'laptop', label: 'Laptop' },
  { value: 'phone', label: 'Teléfono' },
  { value: 'printer', label: 'Impresora' },
  { value: 'server', label: 'Servidor' },
  { value: 'router', label: 'Router' },
  { value: 'switch', label: 'Switch' },
  { value: 'tablet', label: 'Tablet' },
  { value: 'camera', label: 'Cámara' },
  { value: 'unknown', label: 'Desconocido' },
]

const getStatusRing = (status) => {
  if (status === 'green') return 'ring-2 ring-emerald-400/60 shadow-emerald-500/30'
  if (status === 'red') return 'ring-2 ring-red-400/60 shadow-red-500/30'
  return 'ring-1 ring-slate-500/30'
}

const getStatusLabel = (status) => {
  if (status === 'green') return 'Activo'
  if (status === 'red') return 'Inactivo'
  return 'Sin escanear'
}

const getStatusDot = (status) => {
  if (status === 'green') return 'bg-emerald-400'
  if (status === 'red') return 'bg-red-400'
  return 'bg-slate-400'
}
</script>

<template>
  <div class="space-y-5">
    <!-- Top bar -->
    <div class="flex items-center justify-between">
      <button
        @click="emit('back')"
        class="flex items-center gap-2 px-3 py-2 rounded-xl font-semibold text-sm transition-all"
        :class="isDark() ? 'text-slate-300 hover:bg-slate-800' : 'text-slate-600 hover:bg-slate-100'"
      >
        <ArrowLeft class="w-4 h-4" />
        Volver
      </button>

      <div class="flex items-center gap-2">
        <button
          v-if="canExecuteScans"
          @click="showShutdownForm = !showShutdownForm"
          :disabled="shuttingDown || stats.green === 0"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs transition-all duration-300 shadow-md bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white shadow-red-500/15 border border-red-400/40 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Power class="w-4 h-4" />
          {{ shuttingDown ? 'Apagando...' : 'Apagar Lab' }}
        </button>

        <button
          v-if="canExecuteScans"
          @click="scanSubnet"
          :disabled="scanning || isScanning"
          class="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all duration-300 shadow-md bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-violet-500/15 border border-violet-400/40 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': scanning }" />
          {{ scanning ? 'Escaneando...' : 'Escanear' }}
        </button>
      </div>
    </div>

    <!-- Shutdown credentials panel -->
    <Transition name="fade-slide">
      <div 
        v-if="showShutdownForm"
        class="rounded-xl p-4 shadow-lg space-y-3"
        :class="isDark() ? 'bg-red-950/20 border border-red-500/25' : 'bg-red-50 border border-red-300'"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Power class="w-4 h-4 text-red-400" />
            <h3 class="text-sm font-bold" :class="isDark() ? 'text-red-300' : 'text-red-700'">
              Apagar laboratorio
            </h3>
            <span class="text-xs px-2 py-0.5 rounded-full" :class="isDark() ? 'bg-red-500/20 text-red-300' : 'bg-red-100 text-red-600'">
              {{ stats.green }} activos
            </span>
          </div>
          <button
            @click="showShutdownForm = false; showManualCreds = false"
            class="p-1 rounded-lg transition-colors"
            :class="isDark() ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-200' : 'text-slate-500 hover:bg-slate-200 hover:text-slate-700'"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <!-- Saved credentials as action buttons -->
        <div v-if="savedCredentials.length > 0" class="space-y-2">
          <p class="text-xs font-semibold" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
            Selecciona una credencial para apagar:
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="cred in savedCredentials"
              :key="cred.id"
              @click="shutdownWithCredential(cred.id)"
              :disabled="shuttingDown"
              class="group flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 border shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              :class="[
                shuttingDown && selectedCredentialId === cred.id
                  ? (isDark() ? 'bg-red-500/20 border-red-500/50 text-red-300' : 'bg-red-100 border-red-400 text-red-700')
                  : (isDark() ? 'bg-slate-800/60 border-slate-600 text-slate-200 hover:bg-red-500/15 hover:border-red-500/40 hover:text-red-300' : 'bg-white border-slate-300 text-slate-700 hover:bg-red-50 hover:border-red-400 hover:text-red-600')
              ]"
            >
              <Power v-if="shuttingDown && selectedCredentialId === cred.id" class="w-4 h-4 animate-pulse" />
              <Key v-else class="w-4 h-4 opacity-50 group-hover:opacity-100" />
              <span>{{ cred.name }}</span>
              <span class="text-xs opacity-50">({{ cred.username }})</span>
            </button>
          </div>
        </div>

        <div v-else class="text-center py-2">
          <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
            No hay credenciales guardadas. Ingresa manualmente.
          </p>
        </div>

        <!-- Divider + manual fallback -->
        <div class="flex items-center gap-3">
          <div class="flex-1 h-px" :class="isDark() ? 'bg-slate-700/50' : 'bg-slate-300'"></div>
          <button
            @click="showManualCreds = !showManualCreds"
            class="text-[11px] font-semibold px-2 py-0.5 rounded transition-colors"
            :class="isDark() ? 'text-slate-500 hover:text-slate-300' : 'text-slate-400 hover:text-slate-600'"
          >
            {{ showManualCreds ? 'Ocultar manual' : 'Ingresar manualmente' }}
          </button>
          <div class="flex-1 h-px" :class="isDark() ? 'bg-slate-700/50' : 'bg-slate-300'"></div>
        </div>

        <!-- Manual credentials (hidden by default) -->
        <Transition name="fade-slide">
          <div v-if="showManualCreds" class="space-y-3">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input
                v-model="shutdownUser"
                type="text"
                placeholder="Usuario SSH"
                class="rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/60 transition-all"
                :class="isDark() ? 'bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              />
              <input
                v-model="shutdownPass"
                type="password"
                placeholder="Contraseña SSH"
                class="rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/60 transition-all"
                :class="isDark() ? 'bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              />
            </div>
            <button
              @click="shutdownLabManual"
              :disabled="shuttingDown || !shutdownUser.trim() || !shutdownPass.trim()"
              class="flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-xs transition-all bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white shadow-md shadow-red-500/15 border border-red-400/40 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Power class="w-3.5 h-3.5" :class="{ 'animate-pulse': shuttingDown }" />
              {{ shuttingDown ? 'Apagando...' : 'Apagar con estas credenciales' }}
            </button>
          </div>
        </Transition>
      </div>
    </Transition>

    <!-- Header -->
    <div v-if="subnet" 
      class="relative rounded-2xl p-5 shadow-xl overflow-hidden"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-extrabold" :class="isDark() ? 'text-white' : 'text-slate-800'">
            {{ subnet.name }}
          </h2>
          <p class="text-xs font-mono mt-0.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
            {{ subnet.start_ip }} — {{ subnet.end_ip }}
          </p>
        </div>
        <div class="flex items-center gap-5">
          <div class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span class="text-lg font-bold text-emerald-400">{{ stats.green }}</span>
            <span class="text-[10px] uppercase tracking-wider" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Activos</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-red-400"></span>
            <span class="text-lg font-bold text-red-400">{{ stats.red }}</span>
            <span class="text-[10px] uppercase tracking-wider" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Inactivos</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full" :class="isDark() ? 'bg-slate-500' : 'bg-slate-400'"></span>
            <span class="text-lg font-bold" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">{{ stats.grey }}</span>
            <span class="text-[10px] uppercase tracking-wider" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Pendientes</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Scan progress -->
    <Transition name="fade-slide">
      <div v-if="scanning" 
        class="rounded-xl p-3 shadow-md"
        :class="isDark() ? 'bg-violet-900/15 border border-violet-500/25' : 'bg-violet-50 border border-violet-300'"
      >
        <div class="flex items-center gap-2.5">
          <Radar class="w-4 h-4 text-violet-400 animate-pulse" />
          <span class="text-xs font-semibold" :class="isDark() ? 'text-violet-300' : 'text-violet-700'">
            Escaneando {{ stats.total }} dispositivos...
          </span>
          <span v-if="scanProgress.total > 0" class="text-xs font-mono ml-auto" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
            {{ scanProgress.completed }}/{{ scanProgress.total }}
          </span>
        </div>
        <div v-if="scanProgress.total > 0" class="mt-2">
          <div class="relative h-1.5 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-800' : 'bg-slate-200'">
            <div 
              class="h-1.5 rounded-full bg-gradient-to-r from-violet-500 to-indigo-500 transition-all duration-300"
              :style="{ width: Math.round((scanProgress.completed / scanProgress.total) * 100) + '%' }"
            ></div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Device grid -->
    <div v-else-if="devices.length > 0"
      class="rounded-2xl p-5 shadow-xl"
      :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
    >
      <div class="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 gap-3">
        <div
          v-for="device in devices"
          :key="device.id"
          @click="openDevicePanel(device)"
          class="group flex flex-col items-center gap-1.5 p-3 rounded-xl cursor-pointer transition-all duration-200 hover:scale-[1.04] shadow-sm"
          :class="[
            isDark() 
              ? 'bg-slate-900/50 hover:bg-slate-800/70 border border-slate-700/30 hover:border-violet-500/40' 
              : 'bg-white hover:bg-slate-50 border border-slate-200 hover:border-violet-400/50',
            getStatusRing(device.status)
          ]"
        >
          <DeviceIcon 
            :type="device.device_type" 
            :status="device.status" 
            :size="32" 
            :stroke-width="1.5"
          />

          <p class="text-[11px] font-semibold text-center truncate w-full" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
            {{ device.label }}
          </p>

          <p class="text-[9px] font-mono text-center" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
            {{ device.ip }}
          </p>

          <div class="flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full" :class="getStatusDot(device.status)"></span>
            <span class="text-[8px] uppercase tracking-wide font-semibold"
              :class="device.status === 'green' ? 'text-emerald-400' : device.status === 'red' ? 'text-red-400' : (isDark() ? 'text-slate-500' : 'text-slate-400')"
            >
              {{ getStatusLabel(device.status) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Device info panel (modal overlay) -->
    <Transition name="slide-right">
      <DeviceInfoPanel
        v-if="showDevicePanel && selectedDevice"
        :device="selectedDevice"
        :subnetId="subnetId"
        :deviceTypes="DEVICE_TYPES"
        @close="closeDevicePanel"
        @updated="onDeviceUpdated"
      />
    </Transition>
  </div>
</template>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease;
}
.slide-right-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
