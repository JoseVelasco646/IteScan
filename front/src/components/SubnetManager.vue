<script setup>
import { ref, onMounted, computed } from 'vue'
import { scannerAPI } from '../api/scanner'
import { useTheme } from '../composables/useTheme'
import { usePermissions } from '../composables/usePermissions'
import { useToast } from '../composables/useToast'
import { useIPValidation } from '../composables/useIPValidation'
import { useButtonClasses } from '../composables/useButtonClasses'
import { Network, Plus, Trash2, ChevronRight, Map, Wifi, WifiOff, HelpCircle, AlertTriangle } from 'lucide-vue-next'
import SubnetLab from './SubnetLab.vue'
import { ipv4ToNumber } from '../utils/networkHosts'

const { isDark } = useTheme()
const { canExecuteScans } = usePermissions()
const toast = useToast()
const { isValidIPv4 } = useIPValidation()
const { btnPrimaryClass, btnSecondaryClass, btnCTAClass, btnDangerClass } = useButtonClasses()

const subnets = ref([])
const loading = ref(false)
const showCreateForm = ref(false)
const selectedSubnetId = ref(null)

// Delete confirmation
const confirmDelete = ref(null) // { id, name }

// Create form fields
const newName = ref('')
const newStartIp = ref('')
const newEndIp = ref('')
const creating = ref(false)

const fetchSubnets = async () => {
  loading.value = true
  try {
    subnets.value = await scannerAPI.getSubnets()
  } catch (e) {
    toast.error('Error cargando subredes')
  } finally {
    loading.value = false
  }
}

onMounted(fetchSubnets)

const validateIp = (ip) => {
  if (isValidIPv4(ip)) return null
  return `IP inválida: ${ip} (formato esperado x.x.x.x en rango 0-255)`
}

const createSubnet = async () => {
  if (!newName.value.trim() || !newStartIp.value.trim() || !newEndIp.value.trim()) {
    toast.error('Complete todos los campos')
    return
  }

  const startIp = newStartIp.value.trim()
  const endIp = newEndIp.value.trim()

  // Validate IPs format
  const startErr = validateIp(startIp)
  if (startErr) { toast.error(startErr, 'IP Inicio'); return }
  const endErr = validateIp(endIp)
  if (endErr) { toast.error(endErr, 'IP Fin'); return }

  // Validate range order
  if (ipv4ToNumber(endIp) < ipv4ToNumber(startIp)) {
    toast.error(`La IP final (${endIp}) no puede ser menor que la IP inicial (${startIp})`, 'Rango inválido')
    return
  }

  creating.value = true
  try {
    await scannerAPI.createSubnet(newName.value.trim(), startIp, endIp)
    toast.success(`Subred "${newName.value}" creada`)
    newName.value = ''
    newStartIp.value = ''
    newEndIp.value = ''
    showCreateForm.value = false
    await fetchSubnets()
  } catch (e) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      // Pydantic validation errors — show each one individually
      for (const err of detail) {
        const field = err.loc?.slice(-1)[0] || ''
        const fieldLabel = field === 'start_ip' ? 'IP Inicio' : field === 'end_ip' ? 'IP Fin' : field
        const msg = (err.msg || '').replace(/^Value error, ?/i, '')
        toast.error(msg || 'Error de validación', fieldLabel || 'Validación')
      }
    } else {
      toast.error(typeof detail === 'string' ? detail : 'Error creando subred')
    }
  } finally {
    creating.value = false
  }
}

const deleteSubnet = async (id, name) => {
  confirmDelete.value = { id, name }
}

const confirmDeleteAction = async () => {
  if (!confirmDelete.value) return
  const { id, name } = confirmDelete.value
  confirmDelete.value = null
  try {
    await scannerAPI.deleteSubnet(id)
    toast.success(`Subred "${name}" eliminada`)
    if (selectedSubnetId.value === id) selectedSubnetId.value = null
    await fetchSubnets()
  } catch (e) {
    toast.error('Error eliminando subred')
  }
}

const cancelDelete = () => {
  confirmDelete.value = null
}

const goBack = () => {
  selectedSubnetId.value = null
  fetchSubnets()
}
</script>

