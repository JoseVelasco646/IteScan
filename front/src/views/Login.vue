<template>
  <div class="min-h-screen flex items-center justify-center px-4 relative overflow-hidden"
    :class="isDark() ? 'bg-slate-950' : 'bg-gradient-to-br from-slate-50 via-cyan-50/30 to-blue-50'">

    
    <div v-if="isDark()" class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-float-slow"></div>
      <div
        class="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-float-slow-reverse">
      </div>
      <div
        class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-br from-cyan-500/3 to-blue-600/3 rounded-full blur-3xl">
      </div>
     
      <div class="absolute inset-0 opacity-[0.03]"
        style="background-image: radial-gradient(circle, rgba(34,211,238,0.3) 1px, transparent 1px); background-size: 40px 40px;">
      </div>
    </div>

    
    <div v-else class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-20 -right-20 w-72 h-72 bg-cyan-200/30 rounded-full blur-3xl"></div>
      <div class="absolute -bottom-20 -left-20 w-72 h-72 bg-blue-200/30 rounded-full blur-3xl"></div>
    </div>

    <div class="relative w-full max-w-md">
      
      <div v-if="isDark()"
        class="absolute -inset-1 bg-gradient-to-r from-cyan-500/20 via-blue-500/20 to-cyan-500/20 rounded-3xl blur-xl opacity-60">
      </div>

    
      <div
        class="relative w-full p-8 md:p-10 rounded-2xl border shadow-2xl transition-all duration-300 backdrop-blur-sm"
        :class="isDark()
          ? 'bg-slate-900/80 border-slate-700/50 shadow-cyan-500/5'
          : 'bg-white/80 border-slate-200 shadow-slate-200/50'">

        
        <div class="text-center mb-8">
          <div class="flex justify-center mb-5">
            <div class="relative group">
              
              <div class="absolute inset-0 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-none blur-lg transition-opacity duration-300"
                :class="isDark() ? 'opacity-30 group-hover:opacity-50' : 'opacity-15 group-hover:opacity-25'"></div>
              <div
                class="relative w-28 h-28 border-2 shadow-lg transition-all duration-300 overflow-hidden rounded-none"
                :class="isDark()
                  ? 'bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border-cyan-500/50 shadow-cyan-500/20'
                  : 'bg-gradient-to-br from-cyan-50 to-blue-100 border-cyan-300/60 shadow-cyan-200/30'"
              >
                <div class="absolute inset-0 grid place-items-center">
                  <Shield class="w-14 h-14 drop-shadow-lg" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
                </div>
              </div>
            </div>
          </div>

          <h1 class="text-3xl md:text-4xl font-bold tracking-tight font-display mb-1">
            <span :class="isDark() ? 'text-white' : 'text-slate-800'" class="drop-shadow-sm">ITE</span>
            <span
              class="text-4xl md:text-5xl font-extrabold bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent"
              :class="isDark() ? 'drop-shadow-[0_0_10px_rgba(34,211,238,0.6)]' : ''">
              Scan
            </span>
          </h1>
          <p class="text-sm font-medium tracking-wider uppercase"
            :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
            Acceso al Sistema
          </p>
        </div>

        
        <Transition name="shake-fade">
          <div v-if="error" class="mb-6 p-4 rounded-xl flex items-center gap-3 animate-shake border" :class="isDark()
            ? 'bg-red-500/10 border-red-500/30'
            : 'bg-red-50 border-red-200'">
            <div class="p-1.5 rounded-lg flex-shrink-0" :class="isDark() ? 'bg-red-500/20' : 'bg-red-100'">
              <AlertCircle class="w-4 h-4 text-red-500" />
            </div>
            <p class="text-sm font-medium" :class="isDark() ? 'text-red-300' : 'text-red-700'">{{ error }}</p>
          </div>
        </Transition>

       
        <form @submit.prevent="handleLogin" class="space-y-5" aria-label="Formulario de inicio de sesión">
          
          <div>
            <label for="login-username"
              class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider mb-2.5"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
              <User class="w-3.5 h-3.5" aria-hidden="true" />
              Usuario
            </label>
            <div class="relative group">
              <div
                class="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/0 to-blue-500/0 rounded-xl opacity-0 group-focus-within:opacity-100 group-focus-within:from-cyan-500/20 group-focus-within:to-blue-500/20 blur transition-all duration-300">
              </div>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-mono"
                  :class="isDark() ? 'text-slate-600' : 'text-slate-400'">@</span>
                <input id="login-username" v-model="username" type="text" placeholder="nombre_usuario"
                  autocomplete="username" required aria-required="true"
                  class="w-full pl-9 pr-4 py-3.5 rounded-xl font-mono text-sm focus:outline-none focus:ring-2 transition-all border"
                  :class="isDark()
                    ? 'bg-slate-800/60 border-slate-700 text-white placeholder-slate-600 focus:ring-cyan-500/50 focus:border-cyan-500/50'
                    : 'bg-slate-50/80 border-slate-200 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
                  @keydown="error = ''" />
              </div>
            </div>
          </div>

          
          <div>
            <label for="login-password"
              class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider mb-2.5"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
              <Lock class="w-3.5 h-3.5" aria-hidden="true" />
              Contraseña
            </label>
            <div class="relative group">
              <div
                class="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/0 to-blue-500/0 rounded-xl opacity-0 group-focus-within:opacity-100 group-focus-within:from-cyan-500/20 group-focus-within:to-blue-500/20 blur transition-all duration-300">
              </div>
              <div class="relative">
                <Lock class="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2"
                  :class="isDark() ? 'text-slate-600' : 'text-slate-400'" />
                <input id="login-password" v-model="password" :type="showPassword ? 'text' : 'password'"
                  placeholder="••••••••••" autocomplete="current-password" required aria-required="true"
                  class="w-full pl-11 pr-12 py-3.5 rounded-xl text-sm focus:outline-none focus:ring-2 transition-all border"
                  :class="isDark()
                    ? 'bg-slate-800/60 border-slate-700 text-white placeholder-slate-600 focus:ring-cyan-500/50 focus:border-cyan-500/50'
                    : 'bg-slate-50/80 border-slate-200 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
                  @keydown="error = ''" />
                <button type="button" @click="showPassword = !showPassword"
                  :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                  class="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-colors"
                  :class="isDark() ? 'hover:bg-slate-700 text-slate-600 hover:text-slate-400' : 'hover:bg-slate-100 text-slate-400 hover:text-slate-600'">
                  <EyeOff v-if="showPassword" class="w-4 h-4" />
                  <Eye v-else class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

         
          <button type="submit" :disabled="loading || !username || !password"
            class="group relative w-full px-10 py-5 rounded-xl font-bold tracking-widest uppercase text-sm border transition-all duration-300 ease-in-out shadow-[0_0_20px_rgba(34,211,238,0.25)] hover:shadow-[0_0_35px_rgba(34,211,238,0.45)] active:translate-y-1 active:shadow-[0_0_15px_rgba(34,211,238,0.45)] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-y-0 disabled:scale-100 mt-7"
            :class="isDark()
              ? 'bg-transparent text-cyan-400 border-cyan-500/50 hover:border-cyan-500 hover:text-cyan-300'
              : 'bg-transparent text-cyan-400 border-cyan-500/50 hover:border-cyan-500 hover:text-cyan-300'"
          >
            <span class="flex items-center justify-center gap-3 relative z-10">
              <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
              <svg
                v-else
                aria-hidden="true"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                class="w-5 h-5 transition-transform duration-300 group-hover:scale-125"
              >
                <g data-name="Layer 2" id="Layer_2">
                  <path
                    d="m15.626 11.769a6 6 0 1 0 -7.252 0 9.008 9.008 0 0 0 -5.374 8.231 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 9.008 9.008 0 0 0 -5.374-8.231zm-7.626-4.769a4 4 0 1 1 4 4 4 4 0 0 1 -4-4zm10 14h-12a1 1 0 0 1 -1-1 7 7 0 0 1 14 0 1 1 0 0 1 -1 1z">
                  </path>
                </g>
              </svg>

              {{ loading ? 'Iniciando sesión...' : 'Iniciar Sesión' }}

              <svg v-if="!loading" viewBox="0 0 24 24" fill="currentColor"
                class="w-4 h-4 transition-all duration-300 group-hover:-rotate-45 group-hover:scale-150"
                aria-hidden="true">
                <path d="M12 2v20m0-20L4 12m8-10l8 10"></path>
              </svg>
            </span>
            <div
              class="absolute inset-0 -z-10 bg-gradient-to-r from-cyan-600/25 to-blue-600/25 opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-xl rounded-xl">
            </div>
            <div
              class="absolute -inset-1 -z-10 bg-gradient-to-r from-cyan-600 to-blue-600 opacity-20 group-hover:opacity-30 blur-xl rounded-xl transition-all duration-300 group-hover:blur-2xl">
            </div>
          </button>
        </form>

        <!-- Footer -->
        <div class="mt-8 pt-6 border-t text-center" :class="isDark() ? 'border-slate-800' : 'border-slate-100'">
          <p class="text-[11px] uppercase tracking-widest font-medium flex items-center justify-center gap-2"
            :class="isDark() ? 'text-slate-600' : 'text-slate-400'">
            <ShieldCheck class="w-3.5 h-3.5" />
            Acceso exclusivo para administradores
          </p>
        </div>
      </div>
    </div>

    
    <Transition name="shake-fade">
      <div v-if="showForceChange"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
        <div class="relative w-full max-w-md p-8 rounded-2xl border shadow-2xl" :class="isDark()
          ? 'bg-slate-900 border-slate-700/50'
          : 'bg-white border-slate-200'">
          <div class="text-center mb-6">
            <div class="mx-auto w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              :class="isDark() ? 'bg-amber-500/20' : 'bg-amber-100'">
              <AlertCircle class="w-7 h-7 text-amber-500" />
            </div>
            <h2 class="text-xl font-bold mb-1" :class="isDark() ? 'text-white' : 'text-slate-800'">
              Cambio de contraseña requerido
            </h2>
            <p class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
              Por seguridad, debes cambiar tu contraseña antes de continuar.
            </p>
          </div>

          <Transition name="shake-fade">
            <div v-if="forceChangeError" class="mb-4 p-3 rounded-xl flex items-center gap-2 border text-sm"
              :class="isDark() ? 'bg-red-500/10 border-red-500/30 text-red-300' : 'bg-red-50 border-red-200 text-red-700'">
              <AlertCircle class="w-4 h-4 flex-shrink-0 text-red-500" />
              {{ forceChangeError }}
            </div>
          </Transition>

          <form @submit.prevent="handleForceChangePassword" class="space-y-4">
            <div>
              <label class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider mb-2"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
                <Lock class="w-3.5 h-3.5" /> Nueva contraseña
              </label>
              <input v-model="newPassword" type="password" required placeholder="Mínimo 8 caracteres"
                class="w-full px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 transition-all border"
                :class="isDark()
                  ? 'bg-slate-800/60 border-slate-700 text-white placeholder-slate-600 focus:ring-cyan-500/50'
                  : 'bg-slate-50/80 border-slate-200 text-slate-800 placeholder-slate-400 focus:ring-cyan-400'" />
            </div>
            <div>
              <label class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider mb-2"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
                <Lock class="w-3.5 h-3.5" /> Confirmar contraseña
              </label>
              <input v-model="confirmPassword" type="password" required placeholder="Repite la contraseña"
                class="w-full px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 transition-all border"
                :class="isDark()
                  ? 'bg-slate-800/60 border-slate-700 text-white placeholder-slate-600 focus:ring-cyan-500/50'
                  : 'bg-slate-50/80 border-slate-200 text-slate-800 placeholder-slate-400 focus:ring-cyan-400'" />
            </div>
            <!-- Reglas de contraseña -->
            <div v-if="newPassword" class="space-y-1 text-xs">
              <p
                :class="newPassword.length >= 8 ? 'text-emerald-500' : (isDark() ? 'text-slate-500' : 'text-slate-400')">
                {{ newPassword.length >= 8 ? '✓' : '○' }} Mínimo 8 caracteres
              </p>
              <p
                :class="/[A-Z]/.test(newPassword) ? 'text-emerald-500' : (isDark() ? 'text-slate-500' : 'text-slate-400')">
                {{ /[A-Z]/.test(newPassword) ? '✓' : '○' }} Al menos una mayúscula
              </p>
              <p
                :class="/[a-z]/.test(newPassword) ? 'text-emerald-500' : (isDark() ? 'text-slate-500' : 'text-slate-400')">
                {{ /[a-z]/.test(newPassword) ? '✓' : '○' }} Al menos una minúscula
              </p>
              <p
                :class="/\d/.test(newPassword) ? 'text-emerald-500' : (isDark() ? 'text-slate-500' : 'text-slate-400')">
                {{ /\d/.test(newPassword) ? '✓' : '○' }} Al menos un número
              </p>
            </div>
            <button type="submit" :disabled="forceChangeLoading || !newPassword || !confirmPassword"
              class="group relative w-full px-10 py-5 rounded-xl font-bold tracking-widest uppercase text-sm border transition-all duration-300 ease-in-out shadow-[0_0_20px_rgba(34,211,238,0.25)] hover:shadow-[0_0_35px_rgba(34,211,238,0.45)] active:translate-y-1 active:shadow-[0_0_15px_rgba(34,211,238,0.45)] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-y-0 disabled:scale-100"
              :class="isDark()
                ? 'bg-gradient-to-r from-cyan-500/90 to-blue-600/90 text-white border-cyan-500/40 hover:border-cyan-400'
                : 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white border-cyan-500/40 hover:border-cyan-500'">
              <span class="flex items-center justify-center gap-3 relative z-10">
                <Loader2 v-if="forceChangeLoading" class="w-5 h-5 animate-spin" />
                <svg v-else fill="currentColor" viewBox="0 0 24 24"
                  class="w-5 h-5 transition-transform duration-300 group-hover:scale-125" aria-hidden="true">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>

                {{ forceChangeLoading ? 'Cambiando...' : 'Cambiar contraseña' }}

                <svg v-if="!forceChangeLoading" viewBox="0 0 24 24" fill="currentColor"
                  class="w-4 h-4 transition-all duration-300 group-hover:-rotate-45 group-hover:scale-150"
                  aria-hidden="true">
                  <path d="M12 2v20m0-20L4 12m8-10l8 10"></path>
                </svg>
              </span>
              <div
                class="absolute inset-0 -z-10 bg-gradient-to-r from-cyan-600/25 to-blue-600/25 opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-xl rounded-md">
              </div>
              <div
                class="absolute -inset-1 -z-10 bg-gradient-to-r from-cyan-600 to-blue-600 opacity-20 group-hover:opacity-30 blur-xl rounded-md transition-all duration-300 group-hover:blur-2xl">
              </div>
            </button>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Shield, User, Lock, Eye, EyeOff, Loader2, AlertCircle, ShieldCheck } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'
