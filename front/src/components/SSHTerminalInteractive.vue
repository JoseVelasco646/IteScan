<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div class="flex items-center gap-3">
        <div class="p-3 bg-gradient-to-br from-emerald-500/20 to-green-600/20 rounded-xl border-2 border-emerald-500/50">
          <TerminalIcon class="w-6 h-6 text-emerald-400" />
        </div>
        <div>
          <h3 class="text-xl font-bold font-display"
            :class="isDark() ? 'text-white' : 'text-slate-800'">Terminal SSH Interactiva</h3>
          <p class="text-sm"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
            Múltiples sesiones — vim, sudo, htop, colores, autocompletado
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <span class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
          {{ sessions.length }} sesión{{ sessions.length !== 1 ? 'es' : '' }}
        </span>
        <button v-if="sessions.length > 1" @click="broadcastMode = !broadcastMode"
          class="text-sm flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all border"
          :class="broadcastMode
            ? 'bg-orange-500/20 text-orange-400 border-orange-500/50 ring-2 ring-orange-500/30'
            : (isDark() ? 'bg-slate-700/50 text-slate-400 border-slate-600 hover:text-slate-200' : 'bg-slate-100 text-slate-500 border-slate-300 hover:text-slate-700')">
          <Radio class="w-4 h-4" :class="broadcastMode ? 'animate-pulse' : ''" />
          Broadcast
        </button>
        <button @click="showConnectForm = true"
          :class="[btnPrimaryClass, 'text-sm', 'flex', 'items-center', 'gap-1.5']"
          :disabled="sessions.length >= maxSessions">
          <Plus class="w-4 h-4" />
          Nueva sesión
        </button>
      </div>
    </div>

    <!-- Connect modal/form -->
    <div v-if="showConnectForm"
      class="p-5 rounded-2xl border space-y-4"
      :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
      <div class="flex items-center justify-between">
        <h4 class="text-lg font-semibold flex items-center gap-2"
          :class="isDark() ? 'text-white' : 'text-slate-800'">
          <Key class="w-5 h-5 text-cyan-400" />
          Nueva conexión SSH
        </h4>
        <button @click="showConnectForm = false" class="text-slate-400 hover:text-slate-200 transition-colors">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Saved credentials -->
      <div v-if="savedCredentials.length > 0" class="space-y-2">
        <p class="text-xs font-medium flex items-center gap-1.5"
          :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
          <FolderOpen class="w-3.5 h-3.5" />
          Credenciales guardadas
        </p>
        <div class="flex flex-wrap gap-2">
          <button v-for="cred in savedCredentials" :key="cred.id"
            @click="applySavedCredential(cred)"
            class="group relative flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all"
            :class="isDark()
              ? 'bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-cyan-500/20 hover:border-cyan-500/50 hover:text-cyan-300'
              : 'bg-white border-slate-300 text-slate-600 hover:bg-cyan-50 hover:border-cyan-400 hover:text-cyan-700'">
            <Key class="w-3.5 h-3.5" />
            <span>{{ cred.name }}</span>
            <span class="text-xs opacity-60">({{ cred.username }})</span>
            <button @click.stop="deleteSavedCredential(cred.id)"
              class="ml-1 p-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity"
              :class="isDark() ? 'hover:bg-red-500/30 text-red-400' : 'hover:bg-red-100 text-red-500'">
              <Trash2 class="w-3 h-3" />
            </button>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div>
          <label class="text-xs font-medium mb-1 block"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Host</label>
          <input v-model="newConn.host" type="text"
            class="w-full px-3 py-2 rounded-lg focus:outline-none focus:ring-2 text-sm transition-all"
            :class="inputClass" placeholder="192.168.0.1" />
        </div>
        <div>
          <label class="text-xs font-medium mb-1 block"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Usuario</label>
          <input v-model="newConn.username" type="text"
            class="w-full px-3 py-2 rounded-lg focus:outline-none focus:ring-2 text-sm transition-all"
            :class="inputClass" placeholder="usuario" />
        </div>
        <div>
          <label class="text-xs font-medium mb-1 block"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Contraseña</label>
          <input v-model="newConn.password" type="password"
            class="w-full px-3 py-2 rounded-lg focus:outline-none focus:ring-2 text-sm transition-all"
            :class="inputClass" placeholder="••••••••" @keyup.enter="addSession" />
        </div>
        <div>
          <label class="text-xs font-medium mb-1 block"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Puerto</label>
          <input v-model.number="newConn.port" type="number"
            class="w-full px-3 py-2 rounded-lg focus:outline-none focus:ring-2 text-sm transition-all"
            :class="inputClass" placeholder="22" />
        </div>
        <div class="flex items-end">
          <button @click="addSession" :disabled="!canAdd || isConnecting"
            :class="[btnPrimaryClass, 'w-full', 'text-sm', 'flex', 'items-center', 'justify-center', 'gap-1.5', 'py-2']">
            <Loader2 v-if="isConnecting" class="w-4 h-4 animate-spin" />
            <TerminalIcon v-else class="w-4 h-4" />
            {{ isConnecting ? 'Conectando...' : 'Conectar' }}
          </button>
        </div>
      </div>

      <!-- Save credentials button -->
      <div v-if="!showSaveForm" class="flex items-center gap-2">
        <button @click="showSaveForm = true"
          :disabled="!newConn.username || !newConn.password"
          class="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium border transition-all disabled:opacity-40"
          :class="isDark()
            ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/20'
            : 'bg-emerald-50 border-emerald-300 text-emerald-700 hover:bg-emerald-100'">
          <Save class="w-3.5 h-3.5" />
          Guardar credenciales
        </button>
      </div>
      <div v-else class="flex items-center gap-2">
        <input v-model="saveName" type="text"
          class="px-3 py-1.5 rounded-lg focus:outline-none focus:ring-2 text-sm transition-all"
          :class="inputClass" placeholder="Nombre (ej: Router principal)" @keyup.enter="saveCurrentCredentials" />
        <button @click="saveCurrentCredentials" :disabled="!saveName.trim() || !newConn.username || !newConn.password"
          :class="[btnPrimaryClass, 'text-xs', 'px-3', 'py-1.5']">Guardar</button>
        <button @click="showSaveForm = false"
          class="text-xs px-2 py-1.5 rounded-lg transition-colors"
          :class="isDark() ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-700'">Cancelar</button>
      </div>

      <!-- Bulk connect helper -->
      <div class="flex items-center gap-3 pt-2 border-t"
        :class="isDark() ? 'border-slate-700/50' : 'border-slate-200'">
        <label class="text-xs font-medium"
          :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Múltiples hosts:</label>
        <input v-model="bulkHosts" type="text"
          class="flex-1 px-3 py-1.5 rounded-lg focus:outline-none focus:ring-2 text-sm transition-all"
          :class="inputClass"
          placeholder="192.168.0.10, 192.168.0.20, 192.168.0.30 (mismas credenciales)" />
        <button @click="addBulkSessions" :disabled="!bulkHosts.trim() || !newConn.username || !newConn.password"
          :class="[btnSecondaryClass, 'text-xs', 'px-3', 'py-1.5']">
          Conectar todos
        </button>
      </div>
    </div>

    <!-- Info panel when no sessions -->
    <div v-if="sessions.length === 0 && !showConnectForm"
      class="p-5 rounded-2xl border"
      :class="isDark() ? 'bg-blue-500/10 border-blue-400/30' : 'bg-blue-50 border-blue-200'">
      <h4 class="text-lg font-semibold flex items-center gap-2 mb-3"
        :class="isDark() ? 'text-blue-300' : 'text-blue-700'">
        <Info class="w-5 h-5" />
        Características
      </h4>
      <ul class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm"
        :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
        <li class="flex items-start gap-2"><svg class="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          <span><strong>Múltiples sesiones</strong> simultáneas en pestañas</span></li>
        <li class="flex items-start gap-2"><svg class="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Terminal real con xterm.js — colores, cursor, ANSI completo</span></li>
        <li class="flex items-start gap-2"><svg class="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Soporte completo para <strong>vim, nano, htop, top, less</strong></span></li>
        <li class="flex items-start gap-2"><svg class="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Funciona <strong>sudo</strong>, autocompletado con Tab, historial</span></li>
        <li class="flex items-start gap-2"><svg class="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Conectar varios hosts a la vez con mismas credenciales</span></li>
        <li class="flex items-start gap-2"><svg class="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Registro de auditoría para conexiones y desconexiones</span></li>
      </ul>
      <div class="mt-4 p-3 rounded-lg border"
        :class="isDark() ? 'bg-amber-500/10 border-amber-500/30' : 'bg-amber-50 border-amber-200'">
        <p class="text-sm flex items-start gap-2" :class="isDark() ? 'text-amber-300' : 'text-amber-700'">
          <svg class="w-5 h-5 text-amber-400 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span>Esta es una terminal SSH real. Ten cuidado con los comandos que ejecutas.</span>
        </p>
      </div>
    </div>

    <!-- Session tabs + terminal -->
    <div v-if="sessions.length > 0"
      class="overflow-hidden rounded-2xl border"
      :class="isDark() ? 'border-slate-700/50' : 'border-slate-200'">
      
      <!-- Tab bar -->
      <div class="flex items-center overflow-x-auto border-b"
        :class="isDark() ? 'bg-slate-800/80 border-slate-700/50' : 'bg-slate-100 border-slate-200'">
        <button v-for="s in sessions" :key="s.id"
          @click="activateSession(s.id)"
          class="group flex items-center gap-2 px-4 py-2.5 text-sm font-mono border-r whitespace-nowrap transition-colors relative"
          :class="[
            isDark() ? 'border-slate-700/50' : 'border-slate-200',
            activeSessionId === s.id 
              ? (isDark() ? 'bg-slate-900 text-emerald-400' : 'bg-white text-emerald-600')
              : (isDark() ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50')
          ]">
          <!-- Active indicator -->
          <div v-if="activeSessionId === s.id"
            class="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-400"></div>
          
          <!-- Status dot -->
          <div class="w-2 h-2 rounded-full flex-shrink-0"
            :class="s.connected ? 'bg-emerald-400' : s.connecting ? 'bg-yellow-400 animate-pulse' : 'bg-red-400'"></div>
          
          <span class="truncate max-w-[140px]">{{ s.label }}</span>
          
          <!-- Close button -->
          <button @click.stop="closeSession(s.id)"
            class="ml-1 p-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity"
            :class="isDark() ? 'hover:bg-slate-600' : 'hover:bg-slate-200'">
            <X class="w-3 h-3" />
          </button>
        </button>

        <!-- Add tab button -->
        <button @click="showConnectForm = true"
          class="px-3 py-2.5 transition-colors flex-shrink-0"
          :class="isDark() ? 'text-slate-500 hover:text-slate-300' : 'text-slate-400 hover:text-slate-600'"
          :disabled="sessions.length >= maxSessions">
          <Plus class="w-4 h-4" />
        </button>
      </div>

      <!-- Broadcast command bar -->
      <div v-if="broadcastMode && connectedSessions.length > 1"
        class="flex items-center gap-2 px-3 py-2 border-b"
        :class="isDark() ? 'bg-orange-500/10 border-orange-500/30' : 'bg-orange-50 border-orange-200'">
        <Radio class="w-4 h-4 text-orange-400 animate-pulse flex-shrink-0" />
        <span class="text-xs font-medium flex-shrink-0"
          :class="isDark() ? 'text-orange-300' : 'text-orange-600'">
          Broadcast a {{ connectedSessions.length }} sesiones:
        </span>
        <input v-model="broadcastCommand" type="text"
          class="flex-1 px-3 py-1 rounded-lg focus:outline-none focus:ring-2 text-sm font-mono transition-all"
          :class="isDark()
            ? 'bg-slate-900/80 border border-orange-500/40 text-white placeholder-slate-500 focus:ring-orange-500/60'
            : 'bg-white border border-orange-300 text-slate-800 placeholder-slate-400 focus:ring-orange-400'"
          placeholder="Escribe un comando y presiona Enter para enviarlo a todas las sesiones..."
          @keyup.enter="sendBroadcastCommand" />
        <button @click="sendBroadcastCommand" :disabled="!broadcastCommand.trim()"
          class="px-3 py-1 rounded-lg text-sm font-medium flex items-center gap-1 transition-all"
          :class="isDark()
            ? 'bg-orange-500/20 text-orange-300 hover:bg-orange-500/30 disabled:opacity-40'
            : 'bg-orange-100 text-orange-700 hover:bg-orange-200 disabled:opacity-40'">
          <Send class="w-3.5 h-3.5" />
          Enviar
        </button>
      </div>

      <!-- Terminal containers (one per session, only active one visible) -->
      <div v-for="s in sessions" :key="'term-' + s.id"
        v-show="activeSessionId === s.id"
        :ref="el => setTermRef(s.id, el)"
        class="xterm-container"
        @click="focusSession(s.id)">
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted, nextTick, reactive } from 'vue'
import { Terminal as TerminalIcon, Key, Info, Loader2, Plus, X, Radio, Send, Save, FolderOpen, Trash2 } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'
import { useTheme } from '../composables/useTheme'
import { useButtonClasses } from '../composables/useButtonClasses'
import { scannerAPI } from '../api/scanner'

