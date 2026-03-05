<template>
  <div class="min-h-screen p-4 md:p-6 lg:p-8" :class="isDark() ? 'bg-slate-950' : 'bg-slate-50'" role="main" aria-label="Panel de administración de usuarios">
    <div class="max-w-6xl mx-auto space-y-6">

      <!-- ═══ Header ═══ -->
      <div class="flex items-center justify-between flex-wrap gap-4">
        <div class="flex items-center gap-4">
          <div class="p-3 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 rounded-xl border-2 border-cyan-500/50 shadow-lg shadow-cyan-500/10">
            <Users class="w-7 h-7 text-cyan-400" />
          </div>
          <div>
            <h1 class="text-2xl md:text-3xl font-bold font-display" :class="isDark() ? 'text-white' : 'text-slate-800'">
              Gestión de Usuarios
            </h1>
            <p class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
              Administra cuentas, roles y permisos de acceso
            </p>
          </div>
        </div>
        <button
          @click="$router.push('/')"
          class="px-5 py-2.5 rounded-xl font-medium text-sm transition-all flex items-center gap-2 border"
          :class="isDark()
            ? 'bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 border-slate-700 hover:border-slate-600'
            : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200 shadow-sm'"
        >
          <ArrowLeft class="w-4 h-4" />
          Volver al Dashboard
        </button>
      </div>

      <!-- ═══ Current User Card ═══ -->
      <div class="relative overflow-hidden rounded-2xl border p-5"
        :class="isDark() ? 'bg-gradient-to-r from-cyan-950/40 to-slate-800/50 border-cyan-500/30' : 'bg-gradient-to-r from-cyan-50 to-blue-50 border-cyan-200'">
        <div class="absolute top-0 right-0 w-32 h-32 opacity-5">
          <UserCheck class="w-full h-full text-cyan-500" />
        </div>
        <div class="relative flex items-center gap-4 flex-wrap">
          <div class="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center"
            :class="isDark() ? 'bg-cyan-500/20' : 'bg-cyan-100'">
            <UserCheck class="w-6 h-6 text-cyan-500" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-bold text-lg truncate" :class="isDark() ? 'text-white' : 'text-slate-800'">
              {{ currentUser?.display_name || currentUser?.username }}
            </p>
            <p class="text-sm flex items-center gap-2" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
              <span class="font-mono text-xs px-2 py-0.5 rounded-md"
                :class="isDark() ? 'bg-slate-800/60 text-cyan-400' : 'bg-white/80 text-cyan-600'">
                @{{ currentUser?.username }}
              </span>
              <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md font-medium"
                :class="getRoleBadgeClass(currentUser?.role)">
                {{ getRoleLabel(currentUser?.role) }}
              </span>
            </p>
          </div>
          <button
            @click="showChangePassword = true"
            class="px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2 border"
            :class="isDark()
              ? 'bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 border-slate-700 hover:border-slate-600'
              : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200 shadow-sm'"
          >
            <KeyRound class="w-4 h-4" />
            Cambiar Contraseña
          </button>
        </div>
      </div>

      <!-- ═══ Create Admin Form ═══ -->
      <div v-if="isSuperAdmin"
        class="rounded-2xl border overflow-hidden"
        :class="isDark() ? 'bg-slate-900/50 border-slate-700/50' : 'bg-white border-slate-200 shadow-sm'">
        
        <!-- Form header -->
        <div class="px-6 py-4 border-b flex items-center gap-3"
          :class="isDark() ? 'bg-slate-800/40 border-slate-700/50' : 'bg-gradient-to-r from-cyan-50 to-blue-50 border-cyan-200'">
          <UserPlus class="w-5 h-5 text-emerald-400" />
          <h2 class="font-bold text-lg" :class="isDark() ? 'text-white' : 'text-slate-800'">
            Crear Nuevo Usuario
          </h2>
        </div>

        <div class="p-6 space-y-5">
          <!-- Input fields row -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Username -->
            <div>
              <label class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider mb-2"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
                <User class="w-3.5 h-3.5" />
                Usuario
              </label>
              <div class="relative">
                <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500">@</span>
                <input
                  v-model="newAdmin.username"
                  type="text"
                  placeholder="nombre_usuario"
                  class="w-full pl-8 pr-4 py-3 rounded-xl font-mono text-sm focus:outline-none focus:ring-2 transition-all border"
                  :class="isDark()
                    ? 'bg-slate-800/60 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/50 focus:border-cyan-500/50'
                    : 'bg-slate-50 border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
                />
              </div>
            </div>

            <!-- Display name -->
            <div>
              <label class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider mb-2"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
                <User class="w-3.5 h-3.5" />
                Nombre a Mostrar
                <span class="text-[10px] font-normal normal-case tracking-normal opacity-60">(opcional)</span>
              </label>
              <input
                v-model="newAdmin.display_name"
                type="text"
                placeholder="pepito"
                class="w-full px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 transition-all border"
                :class="isDark()
                  ? 'bg-slate-800/60 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/50 focus:border-cyan-500/50'
                  : 'bg-slate-50 border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
              />
            </div>

            <!-- Password -->
            <div>
              <label class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider mb-2"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
                <KeyRound class="w-3.5 h-3.5" />
                Contraseña
              </label>
              <div class="relative">
                <input
                  v-model="newAdmin.password"
                  :type="showNewPassword ? 'text' : 'password'"
                  placeholder="••••••••••"
                  class="w-full px-4 py-3 pr-11 rounded-xl text-sm focus:outline-none focus:ring-2 transition-all border"
                  :class="isDark()
                    ? 'bg-slate-800/60 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/50 focus:border-cyan-500/50'
                    : 'bg-slate-50 border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'"
                />
                <button
                  type="button"
                  @click="showNewPassword = !showNewPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-lg transition-colors"
                  :class="isDark() ? 'hover:bg-slate-700 text-slate-500' : 'hover:bg-slate-200 text-slate-400'"
                >
                  <EyeOff v-if="showNewPassword" class="w-4 h-4" />
                  <Eye v-else class="w-4 h-4" />
                </button>
              </div>
              <!-- Password strength checklist -->
              <div v-if="newAdmin.password" class="mt-2.5 space-y-1">
                <div class="flex gap-1 mb-2">
                  <div v-for="i in 4" :key="i" class="h-1.5 flex-1 rounded-full transition-all duration-300"
                    :class="passwordStrength(newAdmin.password) >= i
                      ? (passwordStrength(newAdmin.password) <= 1 ? 'bg-red-500' : passwordStrength(newAdmin.password) <= 2 ? 'bg-amber-500' : passwordStrength(newAdmin.password) <= 3 ? 'bg-blue-500' : 'bg-emerald-500')
                      : (isDark() ? 'bg-slate-700' : 'bg-slate-200')"
                  />
                </div>
                <div v-for="rule in getPasswordRules(newAdmin.password)" :key="rule.label"
                  class="flex items-center gap-1.5 text-xs transition-all"
                  :class="rule.ok ? (isDark() ? 'text-emerald-400' : 'text-emerald-600') : (isDark() ? 'text-slate-500' : 'text-slate-400')">
                  <Check v-if="rule.ok" class="w-3.5 h-3.5 flex-shrink-0" />
                  <CircleX v-else class="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{{ rule.label }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Role selector cards -->
          <div>
            <label class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider mb-3"
              :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
              <ShieldCheck class="w-3.5 h-3.5" />
              Rol del Usuario
            </label>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
              <button v-for="role in roleOptions" :key="role.value"
                type="button"
                @click="newAdmin.role = role.value"
                class="relative p-4 rounded-xl border-2 transition-all duration-200 text-left group"
                :class="newAdmin.role === role.value
                  ? `border-${role.borderActive} shadow-lg`
                  : isDark()
                    ? 'border-slate-700/50 hover:border-slate-600 bg-slate-800/30 hover:bg-slate-800/60'
                    : 'border-slate-200 hover:border-slate-300 bg-slate-50 hover:bg-white'"
                :style="newAdmin.role === role.value ? `border-color: ${role.hex}; box-shadow: 0 4px 20px ${role.rgba}` : ''"
              >
                <!-- Active check -->
                <div v-if="newAdmin.role === role.value"
                  class="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center text-white text-xs"
                  :style="`background-color: ${role.hex}`">
                  <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
                <div class="w-8 h-8 rounded-lg flex items-center justify-center mb-2"
                  :style="`background-color: ${role.rgba}`">
                  <component :is="role.icon" class="w-4 h-4" :style="`color: ${role.hex}`" />
                </div>
                <p class="font-bold text-sm" :class="isDark() ? 'text-white' : 'text-slate-800'">
                  {{ role.label }}
                </p>
                <p class="text-[11px] mt-0.5 leading-tight" :class="isDark() ? 'text-slate-500' : 'text-slate-500'">
                  {{ role.desc }}
                </p>
              </button>
            </div>
          </div>

          <!-- Submit button -->
          <button
            @click="createAdmin"
            :disabled="!newAdmin.username || !newAdmin.password || loading"
            class="px-6 py-3 rounded-xl font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 text-white shadow-lg"
            :class="loading
              ? 'bg-slate-600'
              : 'bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 shadow-emerald-500/20 hover:shadow-emerald-400/30 hover:scale-[1.02] active:scale-[0.98]'"
          >
            <UserPlus class="w-4 h-4" />
            {{ loading ? 'Creando...' : 'Crear Usuario' }}
          </button>
        </div>
      </div>

      <!-- ═══ Users Table ═══ -->
      <div class="rounded-2xl border"
        :class="isDark() ? 'bg-slate-900/50 border-slate-700/50' : 'bg-white border-slate-200 shadow-sm'">

        <!-- Table header -->
        <div class="px-6 py-4 border-b flex items-center justify-between rounded-t-2xl"
          :class="isDark() ? 'bg-slate-800/40 border-slate-700/50' : 'bg-gradient-to-r from-cyan-50 to-blue-50 border-cyan-200'">
          <h2 class="font-bold text-lg flex items-center gap-2" :class="isDark() ? 'text-white' : 'text-slate-800'">
            <Users class="w-5 h-5 text-cyan-400" />
            Usuarios
            <span class="text-sm font-normal px-2 py-0.5 rounded-lg"
              :class="isDark() ? 'bg-slate-700/60 text-slate-400' : 'bg-slate-100 text-slate-500'">
              {{ admins.length }}
            </span>
          </h2>
        </div>

        <div v-if="admins.length === 0" class="p-12 text-center">
          <Users class="w-12 h-12 mx-auto mb-3 opacity-20" :class="isDark() ? 'text-slate-500' : 'text-slate-300'" />
          <p class="text-sm" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">No hay usuarios registrados</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full" role="table" aria-label="Lista de usuarios del sistema">
            <thead>
              <tr :class="isDark() ? 'bg-slate-800/60' : 'bg-slate-50/80'">
                <th class="px-6 py-3.5 text-left text-[11px] font-semibold uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Usuario</th>
                <th class="px-6 py-3.5 text-left text-[11px] font-semibold uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Nombre</th>
                <th class="px-6 py-3.5 text-left text-[11px] font-semibold uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Rol</th>
                <th class="px-6 py-3.5 text-left text-[11px] font-semibold uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Estado</th>
                <th class="px-6 py-3.5 text-left text-[11px] font-semibold uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Creado</th>
                <th class="px-6 py-3.5 text-right text-[11px] font-semibold uppercase tracking-wider min-w-[160px]" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Acciones</th>
              </tr>
            </thead>
            <tbody :class="isDark() ? 'divide-y divide-slate-800' : 'divide-y divide-slate-100'">
              <tr v-for="admin in admins" :key="admin.id"
                class="transition-colors"
                :class="isDark() ? 'hover:bg-slate-800/40' : 'hover:bg-slate-50'">
                <!-- Username -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold"
                      :class="admin.id === currentUser?.id
                        ? 'bg-cyan-500/20 text-cyan-400'
                        : (isDark() ? 'bg-slate-700/60 text-slate-400' : 'bg-slate-100 text-slate-500')">
                      {{ (admin.username || '?')[0].toUpperCase() }}
                    </div>
                    <div>
                      <span class="font-mono font-semibold text-sm" :class="isDark() ? 'text-white' : 'text-slate-800'">
                        {{ admin.username }}
                      </span>
                      <div class="flex items-center gap-1.5 mt-0.5">
                        <span v-if="admin.is_super_admin"
                          class="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-md font-semibold"
                          :class="isDark() ? 'bg-amber-500/15 text-amber-400' : 'bg-amber-50 text-amber-600'">
                          <ShieldCheck class="w-3 h-3" />
                          Principal
                        </span>
                        <span v-if="admin.id === currentUser?.id && !admin.is_super_admin"
                          class="text-[10px] px-1.5 py-0.5 rounded-md font-medium"
                          :class="isDark() ? 'bg-cyan-500/15 text-cyan-400' : 'bg-cyan-50 text-cyan-600'">
                          Tú
                        </span>
                      </div>
                    </div>
                  </div>
                </td>
                <!-- Name -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm" :class="admin.display_name ? (isDark() ? 'text-slate-300' : 'text-slate-700') : (isDark() ? 'text-slate-600' : 'text-slate-400')">
                    {{ admin.display_name || '—' }}
                  </span>
                </td>
                <!-- Role -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <!-- Editable role selector for other users (not for super_admin unless you are super_admin) -->
                  <div v-if="admin.id !== currentUser?.id && !(admin.is_super_admin && !isSuperAdmin)" class="relative inline-block">
                    <button
                      @click.stop="toggleRoleDropdown(admin.id)"
                      :disabled="loading"
                      class="flex items-center gap-2 pl-3 pr-8 py-1.5 rounded-lg text-xs font-bold focus:outline-none focus:ring-2 focus:ring-cyan-500/50 cursor-pointer disabled:opacity-50 transition-all border relative"
                      :class="getRoleSelectClass(admin.role)"
                    >
                      <component :is="getRoleIcon(admin.role)" class="w-3.5 h-3.5" />
                      {{ getRoleLabel(admin.role) }}
                      <ChevronDown class="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 opacity-50 transition-transform"
                        :class="openRoleDropdown === admin.id ? 'rotate-180' : ''" />
                    </button>
                    <!-- Custom dropdown -->
                    <Transition name="dropdown">
                      <div v-if="openRoleDropdown === admin.id"
                        class="absolute z-50 mt-1.5 left-0 min-w-[160px] rounded-xl border shadow-xl overflow-hidden"
                        :class="isDark() ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'">
                        <button v-for="role in roleOptions" :key="role.value"
                          @click.stop="selectRole(admin, role.value)"
                          class="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-xs font-semibold transition-all text-left"
                          :class="[
                            (admin.role || 'viewer') === role.value
                              ? (isDark() ? 'bg-slate-700/60' : 'bg-slate-50')
                              : (isDark() ? 'hover:bg-slate-700/40' : 'hover:bg-slate-50'),
                            isDark() ? 'text-slate-300' : 'text-slate-700'
                          ]">
                          <div class="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                            :style="`background-color: ${role.rgba}`">
                            <component :is="role.icon" class="w-3.5 h-3.5" :style="`color: ${role.hex}`" />
                          </div>
                          <span>{{ role.label }}</span>
                          <svg v-if="(admin.role || 'viewer') === role.value" class="w-3.5 h-3.5 ml-auto text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        </button>
                      </div>
                    </Transition>
                  </div>
                  <!-- Badge for own role or protected super_admin -->
                  <span v-else
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold"
                    :class="getRoleBadgeClass(admin.role)">
                    <component :is="getRoleIcon(admin.role)" class="w-3.5 h-3.5" />
                    {{ getRoleLabel(admin.role) }}
                  </span>
                </td>
                <!-- Status -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full" :class="admin.is_active ? 'bg-emerald-400' : 'bg-red-400'"></div>
                    <span class="text-xs font-medium"
                      :class="admin.is_active
                        ? (isDark() ? 'text-emerald-400' : 'text-emerald-600')
                        : (isDark() ? 'text-red-400' : 'text-red-600')">
                      {{ admin.is_active ? 'Activo' : 'Inactivo' }}
                    </span>
                  </div>
                </td>
                <!-- Created -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-xs font-mono" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                    {{ formatDate(admin.created_at) }}
                  </span>
                </td>
                <!-- Actions -->
                <td class="px-6 py-4 whitespace-nowrap text-right">
                  <div class="flex items-center gap-1.5 justify-end">
                    <button
                      v-if="admin.id !== currentUser?.id && !admin.is_super_admin"
                      @click="toggleActive(admin)"
                      :disabled="loading"
                      class="p-2 rounded-lg transition-all disabled:opacity-50 group"
                      :class="admin.is_active
                        ? (isDark() ? 'hover:bg-amber-500/15 text-slate-500 hover:text-amber-400' : 'hover:bg-amber-50 text-slate-400 hover:text-amber-600')
                        : (isDark() ? 'hover:bg-emerald-500/15 text-slate-500 hover:text-emerald-400' : 'hover:bg-emerald-50 text-slate-400 hover:text-emerald-600')"
                      :title="admin.is_active ? 'Desactivar' : 'Activar'"
                    >
                      <UserX v-if="admin.is_active" class="w-4 h-4" />
                      <UserCheck v-else class="w-4 h-4" />
                    </button>
                    <button
                      v-if="admin.id !== currentUser?.id && !(admin.is_super_admin && !isSuperAdmin)"
                      @click="openResetPassword(admin)"
                      :disabled="loading"
                      class="p-2 rounded-lg transition-all disabled:opacity-50"
                      :class="isDark() ? 'hover:bg-blue-500/15 text-slate-500 hover:text-blue-400' : 'hover:bg-blue-50 text-slate-400 hover:text-blue-600'"
                      title="Restablecer contraseña"
                    >
                      <KeyRound class="w-4 h-4" />
                    </button>
                    <button
                      v-if="admin.id !== currentUser?.id && isSuperAdmin && !admin.is_super_admin"
                      @click="openDeleteModal(admin)"
                      :disabled="loading"
                      class="p-2 rounded-lg transition-all disabled:opacity-50"
                      :class="isDark() ? 'hover:bg-red-500/15 text-slate-500 hover:text-red-400' : 'hover:bg-red-50 text-slate-400 hover:text-red-600'"
                      title="Eliminar"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <ToastNotification
      :visible="toast.show"
      :message="toast.message"
      :type="toast.type"
      :duration="5000"
      @close="toast.show = false"
    />

    <!-- ═══ Modal: Cambiar Contraseña Propia ═══ -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showChangePassword"
          class="fixed inset-0 z-[9998] flex items-center justify-center p-4"
          @click="showChangePassword = false">
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
          <div class="relative max-w-md w-full rounded-2xl shadow-2xl border overflow-hidden"
            :class="isDark() ? 'bg-slate-900 border-slate-700/50' : 'bg-white border-slate-200'"
            @click.stop>
            <!-- Modal header -->
            <div class="px-6 py-4 border-b flex items-center gap-3"
              :class="isDark() ? 'bg-slate-800/60 border-slate-700/50' : 'bg-gradient-to-r from-cyan-50 to-blue-50 border-cyan-200'">
              <div class="p-2 rounded-lg" :class="isDark() ? 'bg-cyan-500/15' : 'bg-cyan-50'">
                <KeyRound class="w-5 h-5 text-cyan-500" />
              </div>
              <div class="flex-1">
                <h3 class="text-lg font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">Cambiar Contraseña</h3>
                <p class="text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Actualiza tu contraseña de acceso</p>
              </div>
              <button @click="showChangePassword = false"
                class="p-1.5 rounded-lg transition-colors" :class="isDark() ? 'hover:bg-slate-700 text-slate-500' : 'hover:bg-slate-100 text-slate-400'">
                <X class="w-5 h-5" />
              </button>
            </div>
            <!-- Modal body -->
            <div class="p-6 space-y-4">
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider mb-2"
                  :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Contraseña actual</label>
                <input v-model="passwordChange.current" type="password"
                  class="w-full px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 transition-all border"
                  :class="modalInputClass"
                  placeholder="Tu contraseña actual" />
              </div>
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider mb-2"
                  :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Nueva contraseña</label>
                <input v-model="passwordChange.new_password" type="password"
                  class="w-full px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 transition-all border"
                  :class="modalInputClass"
                  placeholder="Nueva contraseña" />
                <!-- Password strength checklist -->
                <div v-if="passwordChange.new_password" class="mt-2.5 space-y-1">
                  <div class="flex gap-1 mb-2">
                    <div v-for="i in 4" :key="i" class="h-1.5 flex-1 rounded-full transition-all duration-300"
                      :class="passwordStrength(passwordChange.new_password) >= i
                        ? (passwordStrength(passwordChange.new_password) <= 1 ? 'bg-red-500' : passwordStrength(passwordChange.new_password) <= 2 ? 'bg-amber-500' : passwordStrength(passwordChange.new_password) <= 3 ? 'bg-blue-500' : 'bg-emerald-500')
                        : (isDark() ? 'bg-slate-700' : 'bg-slate-200')"
                    />
                  </div>
                  <div v-for="rule in getPasswordRules(passwordChange.new_password)" :key="rule.label"
                    class="flex items-center gap-1.5 text-xs transition-all"
                    :class="rule.ok ? (isDark() ? 'text-emerald-400' : 'text-emerald-600') : (isDark() ? 'text-slate-500' : 'text-slate-400')">
                    <Check v-if="rule.ok" class="w-3.5 h-3.5 flex-shrink-0" />
                    <CircleX v-else class="w-3.5 h-3.5 flex-shrink-0" />
                    <span>{{ rule.label }}</span>
                  </div>
                </div>
              </div>
              <div>
                <label class="block text-xs font-semibold uppercase tracking-wider mb-2"
                  :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Confirmar nueva contraseña</label>
                <input v-model="passwordChange.confirm" type="password"
                  class="w-full px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 transition-all border"
                  :class="modalInputClass"
                  placeholder="Repite la nueva contraseña" />
              </div>
            </div>
            <!-- Modal footer -->
            <div class="px-6 py-4 border-t flex gap-3"
              :class="isDark() ? 'bg-slate-800/40 border-slate-700/50' : 'bg-gradient-to-r from-cyan-50 to-blue-50 border-cyan-200'">
              <button @click="showChangePassword = false"
                class="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all border"
                :class="isDark() ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700' : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'">
                Cancelar
              </button>
              <button @click="changePassword"
                :disabled="loading || !passwordChange.current || !passwordChange.new_password"
                class="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-40 text-white bg-gradient-to-r from-cyan-500 to-blue-500 shadow-lg shadow-cyan-500/20">
                {{ loading ? 'Guardando...' : 'Guardar' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ Modal: Reset Contraseña ═══ -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showResetPassword"
          class="fixed inset-0 z-[9998] flex items-center justify-center p-4"
          @click="showResetPassword = false">
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
          <div class="relative max-w-md w-full rounded-2xl shadow-2xl border overflow-hidden"
            :class="isDark() ? 'bg-slate-900 border-slate-700/50' : 'bg-white border-slate-200'"
            @click.stop>
            <div class="px-6 py-4 border-b flex items-center gap-3"
              :class="isDark() ? 'bg-slate-800/60 border-slate-700/50' : 'bg-gradient-to-r from-cyan-50 to-blue-50 border-cyan-200'">
              <div class="p-2 rounded-lg" :class="isDark() ? 'bg-blue-500/15' : 'bg-blue-50'">
                <KeyRound class="w-5 h-5 text-blue-500" />
              </div>
              <div class="flex-1">
                <h3 class="text-lg font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">Restablecer Contraseña</h3>
                <p class="text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                  Para <span class="font-mono font-semibold" :class="isDark() ? 'text-blue-400' : 'text-blue-600'">@{{ resetTarget?.username }}</span>
                </p>
              </div>
              <button @click="showResetPassword = false"
                class="p-1.5 rounded-lg transition-colors" :class="isDark() ? 'hover:bg-slate-700 text-slate-500' : 'hover:bg-slate-100 text-slate-400'">
                <X class="w-5 h-5" />
              </button>
            </div>
            <div class="p-6">
              <label class="block text-xs font-semibold uppercase tracking-wider mb-2"
                :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Nueva contraseña</label>
              <div class="relative">
                <input v-model="resetNewPassword"
                  :type="showResetPwd ? 'text' : 'password'"
                  placeholder="Nueva contraseña"
                  class="w-full px-4 py-3 pr-11 rounded-xl text-sm focus:outline-none focus:ring-2 transition-all border"
                  :class="modalInputClass" />
                <button type="button" @click="showResetPwd = !showResetPwd"
                  class="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-lg transition-colors"
                  :class="isDark() ? 'hover:bg-slate-700 text-slate-500' : 'hover:bg-slate-200 text-slate-400'">
                  <EyeOff v-if="showResetPwd" class="w-4 h-4" />
                  <Eye v-else class="w-4 h-4" />
                </button>
              </div>
              <!-- Password strength checklist -->
              <div v-if="resetNewPassword" class="mt-2.5 space-y-1">
                <div class="flex gap-1 mb-2">
                  <div v-for="i in 4" :key="i" class="h-1.5 flex-1 rounded-full transition-all duration-300"
                    :class="passwordStrength(resetNewPassword) >= i
                      ? (passwordStrength(resetNewPassword) <= 1 ? 'bg-red-500' : passwordStrength(resetNewPassword) <= 2 ? 'bg-amber-500' : passwordStrength(resetNewPassword) <= 3 ? 'bg-blue-500' : 'bg-emerald-500')
                      : (isDark() ? 'bg-slate-700' : 'bg-slate-200')"
                  />
                </div>
                <div v-for="rule in getPasswordRules(resetNewPassword)" :key="rule.label"
                  class="flex items-center gap-1.5 text-xs transition-all"
                  :class="rule.ok ? (isDark() ? 'text-emerald-400' : 'text-emerald-600') : (isDark() ? 'text-slate-500' : 'text-slate-400')">
                  <Check v-if="rule.ok" class="w-3.5 h-3.5 flex-shrink-0" />
                  <CircleX v-else class="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{{ rule.label }}</span>
                </div>
              </div>
            </div>
            <div class="px-6 py-4 border-t flex gap-3"
              :class="isDark() ? 'bg-slate-800/40 border-slate-700/50' : 'bg-gradient-to-r from-cyan-50 to-blue-50 border-cyan-200'">
              <button @click="showResetPassword = false"
                class="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all border"
                :class="isDark() ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700' : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'">
                Cancelar
              </button>
              <button @click="resetPassword"
                :disabled="loading || !resetNewPassword"
                class="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-40 text-white bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-400 hover:to-indigo-400 shadow-lg shadow-blue-500/20">
                {{ loading ? 'Guardando...' : 'Restablecer' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ Modal: Eliminar ═══ -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showDeleteModal"
          class="fixed inset-0 z-[9998] flex items-center justify-center p-4"
          @click="showDeleteModal = false">
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
          <div class="relative max-w-md w-full rounded-2xl shadow-2xl border overflow-hidden"
            :class="isDark() ? 'bg-slate-900 border-slate-700/50' : 'bg-white border-slate-200'"
            @click.stop>
            <div class="p-8 text-center">
              <div class="mx-auto w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                :class="isDark() ? 'bg-red-500/15' : 'bg-red-50'">
                <AlertCircle class="w-8 h-8 text-red-500" />
              </div>
              <h3 class="text-xl font-bold mb-2" :class="isDark() ? 'text-white' : 'text-slate-800'">
                ¿Eliminar usuario?
              </h3>
              <p class="text-sm mb-1" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
                Estás a punto de eliminar al usuario:
              </p>
              <p class="font-mono text-lg font-bold mb-1" :class="isDark() ? 'text-red-400' : 'text-red-600'">
                @{{ deleteTarget?.username }}
              </p>
              <p v-if="deleteTarget?.display_name" class="text-sm mb-4" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                {{ deleteTarget?.display_name }}
              </p>
              <div class="p-3 rounded-xl mb-6"
                :class="isDark() ? 'bg-red-500/10 border border-red-500/20' : 'bg-red-50 border border-red-100'">
                <p class="text-xs font-medium" :class="isDark() ? 'text-red-300' : 'text-red-600'">
                  <svg class="w-4 h-4 inline-block mr-1 -mt-0.5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> Esta acción no se puede deshacer
                </p>
              </div>
              <div class="flex gap-3">
                <button @click="showDeleteModal = false" :disabled="loading"
                  class="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all border"
                  :class="isDark() ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700' : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'">
                  Cancelar
                </button>
                <button @click="confirmDelete" :disabled="loading"
                  class="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-40 text-white bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-400 hover:to-rose-400 shadow-lg shadow-red-500/20 flex items-center justify-center gap-2">
                  <Trash2 class="w-4 h-4" />
                  {{ loading ? 'Eliminando...' : 'Eliminar' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTheme } from '@/composables/useTheme'
import { usePermissions } from '@/composables/usePermissions'
import ToastNotification from './ToastNotification.vue'
import {
  Users, ArrowLeft, UserCheck, UserPlus, UserX, User,
  Trash2, KeyRound, Eye, EyeOff, AlertCircle, ShieldCheck,
  ChevronDown, X, Shield, Zap, Pencil, Check, CircleX
} from 'lucide-vue-next'

const { isDark } = useTheme()
const { isSuperAdmin } = usePermissions()
const API_URL = import.meta.env.VITE_API_URL || window.location.origin.replace(':3000', ':8000')

const admins = ref([])
const loading = ref(false)
const currentUser = ref(null)

const newAdmin = ref({ username: '', password: '', display_name: '', role: 'viewer' })
const showNewPassword = ref(false)

const showChangePassword = ref(false)
const passwordChange = ref({ current: '', new_password: '', confirm: '' })

const showResetPassword = ref(false)
const resetTarget = ref(null)
const resetNewPassword = ref('')
const showResetPwd = ref(false)

const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const openRoleDropdown = ref(null)

const toast = ref({ show: false, message: '', type: 'success' })

const getPasswordRules = (password) => {
  if (!password) return []
  return [
    { label: 'Al menos 8 caracteres', ok: password.length >= 8 },
    { label: 'Una letra mayúscula', ok: /[A-Z]/.test(password) },
    { label: 'Una letra minúscula', ok: /[a-z]/.test(password) },
    { label: 'Un número', ok: /\d/.test(password) }
  ]
}

const passwordStrength = (password) => {
  if (!password) return 0
  const rules = getPasswordRules(password)
  return rules.filter(r => r.ok).length
}

// Role definitions for cards
const roleOptions = [
  { value: 'viewer', label: 'Visor', desc: 'Solo lectura', icon: Eye, hex: '#64748b', rgba: 'rgba(100,116,139,0.15)', borderActive: 'slate-400' },
  { value: 'op', label: 'Operador', desc: 'Ejecutar escaneos', icon: Zap, hex: '#f59e0b', rgba: 'rgba(245,158,11,0.15)', borderActive: 'amber-400' },
  { value: 'mod', label: 'Moderador', desc: 'Editar y administrar', icon: Pencil, hex: '#3b82f6', rgba: 'rgba(59,130,246,0.15)', borderActive: 'blue-400' },
  { value: 'admin', label: 'Admin', desc: 'Acceso completo', icon: Shield, hex: '#a855f7', rgba: 'rgba(168,85,247,0.15)', borderActive: 'purple-400' }
]

const modalInputClass = computed(() =>
  isDark()
    ? 'bg-slate-800/60 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/50 focus:border-cyan-500/50'
    : 'bg-slate-50 border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'
)

const getAuthHeaders = () => {
  const token = localStorage.getItem('admin_token')
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
}

const cleanMsg = (msg) => {
  if (!msg || typeof msg !== 'string') return msg
  return msg.replace(/^Value error,\s*/i, '').replace(/^Assertion error,\s*/i, '')
}

const parseError = (detail, fallback = 'Error') => {
  if (!detail) return fallback
  if (typeof detail === 'string') return cleanMsg(detail)
  if (Array.isArray(detail)) {
    return detail.map(e => cleanMsg(e.msg) || cleanMsg(e.message) || fallback).join('. ')
  }
  if (typeof detail === 'object' && (detail.msg || detail.message)) return cleanMsg(detail.msg || detail.message)
  return fallback
}

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => { toast.value.show = false }, 5000)
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  try {
    return new Date(dateStr).toLocaleString('es-ES', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    })
  } catch { return dateStr }
}

const loadCurrentUser = () => {
  try {
    const userData = localStorage.getItem('admin_user')
    if (userData) currentUser.value = JSON.parse(userData)
  } catch { }
}

const loadAdmins = async () => {
  try {
    const response = await fetch(`${API_URL}/api/admin/users`, { headers: getAuthHeaders() })
    if (response.ok) admins.value = await response.json()
  } catch { showToast('Error al cargar administradores', 'error') }
}

const createAdmin = async () => {
  if (!newAdmin.value.username || !newAdmin.value.password) return
  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/admin/users`, {
      method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(newAdmin.value)
    })
    const data = await response.json()
    if (response.ok) {
      showToast(data.message || 'Usuario creado', 'success')
      newAdmin.value = { username: '', password: '', display_name: '', role: 'viewer' }
      await loadAdmins()
    } else { showToast(parseError(data.detail, 'Error al crear usuario'), 'error') }
  } catch { showToast('Error al crear usuario', 'error') }
  finally { loading.value = false }
}

const toggleActive = async (admin) => {
  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/admin/users/${admin.id}`, {
      method: 'PUT', headers: getAuthHeaders(), body: JSON.stringify({ is_active: !admin.is_active })
    })
    const data = await response.json()
    if (response.ok) { showToast(data.message, 'success'); await loadAdmins() }
    else showToast(parseError(data.detail, 'Error'), 'error')
  } catch { showToast('Error al actualizar', 'error') }
  finally { loading.value = false }
}

