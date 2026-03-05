<script setup>
import { ref, onMounted, watch } from 'vue'
import { scannerAPI } from '../api/scanner'
import { useTheme } from '../composables/useTheme'
import { usePermissions } from '../composables/usePermissions'
import { useToast } from '../composables/useToast'
import { X, Scan, Power, Tag, Monitor, Cpu, Wifi, Server, Edit3, Check, Loader2 } from 'lucide-vue-next'
import DeviceIcon from './DeviceIcon.vue'
import OSIcon from './OSIcon.vue'

const props = defineProps({
  device: { type: Object, required: true },
  subnetId: { type: Number, required: true },
  deviceTypes: { type: Array, required: true },
})
const emit = defineEmits(['close', 'updated'])

const { isDark } = useTheme()
const { canExecuteScans } = usePermissions()
const toast = useToast()

const deviceInfo = ref(null)
const loadingInfo = ref(false)
const scanningDevice = ref(false)
const shuttingDown = ref(false)
const editingLabel = ref(false)
const newLabel = ref(props.device.label || '')
const showShutdownForm = ref(false)
const sshUser = ref('')
const sshPass = ref('')
const changingType = ref(false)
const selectedType = ref(props.device.device_type)

onMounted(() => {
  fetchDeviceInfo()
})

const fetchDeviceInfo = async () => {
  loadingInfo.value = true
  try {
    const data = await scannerAPI.getDeviceInfo(props.subnetId, props.device.id)
    if (data.data) {
      deviceInfo.value = data.data
    }
  } catch (e) {
    // No info available
  } finally {
    loadingInfo.value = false
  }
}

const scanDevice = async () => {
  scanningDevice.value = true
  try {
    const data = await scannerAPI.scanDevice(props.subnetId, props.device.id)
    deviceInfo.value = data.data
    toast.success('Escaneo completado')
  } catch (e) {
    toast.error('Error escaneando dispositivo')
  } finally {
    scanningDevice.value = false
  }
}

const shutdownDevice = async () => {
  if (!sshUser.value || !sshPass.value) {
    toast.error('Ingrese credenciales SSH')
    return
  }
  shuttingDown.value = true
  try {
    const result = await scannerAPI.shutdownDevice(props.subnetId, props.device.id, sshUser.value, sshPass.value)
    if (result.success) {
      toast.success(`${props.device.ip} apagado exitosamente`)
      emit('updated', { ...props.device, status: 'red' })
      showShutdownForm.value = false
    } else {
      toast.error(result.error || 'Error al apagar')
    }
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Error al apagar')
  } finally {
    shuttingDown.value = false
  }
}

const saveLabel = async () => {
  if (!newLabel.value.trim()) return
  try {
    const result = await scannerAPI.updateDeviceLabel(props.subnetId, props.device.id, newLabel.value.trim())
    emit('updated', result)
    editingLabel.value = false
    toast.success('Etiqueta actualizada')
  } catch {
    toast.error('Error actualizando etiqueta')
  }
}

const changeDeviceType = async (type) => {
  changingType.value = true
  try {
    const result = await scannerAPI.updateDeviceType(props.subnetId, props.device.id, type)
    selectedType.value = type
    emit('updated', result)
    toast.success('Tipo de dispositivo actualizado')
  } catch {
    toast.error('Error actualizando tipo')
  } finally {
    changingType.value = false
  }
}
</script>