import { reconnectGlobalWebSocket } from '@/composables/useWebSocket'

const API_URL = import.meta.env.VITE_API_URL || window.location.origin.replace(':3000', ':8000')

const router = useRouter()
const { isDark } = useTheme()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

// Forzar cambio de contraseña
const showForceChange = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')
const forceChangeError = ref('')
const forceChangeLoading = ref(false)
const tempToken = ref('')

const handleLogin = async () => {
  if (!username.value || !password.value) return

  loading.value = true
  error.value = ''

  try {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })

    const data = await response.json()

    if (response.ok) {
      if (data.must_change_password) {
        // Guardar token temporal para la petición de cambio
        tempToken.value = data.token
        showForceChange.value = true
      } else {
        sessionStorage.removeItem('manual_logout')
        localStorage.setItem('admin_token', data.token)
        localStorage.setItem('admin_user', JSON.stringify(data.user))
        reconnectGlobalWebSocket()
        const redirect = router.currentRoute.value.query.redirect || '/'
        router.push(redirect)
      }
    } else {
      error.value = data.detail || 'Error al iniciar sesión'
    }
  } catch (err) {
    error.value = 'No se pudo conectar con el servidor'
  } finally {
    loading.value = false
  }
}

const handleForceChangePassword = async () => {
  forceChangeError.value = ''

  if (newPassword.value !== confirmPassword.value) {
    forceChangeError.value = 'Las contraseñas no coinciden'
    return
  }
  if (newPassword.value.length < 8 || !/[A-Z]/.test(newPassword.value) || !/[a-z]/.test(newPassword.value) || !/\d/.test(newPassword.value)) {
    forceChangeError.value = 'La contraseña no cumple los requisitos de seguridad'
    return
  }
  if (newPassword.value === password.value) {
    forceChangeError.value = 'La nueva contraseña debe ser diferente a la actual'
    return
  }

  forceChangeLoading.value = true
  try {
    const response = await fetch(`${API_URL}/api/auth/change-password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${tempToken.value}`
      },
      body: JSON.stringify({
        current_password: password.value,
        new_password: newPassword.value
      })
    })

    const data = await response.json()

    if (response.ok) {
      sessionStorage.removeItem('manual_logout')
      localStorage.setItem('admin_token', data.token)
      localStorage.setItem('admin_user', JSON.stringify(data.user))
      reconnectGlobalWebSocket()
      const redirect = router.currentRoute.value.query.redirect || '/'
      router.push(redirect)
    } else {
      forceChangeError.value = data.detail || 'Error al cambiar la contraseña'
    }
  } catch (err) {
    forceChangeError.value = 'No se pudo conectar con el servidor'
  } finally {
    forceChangeLoading.value = false
  }
}
</script>

<style scoped>
@keyframes shake {

  0%,
  100% {
    transform: translateX(0);
  }

  25% {
    transform: translateX(-5px);
  }

  75% {
    transform: translateX(5px);
  }
}

.animate-shake {
  animation: shake 0.3s ease-out;
}

@keyframes float-slow {

  0%,
  100% {
    transform: translate(0, 0);
  }

  50% {
    transform: translate(20px, -20px);
  }
}

@keyframes float-slow-reverse {

  0%,
  100% {
    transform: translate(0, 0);
  }

  50% {
    transform: translate(-20px, 20px);
  }
}

.animate-float-slow {
  animation: float-slow 15s ease-in-out infinite;
}

.animate-float-slow-reverse {
  animation: float-slow-reverse 18s ease-in-out infinite;
}

.shake-fade-enter-active {
  transition: all 0.3s ease;
}

.shake-fade-leave-active {
  transition: all 0.2s ease;
}

.shake-fade-enter-from,
.shake-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
