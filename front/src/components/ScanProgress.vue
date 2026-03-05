<template>
  <Transition name="progress">
    <div 
      v-if="progress.active || progress.status === 'completed'" 
      class="mb-6 backdrop-blur-sm rounded-2xl p-6 border shadow-xl animate-slide-down transition-all duration-300"
      :class="isDark() 
        ? 'bg-gradient-to-br from-slate-800/60 to-slate-900/60 border-cyan-500/50' 
        : 'bg-gradient-to-br from-white/80 to-slate-50/80 border-cyan-400/50 shadow-lg'"
    >
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="relative">
            <!-- Spinner animado -->
            <div 
              v-if="progress.status !== 'completed'" 
              class="w-12 h-12 border-4 rounded-full animate-spin"
              :class="isDark() 
                ? 'border-cyan-400/30 border-t-cyan-400' 
                : 'border-cyan-500/30 border-t-cyan-500'"
            ></div>
            <!-- Checkmark completado -->
            <div 
              v-else 
              class="w-12 h-12 border-4 rounded-full flex items-center justify-center"
              :class="isDark()
                ? 'border-green-500/30 bg-green-500/20'
                : 'border-green-400/50 bg-green-100'"
            >
              <svg class="w-6 h-6" :class="isDark() ? 'text-green-400' : 'text-green-600'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <component 
              :is="getScanIcon()" 
              class="w-5 h-5 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" 
              :class="progress.status === 'completed' 
                ? isDark() ? 'text-green-400' : 'text-green-600'
                : isDark() ? 'text-cyan-400' : 'text-cyan-600'" 
            />
          </div>
          <div>
            <h3 
              class="text-lg font-bold font-display"
              :class="isDark() ? 'text-white' : 'text-slate-800'"
            >{{ getScanTitle() }}</h3>
            <p 
              class="text-sm"
              :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
            >{{ getCurrentInfo() }}</p>
          </div>
        </div>
        <div class="text-right">
          <p 
            class="text-3xl font-extrabold tabular-nums transition-all duration-150"
            :class="progress.status === 'completed' 
              ? isDark() ? 'text-green-400' : 'text-green-600'
              : isDark() ? 'text-cyan-400' : 'text-cyan-600'"
          >
            {{ animatedProgress.toFixed(0) }}%
          </p>
          <p 
            v-if="progress.total" 
            class="text-sm tabular-nums"
            :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
          >{{ progress.completed }} / {{ progress.total }}</p>
        </div>
      </div>
      
      <!-- Barra de progreso mejorada -->
      <div 
        class="h-3 rounded-full overflow-hidden relative"
        :class="isDark() ? 'bg-slate-700/50' : 'bg-slate-200'"
      >
        <!-- Fondo con patrón -->
        <div 
          class="absolute inset-0 opacity-20"
          :class="isDark() ? 'bg-slate-600' : 'bg-slate-300'"
        ></div>
        
        <!-- Barra de progreso principal -->
        <div 
          class="h-full rounded-full relative overflow-hidden"
          :class="progress.status === 'completed' 
            ? 'bg-gradient-to-r from-green-500 to-emerald-500' 
            : 'bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500'"
          :style="{ width: `${animatedProgress}%`, transition: 'width 0.15s ease-out' }"
        >
          <!-- Efecto shimmer -->
          <div 
            v-if="progress.status !== 'completed'" 
            class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"
          ></div>
          
          <!-- Efecto de pulso en la punta -->
          <div 
            v-if="progress.status !== 'completed' && animatedProgress > 0"
            class="absolute right-0 top-0 bottom-0 w-2 bg-white/50 animate-pulse"
          ></div>
        </div>
      </div>
      
      <!-- Estadísticas adicionales -->
      <div 
        v-if="progress.total && progress.status !== 'completed'"
        class="flex items-center justify-between mt-3 text-xs"
        :class="isDark() ? 'text-slate-500' : 'text-slate-400'"
      >
        <span>Escaneando: {{ progress.current_host || '...' }}</span>
        <span v-if="estimatedTimeRemaining">
          Tiempo restante: ~{{ estimatedTimeRemaining }}
        </span>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { Activity, Wifi, Server, Shield, Network, Search, Zap } from 'lucide-vue-next'