const toast = useToast()
const { isDark } = useTheme()
const { btnPrimaryClass, btnSecondaryClass } = useButtonClasses()

const maxSessions = 10
const showConnectForm = ref(true)
const isConnecting = ref(false)
const bulkHosts = ref('')
const broadcastMode = ref(false)
const broadcastCommand = ref('')

const newConn = ref({
  host: '',
  username: '',
  password: '',
  port: 22
})

const sessions = ref([])
const activeSessionId = ref(null)

// Saved credentials
const savedCredentials = ref([])
const showSaveForm = ref(false)
const saveName = ref('')

const loadSavedCredentials = async () => {
  try {
    const res = await scannerAPI.getSSHCredentials()
    savedCredentials.value = res
  } catch { savedCredentials.value = [] }
}

const applySavedCredential = async (cred) => {
  try {
    const full = await scannerAPI.getSSHCredential(cred.id)
    newConn.value.username = full.username
    newConn.value.password = full.password || ''
    toast.success(`Credenciales "${cred.name}" aplicadas`, 'SSH')
  } catch (e) {
    toast.error('Error al cargar credencial', 'SSH')
  }
}

const saveCurrentCredentials = async () => {
  if (!saveName.value.trim() || !newConn.value.username || !newConn.value.password) return
  try {
    await scannerAPI.createSSHCredential(saveName.value.trim(), newConn.value.username, newConn.value.password)
    toast.success('Credenciales guardadas', 'SSH')
    saveName.value = ''
    showSaveForm.value = false
    await loadSavedCredentials()
  } catch (e) {
    toast.error('Error al guardar: ' + (e.response?.data?.detail || e.message), 'SSH')
  }
}