const openResetPassword = (admin) => {
  resetTarget.value = admin; resetNewPassword.value = ''; showResetPassword.value = true
}

const resetPassword = async () => {
  if (!resetNewPassword.value || !resetTarget.value) return
  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/admin/users/${resetTarget.value.id}`, {
      method: 'PUT', headers: getAuthHeaders(), body: JSON.stringify({ new_password: resetNewPassword.value })
    })
    const data = await response.json()
    if (response.ok) { showToast(`Contraseña de '${resetTarget.value.username}' restablecida`, 'success'); showResetPassword.value = false }
    else showToast(parseError(data.detail, 'Error al restablecer'), 'error')
  } catch { showToast('Error al restablecer contraseña', 'error') }
  finally { loading.value = false }
}

const changePassword = async () => {
  if (passwordChange.value.new_password !== passwordChange.value.confirm) {
    showToast('Las contraseñas no coinciden', 'error'); return
  }
  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/auth/change-password`, {
      method: 'PUT', headers: getAuthHeaders(),
      body: JSON.stringify({ current_password: passwordChange.value.current, new_password: passwordChange.value.new_password })
    })
    const data = await response.json()
    if (response.ok) {
      showToast('Contraseña actualizada', 'success')
      showChangePassword.value = false
      passwordChange.value = { current: '', new_password: '', confirm: '' }
    } else showToast(parseError(data.detail, 'Error al cambiar contraseña'), 'error')
  } catch { showToast('Error al cambiar contraseña', 'error') }
  finally { loading.value = false }
}

