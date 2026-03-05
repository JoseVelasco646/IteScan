<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="p-3 bg-gradient-to-br from-emerald-500/20 to-green-600/20 rounded-xl border-2 border-emerald-500/50">
          <Terminal class="w-6 h-6 text-emerald-400" />
        </div>
        <div>
          <h3 
            class="text-xl font-bold font-display"
            :class="isDark() ? 'text-white' : 'text-slate-800'"
          >Terminal SSH</h3>
          <p 
            class="text-sm"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
          >Ejecuta comandos en múltiples hosts simultáneamente</p>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div 
        class="p-5 space-y-4"
        :class="isDark() ? 'bg-slate-800/30 border border-slate-700/50 rounded-2xl' : 'bg-slate-50 border border-slate-200 rounded-2xl'"
      >
        <h4 
          class="text-lg font-semibold flex items-center gap-2"
          :class="isDark() ? 'text-white' : 'text-slate-800'"
        >
          <Key class="w-5 h-5 text-cyan-400" />
          Credenciales SSH
        </h4>
        
        <!-- Saved credentials selector -->
        <div v-if="savedCredentials.length > 0" class="space-y-2">
          <label class="text-xs font-semibold block" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
            <FolderOpen class="w-3.5 h-3.5 inline mr-1" />
            Credenciales guardadas
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="cred in savedCredentials"
              :key="cred.id"
              @click="applySavedCredential(cred.id)"
              class="group flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border"
              :class="[
                selectedCredentialId === cred.id
                  ? (isDark() ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300' : 'bg-cyan-50 border-cyan-400 text-cyan-700')
                  : (isDark() ? 'bg-slate-800/50 border-slate-600 text-slate-300 hover:border-cyan-500/40' : 'bg-white border-slate-300 text-slate-600 hover:border-cyan-400')
              ]"
            >
              <Key class="w-3 h-3" />
              {{ cred.name }}
              <span class="opacity-50">({{ cred.username }})</span>
              <span
                @click.stop="deleteSavedCredential(cred.id)"
                class="ml-1 opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity"
              >
                <Trash2 class="w-3 h-3" />
              </span>
            </button>
          </div>
        </div>

        <div class="space-y-3">
          <div>
            <label 
              class="text-sm font-semibold mb-2 block"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
            >Usuario</label>
            <input
              v-model="credentials.username"
              type="text"
              class="w-full px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-500/60 transition-all"
              :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              placeholder="usuario"
            />
          </div>
          
          <div>
            <label 
              class="text-sm font-semibold mb-2 block"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
            >Contraseña</label>
            <input
              v-model="credentials.password"
              type="password"
              class="w-full px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-500/60 transition-all"
              :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              placeholder="••••••••"
            />
          </div>

          <!-- Save credentials button -->
          <div class="pt-1">
            <button
              v-if="!showSaveForm"
              @click="showSaveForm = true"
              :disabled="!credentials.username || !credentials.password"
              class="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              :class="isDark() ? 'text-cyan-400 hover:bg-cyan-500/10 border border-cyan-500/30' : 'text-cyan-600 hover:bg-cyan-50 border border-cyan-300'"
            >
              <Save class="w-3.5 h-3.5" />
              Guardar credenciales
            </button>
            <div v-else class="flex items-center gap-2">
              <input
                v-model="credentialName"
                type="text"
                placeholder="Nombre (ej: Lab SSH)"
                class="flex-1 px-3 py-1.5 text-xs rounded-lg focus:outline-none focus:ring-1 focus:ring-cyan-500/60 transition-all"
                :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
                @keyup.enter="saveCurrentCredentials"
              />
              <button
                @click="saveCurrentCredentials"
                class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-cyan-500 text-white hover:bg-cyan-400 transition-all"
              >Guardar</button>
              <button
                @click="showSaveForm = false; credentialName = ''"
                class="px-2 py-1.5 text-xs rounded-lg transition-all"
                :class="isDark() ? 'text-slate-400 hover:bg-slate-700' : 'text-slate-500 hover:bg-slate-200'"
              >Cancelar</button>
            </div>
          </div>
        </div>
      </div>

      <div 
        class="p-5 space-y-4"
        :class="isDark() ? 'bg-slate-800/30 border border-slate-700/50 rounded-2xl' : 'bg-slate-50 border border-slate-200 rounded-2xl'"
      >
        <h4 
          class="text-lg font-semibold flex items-center gap-2"
          :class="isDark() ? 'text-white' : 'text-slate-800'"
        >
          <Server class="w-5 h-5 text-blue-400" />
          Hosts Objetivo
        </h4>
        
        <div class="space-y-3">
          <div>
            <label 
              class="text-sm font-semibold mb-2 block"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
            >IPs (separadas por coma o rango)</label>
            <input
              v-model="targetInput"
              type="text"
              class="w-full px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-500/60 transition-all"
              :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
              placeholder="192.168.0.10, 192.168.0.20 o 192.168.0.10-192.168.0.50"
            />
          </div>
          
          <div class="flex items-center gap-2">
            <span class="badge badge-info">{{ parsedHosts.length }} hosts</span>
            <button
              v-if="selectedFromTable.length > 0"
              @click="useSelectedHosts"
              class="btn btn-secondary text-sm py-1.5"
            >
              <Users class="w-4 h-4" />
              Usar seleccionados ({{ selectedFromTable.length }})
            </button>
          </div>
        </div>
      </div>
    </div>

    <div 
      class="p-5 space-y-4"
      :class="isDark() ? 'bg-slate-800/30 border border-slate-700/50 rounded-2xl' : 'bg-slate-50 border border-slate-200 rounded-2xl'"
    >
      <h4 
        class="text-lg font-semibold flex items-center gap-2"
        :class="isDark() ? 'text-white' : 'text-slate-800'"
      >
        <TerminalSquare class="w-5 h-5 text-purple-400" />
        Comando
      </h4>
      
      <div class="flex gap-3">
        <input
          v-model="command"
          type="text"
          class="flex-1 font-mono px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-500/60 transition-all"
          :class="isDark() ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'"
          placeholder="Ej: hostname, uptime, df -h, etc."
          @keyup.enter="executeCommand"
        />
        
        <button
          @click="executeCommand"
          :disabled="!canExecute || isExecuting"
          class="btn btn-primary whitespace-nowrap"
        >
          <Play v-if="!isExecuting" class="w-5 h-5" />
          <Loader2 v-else class="w-5 h-5 animate-spin" />
          {{ isExecuting ? 'Ejecutando...' : 'Ejecutar' }}
        </button>
      </div>

      <div class="flex flex-wrap gap-2">
        <span class="text-sm text-theme-muted">Comandos rápidos:</span>
        <button
          v-for="cmd in quickCommands"
          :key="cmd.label"
          @click="command = cmd.command"
          class="px-3 py-1 text-xs font-medium rounded-lg bg-slate-700/50 text-slate-300 hover:bg-cyan-500/20 hover:text-cyan-400 transition-all"
        >
          {{ cmd.label }}
        </button>
      </div>
    </div>

    <div 
      class="overflow-hidden"
      :class="isDark() ? 'bg-slate-800/30 border border-slate-700/50 rounded-2xl' : 'bg-white border border-slate-200 rounded-2xl'"
    >
      <div 
        class="flex items-center justify-between px-4 py-3"
        :class="isDark() ? 'bg-slate-800/80 border-b border-slate-700/50' : 'bg-slate-100 border-b border-slate-200'"
      >
        <div class="flex items-center gap-2">
          <div class="flex gap-1.5">
            <span class="w-3 h-3 rounded-full bg-red-500"></span>
            <span class="w-3 h-3 rounded-full bg-yellow-500"></span>
            <span class="w-3 h-3 rounded-full bg-green-500"></span>
          </div>
          <span 
            class="text-sm font-mono"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
          >Terminal Output</span>
        </div>
        <button
          @click="clearOutput"
          class="text-xs text-slate-400 hover:text-cyan-400 transition-colors"
        >
          Limpiar
        </button>
      </div>
      
      <div 
        ref="terminalRef"
        class="bg-slate-950 p-4 font-mono text-sm h-96 overflow-y-auto"
      >
        <div v-if="output.length === 0" class="text-slate-500 flex items-center gap-2">
          <span class="text-cyan-400">$</span>
          <span>Esperando comandos...</span>
          <span class="terminal-cursor"></span>
        </div>
        
        <div v-for="(entry, index) in output" :key="index" class="mb-4">
          <div class="flex items-center gap-2 text-slate-400 mb-1">
            <span class="text-cyan-400">$</span>
            <span class="text-yellow-400">{{ entry.host }}</span>
            <span class="text-slate-500">></span>
            <span class="text-white">{{ entry.command }}</span>
          </div>
          
          <div 
            class="pl-4 border-l-2 ml-2"
            :class="entry.success ? 'border-emerald-500/50' : 'border-red-500/50'"
          >
            <pre 
              class="whitespace-pre-wrap break-all"
              :class="entry.success ? 'text-emerald-400' : 'text-red-400'"
            >{{ entry.output || entry.error }}</pre>
          </div>
          
          <div class="flex items-center gap-2 mt-1 ml-4">
            <span 
              class="badge text-xs"
              :class="entry.success ? 'badge-success' : 'badge-danger'"
            >
              {{ entry.success ? 'Éxito' : 'Error' }}
            </span>
            <span class="text-xs text-slate-500">
              Exit code: {{ entry.exit_code }}
            </span>
          </div>
        </div>
        
        <div v-if="isExecuting" class="flex items-center gap-2 text-cyan-400">
          <Loader2 class="w-4 h-4 animate-spin" />
          <span>Ejecutando en {{ pendingHosts }} host(s)...</span>
        </div>
      </div>
    </div>

    <div v-if="isExecuting && totalHosts > 0" class="card p-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm text-theme-secondary">Progreso de ejecución</span>
        <span class="text-sm font-semibold text-cyan-400">{{ completedHosts }}/{{ totalHosts }}</span>
      </div>
      <div class="h-2 bg-slate-700/50 rounded-full overflow-hidden">
        <div 
          class="h-full bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full transition-all duration-300"
          :style="{ width: `${(completedHosts / totalHosts) * 100}%` }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { Terminal, Key, Server, Users, Play, Loader2, TerminalSquare, Save, FolderOpen, Trash2 } from 'lucide-vue-next'