<template>
  <!-- Overlay -->
  <div class="fixed inset-0 z-50 flex justify-end" @click.self="emit('close')">
    <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="emit('close')"></div>
    
    <!-- Panel -->
    <div 
      class="relative w-full max-w-lg h-full overflow-y-auto shadow-2xl"
      :class="isDark() ? 'bg-slate-950 border-l border-slate-700/50' : 'bg-white border-l border-slate-200'"
    >
      <!-- Header -->
      <div 
        class="sticky top-0 z-10 p-6 border-b"
        :class="isDark() ? 'bg-slate-950/95 backdrop-blur border-slate-700/50' : 'bg-white/95 backdrop-blur border-slate-200'"
      >
        <div class="flex items-center justify-between mb-4">
          <button
            @click="emit('close')"
            class="w-9 h-9 rounded-lg flex items-center justify-center transition-colors"
            :class="isDark() ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="flex items-center gap-4">
          <div 
            class="w-16 h-16 rounded-2xl flex items-center justify-center"
            :class="device.status === 'green' ? 'bg-emerald-500/10 border-2 border-emerald-500/30' : device.status === 'red' ? 'bg-red-500/10 border-2 border-red-500/30' : (isDark() ? 'bg-slate-800 border-2 border-slate-600' : 'bg-slate-100 border-2 border-slate-300')"
          >
            <DeviceIcon :type="selectedType" :status="device.status" :size="36" />
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <template v-if="editingLabel">
                <input 
                  v-model="newLabel"
                  @keyup.enter="saveLabel"
                  class="text-lg font-bold px-2 py-1 rounded-lg w-full"
                  :class="isDark() ? 'bg-slate-800 text-white border border-slate-600' : 'bg-slate-100 text-slate-800 border border-slate-300'"
                  autofocus
                />
                <button @click="saveLabel" class="text-emerald-400 hover:text-emerald-300">
                  <Check class="w-5 h-5" />
                </button>
              </template>
              <template v-else>
                <h3 class="text-lg font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">
                  {{ device.label }}
                </h3>
                <button v-if="canExecuteScans" @click="editingLabel = true; newLabel = device.label" 
                  class="opacity-50 hover:opacity-100 transition-opacity"
                  :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
                >
                  <Edit3 class="w-3.5 h-3.5" />
                </button>
              </template>
            </div>
            <p class="font-mono text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">{{ device.ip }}</p>
            <div class="flex items-center gap-1.5 mt-1">
              <span class="w-2 h-2 rounded-full" :class="device.status === 'green' ? 'bg-emerald-400' : device.status === 'red' ? 'bg-red-400' : 'bg-slate-400'"></span>
              <span class="text-xs font-semibold"
                :class="device.status === 'green' ? 'text-emerald-400' : device.status === 'red' ? 'text-red-400' : (isDark() ? 'text-slate-500' : 'text-slate-400')"
              >
                {{ device.status === 'green' ? 'Activo' : device.status === 'red' ? 'Inactivo' : 'Sin escanear' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="p-6 space-y-6">
        <!-- Device type selector -->
        <div>
          <h4 class="text-sm font-semibold uppercase tracking-wide mb-3" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
            <Tag class="w-4 h-4 inline mr-1" />
            Tipo de dispositivo
          </h4>
          <div class="grid grid-cols-5 gap-2">
            <button
              v-for="dt in deviceTypes"
              :key="dt.value"
              @click="changeDeviceType(dt.value)"
              :disabled="changingType"
              class="flex flex-col items-center gap-1 p-2.5 rounded-xl transition-all text-center"
              :class="[
                selectedType === dt.value 
                  ? 'bg-violet-500/20 border-2 border-violet-500/50 shadow-lg shadow-violet-500/10' 
                  : (isDark() ? 'bg-slate-800/50 border border-slate-700/40 hover:border-violet-500/30' : 'bg-slate-50 border border-slate-200 hover:border-violet-400'),
                changingType ? 'opacity-50' : ''
              ]"
            >
              <DeviceIcon :type="dt.value" :status="device.status" :size="22" />
              <span class="text-[9px] font-semibold uppercase" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">{{ dt.label }}</span>
            </button>
          </div>
        </div>

        <!-- Action buttons -->
        <div class="space-y-3" v-if="canExecuteScans">
          <button
            @click="scanDevice"
            :disabled="scanningDevice"
            class="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl font-bold text-sm transition-all shadow-lg bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white border-2 border-violet-400/50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Loader2 v-if="scanningDevice" class="w-5 h-5 animate-spin" />
            <Scan v-else class="w-5 h-5" />
            {{ scanningDevice ? 'Escaneando...' : 'Escanear dispositivo' }}
          </button>

          <button
            @click="showShutdownForm = !showShutdownForm"
            class="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl font-bold text-sm transition-all shadow-lg border-2"
            :class="showShutdownForm 
              ? (isDark() ? 'bg-slate-800 text-slate-300 border-slate-600' : 'bg-slate-200 text-slate-600 border-slate-300')
              : 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white border-red-400/50'"
          >
            <Power class="w-5 h-5" />
            {{ showShutdownForm ? 'Cancelar' : 'Apagar dispositivo' }}
          </button>
        </div>

        <!-- Shutdown form -->
        <Transition name="fade">
          <div v-if="showShutdownForm" 
            class="rounded-2xl p-4 space-y-3"
            :class="isDark() ? 'bg-red-900/20 border border-red-500/30' : 'bg-red-50 border border-red-300'"
          >
            <p class="text-xs font-semibold" :class="isDark() ? 'text-red-300' : 'text-red-700'">Credenciales SSH para apagar</p>
            <input
              v-model="sshUser"
              type="text"
              placeholder="Usuario SSH"
              class="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/60"
              :class="isDark() ? 'bg-slate-900 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
            />
            <input
              v-model="sshPass"
              type="password"
              placeholder="Contraseña SSH"
              class="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/60"
              :class="isDark() ? 'bg-slate-900 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
            />
            <button
              @click="shutdownDevice"
              :disabled="shuttingDown"
              class="w-full py-3 rounded-xl font-bold text-sm bg-red-600 hover:bg-red-500 text-white transition-colors disabled:opacity-50"
            >
              {{ shuttingDown ? 'Apagando...' : 'Confirmar apagado' }}
            </button>
          </div>
        </Transition>

        <!-- Device info -->
        <div>
          <h4 class="text-sm font-semibold uppercase tracking-wide mb-3" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
            <Cpu class="w-4 h-4 inline mr-1" />
            Información del dispositivo
          </h4>

          <div v-if="loadingInfo" class="flex items-center justify-center py-8">
            <div class="w-8 h-8 border-3 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
          </div>

          <div v-else-if="scanningDevice" class="text-center py-8">
            <Loader2 class="w-10 h-10 mx-auto mb-2 text-violet-400 animate-spin" />
            <p class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Escaneando dispositivo...</p>
            <p class="text-xs mt-1" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Obteniendo MAC, puertos, servicios y OS</p>
          </div>

          <div v-else-if="deviceInfo" class="space-y-4">
            <!-- MAC / Vendor -->
            <div 
              class="rounded-xl p-4"
              :class="isDark() ? 'bg-slate-800/50 border border-slate-700/40' : 'bg-slate-50 border border-slate-200'"
            >
              <div class="flex items-center gap-2 mb-2">
                <Wifi class="w-4 h-4 text-violet-400" />
                <span class="text-xs font-semibold uppercase tracking-wide" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">MAC / Fabricante</span>
              </div>
              <p class="font-mono text-sm" :class="isDark() ? 'text-white' : 'text-slate-800'">
                {{ deviceInfo.mac || 'No detectada' }}
              </p>
              <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                {{ deviceInfo.vendor || 'Fabricante desconocido' }}
              </p>
            </div>

            <!-- OS -->
            <div v-if="deviceInfo.os_name"
              class="rounded-xl p-4"
              :class="isDark() ? 'bg-slate-800/50 border border-slate-700/40' : 'bg-slate-50 border border-slate-200'"
            >
              <div class="flex items-center gap-2 mb-2">
                <Monitor class="w-4 h-4 text-violet-400" />
                <span class="text-xs font-semibold uppercase tracking-wide" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">Sistema Operativo</span>
              </div>
              <div class="flex items-center gap-3">
                <OSIcon :name="deviceInfo.os_name" :size="28" />
                <div>
                  <p class="font-semibold text-sm" :class="isDark() ? 'text-white' : 'text-slate-800'">{{ deviceInfo.os_name }}</p>
                  <p v-if="deviceInfo.os_accuracy" class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                    Confianza: {{ deviceInfo.os_accuracy }}%
                  </p>
                </div>
              </div>
            </div>

            <!-- Ports -->
            <div v-if="deviceInfo.ports && deviceInfo.ports.length > 0"
              class="rounded-xl p-4"
              :class="isDark() ? 'bg-slate-800/50 border border-slate-700/40' : 'bg-slate-50 border border-slate-200'"
            >
              <div class="flex items-center gap-2 mb-2">
                <Server class="w-4 h-4 text-violet-400" />
                <span class="text-xs font-semibold uppercase tracking-wide" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
                  Puertos abiertos ({{ deviceInfo.ports.length }})
                </span>
              </div>
              <div class="space-y-1.5 max-h-48 overflow-y-auto">
                <div v-for="(port, i) in deviceInfo.ports" :key="i"
                  class="flex items-center justify-between py-1.5 px-3 rounded-lg text-xs"
                  :class="isDark() ? 'bg-slate-900/60' : 'bg-white'"
                >
                  <span class="font-mono font-bold" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">
                    {{ port.port }}/{{ port.protocol || 'tcp' }}
                  </span>
                  <span :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                    {{ port.service || port.state || '' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Services -->
            <div v-if="deviceInfo.services && deviceInfo.services.length > 0"
              class="rounded-xl p-4"
              :class="isDark() ? 'bg-slate-800/50 border border-slate-700/40' : 'bg-slate-50 border border-slate-200'"
            >
              <div class="flex items-center gap-2 mb-2">
                <Server class="w-4 h-4 text-indigo-400" />
                <span class="text-xs font-semibold uppercase tracking-wide" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
                  Servicios ({{ deviceInfo.services.length }})
                </span>
              </div>
              <div class="space-y-1.5 max-h-48 overflow-y-auto">
                <div v-for="(svc, i) in deviceInfo.services" :key="i"
                  class="flex items-center justify-between py-1.5 px-3 rounded-lg text-xs"
                  :class="isDark() ? 'bg-slate-900/60' : 'bg-white'"
                >
                  <span class="font-mono font-bold" :class="isDark() ? 'text-indigo-400' : 'text-indigo-600'">
                    {{ svc.port }}/{{ svc.protocol || 'tcp' }}
                  </span>
                  <span :class="isDark() ? 'text-slate-300' : 'text-slate-600'">
                    {{ svc.service || svc.service_name || '' }}
                    <span v-if="svc.product" class="text-slate-500"> — {{ svc.product }} {{ svc.version || '' }}</span>
                  </span>
                </div>
              </div>
            </div>

            <!-- Source badge -->
            <div class="text-center">
              <span class="inline-block text-[10px] px-3 py-1 rounded-full font-semibold uppercase tracking-wider"
                :class="deviceInfo.source === 'database' 
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : deviceInfo.source === 'cache'
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    : 'bg-violet-500/10 text-violet-400 border border-violet-500/30'"
              >
                Fuente: {{ deviceInfo.source === 'database' ? 'Base de datos' : deviceInfo.source === 'cache' ? 'Caché' : 'Escaneo en vivo' }}
              </span>
            </div>
          </div>

          <!-- No info available -->
          <div v-else class="text-center py-8 rounded-xl" :class="isDark() ? 'bg-slate-800/30' : 'bg-slate-50'">
            <Scan class="w-10 h-10 mx-auto mb-2" :class="isDark() ? 'text-slate-600' : 'text-slate-400'" />
            <p class="text-sm font-semibold" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Sin información disponible</p>
            <p class="text-xs mt-1" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
              Presiona "Escanear dispositivo" para obtener datos
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