const deleteSavedCredential = async (id) => {
  try {
    await scannerAPI.deleteSSHCredential(id)
    toast.success('Credencial eliminada', 'SSH')
    await loadSavedCredentials()
  } catch (e) {
    toast.error('Error al eliminar', 'SSH')
  }
}

onMounted(() => {
  loadSavedCredentials()
})

// Store xterm instances, ws connections, etc. keyed by session id
const sessionData = {}
const termRefs = {}

const inputClass = computed(() =>
  isDark()
    ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60'
    : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400'
)

const canAdd = computed(() =>
  newConn.value.host && newConn.value.username && newConn.value.password
)

const getApiBaseUrl = () => '192.168.0.11:8000'

const setTermRef = (id, el) => {
  if (el) termRefs[id] = el
}

// ── Xterm modules cache (loaded once) ──
let xtermModules = null
const loadXtermModules = async () => {
  if (xtermModules) return xtermModules
  const [
    { Terminal }, { FitAddon }, { WebLinksAddon }, { Unicode11Addon }
  ] = await Promise.all([
    import('@xterm/xterm'),
    import('@xterm/addon-fit'),
    import('@xterm/addon-web-links'),
    import('@xterm/addon-unicode11')
  ])
  await import('@xterm/xterm/css/xterm.css')
  xtermModules = { Terminal, FitAddon, WebLinksAddon, Unicode11Addon }
  return xtermModules
}

