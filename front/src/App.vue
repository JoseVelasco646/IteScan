<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Shield, Sun, Moon, Lock } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import axios from 'axios'
import ToastNotification from './components/ToastNotification.vue'
import { useToast } from './composables/useToast'
import { useTheme } from './composables/useTheme'

const router = useRouter()
const isBackendOnline = ref(false)
const isIpBlocked = ref(false)
let statusCheckInterval = null

const { toasts } = useToast()
const { theme, toggleTheme, isDark } = useTheme()

const checkBackendStatus = async () => {
  if (router.currentRoute.value.path === '/access-denied') {
    return
  }

  try {
    const response = await axios.get('http://192.168.0.10:8000/health', { timeout: 3000 })
    isBackendOnline.value = true
    isIpBlocked.value = false
  } catch (error) {
    if (error.response && error.response.status === 403) {
      isIpBlocked.value = true
      
      try {
        const ipResponse = await axios.get('http://192.168.0.10:8000/api/get-client-ip', { 
          timeout: 2000,
          validateStatus: () => true 
        })
        if (ipResponse.data && ipResponse.data.ip) {
          localStorage.setItem('blocked_ip', ipResponse.data.ip)
        }
      } catch (ipError) {
        console.error('No se pudo obtener IP:', ipError)
      }
      
      router.push('/access-denied')
    }
    isBackendOnline.value = false
  }
}

onMounted(() => {
  checkBackendStatus()
 
  statusCheckInterval = setInterval(checkBackendStatus, 10000)
})

onUnmounted(() => {
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval)
  }
})

// dark y light
const headerClasses = computed(() => {
  return isDark()
    ? 'bg-gradient-to-r from-slate-900 via-slate-950 to-slate-900 border-slate-700/50'
    : 'bg-gradient-to-r from-white via-slate-50 to-white border-slate-200 shadow-lg'
})

const iconContainerClasses = computed(() => {
  return isDark()
    ? 'bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border-cyan-500/50 shadow-cyan-500/30'
    : 'bg-gradient-to-br from-cyan-100 to-blue-100 border-cyan-400/50 shadow-cyan-400/20'
})

const titleClasses = computed(() => {
  return isDark() ? 'text-slate-200' : 'text-slate-800'
})

const subtitleClasses = computed(() => {
  return isDark() ? 'text-cyan-400/80' : 'text-cyan-600'
})
</script>

