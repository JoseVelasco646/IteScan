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
          >Terminal SSH Interactiva</h3>
          <p 
            class="text-sm"
            :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
          >Conexión SSH en tiempo real con sesión persistente</p>
        </div>
      </div>
      
      <div class="flex items-center gap-3">
        <div 
          class="px-4 py-2 rounded-lg flex items-center gap-2"
          :class="isConnected 
            ? 'bg-emerald-500/20 border border-emerald-500/50' 
            : isDark() ? 'bg-slate-700/50 border border-slate-600' : 'bg-slate-200 border border-slate-300'"
        >
          <div 
            class="w-2 h-2 rounded-full"
            :class="isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'"
          ></div>
          <span 
            class="text-sm font-medium"
            :class="isConnected ? 'text-emerald-400' : isDark() ? 'text-slate-400' : 'text-slate-600'"
          >
            {{ isConnected ? 'Conectado' : 'Desconectado' }}
          </span>
        </div>
        
        <button
          v-if="isConnected"
          @click="disconnect"
          class="btn btn-danger text-sm"
        >
          Desconectar
        </button>
      </div>
    </div>

    <div 
      v-if="!isConnected"
      class="grid grid-cols-1 lg:grid-cols-2 gap-6"
    >
      <div 
        class="p-5 space-y-4 rounded-2xl border"
        :class="isDark() ? 'bg-slate-800/30 border-slate-700/50' : 'bg-slate-50 border-slate-200'"
      >
        <h4 
          class="text-lg font-semibold flex items-center gap-2"
          :class="isDark() ? 'text-white' : 'text-slate-800'"
        >
          <Key class="w-5 h-5 text-cyan-400" />
          Credenciales SSH
        </h4>
        
        <div class="space-y-3">
          <div>
            <label 
              class="text-sm font-medium mb-1 block"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
            >Host</label>
            <input
              v-model="connectionConfig.host"
              type="text"
              class="w-full px-4 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all"
              :class="isDark() 
                ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60' 
                : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400'"
              placeholder="192.168.0.1"
            />
          </div>
          
          <div>
            <label 
              class="text-sm font-medium mb-1 block"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
            >Usuario</label>
            <input
              v-model="connectionConfig.username"
              type="text"
              class="w-full px-4 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all"
              :class="isDark() 
                ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60' 
                : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400'"
              placeholder="usuario"
            />
          </div>
          
          <div>
            <label 
              class="text-sm font-medium mb-1 block"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
            >Contraseña</label>
            <input
              v-model="connectionConfig.password"
              type="password"
              class="w-full px-4 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all"
              :class="isDark() 
                ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60' 
                : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400'"
              placeholder="••••••••"
              @keyup.enter="connect"
            />
          </div>
          
          <div>
            <label 
              class="text-sm font-medium mb-1 block"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
            >Puerto</label>
            <input
              v-model.number="connectionConfig.port"
              type="number"
              class="w-full px-4 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all"
              :class="isDark() 
                ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60' 
                : 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400'"
              placeholder="22"
            />
          </div>
          
          <button
            @click="connect"
            :disabled="!canConnect || isConnecting"
            class="w-full btn btn-primary flex items-center justify-center gap-2"
          >
            <Loader2 v-if="isConnecting" class="w-5 h-5 animate-spin" />
            <Terminal v-else class="w-5 h-5" />
            {{ isConnecting ? 'Conectando...' : 'Conectar' }}
          </button>
        </div>
      </div>

      <div 
        class="p-5 space-y-4 rounded-2xl border"
        :class="isDark() ? 'bg-blue-500/10 border-blue-400/30' : 'bg-blue-50 border-blue-200'"
      >
        <h4 
          class="text-lg font-semibold flex items-center gap-2"
          :class="isDark() ? 'text-blue-300' : 'text-blue-700'"
        >
          <Info class="w-5 h-5" />
          Características
        </h4>
        
        <ul class="space-y-2 text-sm" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
          <li class="flex items-start gap-2">
            <span class="text-emerald-400 mt-0.5">✓</span>
            <span>Sesión SSH persistente y en tiempo real</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-emerald-400 mt-0.5">✓</span>
            <span>Soporte para comandos interactivos (top, htop, vim, etc.)</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-emerald-400 mt-0.5">✓</span>
            <span>Navegación de directorios (cd) mantiene el contexto</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-emerald-400 mt-0.5">✓</span>
            <span>Variables de entorno persistentes</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-emerald-400 mt-0.5">✓</span>
            <span>Output streaming en tiempo real</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-emerald-400 mt-0.5">✓</span>
            <span>Pseudo-terminal (PTY) completo</span>
          </li>
        </ul>
        
        <div 
          class="p-3 rounded-lg border"
          :class="isDark() ? 'bg-amber-500/10 border-amber-500/30' : 'bg-amber-50 border-amber-200'"
        >
          <p class="text-sm flex items-start gap-2" :class="isDark() ? 'text-amber-300' : 'text-amber-700'">
            <span class="text-lg">⚠️</span>
            <span>Esta es una terminal SSH real. Ten cuidado con los comandos que ejecutas.</span>
          </p>
        </div>
      </div>
    </div>

    <div 
      v-else
      class="overflow-hidden rounded-2xl border"
      :class="isDark() ? 'bg-slate-800/30 border-slate-700/50' : 'bg-white border-slate-200'"
    >
      <div 
        class="flex items-center justify-between px-4 py-3 border-b"
        :class="isDark() ? 'bg-slate-800/80 border-slate-700/50' : 'bg-slate-100 border-slate-200'"
      >
        <div class="flex items-center gap-3">
          <div class="flex gap-1.5">
            <span class="w-3 h-3 rounded-full bg-red-500 cursor-pointer hover:bg-red-600 transition-colors" @click="disconnect"></span>
            <span class="w-3 h-3 rounded-full bg-yellow-500"></span>
            <span class="w-3 h-3 rounded-full bg-green-500"></span>
          </div>
          <span 
            class="text-sm font-mono font-medium"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >{{ connectionConfig.username }}@{{ connectionConfig.host }}</span>
        </div>
        <button
          @click="clearTerminal"
          class="text-xs hover:text-cyan-400 transition-colors"
          :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
        >
          Limpiar
        </button>
      </div>
      
      <div 
        ref="terminalRef"
        class="p-4 font-mono text-sm h-[600px] overflow-y-auto cursor-text"
        :class="isDark() ? 'bg-slate-950 text-green-400' : 'bg-slate-900 text-green-300'"
        @click="focusInput"
      >
        <div class="whitespace-pre-wrap break-all" v-html="formattedOutput"></div>
        
        <div class="flex items-start">
          <span class="text-green-400 select-none">$ </span>
          <input
            ref="inputRef"
            v-model="currentInput"
            type="text"
            class="flex-1 bg-transparent outline-none border-none text-green-400 font-mono caret-green-400"
            @keydown="handleKeyDown"
            @paste="handlePaste"
            autocomplete="off"
            autocorrect="off"
            autocapitalize="off"
            spellcheck="false"
          />
          <span class="animate-pulse text-green-400">|</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { Terminal, Key, Info, Loader2 } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'
