<script setup>
import { computed } from 'vue'
import { useScanState } from '../composables/useScanState'
import { useTheme } from '../composables/useTheme'
import { AlertTriangle, XCircle, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  myScanType: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['cancelled'])

const { isScanning, currentScanType, scanDisplayName, cancelActiveScan } = useScanState()
const { isDark } = useTheme()

// Mostrar si hay un scan activo y no es de este componente
const showBanner = computed(() => {
  if (!isScanning.value) return false
  // Si el scan activo es del mismo tipo que este componente, no mostrar banner
  if (currentScanType.value === props.myScanType) return false
  // Para FullScan, ambas variantes (single/range) son del mismo componente
  if (props.myScanType === 'fullscan') {
    return !currentScanType.value.startsWith('full-scan')
  }
  return true
})

const handleCancel = () => {
  cancelActiveScan()
  emit('cancelled')
}
</script>

<template>
  <Transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="opacity-0 -translate-y-2 scale-98"
    enter-to-class="opacity-100 translate-y-0 scale-100"
    leave-active-class="transition-all duration-200 ease-in"
    leave-from-class="opacity-100 translate-y-0"
    leave-to-class="opacity-0 -translate-y-2"
  >
    <div
      v-if="showBanner"
      class="rounded-2xl p-5 border-2 backdrop-blur-sm mb-6"
      :class="isDark()
        ? 'bg-gradient-to-r from-amber-900/30 via-orange-900/20 to-amber-900/30 border-amber-500/40'
        : 'bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 border-amber-300'"
    >
      <div class="flex items-start gap-4">
        <div class="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center"
          :class="isDark() ? 'bg-amber-500/20' : 'bg-amber-100'">
          <AlertTriangle class="w-6 h-6" :class="isDark() ? 'text-amber-400' : 'text-amber-600'" />
        </div>

        <div class="flex-1 min-w-0">
          <h4 class="font-bold text-lg mb-1" :class="isDark() ? 'text-amber-300' : 'text-amber-700'">
            Escaneo en curso
          </h4>
          <p class="text-sm mb-3" :class="isDark() ? 'text-amber-200/80' : 'text-amber-600'">
            Hay un <span class="font-bold">{{ scanDisplayName }}</span> ejecutándose en segundo plano.
            Debe cancelarlo antes de iniciar un nuevo escaneo.
          </p>

          <div class="flex items-center gap-3">
            <!-- Indicador de actividad -->
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold"
              :class="isDark() ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'">
              <Loader2 class="w-3.5 h-3.5 animate-spin" />
              <span>{{ scanDisplayName }} activo</span>
            </div>

            <!-- Botón cancelar -->
            <button
              @click="handleCancel"
              class="flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all duration-200"
              :class="isDark()
                ? 'bg-red-500/20 text-red-300 border border-red-500/40 hover:bg-red-500/30 hover:border-red-400'
                : 'bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 hover:border-red-300'"
            >
              <XCircle class="w-3.5 h-3.5" />
              <span>Cancelar escaneo actual</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>