// ── Create a single session ──
const createSession = async (host, username, password, port) => {
  const id = `ssh_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
  const label = `${username}@${host}`

  const session = reactive({
    id,
    host,
    username,
    port,
    label,
    connected: false,
    connecting: true
  })

  sessions.value.push(session)
  activeSessionId.value = id

  await nextTick()

  try {
    const { Terminal, FitAddon, WebLinksAddon, Unicode11Addon } = await loadXtermModules()

    const term = new Terminal({
      cursorBlink: true,
      cursorStyle: 'block',
      fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", "Menlo", "Consolas", monospace',
      fontSize: 14,
      lineHeight: 1.2,
      scrollback: 10000,
      allowProposedApi: true,
      theme: {
        background: '#0f172a',
        foreground: '#e2e8f0',
        cursor: '#22d3ee',
        cursorAccent: '#0f172a',
        selectionBackground: '#334155',
        selectionForeground: '#f8fafc',
        black: '#1e293b', red: '#ef4444', green: '#22c55e', yellow: '#eab308',
        blue: '#3b82f6', magenta: '#a855f7', cyan: '#06b6d4', white: '#e2e8f0',
        brightBlack: '#475569', brightRed: '#f87171', brightGreen: '#4ade80',
        brightYellow: '#facc15', brightBlue: '#60a5fa', brightMagenta: '#c084fc',
        brightCyan: '#22d3ee', brightWhite: '#f8fafc'
      }
    })

    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.loadAddon(new WebLinksAddon())
    const u11 = new Unicode11Addon()
    term.loadAddon(u11)
    term.unicode.activeVersion = '11'

    await nextTick()
    const container = termRefs[id]
    if (!container) throw new Error('Container not found')
    term.open(container)
    await nextTick()
    try { fitAddon.fit() } catch {}

    const cols = term.cols
    const rows = term.rows

    // WebSocket
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const token = localStorage.getItem('admin_token')
    const wsUrl = `${wsProtocol}//${getApiBaseUrl()}/ws/ssh/${id}?token=${token}`
    const ws = new WebSocket(wsUrl)
    ws.binaryType = 'arraybuffer'

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'connect', host, username, password, port, cols, rows
      }))
    }

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        term.write(new TextDecoder().decode(event.data))
      } else {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'connected') {
            session.connected = true
            session.connecting = false
            toast.success(`Conectado a ${host}`, 'SSH')
            nextTick(() => {
              try { fitAddon.fit() } catch {}
              if (activeSessionId.value === id) term.focus()
            })
          } else if (msg.type === 'error') {
            toast.error(msg.message, 'Error SSH')
            session.connecting = false
            removeSession(id)
          } else if (msg.type === 'disconnected') {
            toast.warning(msg.message || 'Sesión terminada', 'SSH')
            session.connected = false
            session.connecting = false
          }
        } catch {}
      }
    }

    ws.onerror = () => {
      toast.error(`Error WebSocket: ${host}`, 'SSH')
      session.connecting = false
      removeSession(id)
    }

    ws.onclose = () => {
      session.connected = false
      session.connecting = false
    }

    // Forward keystrokes (with broadcast support)
    term.onData((data) => {
      if (broadcastMode.value) {
        // Send to ALL connected sessions
        for (const s of sessions.value) {
          const sd = sessionData[s.id]
          if (sd?.ws?.readyState === WebSocket.OPEN && s.connected) {
            sd.ws.send(JSON.stringify({ type: 'input', data }))
          }
        }
      } else {
        // Send only to this session
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'input', data }))
        }
      }
    })
    term.onBinary((data) => {
      if (broadcastMode.value) {
        for (const s of sessions.value) {
          const sd = sessionData[s.id]
          if (sd?.ws?.readyState === WebSocket.OPEN && s.connected) {
            sd.ws.send(JSON.stringify({ type: 'input', data }))
          }
        }
      } else {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'input', data }))
        }
      }
    })

    // Resize observer
    const ro = new ResizeObserver(() => {
      if (session.connected && activeSessionId.value === id) {
        try {
          fitAddon.fit()
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }))
          }
        } catch {}
      }
    })
    ro.observe(container)

    // Keep-alive
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)

    sessionData[id] = { term, fitAddon, ws, resizeObserver: ro, pingInterval: ping }

  } catch (err) {
    toast.error('Error: ' + err.message, 'SSH')
    removeSession(id)
  }
}