<template>
  <header
    class="w-full p-6 md:p-8 border-b backdrop-blur-xl sticky top-0 z-50 transition-all duration-300"
    :class="headerClasses"
  >
    <div class="w-full flex items-center justify-between">
      <div class="flex items-center gap-6">
        <div 
          class="h-16 w-px bg-gradient-to-b from-transparent to-transparent"
          :class="isDark() ? 'via-cyan-500/50' : 'via-cyan-400/50'"
        ></div>

        <div class="relative group">
          <div 
            class="absolute inset-0 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl blur-xl transition-opacity duration-300"
            :class="isDark() ? 'opacity-30 group-hover:opacity-50' : 'opacity-20 group-hover:opacity-30'"
          ></div>
          <div 
            class="relative p-4 rounded-2xl border-2 shadow-lg transition-all duration-300"
            :class="iconContainerClasses"
          >
            <Shield 
              class="w-10 h-10 drop-shadow-lg"
              :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
            />
            <span class="absolute -top-1 -right-1 flex h-4 w-4">
              <span
                class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                :class="isDark() ? 'bg-cyan-400' : 'bg-cyan-500'"
              ></span>
              <span 
                class="relative inline-flex rounded-full h-4 w-4 shadow-lg"
                :class="isDark() ? 'bg-cyan-500 shadow-cyan-500/50' : 'bg-cyan-600 shadow-cyan-600/30'"
              ></span>
            </span>
          </div>
        </div>

        <div>
          <h1 class="flex items-baseline gap-2 text-3xl md:text-4xl font-bold tracking-tight font-display">
            <span :class="titleClasses" class="drop-shadow-lg">ITE</span>
            <span
              class="text-4xl md:text-5xl font-extrabold bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent animate-pulse"
              :class="isDark() ? 'drop-shadow-[0_0_12px_rgba(34,211,238,0.8)]' : 'drop-shadow-[0_0_8px_rgba(8,145,178,0.5)]'"
            >
              Scan
            </span>
          </h1>

          <p 
            class="text-sm md:text-base font-medium tracking-widest uppercase mt-1 flex items-center gap-2"
            :class="subtitleClasses"
          >
            Sistema de Análisis y Monitoreo de Redes
          </p>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <button
          v-if="!isIpBlocked"
          @click="router.push('/whitelist')"
          class="relative p-3 rounded-xl border-2 transition-all duration-300 group"
          :class="isDark() 
            ? 'border-slate-700/50 bg-slate-900/50 hover:bg-slate-800/50 hover:border-purple-500/50' 
            : 'border-slate-200 bg-white hover:bg-slate-50 hover:border-purple-400/50 shadow-sm'"
          title="Administrar Whitelist"
        >
          <Lock
            class="w-6 h-6 transition-transform duration-300 group-hover:scale-110"
            :class="isDark() ? 'text-purple-400' : 'text-purple-600'"
          />
        </button>

        <button
          @click="toggleTheme"
          class="relative p-3 rounded-xl border-2 transition-all duration-300 group"
          :class="isDark() 
            ? 'border-slate-700/50 bg-slate-900/50 hover:bg-slate-800/50 hover:border-cyan-500/50' 
            : 'border-slate-200 bg-white hover:bg-slate-50 hover:border-cyan-400/50 shadow-sm'"
          :aria-label="theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
        >
          <div class="relative w-6 h-6">
            <Transition name="theme-icon">
              <Sun
                v-if="theme === 'light'"
                key="sun"
                class="absolute inset-0 w-6 h-6 text-amber-500 group-hover:rotate-90 transition-transform duration-300"
              />
              <Moon
                v-else
                key="moon"
                class="absolute inset-0 w-6 h-6 text-cyan-400 group-hover:-rotate-12 transition-transform duration-300"
              />
            </Transition>
          </div>
        </button>

        <div
          class="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl border-2 transition-all duration-300"
          :class="
            isBackendOnline
              ? isDark() 
                ? 'bg-green-500/20 border-green-500/50 shadow-lg shadow-green-500/20'
                : 'bg-green-50 border-green-300 shadow-md shadow-green-100'
              : isDark()
                ? 'bg-red-500/20 border-red-500/50 shadow-lg shadow-red-500/20'
                : 'bg-red-50 border-red-300 shadow-md shadow-red-100'
          "
        >
          <span class="relative flex h-3 w-3">
            <span
              class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
              :class="isBackendOnline ? 'bg-green-400' : 'bg-red-400'"
            ></span>
            <span
              class="relative inline-flex rounded-full h-3 w-3"
              :class="isBackendOnline ? 'bg-green-500' : 'bg-red-500'"
            ></span>
          </span>
          <span
            class="text-sm font-semibold uppercase tracking-wider"
            :class="isBackendOnline 
              ? isDark() ? 'text-green-400' : 'text-green-600'
              : isDark() ? 'text-red-400' : 'text-red-600'"
          >
            {{ isBackendOnline ? 'Online' : 'Offline' }}
          </span>
        </div>
      </div>
    </div>
  </header>

  <router-view></router-view>

  <div class="toast-container">
    <ToastNotification
      v-for="toast in toasts"
      :key="toast.id"
      :type="toast.type"
      :title="toast.title"
      :message="toast.message"
      :duration="toast.duration"
      :visible="toast.visible"
      @close="() => toast.visible = false"
    />
  </div>
</template>

<style>
.toast-container {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 9999;
  pointer-events: none;
}

.toast-container > * {
  pointer-events: auto;
}

.theme-icon-enter-active,
.theme-icon-leave-active {
  transition: all 0.3s ease;
}

.theme-icon-enter-from {
  opacity: 0;
  transform: rotate(-90deg) scale(0.5);
}

.theme-icon-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.5);
}
</style>