import { useTheme } from '../composables/useTheme'

const toast = useToast()
const { isDark } = useTheme()

const getApiBaseUrl = () => {
  return '192.168.0.6:8000'
}

const connectionConfig = ref({
  host: '',
  username: '',
  password: '',
  port: 22
})

const isConnected = ref(false)
const isConnecting = ref(false)
const terminalOutput = ref('')
const currentInput = ref('')
const ws = ref(null)
const sessionId = ref('')

const terminalRef = ref(null)
const inputRef = ref(null)

const canConnect = computed(() => {
  return connectionConfig.value.host && 
         connectionConfig.value.username && 
         connectionConfig.value.password
})

const formattedOutput = computed(() => {
  let output = terminalOutput.value
    .replace(/\x1B\[\?[0-9;]*[a-zA-Z]/g, '') 
    .replace(/\x1B\][0-9];[^\x07]*\x07/g, '') 
    .replace(/\x1B\[[0-9;]*[JKmHf]/g, '') 
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\r\n/g, '<br>')
    .replace(/\n/g, '<br>')
    .replace(/\r/g, '<br>')
  
  return output
})

const connect = async () => {
  if (!canConnect.value || isConnecting.value) return
  
  isConnecting.value = true
  sessionId.value = `ssh_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  try {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const apiHost = getApiBaseUrl()
    const wsUrl = `${wsProtocol}//${apiHost}/ws/ssh/${sessionId.value}`
    
    console.log('Connecting to WebSocket:', wsUrl)
    
    ws.value = new WebSocket(wsUrl)
    
    ws.value.onopen = () => {
      console.log('🔌 WebSocket connected, sending credentials...')
      ws.value.send(JSON.stringify({
        type: 'connect',
        host: connectionConfig.value.host,
        username: connectionConfig.value.username,
        password: connectionConfig.value.password,
        port: connectionConfig.value.port
      }))
    }
    
    ws.value.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('📩 WebSocket message received:', message)
          
        if (message.type === 'connected') {
          isConnected.value = true
          isConnecting.value = false
          console.log('✅ SSH Connected successfully')
          toast.success(`Conectado a ${connectionConfig.value.host}`, 'SSH Terminal')
          
          setTimeout(() => {
            sendInput('\n')
          }, 500)
          
          nextTick(() => {
            focusInput()
          })
        } else if (message.type === 'output') {
          if (message.data) {
            console.log('📤 Output received:', message.data.substring(0, 100) + '...')
            console.log('📤 Output hex:', message.data.split('').map(c => c.charCodeAt(0).toString(16)).join(' '))
            terminalOutput.value += message.data
            scrollToBottom()
          }
        } else if (message.type === 'error') {
          console.error('❌ SSH Error:', message.message)
          toast.error(message.message, 'SSH Error')
          isConnecting.value = false
          disconnect()
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e, event.data)
      }
    }
    
    ws.value.onerror = (error) => {
      console.error('WebSocket error:', error)
      toast.error('Error de conexión WebSocket', 'SSH Terminal')
      isConnecting.value = false
    }
    
    ws.value.onclose = () => {
      if (isConnected.value) {
        toast.warning('Conexión SSH cerrada', 'SSH Terminal')
      }
      isConnected.value = false
      isConnecting.value = false
    }
    
  } catch (error) {
    console.error('Connection error:', error)
    toast.error('Error al conectar: ' + error.message, 'SSH Terminal')
    isConnecting.value = false
  }
}