import { scannerAPI } from '../api/scanner'
import { useToast } from '../composables/useToast'
import { useGlobalWebSocket } from '../composables/useWebSocket'
import { useTheme } from '../composables/useTheme'

const toast = useToast()
const ws = useGlobalWebSocket()
const { isDark } = useTheme()

const credentials = ref({
  username: '',
  password: ''
})

const savedCredentials = ref([])
const selectedCredentialId = ref(null)
const showSaveForm = ref(false)
const credentialName = ref('')
const loadingCredentials = ref(false)

const loadSavedCredentials = async () => {
  loadingCredentials.value = true
  try {
    savedCredentials.value = await scannerAPI.getSSHCredentials()
  } catch { /* ignore */ } finally {
    loadingCredentials.value = false
  }
}

const applySavedCredential = async (id) => {
  try {
    const cred = await scannerAPI.getSSHCredential(id)
    credentials.value.username = cred.username
    credentials.value.password = cred.password
    selectedCredentialId.value = id
    toast.success(`Credenciales "${cred.name}" cargadas`)
  } catch {
    toast.error('Error cargando credencial')
  }
}

const saveCurrentCredentials = async () => {
  if (!credentialName.value.trim() || !credentials.value.username || !credentials.value.password) {
    toast.error('Complete nombre, usuario y contraseña')
    return
  }
  try {
    await scannerAPI.createSSHCredential(credentialName.value.trim(), credentials.value.username, credentials.value.password)
    toast.success('Credencial guardada')
    credentialName.value = ''
    showSaveForm.value = false
    await loadSavedCredentials()
  } catch {
    toast.error('Error guardando credencial')
  }
}