import { useTheme } from '../composables/useTheme'

const { isDark } = useTheme()

const props = defineProps({
  progress: {
    type: Object,
    required: true,
    default: () => ({
      active: false,
      scan_id: null,
      scan_type: null,
      status: 'idle',
      total: 0,
      completed: 0,
      progress: 0,
      current_host: null,
      stage: null
    })
  }
})

// Progreso animado para transiciones suaves
const animatedProgress = ref(0)
let animationFrame = null
let startTime = null

// Declarar función ANTES del watch
const animateProgress = (targetValue) => {
  if (animationFrame) {
    cancelAnimationFrame(animationFrame)
  }
  
  const startValue = animatedProgress.value
  const duration = 150 // 150ms para animación rápida
  startTime = performance.now()
  
  const animate = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    
    // Easing function (ease-out)
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedProgress.value = startValue + (targetValue - startValue) * eased
    
    if (progress < 1) {
      animationFrame = requestAnimationFrame(animate)
    }
  }
  
  animationFrame = requestAnimationFrame(animate)
}

// Watch DESPUÉS de declarar la función
watch(() => props.progress.progress, (newVal) => {
  animateProgress(newVal)
}, { immediate: true })

onUnmounted(() => {
  if (animationFrame) {
    cancelAnimationFrame(animationFrame)
  }
})

// Calcular tiempo restante estimado
const estimatedTimeRemaining = computed(() => {
  if (!props.progress.completed || !props.progress.total || props.progress.completed === 0) {
    return null
  }
  
  const remaining = props.progress.total - props.progress.completed
  
  // Usar host_timeout si está disponible, de lo contrario usar estimación predeterminada
  let secondsPerHost = 0.5 // valor por defecto
  
  if (props.progress.host_timeout) {
    // Usar el 70% del timeout como estimación (ya que no siempre usa todo el tiempo)
    secondsPerHost = props.progress.host_timeout * 0.7
  } else if (props.progress.scan_type === 'services' || props.progress.scan_type === 'full') {
    secondsPerHost = 60 // Para servicios/full scan sin timeout, asumir 60s
  }
  
  const secondsRemaining = remaining * secondsPerHost
  
  if (secondsRemaining < 60) {
    return `${Math.round(secondsRemaining)}s`
  } else {
    const minutes = Math.floor(secondsRemaining / 60)
    const seconds = Math.round(secondsRemaining % 60)
    return `${minutes}m ${seconds}s`
  }
})

const getScanIcon = () => {
  const icons = {
    ping: Wifi,
    ports: Server,
    services: Search,
    os: Shield,
    mac: Network,
    full: Zap
  }
  return icons[props.progress.scan_type] || Activity
}

const getScanTitle = () => {
  const titles = {
    ping: 'Escaneo de Red',
    ports: 'Escaneo de Puertos',
    services: 'Detección de Servicios',
    os: 'Detección de Sistema Operativo',
    mac: 'Escaneo de Direcciones MAC',
    full: 'Escaneo Completo'
  }
  return titles[props.progress.scan_type] || 'Escaneando'
}

const getCurrentInfo = () => {
  if (props.progress.status === 'completed') {
    return 'Escaneo completado exitosamente'
  }
  
  if (props.progress.stage) {
    const stages = {
      ping: 'Verificando conectividad',
      mac: 'Obteniendo dirección MAC',
      ports: 'Escaneando puertos',
      'services & os': 'Detectando servicios y OS',
      vulnerabilities: 'Escaneando vulnerabilidades'
    }
    return stages[props.progress.stage] || props.progress.stage
  }
  
  if (props.progress.current_host) {
    return props.progress.current_host
  }
  
  if (props.progress.network) {
    return props.progress.network
  }
  
  if (props.progress.status === 'started') {
    return 'Iniciando escaneo...'
  }
  
  return 'Procesando...'
}
</script>

<style scoped>
@keyframes slide-down {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(200%);
  }
}

.animate-slide-down {
  animation: slide-down 0.3s ease-out;
}

.animate-shimmer {
  animation: shimmer 1.5s infinite;
}

.progress-enter-active,
.progress-leave-active {
  transition: all 0.3s ease;
}

.progress-enter-from,
.progress-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}
</style>
