<template>
  <div class="min-h-screen flex items-center justify-center px-4" :class="isDark() ? 'bg-gray-900' : 'bg-gray-50'">
    <div class="text-center max-w-2xl">
      <div class="mb-8 relative">
        <div class="text-9xl font-bold" :class="isDark() ? 'text-gray-700' : 'text-gray-300'">
          404
        </div>
        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <div class="text-6xl animate-bounce">🔍</div>
        </div>
      </div>

      <h1 class="text-4xl font-bold mb-4" :class="isDark() ? 'text-white' : 'text-gray-900'">
        Página No Encontrada
      </h1>
      <p class="text-xl mb-8" :class="isDark() ? 'text-gray-400' : 'text-gray-600'">
        Lo sentimos, la página que buscas no existe o ha sido movida.
      </p>

      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          @click="goHome"
          class="px-6 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105"
          :class="isDark() ? 
            'bg-blue-600 text-white hover:bg-blue-700' : 
            'bg-blue-500 text-white hover:bg-blue-600'"
        >
          ← Volver al Dashboard
        </button>
        <button
          @click="goBack"
          class="px-6 py-3 rounded-lg font-semibold transition-all duration-200"
          :class="isDark() ? 
            'bg-gray-700 text-white hover:bg-gray-600' : 
            'bg-gray-200 text-gray-800 hover:bg-gray-300'"
        >
          Regresar
        </button>
      </div>

      <div class="mt-12 p-6 rounded-lg" :class="isDark() ? 'bg-gray-800' : 'bg-white shadow-md'">
        <h2 class="text-lg font-semibold mb-3" :class="isDark() ? 'text-white' : 'text-gray-900'">
          ¿Necesitas ayuda?
        </h2>
        <p class="text-sm" :class="isDark() ? 'text-gray-400' : 'text-gray-600'">
          Si crees que esto es un error, por favor verifica la URL o contacta al administrador del sistema.
        </p>
        <div class="mt-4 flex items-center justify-center gap-2 text-sm" :class="isDark() ? 'text-gray-500' : 'text-gray-500'">
          <span>URL solicitada:</span>
          <code class="px-2 py-1 rounded" :class="isDark() ? 'bg-gray-700 text-blue-400' : 'bg-gray-100 text-blue-600'">
            {{ currentPath }}
          </code>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import { computed } from 'vue'

const router = useRouter()
const route = useRoute()
const { isDark } = useTheme()

const currentPath = computed(() => route.fullPath)

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.animate-bounce {
  animation: bounce 2s infinite;
}
</style>
