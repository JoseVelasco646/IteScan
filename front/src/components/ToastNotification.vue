<template>
  <Transition name="toast">
    <div
      v-if="visible"
      class="fixed top-6 right-6 z-[9999] max-w-md animate-slide-in-right"
      role="alert"
      aria-live="assertive"
    >
      <div
        class="relative overflow-hidden rounded-2xl border-2 shadow-2xl backdrop-blur-xl"
        :class="toastClasses"
      >
        <div
          v-if="duration > 0"
          class="absolute bottom-0 left-0 h-1 transition-all ease-linear"
          :class="progressBarClass"
          :style="{ width: `${progress}%`, transitionDuration: `${duration}ms` }"
        ></div>

        <div class="relative z-10 p-5 flex items-start gap-4">
          <div
            class="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center"
            :class="iconBgClass"
          >
            <component :is="icon" class="w-6 h-6" :class="iconColorClass" />
          </div>

          <div class="flex-1 pt-1">
            <h4 v-if="title" class="font-bold text-lg mb-1" :class="titleColorClass">
              {{ title }}
            </h4>
            <p class="text-sm leading-relaxed" :class="messageColorClass">
              {{ message }}
            </p>
          </div>

          <button
            @click="close"
            class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all hover:scale-110"
            :class="closeBtnClass"
            aria-label="Cerrar notificación"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <div class="absolute inset-0 opacity-20 pointer-events-none">
          <div
            class="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent -translate-x-full animate-shimmer"
          ></div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-vue-next'

const props = defineProps({
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
  },
  title: {
    type: String,
    default: ''
  },
  message: {
    type: String,
    required: true
  },
  duration: {
    type: Number,
    default: 4000
  },
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const progress = ref(100)
let progressInterval = null

const icon = computed(() => {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertCircle,
    info: Info
  }
  return icons[props.type]
})

const toastClasses = computed(() => {
  const classes = {
    success: 'bg-gradient-to-br from-emerald-900/90 to-emerald-950/90 border-emerald-500/50',
    error: 'bg-gradient-to-br from-red-900/90 to-red-950/90 border-red-500/50',
    warning: 'bg-gradient-to-br from-amber-900/90 to-amber-950/90 border-amber-500/50',
    info: 'bg-gradient-to-br from-blue-900/90 to-blue-950/90 border-blue-500/50'
  }
  return classes[props.type]
})

const iconBgClass = computed(() => {
  const classes = {
    success: 'bg-emerald-500/20',
    error: 'bg-red-500/20',
    warning: 'bg-amber-500/20',
    info: 'bg-blue-500/20'
  }
  return classes[props.type]
})

const iconColorClass = computed(() => {
  const classes = {
    success: 'text-emerald-400',
    error: 'text-red-400',
    warning: 'text-amber-400',
    info: 'text-blue-400'
  }
  return classes[props.type]
})

const titleColorClass = computed(() => {
  const classes = {
    success: 'text-emerald-300',
    error: 'text-red-300',
    warning: 'text-amber-300',
    info: 'text-blue-300'
  }
  return classes[props.type]
})

const messageColorClass = computed(() => {
  const classes = {
    success: 'text-emerald-200/90',
    error: 'text-red-200/90',
    warning: 'text-amber-200/90',
    info: 'text-blue-200/90'
  }
  return classes[props.type]
})

const closeBtnClass = computed(() => {
  const classes = {
    success: 'text-emerald-400 hover:bg-emerald-500/20',
    error: 'text-red-400 hover:bg-red-500/20',
    warning: 'text-amber-400 hover:bg-amber-500/20',
    info: 'text-blue-400 hover:bg-blue-500/20'
  }
  return classes[props.type]
})

const progressBarClass = computed(() => {
  const classes = {
    success: 'bg-emerald-500',
    error: 'bg-red-500',
    warning: 'bg-amber-500',
    info: 'bg-blue-500'
  }
  return classes[props.type]
})

const close = () => {
  if (progressInterval) {
    clearInterval(progressInterval)
  }
  emit('close')
}

watch(
  () => props.visible,
  (newVal) => {
    if (newVal && props.duration > 0) {
      progress.value = 100
      const step = 100 / (props.duration / 100)
      
      progressInterval = setInterval(() => {
        progress.value -= step
        if (progress.value <= 0) {
          clearInterval(progressInterval)
          close()
        }
      }, 100)
    }
  },
  { immediate: true }
)
</script>

<style scoped>
@keyframes slide-in-right {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.animate-slide-in-right {
  animation: slide-in-right 0.3s ease-out;
}

.animate-shimmer {
  animation: shimmer 3s infinite;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.toast-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