const openDeleteModal = (admin) => { deleteTarget.value = admin; showDeleteModal.value = true }

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/admin/users/${deleteTarget.value.id}`, {
      method: 'DELETE', headers: getAuthHeaders()
    })
    const data = await response.json()
    if (response.ok) { showToast(data.message, 'success'); showDeleteModal.value = false; await loadAdmins() }
    else showToast(parseError(data.detail, 'Error al eliminar'), 'error')
  } catch { showToast('Error al eliminar', 'error') }
  finally { loading.value = false }
}

const getRoleLabel = (role) => {
  return { admin: 'Admin', mod: 'Moderador', op: 'Operador', viewer: 'Visor' }[role] || 'Visor'
}

const getRoleIcon = (role) => {
  return { admin: Shield, mod: Pencil, op: Zap, viewer: Eye }[role] || Eye
}

const getRoleBadgeClass = (role) => {
  const d = isDark()
  return {
    admin: d ? 'bg-purple-500/15 text-purple-400' : 'bg-purple-50 text-purple-700',
    mod: d ? 'bg-blue-500/15 text-blue-400' : 'bg-blue-50 text-blue-700',
    op: d ? 'bg-amber-500/15 text-amber-400' : 'bg-amber-50 text-amber-700',
    viewer: d ? 'bg-slate-700/60 text-slate-400' : 'bg-slate-100 text-slate-600'
  }[role] || (d ? 'bg-slate-700/60 text-slate-400' : 'bg-slate-100 text-slate-600')
}

const getRoleSelectClass = (role) => {
  const d = isDark()
  return {
    admin: d ? 'bg-purple-500/15 text-purple-300 border-purple-500/30' : 'bg-purple-50 text-purple-700 border-purple-200',
    mod: d ? 'bg-blue-500/15 text-blue-300 border-blue-500/30' : 'bg-blue-50 text-blue-700 border-blue-200',
    op: d ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' : 'bg-amber-50 text-amber-700 border-amber-200',
    viewer: d ? 'bg-slate-700/60 text-slate-300 border-slate-600' : 'bg-slate-100 text-slate-700 border-slate-200'
  }[role] || (d ? 'bg-slate-700/60 text-slate-300 border-slate-600' : 'bg-slate-100 text-slate-700 border-slate-200')
}

const toggleRoleDropdown = (adminId) => {
  openRoleDropdown.value = openRoleDropdown.value === adminId ? null : adminId
}

const selectRole = (admin, newRole) => {
  openRoleDropdown.value = null
  if ((admin.role || 'viewer') !== newRole) changeRole(admin, newRole)
}

const closeRoleDropdown = () => { openRoleDropdown.value = null }

const changeRole = async (admin, newRole) => {
  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/admin/users/${admin.id}`, {
      method: 'PUT', headers: getAuthHeaders(), body: JSON.stringify({ role: newRole })
    })
    const data = await response.json()
    if (response.ok) { showToast(`Rol de '${admin.username}' cambiado a ${getRoleLabel(newRole)}`, 'success'); await loadAdmins() }
    else { showToast(parseError(data.detail, 'Error al cambiar rol'), 'error'); await loadAdmins() }
  } catch { showToast('Error al cambiar rol', 'error'); await loadAdmins() }
  finally { loading.value = false }
}

onMounted(() => {
  loadCurrentUser(); loadAdmins()
  document.addEventListener('click', closeRoleDropdown)
})

onUnmounted(() => { document.removeEventListener('click', closeRoleDropdown) })
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-active .relative,
.modal-fade-leave-active .relative {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-fade-enter-from .relative {
  transform: scale(0.95);
  opacity: 0;
}
.modal-fade-leave-to .relative {
  transform: scale(0.95);
  opacity: 0;
}
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.95);
}
</style>