// ── Add session from form ──
const addSession = async () => {
  if (!canAdd.value || isConnecting.value) return
  isConnecting.value = true
  await createSession(
    newConn.value.host,
    newConn.value.username,
    newConn.value.password,
    newConn.value.port
  )
  isConnecting.value = false
  newConn.value.host = ''
  showConnectForm.value = false
}

// ── Bulk add sessions ──
const addBulkSessions = async () => {
  const hosts = bulkHosts.value.split(',').map(h => h.trim()).filter(Boolean)
  if (!hosts.length || !newConn.value.username || !newConn.value.password) return
  isConnecting.value = true
  for (const host of hosts) {
    if (sessions.value.length >= maxSessions) break
    await createSession(host, newConn.value.username, newConn.value.password, newConn.value.port)
  }
  isConnecting.value = false
  bulkHosts.value = ''
  showConnectForm.value = false
}

// ── Activate tab ──
const activateSession = (id) => {
  activeSessionId.value = id
  nextTick(() => {
    const sd = sessionData[id]
    if (sd) {
      try { sd.fitAddon.fit() } catch {}
      sd.term.focus()
      const s = sessions.value.find(x => x.id === id)
      if (s?.connected && sd.ws.readyState === WebSocket.OPEN) {
        sd.ws.send(JSON.stringify({ type: 'resize', cols: sd.term.cols, rows: sd.term.rows }))
      }
    }
  })
}