const disconnect = () => {
  if (ws.value) {
    ws.value.send(JSON.stringify({ type: 'close' }))
    ws.value.close()
    ws.value = null
  }
  isConnected.value = false
  isConnecting.value = false
  terminalOutput.value = ''
  currentInput.value = ''
}

const handleKeyDown = (event) => {
  if (!isConnected.value) return
  
  if (event.key === 'Enter') {
    event.preventDefault()
    const command = currentInput.value
    terminalOutput.value += `$ ${command}\n`
    sendInput(command + '\n')
    currentInput.value = ''
    scrollToBottom()
  }
  else if (event.ctrlKey && event.key === 'c') {
    event.preventDefault()
    terminalOutput.value += '^C\n'
    sendInput('\x03') 
    currentInput.value = ''
  }
  
  else if (event.ctrlKey && event.key === 'd') {
    event.preventDefault()
    sendInput('\x04') 
  }
  
  else if (event.ctrlKey && event.key === 'z') {
    event.preventDefault()
    sendInput('\x1A')
  }
  
  else if (event.key === 'Tab') {
    event.preventDefault()
    sendInput('\t')
  }
  else if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
    event.preventDefault()
    const specialKeys = {
      'ArrowUp': '\x1B[A',
      'ArrowDown': '\x1B[B',
      'ArrowRight': '\x1B[C',
      'ArrowLeft': '\x1B[D'
    }
    sendInput(specialKeys[event.key])
  }
  else if (['Backspace', 'Delete'].includes(event.key)) {
    event.preventDefault()
    const specialKeys = {
      'Backspace': '\x7F',
      'Delete': '\x1B[3~'
    }
    sendInput(specialKeys[event.key])
    if (event.key === 'Backspace' && currentInput.value.length > 0) {
      currentInput.value = currentInput.value.slice(0, -1)
    }
  }
}

const handlePaste = (event) => {
  event.preventDefault()
  const text = event.clipboardData.getData('text')
  sendInput(text)
  currentInput.value = ''
}

const sendInput = (data) => {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    console.log('⌨️ Sending input:', data.replace(/\n/g, '\\n').substring(0, 50))
    ws.value.send(JSON.stringify({
      type: 'input',
      data: data
    }))
  } else {
    console.error('❌ Cannot send input - WebSocket not open')
  }
}

const clearTerminal = () => {
  terminalOutput.value = ''
  currentInput.value = ''
  sendInput('clear\n')
}

const focusInput = () => {
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus()
    }
  })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (terminalRef.value) {
      terminalRef.value.scrollTop = terminalRef.value.scrollHeight
    }
  })
}

onMounted(() => {
  focusInput()
})

onBeforeUnmount(() => {
  disconnect()
})
</script>

<style scoped>
input[type="text"]:not([class*="px-"]) {
  caret-color: #4ade80;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.5);
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.7);
}
</style>