const deleteSavedCredential = async (id) => {
  try {
    await scannerAPI.deleteSSHCredential(id)
    toast.success('Credencial eliminada')
    if (selectedCredentialId.value === id) selectedCredentialId.value = null
    await loadSavedCredentials()
  } catch {
    toast.error('Error eliminando credencial')
  }
}

onMounted(() => {
  loadSavedCredentials()
})

const targetInput = ref('')
const command = ref('')
const output = ref([])
const isExecuting = ref(false)
const terminalRef = ref(null)
const selectedFromTable = ref([])

const totalHosts = ref(0)
const completedHosts = ref(0)
const pendingHosts = ref(0)

const quickCommands = [
  { label: 'hostname', command: 'hostname' },
  { label: 'uptime', command: 'uptime' },
  { label: 'df -h', command: 'df -h' },
  { label: 'free -m', command: 'free -m' },
  { label: 'who', command: 'who' },
  { label: 'ps aux', command: 'ps aux | head -20' },
  { label: 'netstat', command: 'netstat -tuln | head -20' },
  { label: 'ip addr', command: 'ip addr show' }
]

const parsedHosts = computed(() => {
  if (!targetInput.value.trim()) return []
  
  const hosts = []
  const parts = targetInput.value.split(',').map(p => p.trim())
  
  for (const part of parts) {
    if (part.includes('-') && !part.includes('/')) {
      // Range format: 192.168.0.10-192.168.0.50
      const [start, end] = part.split('-').map(s => s.trim())
      if (start && end) {
        const startParts = start.split('.').map(Number)
        const endParts = end.split('.').map(Number)
        
        if (startParts.length === 4 && endParts.length === 4) {
          const startNum = startParts[3]
          const endNum = endParts[3]
          const base = startParts.slice(0, 3).join('.')
          
          for (let i = startNum; i <= endNum; i++) {
            hosts.push(`${base}.${i}`)
          }
        }
      }
    } else if (part) {
      hosts.push(part)
    }
  }
  
  return hosts
})