const connectedSessions = computed(() =>
  sessions.value.filter(s => s.connected)
)

// ── Send broadcast command to all sessions ──
const sendBroadcastCommand = () => {
  const cmd = broadcastCommand.value
  if (!cmd.trim()) return
  const payload = cmd + '\n'
  for (const s of sessions.value) {
    const sd = sessionData[s.id]
    if (sd?.ws?.readyState === WebSocket.OPEN && s.connected) {
      sd.ws.send(JSON.stringify({ type: 'input', data: payload }))
    }
  }
  toast.success(`Comando enviado a ${connectedSessions.value.length} sesiones`, 'Broadcast')
  broadcastCommand.value = ''
}

// ── Focus current terminal ──
const focusSession = (id) => {
  const sd = sessionData[id]
  if (sd) sd.term.focus()
}

// ── Close session ──
const closeSession = (id) => {
  const sd = sessionData[id]
  if (sd) {
    if (sd.ws && sd.ws.readyState === WebSocket.OPEN) {
      sd.ws.send(JSON.stringify({ type: 'close' }))
    }
    cleanupSession(id)
  }
  removeSession(id)
}

const cleanupSession = (id) => {
  const sd = sessionData[id]
  if (!sd) return
  if (sd.pingInterval) clearInterval(sd.pingInterval)
  if (sd.resizeObserver) sd.resizeObserver.disconnect()
  if (sd.ws) try { sd.ws.close() } catch {}
  if (sd.term) sd.term.dispose()
  delete sessionData[id]
  delete termRefs[id]
}

const removeSession = (id) => {
  cleanupSession(id)
  const idx = sessions.value.findIndex(s => s.id === id)
  if (idx !== -1) sessions.value.splice(idx, 1)
  if (activeSessionId.value === id) {
    activeSessionId.value = sessions.value.length > 0 ? sessions.value[sessions.value.length - 1].id : null
    if (activeSessionId.value) {
      nextTick(() => activateSession(activeSessionId.value))
    }
  }
  if (sessions.value.length === 0) showConnectForm.value = true
}

onBeforeUnmount(() => {
  for (const s of sessions.value) {
    const sd = sessionData[s.id]
    if (sd?.ws?.readyState === WebSocket.OPEN) {
      sd.ws.send(JSON.stringify({ type: 'close' }))
    }
    cleanupSession(s.id)
  }
  sessions.value = []
})
</script>

<style>
.xterm-container {
  width: 100%;
  height: 600px;
  background: #0f172a;
}
.xterm-container .xterm {
  padding: 8px;
  height: 100%;
}
.xterm-container .xterm-viewport {
  overflow-y: auto !important;
}
.xterm-container .xterm-viewport::-webkit-scrollbar {
  width: 8px;
}
.xterm-container .xterm-viewport::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
}
.xterm-container .xterm-viewport::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.5);
  border-radius: 4px;
}
.xterm-container .xterm-viewport::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.7);
}
</style>