<template>
  <div class="space-y-3">
    <!-- If a subnet is selected, show detail view -->
    <SubnetLab v-if="selectedSubnetId" :subnetId="selectedSubnetId" @back="goBack" />

    <!-- Otherwise show subnet list -->
    <template v-else>
      <!-- Header -->
      <div 
        class="relative rounded-3xl p-6 shadow-2xl overflow-hidden"
        :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
      >
        <div class="absolute inset-0 opacity-5">
          <div class="absolute top-0 left-0 w-96 h-96 bg-violet-500 rounded-full blur-3xl"></div>
          <div class="absolute bottom-0 right-0 w-96 h-96 bg-indigo-500 rounded-full blur-3xl"></div>
        </div>
        <div class="relative z-10">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-violet-500/30">
              <Network class="w-7 h-7 text-white" />
            </div>
            <div>
              <h2 
                class="text-3xl font-extrabold mb-1 tracking-tight"
                :class="isDark() ? 'text-white' : 'text-slate-800'"
              >
                Subnet <span class="text-violet-400">Labs</span>
              </h2>
              <p 
                class="font-tagesschrift text-lg font-semibold tracking-wide"
                :class="isDark() ? 'text-gray-200' : 'text-slate-600'"
              >Gestión de subredes y laboratorios</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Create button -->
      <div v-if="canExecuteScans" class="flex justify-end">
        <button
          @click="showCreateForm = !showCreateForm"
          :class="[showCreateForm ? btnSecondaryClass : btnPrimaryClass, 'px-6', 'py-3', 'text-sm']"
        >
          <Plus class="w-5 h-5" />
          {{ showCreateForm ? 'Cancelar' : 'Nueva Subred' }}
        </button>
      </div>

      <!-- Create form -->
      <Transition name="fade-slide">
        <div 
          v-if="showCreateForm"
          class="rounded-3xl p-8 shadow-2xl space-y-5"
          :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
        >
          <h3 
            class="text-xl font-bold flex items-center gap-2"
            :class="isDark() ? 'text-white' : 'text-slate-800'"
          >
            <Map class="w-5 h-5 text-violet-400" />
            Crear nueva subred
          </h3>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide mb-2 block" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">Nombre</label>
              <input
                v-model="newName"
                type="text"
                placeholder="Laboratorio 1"
                class="w-full rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-violet-500/60 transition-all text-sm"
                :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide mb-2 block" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">IP Inicio</label>
              <input
                v-model="newStartIp"
                type="text"
                placeholder="10.4.10.1"
                class="w-full rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-violet-500/60 transition-all font-mono text-sm"
                :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide mb-2 block" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">IP Fin</label>
              <input
                v-model="newEndIp"
                type="text"
                placeholder="10.4.10.30"
                class="w-full rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-violet-500/60 transition-all font-mono text-sm"
                :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              />
            </div>
          </div>

          <button
            @click="createSubnet"
            :disabled="creating"
            :class="btnCTAClass"
          >
            <span class="flex items-center justify-center gap-2">
              <Plus class="w-5 h-5" />
              {{ creating ? 'Creando...' : 'Crear Subred' }}
            </span>
          </button>
        </div>
      </Transition>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-16">
        <div class="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <!-- Empty state -->
      <div 
        v-else-if="subnets.length === 0" 
        class="text-center py-16 rounded-3xl shadow-2xl"
        :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
      >
        <Network class="w-16 h-16 mx-auto mb-4" :class="isDark() ? 'text-slate-600' : 'text-slate-400'" />
        <p :class="isDark() ? 'text-slate-400' : 'text-slate-500'" class="text-lg font-semibold">No hay subredes configuradas</p>
        <p :class="isDark() ? 'text-slate-500' : 'text-slate-400'" class="text-sm mt-1">Crea una subred para comenzar a monitorear tus laboratorios</p>
      </div>

      <!-- Subnet cards grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <div
          v-for="subnet in subnets"
          :key="subnet.id"
          class="group relative rounded-3xl p-6 shadow-xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl overflow-hidden"
          :class="isDark() 
            ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50 hover:border-violet-500/40' 
            : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200 hover:border-violet-400/60'"
          @click="selectedSubnetId = subnet.id"
        >
          <!-- Glow on hover -->
          <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-br from-violet-500/5 via-transparent to-indigo-500/5"></div>

          <div class="relative z-10">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="w-12 h-12 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-violet-500/20">
                  <Map class="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 class="text-lg font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">{{ subnet.name }}</h3>
                  <p class="text-xs font-mono" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                    {{ subnet.start_ip }} — {{ subnet.end_ip }}
                  </p>
                </div>
              </div>
              <button
                v-if="canExecuteScans"
                @click.stop="deleteSubnet(subnet.id, subnet.name)"
                class="w-9 h-9 rounded-lg flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100"
                :class="isDark() ? 'hover:bg-red-500/20 text-slate-500 hover:text-red-400' : 'hover:bg-red-100 text-slate-400 hover:text-red-500'"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-3 gap-3 mb-4">
              <div 
                class="rounded-xl p-3 text-center"
                :class="isDark() ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-emerald-50 border border-emerald-200'"
              >
                <div class="flex items-center justify-center gap-1 mb-1">
                  <Wifi class="w-3.5 h-3.5 text-emerald-400" />
                </div>
                <p class="text-lg font-bold text-emerald-400">{{ subnet.active_count }}</p>
                <p class="text-[10px] uppercase tracking-wider" :class="isDark() ? 'text-emerald-400/60' : 'text-emerald-600/70'">Activos</p>
              </div>
              <div 
                class="rounded-xl p-3 text-center"
                :class="isDark() ? 'bg-red-500/10 border border-red-500/20' : 'bg-red-50 border border-red-200'"
              >
                <div class="flex items-center justify-center gap-1 mb-1">
                  <WifiOff class="w-3.5 h-3.5 text-red-400" />
                </div>
                <p class="text-lg font-bold text-red-400">{{ subnet.inactive_count }}</p>
                <p class="text-[10px] uppercase tracking-wider" :class="isDark() ? 'text-red-400/60' : 'text-red-600/70'">Inactivos</p>
              </div>
              <div 
                class="rounded-xl p-3 text-center"
                :class="isDark() ? 'bg-slate-500/10 border border-slate-500/20' : 'bg-slate-50 border border-slate-200'"
              >
                <div class="flex items-center justify-center gap-1 mb-1">
                  <HelpCircle class="w-3.5 h-3.5 text-slate-400" />
                </div>
                <p class="text-lg font-bold" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">{{ subnet.unknown_count }}</p>
                <p class="text-[10px] uppercase tracking-wider" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Sin escanear</p>
              </div>
            </div>

            <div class="flex items-center justify-between">
              <span class="text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                {{ subnet.device_count }} dispositivos
              </span>
              <ChevronRight class="w-5 h-5 text-violet-400 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <Transition name="fade-slide">
        <div v-if="confirmDelete" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="cancelDelete"></div>
          <!-- Modal -->
          <div 
            class="relative z-10 w-full max-w-md rounded-3xl p-8 shadow-2xl"
            :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
          >
            <div class="flex flex-col items-center text-center space-y-5">
              <div class="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center border border-red-500/20">
                <AlertTriangle class="w-8 h-8 text-red-400" />
              </div>
              <div>
                <h3 class="text-xl font-bold mb-2" :class="isDark() ? 'text-white' : 'text-slate-800'">
                  Eliminar subred
                </h3>
                <p class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                  ¿Eliminar la subred <span class="font-bold" :class="isDark() ? 'text-white' : 'text-slate-700'">{{ confirmDelete.name }}</span>?
                  <br>Esta acción no se puede deshacer.
                </p>
              </div>
              <div class="flex gap-3 w-full">
                <button
                  @click="cancelDelete"
                  :class="[btnSecondaryClass, 'flex-1', 'py-3', 'text-sm', 'justify-center']"
                >
                  Cancelar
                </button>
                <button
                  @click="confirmDeleteAction"
                  :class="[btnDangerClass, 'flex-1', 'py-3', 'text-sm', 'justify-center']"
                >
                  Eliminar
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
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
</style>