const canExecute = computed(() => {
  return credentials.value.username && 
         credentials.value.password && 
         parsedHosts.value.length > 0 && 
         command.value.trim()
})

const useSelectedHosts = () => {
  if (selectedFromTable.value.length > 0) {
    targetInput.value = selectedFromTable.value.join(', ')
    toast.success(`${selectedFromTable.value.length} hosts cargados`)
  }
}

const executeCommand = async () => {
  if (!canExecute.value || isExecuting.value) return
  
  isExecuting.value = true
  const hosts = parsedHosts.value
  totalHosts.value = hosts.length
  completedHosts.value = 0
  pendingHosts.value = hosts.length
  
  output.value.push({
    type: 'header',
    text: `Ejecutando "${command.value}" en ${hosts.length} host(s)...`,
    timestamp: new Date().toISOString()
  })
  
  scrollToBottom()
  
  try {
    const promises = hosts.map(async (host) => {
      try {
        const result = await scannerAPI.executeSSHCommand(
          host,
          command.value,
          credentials.value.username,
          credentials.value.password
        )
        
        completedHosts.value++
        pendingHosts.value--
        
        output.value.push({
          host,
          command: command.value,
          success: result.success,
          output: result.stdout,
          error: result.stderr,
          exit_code: result.exit_code
        })
        
        scrollToBottom()
        return result
      } catch (err) {
        completedHosts.value++
        pendingHosts.value--
        
        output.value.push({
          host,
          command: command.value,
          success: false,
          error: err.message || 'Error de conexión',
          exit_code: -1
        })
        
        scrollToBottom()
        return { success: false, error: err.message }
      }
    })
    
    await Promise.allSettled(promises)
    
    const successCount = output.value.filter(o => o.success).length
    const failCount = output.value.filter(o => o.success === false).length
    
    toast.success(`Completado: ${successCount} éxitos, ${failCount} errores`)
    
  } catch (err) {
    toast.error('Error ejecutando comandos')
  } finally {
    isExecuting.value = false
  }
}

const clearOutput = () => {
  output.value = []
}

const scrollToBottom = async () => {
  await nextTick()
  if (terminalRef.value) {
    terminalRef.value.scrollTop = terminalRef.value.scrollHeight
  }
}

ws.on('hosts_selected', (data) => {
  if (data.hosts) {
    selectedFromTable.value = data.hosts.map(h => h.ip)
  }
})
</script>

<style scoped>
.terminal-cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background-color: #22d3ee;
  animation: blink 1s step-end infinite;
  vertical-align: middle;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}
</style>
