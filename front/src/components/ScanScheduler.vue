<template>
  <div
    class="rounded-2xl p-5 shadow-2xl"
    :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
  >
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="relative">
          <div class="p-2.5 rounded-xl border" :class="isDark() ? 'bg-cyan-500/10 border-cyan-500/30' : 'bg-cyan-50 border-cyan-300/50'">
            <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none">
              <!-- Calendar body -->
              <rect x="3" y="5" width="18" height="16" rx="3" :stroke="isDark() ? '#22d3ee' : '#0891b2'" stroke-width="1.5" fill="none" />
              <!-- Top clips -->
              <line x1="8" y1="3" x2="8" y2="7" :stroke="isDark() ? '#22d3ee' : '#0891b2'" stroke-width="1.5" stroke-linecap="round" />
              <line x1="16" y1="3" x2="16" y2="7" :stroke="isDark() ? '#22d3ee' : '#0891b2'" stroke-width="1.5" stroke-linecap="round" />
              <!-- Divider -->
              <line x1="3" y1="10" x2="21" y2="10" :stroke="isDark() ? '#22d3ee' : '#0891b2'" stroke-width="1.5" opacity="0.4" />
              <!-- Mini clock face -->
              <circle cx="12" cy="15.5" r="3.5" :stroke="isDark() ? '#a78bfa' : '#7c3aed'" stroke-width="1.3" fill="none" />
              <line x1="12" y1="15.5" x2="12" y2="13.8" :stroke="isDark() ? '#a78bfa' : '#7c3aed'" stroke-width="1.3" stroke-linecap="round" class="origin-center" style="transform-origin: 12px 15.5px;" />
              <line x1="12" y1="15.5" x2="13.8" y2="15.5" :stroke="isDark() ? '#a78bfa' : '#7c3aed'" stroke-width="1.3" stroke-linecap="round" />
            </svg>
          </div>
          <span class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full animate-pulse" :class="isDark() ? 'bg-cyan-400' : 'bg-cyan-500'"></span>
        </div>
        <div>
          <h3 
            class="text-base font-bold tracking-wide"
            :class="isDark() ? 'text-gray-200' : 'text-slate-800'"
          >
            Escaneos Programados
          </h3>
          <p 
            class="text-xs"
            :class="isDark() ? 'text-gray-400' : 'text-slate-500'"
          >
            Automatiza tus escaneos de red
          </p>
        </div>
      </div>
      <button
        v-if="canManageSchedulers"
        @click="showScheduleModal = true"
        class="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all duration-300 flex items-center gap-2"
        aria-label="Crear nuevo escaneo programado"
      >
        <Plus class="w-5 h-5" />
        Nuevo Schedule
      </button>
    </div>

    <!-- Scheduled Scans List -->
    <div v-if="loading" class="text-center py-12">
      <div
        class="w-8 h-8 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"
      ></div>
      <p :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Cargando programaciones...</p>
    </div>

    <div v-else-if="schedules.length === 0" class="text-center py-12">
      <div class="mx-auto mb-5 w-20 h-20 relative">
        <svg class="w-20 h-20" viewBox="0 0 80 80" fill="none">
          <!-- Outer ring -->
          <circle cx="40" cy="40" r="34" :stroke="isDark() ? '#334155' : '#cbd5e1'" stroke-width="2" fill="none" />
          <!-- Tick marks -->
          <line v-for="i in 12" :key="i"
            :x1="40 + 28 * Math.cos((i * 30 - 90) * Math.PI / 180)"
            :y1="40 + 28 * Math.sin((i * 30 - 90) * Math.PI / 180)"
            :x2="40 + 31 * Math.cos((i * 30 - 90) * Math.PI / 180)"
            :y2="40 + 31 * Math.sin((i * 30 - 90) * Math.PI / 180)"
            :stroke="isDark() ? '#475569' : '#94a3b8'" stroke-width="2" stroke-linecap="round" />
          <!-- Hour hand -->
          <line x1="40" y1="40" x2="40" y2="22" :stroke="isDark() ? '#64748b' : '#94a3b8'" stroke-width="2.5" stroke-linecap="round" />
          <!-- Minute hand -->
          <line x1="40" y1="40" x2="54" y2="33" :stroke="isDark() ? '#64748b' : '#94a3b8'" stroke-width="2" stroke-linecap="round" />
          <!-- Center dot -->
          <circle cx="40" cy="40" r="2.5" :fill="isDark() ? '#475569' : '#94a3b8'" />
        </svg>
        <div class="absolute inset-0 flex items-center justify-center">
          <Plus class="w-5 h-5 absolute -bottom-1 -right-1 p-0.5 rounded-full" :class="isDark() ? 'text-slate-500 bg-slate-900' : 'text-slate-400 bg-white'" />
        </div>
      </div>
      <p 
        class="text-lg font-semibold"
        :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
      >No hay escaneos programados</p>
      <p 
        class="text-sm mt-1.5"
        :class="isDark() ? 'text-slate-500' : 'text-slate-400'"
      >
        Crea tu primer escaneo automático
      </p>
      <button
        v-if="canManageSchedulers"
        @click="showScheduleModal = true"
        class="mt-4 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-xl text-sm font-semibold hover:shadow-lg hover:shadow-cyan-500/30 transition-all duration-300 inline-flex items-center gap-2"
      >
        <Plus class="w-4 h-4" />
        Crear Schedule
      </button>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="schedule in schedules"
        :key="schedule.id"
        class="rounded-xl p-4 transition-all duration-300 relative overflow-hidden group/card"
        :class="[
          schedule.action_type === 'shutdown' || schedule.action_type === 'both'
            ? (isDark()
              ? 'bg-gradient-to-br from-red-900/30 via-orange-900/20 to-red-900/30 border-2 border-red-500/50 hover:border-red-400/70 shadow-lg shadow-red-500/10'
              : 'bg-gradient-to-br from-red-50 via-orange-50 to-red-50 border-2 border-red-300/50 hover:border-red-400/70 shadow-sm')
            : (isDark()
              ? 'bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50'
              : 'bg-white border border-slate-200 hover:border-cyan-400/50 shadow-sm hover:shadow-md')
        ]"
      >
        <!-- Indicator de apagado automático -->
        <div
          v-if="schedule.action_type === 'shutdown' || schedule.action_type === 'both'"
          class="absolute top-0 right-0 bg-gradient-to-br from-red-500 to-orange-600 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-bl-lg flex items-center gap-1"
        >
          <Power class="w-3 h-3" />
          {{ schedule.action_type === 'shutdown' ? 'APAGADO AUTO' : 'SCAN + APAGADO' }}
        </div>
        
        <div class="flex flex-col sm:flex-row sm:items-center gap-3">
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <!-- Type Icon -->
            <div
              class="p-2.5 rounded-xl flex-shrink-0"
              :class="schedule.action_type === 'shutdown' || schedule.action_type === 'both'
                ? (isDark() ? 'bg-gradient-to-br from-red-500/30 to-orange-500/30 border border-red-500/50' : 'bg-gradient-to-br from-red-100 to-orange-100 border border-red-300/50')
                : getScanTypeColor(schedule.scan_type)"
            >
              <component
                v-if="schedule.action_type === 'shutdown'"
                :is="Power"
                class="w-5 h-5 text-red-400"
              />
              <component
                v-else
                :is="getScanTypeIcon(schedule.scan_type)"
                class="w-5 h-5"
              />
            </div>

            <!-- Schedule Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1.5">
                <h4 
                  class="font-semibold truncate"
                  :class="schedule.action_type === 'shutdown' || schedule.action_type === 'both'
                    ? (isDark() ? 'text-red-200' : 'text-red-800')
                    : (isDark() ? 'text-slate-200' : 'text-slate-800')"
                >
                  {{ schedule.name }}
                </h4>
                <span
                  class="px-2 py-0.5 text-[10px] font-bold rounded-full flex-shrink-0 uppercase tracking-wider"
                  :class="
                    schedule.enabled
                      ? (isDark() ? 'bg-green-500/20 text-green-400 border border-green-500/50' : 'bg-green-100 text-green-700 border border-green-300')
                      : (isDark() ? 'bg-slate-700/50 text-slate-400 border border-slate-600/50' : 'bg-slate-100 text-slate-500 border border-slate-300')
                  "
                >
                  {{ schedule.enabled ? "Activo" : "Inactivo" }}
                </span>
              </div>
              <!-- Info chips - wrapped on mobile -->
              <div 
                class="flex items-center gap-2 flex-wrap text-xs"
                :class="schedule.action_type === 'shutdown' || schedule.action_type === 'both'
                  ? (isDark() ? 'text-red-300/80' : 'text-red-600/80')
                  : (isDark() ? 'text-slate-400' : 'text-slate-500')"
              >
                <span v-if="schedule.created_by" class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md" :class="isDark() ? 'bg-blue-500/10 text-blue-400/80' : 'bg-blue-50 text-blue-600'">
                  <User class="w-3 h-3" />
                  {{ schedule.created_by }}
                </span>
                <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md" :class="isDark() ? 'bg-slate-700/40' : 'bg-slate-100'">
                  <Tag class="w-3 h-3" />
                  {{ getScanTypeName(schedule.scan_type) }}
                </span>
                <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md" :class="isDark() ? 'bg-slate-700/40' : 'bg-slate-100'">
                  <svg class="w-3 h-3" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.2" />
                    <line x1="8" y1="8" x2="8" y2="4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" />
                    <line x1="8" y1="8" x2="11" y2="8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" />
                  </svg>
                  {{ getScheduleDescription(schedule) }}
                </span>
                <span v-if="schedule.next_run" class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md" :class="isDark() ? 'bg-purple-500/10 text-purple-400' : 'bg-purple-50 text-purple-600'">
                  <Activity class="w-3 h-3" />
                  Próximo: {{ formatNextRun(schedule.next_run) }}
                </span>
                <span
                  v-if="schedule.last_run"
                  class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md"
                  :class="isDark() ? 'bg-green-500/10 text-green-400' : 'bg-green-50 text-green-600'"
                >
                  <CheckCircle class="w-3 h-3" />
                  Último: {{ formatNextRun(schedule.last_run) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Actions - responsive -->
          <div class="flex items-center gap-1.5 sm:gap-2 flex-shrink-0 ml-auto sm:ml-0">
            <button
              v-if="schedule.last_run"
              @click="viewResults(schedule.id)"
              class="p-2 rounded-lg transition-all duration-200 flex items-center gap-1 group/btn"
              :class="hasResults(schedule.id) 
                ? (isDark() ? 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30' : 'bg-purple-50 text-purple-600 hover:bg-purple-100')
                : (isDark() ? 'bg-slate-700/50 text-slate-500 cursor-not-allowed' : 'bg-slate-100 text-slate-400 cursor-not-allowed')"
              :title="hasResults(schedule.id) ? 'Ver resultados' : 'Sin resultados'"
              :disabled="!hasResults(schedule.id)"
            >
              <Database class="w-4 h-4" />
            </button>
            <button
              v-if="canRunSchedulers"
              @click="runScheduleNow(schedule.id)"
              class="p-2 rounded-lg transition-all duration-200"
              :class="isDark() ? 'bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30' : 'bg-cyan-50 text-cyan-600 hover:bg-cyan-100'"
              title="Ejecutar ahora"
            >
              <Play class="w-4 h-4" />
            </button>
            <button
              v-if="canManageSchedulers"
              @click="toggleSchedule(schedule.id)"
              class="p-2 rounded-lg transition-all duration-200"
              :class="
                schedule.enabled
                  ? (isDark() ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30' : 'bg-green-50 text-green-600 hover:bg-green-100')
                  : (isDark() ? 'bg-slate-700/50 text-slate-400 hover:bg-slate-700' : 'bg-slate-100 text-slate-500 hover:bg-slate-200')
              "
              :title="schedule.enabled ? 'Desactivar' : 'Activar'"
            >
              <Power class="w-4 h-4" />
            </button>
            <button
              v-if="canManageSchedulers"
              @click="editSchedule(schedule)"
              class="p-2 rounded-lg transition-all duration-200"
              :class="isDark() ? 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30' : 'bg-blue-50 text-blue-600 hover:bg-blue-100'"
              title="Editar"
            >
              <Edit class="w-4 h-4" />
            </button>
            <button
              v-if="canManageSchedulers"
              @click="deleteSchedule(schedule.id, schedule.name)"
              class="p-2 rounded-lg transition-all duration-200"
              :class="isDark() ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' : 'bg-red-50 text-red-600 hover:bg-red-100'"
              title="Eliminar"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Historial de Ejecuciones -->
    <div class="mt-6">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2.5">
          <div class="p-2 rounded-lg border" :class="isDark() ? 'bg-purple-500/10 border-purple-500/30' : 'bg-purple-50 border-purple-300/50'">
            <svg class="w-4.5 h-4.5" viewBox="0 0 18 18" fill="none">
              <circle cx="9" cy="9" r="7" :stroke="isDark() ? '#a78bfa' : '#7c3aed'" stroke-width="1.4" fill="none" />
              <line x1="9" y1="9" x2="9" y2="5" :stroke="isDark() ? '#a78bfa' : '#7c3aed'" stroke-width="1.4" stroke-linecap="round" />
              <line x1="9" y1="9" x2="13" y2="9" :stroke="isDark() ? '#a78bfa' : '#7c3aed'" stroke-width="1.4" stroke-linecap="round" />
              <circle cx="9" cy="9" r="1" :fill="isDark() ? '#a78bfa' : '#7c3aed'" />
            </svg>
          </div>
          <div>
            <h3 
              class="text-base font-bold tracking-wide"
              :class="isDark() ? 'text-gray-200' : 'text-slate-800'"
            >
              Historial de Ejecuciones
            </h3>
            <p 
              class="text-xs"
              :class="isDark() ? 'text-gray-400' : 'text-slate-500'"
            >
              Registro de escaneos ejecutados
            </p>
          </div>
        </div>
        <button
          @click="loadHistory"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5"
          :class="isDark() 
            ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 hover:bg-purple-500/30' 
            : 'bg-purple-50 text-purple-600 border border-purple-200 hover:bg-purple-100'"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loadingHistory }" />
          Actualizar
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loadingHistory" class="text-center py-8">
        <div class="w-6 h-6 border-3 border-purple-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p :class="isDark() ? 'text-slate-400 text-sm' : 'text-slate-600 text-sm'">Cargando historial...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!historyItems.length" class="text-center py-8">
        <div class="mx-auto mb-3 w-12 h-12">
          <svg class="w-12 h-12" viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="20" :stroke="isDark() ? '#334155' : '#cbd5e1'" stroke-width="1.5" fill="none" />
            <line v-for="i in 12" :key="i"
              :x1="24 + 16 * Math.cos((i * 30 - 90) * Math.PI / 180)"
              :y1="24 + 16 * Math.sin((i * 30 - 90) * Math.PI / 180)"
              :x2="24 + 18 * Math.cos((i * 30 - 90) * Math.PI / 180)"
              :y2="24 + 18 * Math.sin((i * 30 - 90) * Math.PI / 180)"
              :stroke="isDark() ? '#475569' : '#94a3b8'" stroke-width="1.5" stroke-linecap="round" />
            <line x1="24" y1="24" x2="24" y2="14" :stroke="isDark() ? '#64748b' : '#94a3b8'" stroke-width="2" stroke-linecap="round" />
            <line x1="24" y1="24" x2="32" y2="24" :stroke="isDark() ? '#64748b' : '#94a3b8'" stroke-width="1.5" stroke-linecap="round" />
            <circle cx="24" cy="24" r="1.5" :fill="isDark() ? '#475569' : '#94a3b8'" />
          </svg>
        </div>
        <p :class="isDark() ? 'text-slate-400' : 'text-slate-600'">No hay ejecuciones registradas</p>
        <p :class="isDark() ? 'text-slate-500 text-xs mt-1' : 'text-slate-500 text-xs mt-1'">
          Las ejecuciones de escaneos programados aparecerán aquí
        </p>
      </div>

      <!-- History Table (desktop) / Cards (mobile) -->
      <div v-else>
        <!-- Desktop table -->
        <div class="hidden md:block overflow-x-auto rounded-xl border" :class="isDark() ? 'border-slate-700/50' : 'border-slate-200'">
          <table class="w-full text-sm">
            <thead>
              <tr :class="isDark() ? 'bg-slate-800/80' : 'bg-slate-100'">
                <th class="px-4 py-3 text-left font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Fecha</th>
                <th class="px-4 py-3 text-left font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Schedule</th>
                <th class="px-4 py-3 text-left font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Tipo</th>
                <th class="px-4 py-3 text-center font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Objetivos</th>
                <th class="px-4 py-3 text-center font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Estado</th>
                <th class="px-4 py-3 text-center font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Duración</th>
                <th class="px-4 py-3 text-center font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="entry in historyItems"
                :key="entry.id"
                class="border-t transition-colors"
                :class="isDark() ? 'border-slate-700/50 hover:bg-slate-800/40' : 'border-slate-200 hover:bg-slate-50'"
              >
                <td class="px-4 py-3" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
                  <span class="text-xs font-mono">{{ formatTimestamp(entry.executed_at) }}</span>
                </td>
                <td class="px-4 py-3">
                  <span class="font-medium" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                    {{ entry.schedule_name || '—' }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span
                    class="px-2 py-1 text-xs font-semibold rounded-full"
                    :class="getScanTypeColor(entry.scan_type)"
                  >
                    {{ getScanTypeName(entry.scan_type) }}
                  </span>
                  <span
                    v-if="entry.action_type === 'shutdown' || entry.action_type === 'both'"
                    class="ml-1 px-2 py-1 text-xs font-semibold rounded-full"
                    :class="isDark() ? 'bg-red-500/20 text-red-400' : 'bg-red-100 text-red-600'"
                  >
                    {{ entry.action_type === 'shutdown' ? 'Apagado' : '+ Apagado' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span class="font-mono text-xs" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">
                    {{ entry.targets_count }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span
                    class="px-2 py-1 text-xs font-bold rounded-full"
                    :class="entry.status === 'success' 
                      ? (isDark() ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-green-100 text-green-700 border border-green-300')
                      : (isDark() ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-red-100 text-red-700 border border-red-300')"
                  >
                    {{ entry.status === 'success' ? 'Exitoso' : 'Error' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span class="text-xs font-mono" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
                    {{ formatDuration(entry.duration_seconds) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <div class="flex items-center justify-center gap-1.5">
                    <button
                      @click="viewHistoryDetail(entry.id)"
                      class="p-1.5 rounded-lg transition-all duration-200"
                      :class="isDark() ? 'bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30' : 'bg-cyan-50 text-cyan-600 hover:bg-cyan-100'"
                      title="Ver detalle"
                    >
                      <Search class="w-4 h-4" />
                    </button>
                    <button
                      v-if="canDeleteResources"
                      @click="deleteHistory(entry.id)"
                      class="p-1.5 rounded-lg transition-all duration-200"
                      :class="isDark() ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' : 'bg-red-50 text-red-600 hover:bg-red-100'"
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

        <!-- Mobile cards -->
        <div class="md:hidden space-y-2">
          <div
            v-for="entry in historyItems"
            :key="'m-' + entry.id"
            class="rounded-xl border p-3 transition-all"
            :class="isDark() ? 'bg-slate-800/30 border-slate-700/50' : 'bg-white border-slate-200'"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-sm truncate" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                {{ entry.schedule_name || '—' }}
              </span>
              <span
                class="px-2 py-0.5 text-[10px] font-bold rounded-full flex-shrink-0 ml-2"
                :class="entry.status === 'success' 
                  ? (isDark() ? 'bg-green-500/20 text-green-400' : 'bg-green-100 text-green-700')
                  : (isDark() ? 'bg-red-500/20 text-red-400' : 'bg-red-100 text-red-700')"
              >
                {{ entry.status === 'success' ? 'Exitoso' : 'Error' }}
              </span>
            </div>
            <div class="flex items-center gap-2 flex-wrap text-xs mb-2" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
              <span class="px-1.5 py-0.5 rounded" :class="getScanTypeColor(entry.scan_type)">{{ getScanTypeName(entry.scan_type) }}</span>
              <span class="font-mono">{{ entry.targets_count }} obj.</span>
              <span class="font-mono">{{ formatDuration(entry.duration_seconds) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-mono" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">{{ formatTimestamp(entry.executed_at) }}</span>
              <div class="flex gap-1">
                <button @click="viewHistoryDetail(entry.id)" class="p-1.5 rounded-lg" :class="isDark() ? 'bg-cyan-500/20 text-cyan-400' : 'bg-cyan-50 text-cyan-600'">
                  <Search class="w-3.5 h-3.5" />
                </button>
                <button v-if="canDeleteResources" @click="deleteHistory(entry.id)" class="p-1.5 rounded-lg" :class="isDark() ? 'bg-red-500/20 text-red-400' : 'bg-red-50 text-red-600'">
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="historyTotal > historyLimit" class="flex items-center justify-between px-4 py-3 mt-2 rounded-xl border" :class="isDark() ? 'border-slate-700/50 bg-slate-800/50' : 'border-slate-200 bg-slate-50'">
          <span class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">
            {{ historyItems.length }} de {{ historyTotal }}
          </span>
          <div class="flex gap-2">
            <button
              @click="historyPage > 0 && (historyPage--, loadHistory())"
              :disabled="historyPage === 0"
              class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200"
              :class="historyPage === 0 
                ? (isDark() ? 'bg-slate-700/30 text-slate-500 cursor-not-allowed' : 'bg-slate-100 text-slate-400 cursor-not-allowed')
                : (isDark() ? 'bg-slate-700 text-slate-300 hover:bg-slate-600' : 'bg-slate-200 text-slate-700 hover:bg-slate-300')"
            >
              Anterior
            </button>
            <button
              @click="(historyPage + 1) * historyLimit < historyTotal && (historyPage++, loadHistory())"
              :disabled="(historyPage + 1) * historyLimit >= historyTotal"
              class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200"
              :class="(historyPage + 1) * historyLimit >= historyTotal 
                ? (isDark() ? 'bg-slate-700/30 text-slate-500 cursor-not-allowed' : 'bg-slate-100 text-slate-400 cursor-not-allowed')
                : (isDark() ? 'bg-slate-700 text-slate-300 hover:bg-slate-600' : 'bg-slate-200 text-slate-700 hover:bg-slate-300')"
            >
              Siguiente
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- History Detail Modal -->
    <teleport to="body">
      <div
        v-if="showHistoryDetailModal"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto"
        @click.self="showHistoryDetailModal = false"
      >
        <div
          class="rounded-2xl p-6 max-w-4xl w-full shadow-2xl my-8 max-h-[calc(100vh-4rem)] overflow-y-auto"
          :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
        >
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-xl font-bold" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
              Detalle de Ejecución
            </h3>
            <button
              @click="showHistoryDetailModal = false"
              class="p-1.5 rounded-lg transition-colors"
              :class="isDark() ? 'hover:bg-slate-800' : 'hover:bg-slate-200'"
            >
              <X class="w-5 h-5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'" />
            </button>
          </div>

          <div v-if="loadingHistoryDetail" class="text-center py-8">
            <div class="w-6 h-6 border-3 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p :class="isDark() ? 'text-slate-400 text-sm' : 'text-slate-600 text-sm'">Cargando detalle...</p>
          </div>

          <div v-else-if="historyDetail" class="space-y-4">
            <!-- Info Header -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div class="rounded-lg p-3 border text-center" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
                <p class="text-2xl font-bold" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">{{ historyDetail.targets_count }}</p>
                <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Objetivos</p>
              </div>
              <div class="rounded-lg p-3 border text-center" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
                <p class="text-2xl font-bold flex justify-center" :class="historyDetail.status === 'success' ? (isDark() ? 'text-green-400' : 'text-green-600') : (isDark() ? 'text-red-400' : 'text-red-600')">
                  <svg v-if="historyDetail.status === 'success'" class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  <svg v-else class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </p>
                <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">{{ historyDetail.status === 'success' ? 'Exitoso' : 'Error' }}</p>
              </div>
              <div class="rounded-lg p-3 border text-center" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
                <p class="text-2xl font-bold" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">{{ formatDuration(historyDetail.duration_seconds) }}</p>
                <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Duración</p>
              </div>
              <div class="rounded-lg p-3 border text-center" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
                <p class="text-sm font-bold truncate" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">{{ historyDetail.schedule_name }}</p>
                <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                  {{ formatTimestamp(historyDetail.executed_at) }}
                </p>
              </div>
            </div>

            <!-- Error Message -->
            <div v-if="historyDetail.error_message" class="rounded-xl p-4 border" :class="isDark() ? 'bg-red-500/10 border-red-500/50' : 'bg-red-50 border-red-200'">
              <p class="font-semibold mb-1" :class="isDark() ? 'text-red-400' : 'text-red-600'">Error</p>
              <p class="text-sm" :class="isDark() ? 'text-red-300' : 'text-red-500'">{{ historyDetail.error_message }}</p>
            </div>

            <!-- Scan Results - Vista mejorada -->
            <div v-if="historyDetail.scan_results && historyDetail.scan_results.length" class="rounded-xl p-4 border" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
              <h4 class="font-bold mb-3 flex items-center gap-2" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                <Database class="w-5 h-5" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
                Resultados del Escaneo ({{ historyDetail.scan_results.length }} registros)
              </h4>

              <!-- Resumen stats -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                <div class="rounded-lg p-2.5 text-center" :class="isDark() ? 'bg-slate-900/50' : 'bg-white'">
                  <p class="text-lg font-bold" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">
                    {{ historyDetail.scan_results.filter(r => r.status === 'up' || r.alive === true).length }}
                  </p>
                  <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Activos</p>
                </div>
                <div class="rounded-lg p-2.5 text-center" :class="isDark() ? 'bg-slate-900/50' : 'bg-white'">
                  <p class="text-lg font-bold" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                    {{ historyDetail.scan_results.filter(r => r.status === 'down' || r.status === 'error' || r.alive === false).length }}
                  </p>
                  <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Inactivos</p>
                </div>
                <div class="rounded-lg p-2.5 text-center" :class="isDark() ? 'bg-slate-900/50' : 'bg-white'">
                  <p class="text-lg font-bold" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">
                    {{ historyDetail.scan_results.reduce((s, r) => s + (r.ports?.length || 0), 0) }}
                  </p>
                  <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puertos</p>
                </div>
                <div class="rounded-lg p-2.5 text-center" :class="isDark() ? 'bg-slate-900/50' : 'bg-white'">
                  <p class="text-lg font-bold" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">
                    {{ historyDetail.scan_results.reduce((s, r) => s + (r.services?.length || 0), 0) }}
                  </p>
                  <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicios</p>
                </div>
              </div>

              <!-- Resultados por host -->
              <div class="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                <div v-for="(result, ri) in historyDetail.scan_results" :key="ri"
                  class="rounded-lg border p-3" :class="isDark() ? 'border-slate-700/50 bg-slate-900/50' : 'border-slate-200 bg-white'">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: (result.status === 'up' || result.alive === true) ? '#10b981' : '#64748b' }"></div>
                      <span class="font-mono font-bold text-sm" :class="isDark() ? 'text-white' : 'text-slate-800'">{{ result.host || result.ip || '—' }}</span>
                      <span v-if="result.hostname" class="text-xs" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">{{ result.hostname }}</span>
                    </div>
                    <div class="flex items-center gap-2 text-xs">
                      <span v-if="result.mac" class="font-mono px-1.5 py-0.5 rounded" :class="isDark() ? 'bg-slate-800 text-slate-400' : 'bg-slate-100 text-slate-500'">{{ result.mac }}</span>
                      <span v-if="result.vendor" class="px-1.5 py-0.5 rounded" :class="isDark() ? 'bg-slate-800 text-amber-400' : 'bg-amber-50 text-amber-700'">{{ result.vendor }}</span>
                      <span v-if="result.os?.name" class="px-1.5 py-0.5 rounded" :class="isDark() ? 'bg-slate-800 text-blue-400' : 'bg-blue-50 text-blue-700'">{{ result.os.name }}</span>
                      <span v-if="result.latency_ms" class="font-mono" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">{{ result.latency_ms?.toFixed(1) }}ms</span>
                    </div>
                  </div>

                  <!-- Puertos y Servicios inline -->
                  <div v-if="result.ports?.length || result.services?.length" class="mt-2 pt-2 border-t flex flex-wrap gap-1.5" :class="isDark() ? 'border-slate-800' : 'border-slate-100'">
                    <span v-for="p in (result.ports || []).slice(0, 15)" :key="'p' + p.port" class="px-1.5 py-0.5 rounded text-xs font-mono" :class="isDark() ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'">
                      {{ p.port || p }}<span v-if="p.service" class="opacity-60">/{{ p.service }}</span>
                    </span>
                    <span v-if="(result.ports || []).length > 15" class="px-1.5 py-0.5 text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
                      +{{ result.ports.length - 15 }} más
                    </span>
                    <template v-if="result.services?.length">
                      <span v-for="svc in result.services.filter(s => s.product).slice(0, 5)" :key="'s' + svc.port" class="px-1.5 py-0.5 rounded text-xs" :class="isDark() ? 'bg-purple-500/10 text-purple-300 border border-purple-500/20' : 'bg-purple-50 text-purple-700 border border-purple-200'">
                        {{ svc.product }}<span v-if="svc.version" class="opacity-60"> v{{ svc.version }}</span>
                      </span>
                    </template>
                  </div>
                </div>
              </div>
            </div>

            <!-- Shutdown Results - Mejorado -->
            <div v-if="historyDetail.shutdown_results" class="rounded-xl p-4 border" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
              <h4 class="font-bold mb-3 flex items-center gap-2" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                <Power class="w-5 h-5 text-red-400" />
                Resultados de Apagado
              </h4>
              
              <!-- Si tiene la estructura procesada (active_ips, success_ips, etc.) -->
              <div v-if="historyDetail.shutdown_results.total_active !== undefined" class="space-y-3">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <div class="rounded-lg p-2.5 text-center" :class="isDark() ? 'bg-slate-900/50' : 'bg-white'">
                    <p class="text-lg font-bold" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">{{ historyDetail.shutdown_results.total_active }}</p>
                    <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Activos detectados</p>
                  </div>
                  <div class="rounded-lg p-2.5 text-center" :class="isDark() ? 'bg-slate-900/50' : 'bg-white'">
                    <p class="text-lg font-bold" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">{{ historyDetail.shutdown_results.total_success }}</p>
                    <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Apagados OK</p>
                  </div>
                  <div class="rounded-lg p-2.5 text-center" :class="isDark() ? 'bg-slate-900/50' : 'bg-white'">
                    <p class="text-lg font-bold" :class="isDark() ? 'text-red-400' : 'text-red-600'">{{ historyDetail.shutdown_results.total_failed }}</p>
                    <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Fallidos</p>
                  </div>
                  <div class="rounded-lg p-2.5 text-center" :class="isDark() ? 'bg-slate-900/50' : 'bg-white'">
                    <p class="text-lg font-bold" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">{{ historyDetail.shutdown_results.total_inactive }}</p>
                    <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Ya inactivos</p>
                  </div>
                </div>
                <div v-if="historyDetail.shutdown_results.success_ips?.length" class="flex flex-wrap gap-1.5">
                  <span class="text-xs font-semibold mr-1" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">Apagados:</span>
                  <span v-for="ip in historyDetail.shutdown_results.success_ips" :key="ip" class="px-1.5 py-0.5 rounded font-mono text-xs" :class="isDark() ? 'bg-emerald-500/10 text-emerald-300' : 'bg-emerald-50 text-emerald-700'">{{ ip }}</span>
                </div>
                <div v-if="historyDetail.shutdown_results.failed_ips?.length" class="flex flex-wrap gap-1.5">
                  <span class="text-xs font-semibold mr-1" :class="isDark() ? 'text-red-400' : 'text-red-600'">Fallidos:</span>
                  <span v-for="f in historyDetail.shutdown_results.failed_ips" :key="f.host" class="px-1.5 py-0.5 rounded font-mono text-xs" :class="isDark() ? 'bg-red-500/10 text-red-300' : 'bg-red-50 text-red-700'">{{ f.host || f }}<span v-if="f.error" class="opacity-60 ml-1">({{ f.error }})</span></span>
                </div>
              </div>
              
              <!-- Fallback: JSON formateado -->
              <div v-else class="max-h-96 overflow-y-auto">
                <pre class="text-xs p-4 rounded-lg" :class="isDark() ? 'text-slate-300 bg-slate-900/50' : 'text-slate-700 bg-white'">{{ JSON.stringify(historyDetail.shutdown_results, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Schedule Modal -->
    <teleport to="body">
      <div
        v-if="showScheduleModal"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto"
        @click.self="closeModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="schedule-modal-title"
      >
        <div
          class="rounded-2xl max-w-3xl w-full shadow-2xl my-8 max-h-[calc(100vh-1rem)] overflow-y-auto"
          :class="isDark() ? 'bg-slate-900 border border-slate-700/60' : 'bg-white border border-slate-200'"
        >
          <!-- Modal header -->
          <div class="flex items-center justify-between px-5 py-4 border-b sticky top-0 z-10"
               :class="isDark() ? 'bg-slate-900 border-slate-700/60' : 'bg-white border-slate-200'">
            <div class="flex items-center gap-2.5">
              <div class="p-2 rounded-lg" :class="isDark() ? 'bg-cyan-500/15' : 'bg-cyan-50'">
                <Calendar class="w-4 h-4 text-cyan-500" />
              </div>
              <h3 id="schedule-modal-title" class="text-base font-bold" :class="isDark() ? 'text-slate-100' : 'text-slate-800'">
                {{ editingSchedule ? "Editar" : "Nueva" }} Programación
              </h3>
            </div>
            <button @click="closeModal" class="p-1.5 rounded-lg transition-colors" :class="isDark() ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'">
              <X class="w-4.5 h-4.5" />
            </button>
          </div>

          <form @submit.prevent="saveSchedule" class="px-5 py-4 space-y-4">

            <!-- ─── Name ─── -->
            <div>
              <label for="schedule-name" class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Nombre</label>
              <input id="schedule-name" v-model="formData.name" type="text" required
                class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all"
                :class="isDark() ? 'bg-slate-800/60 border border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-cyan-500/60 focus:ring-cyan-500/20' : 'bg-slate-50 border border-slate-200 text-slate-800 placeholder:text-slate-400 focus:border-cyan-500 focus:ring-cyan-500/20'"
                placeholder="Ej: Escaneo diario de red" />
            </div>

            <!-- ─── Action Type — segmented control ─── -->
            <div>
              <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Tipo de acción</label>
              <div class="flex rounded-lg overflow-hidden border" :class="isDark() ? 'border-slate-700 bg-slate-800/40' : 'border-slate-200 bg-slate-50'">
                <button type="button" v-for="opt in [
                  { val: 'scan', icon: Wifi, label: 'Escaneo', color: 'cyan' },
                  { val: 'shutdown', icon: Power, label: 'Apagado', color: 'red' },
                  { val: 'both', icon: Activity, label: 'Ambos', color: 'amber' }
                ]" :key="opt.val"
                  @click="formData.actionType = opt.val"
                  class="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-semibold transition-all relative"
                  :class="formData.actionType === opt.val
                    ? `bg-${opt.color}-500/20 text-${opt.color}-400 shadow-sm`
                    : (isDark() ? 'text-slate-500 hover:text-slate-300 hover:bg-slate-700/40' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100')">
                  <component :is="opt.icon" class="w-3.5 h-3.5" />
                  {{ opt.label }}
                  <div v-if="formData.actionType === opt.val" class="absolute bottom-0 inset-x-2 h-0.5 rounded-full" :class="`bg-${opt.color}-400`"></div>
                </button>
              </div>
            </div>

            <!-- ─── Scan Type — icon cards (only for scan/both) ─── -->
            <div v-if="formData.actionType === 'scan' || formData.actionType === 'both'">
              <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Tipo de escaneo</label>
              <div class="grid grid-cols-3 gap-1.5">
                <button type="button" v-for="st in [
                  { val: 'ping', icon: Wifi, label: 'Ping' },
                  { val: 'ports', icon: Server, label: 'Puertos' },
                  { val: 'services', icon: Shield, label: 'Servicios' },
                  { val: 'os', icon: Monitor, label: 'SO' },
                  { val: 'mac', icon: Search, label: 'MAC' },
                  { val: 'full', icon: Database, label: 'Completo' }
                ]" :key="st.val"
                  @click="formData.scanType = st.val"
                  class="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-all"
                  :class="formData.scanType === st.val
                    ? (isDark() ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-300' : 'bg-cyan-50 border-cyan-400 text-cyan-700')
                    : (isDark() ? 'border-slate-700/50 text-slate-400 hover:border-slate-600 hover:text-slate-300' : 'border-slate-200 text-slate-500 hover:border-slate-300 hover:text-slate-700')">
                  <component :is="st.icon" class="w-3.5 h-3.5 flex-shrink-0" />
                  {{ st.label }}
                </button>
              </div>
            </div>

            <!-- ─── Frequency + Time row ─── -->
            <div class="grid grid-cols-2 gap-3">
              <!-- Frequency pills -->
              <div>
                <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Frecuencia</label>
                <div class="flex flex-wrap gap-1.5">
                  <button type="button" v-for="fr in [
                    { val: 'hourly', label: 'Hora' },
                    { val: 'daily', label: 'Diario' },
                    { val: 'weekly', label: 'Semanal' },
                    { val: 'monthly', label: 'Mensual' }
                  ]" :key="fr.val"
                    @click="formData.frequency = fr.val"
                    class="px-2.5 py-1.5 rounded-md text-xs font-medium border transition-all"
                    :class="formData.frequency === fr.val
                      ? (isDark() ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-300' : 'bg-cyan-50 border-cyan-400 text-cyan-700')
                      : (isDark() ? 'border-slate-700 text-slate-500 hover:text-slate-300 hover:border-slate-600' : 'border-slate-200 text-slate-400 hover:text-slate-600 hover:border-slate-300')">
                    {{ fr.label }}
                  </button>
                </div>
              </div>

              <!-- Time picker (hidden for hourly) -->
              <div v-if="formData.frequency !== 'hourly'">
                <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Hora</label>
                <div class="relative">
                  <!-- Trigger button -->
                  <button type="button" @click="syncTimeFromForm(); showTimePicker = !showTimePicker"
                    class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-mono border transition-all"
                    :class="isDark()
                      ? 'bg-slate-800/60 border-slate-700 text-slate-100 hover:border-cyan-500/40'
                      : 'bg-slate-50 border-slate-200 text-slate-800 hover:border-cyan-400'">
                    <!-- Mini analog clock -->
                    <svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 20 20" fill="none">
                      <circle cx="10" cy="10" r="8.5" :stroke="isDark() ? '#22d3ee' : '#0891b2'" stroke-width="1.2" fill="none" />
                      <line v-for="i in 12" :key="i"
                        :x1="10 + 6.5 * Math.cos((i * 30 - 90) * Math.PI / 180)"
                        :y1="10 + 6.5 * Math.sin((i * 30 - 90) * Math.PI / 180)"
                        :x2="10 + 7.5 * Math.cos((i * 30 - 90) * Math.PI / 180)"
                        :y2="10 + 7.5 * Math.sin((i * 30 - 90) * Math.PI / 180)"
                        :stroke="isDark() ? '#475569' : '#94a3b8'" stroke-width="1" stroke-linecap="round" />
                      <line x1="10" y1="10"
                        :x2="10 + 4 * Math.cos(((parseInt(formData.time?.split(':')[0] || 0) % 12) * 30 + parseInt(formData.time?.split(':')[1] || 0) * 0.5 - 90) * Math.PI / 180)"
                        :y2="10 + 4 * Math.sin(((parseInt(formData.time?.split(':')[0] || 0) % 12) * 30 + parseInt(formData.time?.split(':')[1] || 0) * 0.5 - 90) * Math.PI / 180)"
                        :stroke="isDark() ? '#22d3ee' : '#0891b2'" stroke-width="1.5" stroke-linecap="round" />
                      <line x1="10" y1="10"
                        :x2="10 + 6 * Math.cos((parseInt(formData.time?.split(':')[1] || 0) * 6 - 90) * Math.PI / 180)"
                        :y2="10 + 6 * Math.sin((parseInt(formData.time?.split(':')[1] || 0) * 6 - 90) * Math.PI / 180)"
                        :stroke="isDark() ? '#a78bfa' : '#7c3aed'" stroke-width="1" stroke-linecap="round" />
                      <circle cx="10" cy="10" r="1" :fill="isDark() ? '#22d3ee' : '#0891b2'" />
                    </svg>
                    <span class="text-base font-bold tabular-nums">{{ formData.time || '00:00' }}</span>
                    <span class="text-xs ml-auto" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">hrs</span>
                  </button>

                  <!-- Dropdown time picker -->
                  <div v-if="showTimePicker"
                    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
                    @click.self="showTimePicker = false">
                    <div class="rounded-xl border shadow-2xl p-4 w-72"
                      :class="isDark() ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'">

                      <div class="flex items-center gap-4">
                        <!-- Analog clock preview (compact) -->
                        <svg class="w-20 h-20 flex-shrink-0" viewBox="0 0 80 80" fill="none">
                          <circle cx="40" cy="40" r="37" :stroke="isDark() ? '#1e293b' : '#f1f5f9'" stroke-width="3" :fill="isDark() ? '#0f172a' : '#f8fafc'" />
                          <circle cx="40" cy="40" r="37" :stroke="isDark() ? '#334155' : '#e2e8f0'" stroke-width="1.2" fill="none" />
                          <g v-for="i in 12" :key="i">
                            <line
                              :x1="40 + 30 * Math.cos((i * 30 - 90) * Math.PI / 180)"
                              :y1="40 + 30 * Math.sin((i * 30 - 90) * Math.PI / 180)"
                              :x2="40 + (i % 3 === 0 ? 33 : 34) * Math.cos((i * 30 - 90) * Math.PI / 180)"
                              :y2="40 + (i % 3 === 0 ? 33 : 34) * Math.sin((i * 30 - 90) * Math.PI / 180)"
                              :stroke="isDark() ? '#475569' : '#94a3b8'" :stroke-width="i % 3 === 0 ? 2 : 1" stroke-linecap="round" />
                          </g>
                          <text v-for="i in 12" :key="'n'+i"
                            :x="40 + 25 * Math.cos((i * 30 - 90) * Math.PI / 180)"
                            :y="40 + 25 * Math.sin((i * 30 - 90) * Math.PI / 180) + 3"
                            text-anchor="middle" :fill="isDark() ? '#64748b' : '#94a3b8'" font-size="7" font-weight="600">{{ i }}</text>
                          <line x1="40" y1="40"
                            :x2="40 + 15 * Math.cos((hourHandAngle - 90) * Math.PI / 180)"
                            :y2="40 + 15 * Math.sin((hourHandAngle - 90) * Math.PI / 180)"
                            :stroke="isDark() ? '#22d3ee' : '#0891b2'" stroke-width="2.5" stroke-linecap="round" />
                          <line x1="40" y1="40"
                            :x2="40 + 23 * Math.cos((minuteHandAngle - 90) * Math.PI / 180)"
                            :y2="40 + 23 * Math.sin((minuteHandAngle - 90) * Math.PI / 180)"
                            :stroke="isDark() ? '#a78bfa' : '#7c3aed'" stroke-width="1.5" stroke-linecap="round" />
                          <circle cx="40" cy="40" r="2.5" :fill="isDark() ? '#22d3ee' : '#0891b2'" />
                          <circle cx="40" cy="40" r="1" :fill="isDark() ? '#0f172a' : '#f8fafc'" />
                        </svg>

                        <!-- Digital spinners -->
                        <div class="flex items-center gap-1">
                          <div class="flex flex-col items-center gap-0.5">
                            <button type="button" @click="adjustHour(1)" class="p-1 rounded-md transition-colors" :class="isDark() ? 'hover:bg-slate-700 text-slate-400' : 'hover:bg-slate-100 text-slate-500'">
                              <svg class="w-4 h-4" viewBox="0 0 16 16" fill="none"><path d="M4 10l4-4 4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                            </button>
                            <div class="w-12 text-center py-1.5 rounded-lg text-xl font-bold tabular-nums" :class="isDark() ? 'bg-slate-800 text-cyan-400' : 'bg-slate-100 text-cyan-700'">
                              {{ String(selectedHour).padStart(2, '0') }}
                            </div>
                            <button type="button" @click="adjustHour(-1)" class="p-1 rounded-md transition-colors" :class="isDark() ? 'hover:bg-slate-700 text-slate-400' : 'hover:bg-slate-100 text-slate-500'">
                              <svg class="w-4 h-4" viewBox="0 0 16 16" fill="none"><path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                            </button>
                          </div>
                          <span class="text-xl font-bold pb-1" :class="isDark() ? 'text-slate-500' : 'text-slate-300'">:</span>
                          <div class="flex flex-col items-center gap-0.5">
                            <button type="button" @click="adjustMinute(5)" class="p-1 rounded-md transition-colors" :class="isDark() ? 'hover:bg-slate-700 text-slate-400' : 'hover:bg-slate-100 text-slate-500'">
                              <svg class="w-4 h-4" viewBox="0 0 16 16" fill="none"><path d="M4 10l4-4 4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                            </button>
                            <div class="w-12 text-center py-1.5 rounded-lg text-xl font-bold tabular-nums" :class="isDark() ? 'bg-slate-800 text-purple-400' : 'bg-slate-100 text-purple-700'">
                              {{ String(selectedMinute).padStart(2, '0') }}
                            </div>
                            <button type="button" @click="adjustMinute(-5)" class="p-1 rounded-md transition-colors" :class="isDark() ? 'hover:bg-slate-700 text-slate-400' : 'hover:bg-slate-100 text-slate-500'">
                              <svg class="w-4 h-4" viewBox="0 0 16 16" fill="none"><path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                            </button>
                          </div>
                        </div>
                      </div>

                      <!-- Quick presets + confirm in one row -->
                      <div class="flex items-center gap-1.5 mt-3 pt-3 border-t" :class="isDark() ? 'border-slate-700/50' : 'border-slate-200'">
                        <button type="button" v-for="m in [0, 15, 30, 45]" :key="m"
                          @click="selectedMinute = m; updateFormTime()"
                          class="flex-1 py-1.5 rounded-md text-xs font-semibold transition-all"
                          :class="selectedMinute === m
                            ? (isDark() ? 'bg-purple-500/20 text-purple-300 ring-1 ring-purple-500/40' : 'bg-purple-50 text-purple-700 ring-1 ring-purple-300')
                            : (isDark() ? 'text-slate-500 hover:bg-slate-800 hover:text-slate-300' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600')">
                          :{{ String(m).padStart(2, '0') }}
                        </button>
                        <button type="button" @click="showTimePicker = false"
                          class="flex-1 py-1.5 rounded-md text-xs font-bold transition-all"
                          :class="isDark() ? 'bg-cyan-500/15 text-cyan-300 hover:bg-cyan-500/25' : 'bg-cyan-50 text-cyan-700 hover:bg-cyan-100'">
                          Listo
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- ─── Day of Week — pill buttons (weekly only) ─── -->
            <div v-if="formData.frequency === 'weekly'">
              <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Día de la semana</label>
              <div class="flex gap-1">
                <button type="button" v-for="d in [
                  { val: '1', label: 'L' }, { val: '2', label: 'M' }, { val: '3', label: 'X' },
                  { val: '4', label: 'J' }, { val: '5', label: 'V' }, { val: '6', label: 'S' }, { val: '0', label: 'D' }
                ]" :key="d.val"
                  @click="formData.dayOfWeek = d.val"
                  class="flex-1 py-2 rounded-lg text-xs font-bold transition-all text-center"
                  :class="formData.dayOfWeek === d.val
                    ? (isDark() ? 'bg-cyan-500/20 text-cyan-300 ring-1 ring-cyan-500/50' : 'bg-cyan-50 text-cyan-700 ring-1 ring-cyan-400')
                    : (isDark() ? 'text-slate-500 hover:bg-slate-800 hover:text-slate-300' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600')">
                  {{ d.label }}
                </button>
              </div>
            </div>

            <!-- ─── Day of Month (monthly only) ─── -->
            <div v-if="formData.frequency === 'monthly'">
              <label for="day-of-month" class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Día del mes</label>
              <input id="day-of-month" v-model.number="formData.dayOfMonth" type="number" min="1" max="31" required
                class="w-24 px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all"
                :class="isDark() ? 'bg-slate-800/60 border border-slate-700 text-slate-100 focus:border-cyan-500/60 focus:ring-cyan-500/20' : 'bg-slate-50 border border-slate-200 text-slate-800 focus:border-cyan-500 focus:ring-cyan-500/20'" />
            </div>

            <!-- ─── Target Configuration ─── -->
            <div class="pt-1">
              <label class="block text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Objetivo</label>
              <!-- Target type tabs -->
              <div class="flex gap-1 mb-2">
                <button type="button" v-for="tt in [
                  { val: 'subnet', label: 'Subred' }, { val: 'range', label: 'Rango' }, { val: 'hosts', label: 'Hosts' }
                ]" :key="tt.val"
                  @click="targetType = tt.val"
                  class="px-3 py-1.5 rounded-md text-xs font-semibold transition-all"
                  :class="targetType === tt.val
                    ? (isDark() ? 'bg-slate-700 text-slate-100' : 'bg-slate-200 text-slate-800')
                    : (isDark() ? 'text-slate-500 hover:text-slate-300' : 'text-slate-400 hover:text-slate-600')">
                  {{ tt.label }}
                </button>
              </div>
              <input
                v-if="targetType === 'subnet'" v-model="formData.targetSubnet" type="text" placeholder="192.168.0.0/24"
                class="w-full px-3 py-2 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 transition-all"
                :class="isDark() ? 'bg-slate-800/60 border border-slate-700 text-slate-100 placeholder:text-slate-600 focus:border-cyan-500/60 focus:ring-cyan-500/20' : 'bg-slate-50 border border-slate-200 text-slate-800 placeholder:text-slate-400 focus:border-cyan-500 focus:ring-cyan-500/20'" />
              <input
                v-else-if="targetType === 'range'" v-model="formData.targetRange" type="text" placeholder="192.168.0.1-192.168.0.254"
                class="w-full px-3 py-2 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 transition-all"
                :class="isDark() ? 'bg-slate-800/60 border border-slate-700 text-slate-100 placeholder:text-slate-600 focus:border-cyan-500/60 focus:ring-cyan-500/20' : 'bg-slate-50 border border-slate-200 text-slate-800 placeholder:text-slate-400 focus:border-cyan-500 focus:ring-cyan-500/20'" />
              <input
                v-else v-model="formData.targetHosts" type="text" placeholder="192.168.0.10, 192.168.0.20"
                class="w-full px-3 py-2 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 transition-all"
                :class="isDark() ? 'bg-slate-800/60 border border-slate-700 text-slate-100 placeholder:text-slate-600 focus:border-cyan-500/60 focus:ring-cyan-500/20' : 'bg-slate-50 border border-slate-200 text-slate-800 placeholder:text-slate-400 focus:border-cyan-500 focus:ring-cyan-500/20'" />
            </div>

            <!-- ─── Shutdown config (shutdown / both only) ─── -->
            <div v-if="formData.actionType === 'shutdown' || formData.actionType === 'both'"
              class="rounded-xl p-3.5 space-y-3 border"
              :class="isDark() ? 'bg-red-500/5 border-red-500/20' : 'bg-red-50/50 border-red-200'">

              <div class="flex items-center gap-2">
                <Power class="w-3.5 h-3.5 text-red-400" />
                <span class="text-xs font-bold" :class="isDark() ? 'text-red-300' : 'text-red-700'">Configuración de Apagado</span>
              </div>

              <!-- Shutdown after scan toggle (both mode) -->
              <label v-if="formData.actionType === 'both'"
                class="flex items-center gap-2.5 cursor-pointer rounded-lg px-3 py-2"
                :class="isDark() ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-amber-50 border border-amber-200'">
                <input v-model="formData.shutdownAfterScan" type="checkbox"
                  class="w-3.5 h-3.5 rounded text-red-500 focus:ring-red-500/50"
                  :class="isDark() ? 'border-slate-600' : 'border-slate-300'" />
                <span class="text-xs font-medium" :class="isDark() ? 'text-amber-300' : 'text-amber-700'">Apagar después del escaneo</span>
              </label>

              <!-- SSH Credentials -->
              <div class="space-y-2">
                <p class="text-xs font-semibold" :class="isDark() ? 'text-slate-300' : 'text-slate-600'">Credenciales SSH</p>

                <!-- Saved credentials quick-pick -->
                <div v-if="savedSSHCredentials.length > 0" class="flex flex-wrap gap-1.5">
                  <button v-for="cred in savedSSHCredentials" :key="cred.id" type="button"
                    @click="applySavedSSHCredential(cred)"
                    class="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium border transition-all"
                    :class="isDark()
                      ? 'bg-slate-800/60 border-slate-600 text-slate-300 hover:bg-cyan-500/15 hover:border-cyan-500/40 hover:text-cyan-300'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-cyan-50 hover:border-cyan-400 hover:text-cyan-700'">
                    <Key class="w-3 h-3 flex-shrink-0" />
                    {{ cred.name }}
                    <span class="opacity-50">({{ cred.username }})</span>
                  </button>
                </div>

                <div class="grid grid-cols-2 gap-2">
                  <div>
                    <label for="ssh-username" class="block text-xs mb-1 font-medium" :class="isDark() ? 'text-slate-500' : 'text-slate-500'">Usuario</label>
                    <input id="ssh-username" v-model="formData.sshUsername" type="text" placeholder="usuario" required
                      class="w-full px-2.5 py-1.5 rounded-lg text-sm focus:outline-none focus:ring-1 transition-all"
                      :class="isDark() ? 'bg-slate-800/80 border border-slate-700 text-slate-200 focus:border-red-500/60 focus:ring-red-500/30' : 'bg-white border border-slate-200 text-slate-800 focus:border-red-400 focus:ring-red-400/30'" />
                  </div>
                  <div>
                    <label for="ssh-password" class="block text-xs mb-1 font-medium" :class="isDark() ? 'text-slate-500' : 'text-slate-500'">Contraseña</label>
                    <input id="ssh-password" v-model="formData.sshPassword" type="password" placeholder="••••••••" required
                      class="w-full px-2.5 py-1.5 rounded-lg text-sm focus:outline-none focus:ring-1 transition-all"
                      :class="isDark() ? 'bg-slate-800/80 border border-slate-700 text-slate-200 focus:border-red-500/60 focus:ring-red-500/30' : 'bg-white border border-slate-200 text-slate-800 focus:border-red-400 focus:ring-red-400/30'" />
                  </div>
                </div>
              </div>
            </div>

            <!-- ─── Footer: Enabled toggle + Actions ─── -->
            <div class="flex items-center justify-between pt-2 border-t" :class="isDark() ? 'border-slate-700/50' : 'border-slate-200'">
              <label class="flex items-center gap-2 cursor-pointer select-none">
                <input v-model="formData.enabled" type="checkbox"
                  class="w-3.5 h-3.5 rounded text-cyan-500 focus:ring-cyan-500/50"
                  :class="isDark() ? 'border-slate-600' : 'border-slate-300'" />
                <span class="text-xs font-medium" :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Activar inmediatamente</span>
              </label>
              <div class="flex gap-2">
                <button type="button" @click="closeModal"
                  class="px-4 py-2 rounded-lg text-xs font-semibold transition-all"
                  :class="isDark() ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-200' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'">
                  Cancelar
                </button>
                <button type="submit"
                  class="px-5 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg text-xs font-bold hover:shadow-lg hover:shadow-cyan-500/30 transition-all">
                  {{ editingSchedule ? "Actualizar" : "Crear" }}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </teleport>

    <!-- Results Modal -->
    <teleport to="body">
      <div
        v-if="showResultsModal"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="closeResultsModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="results-modal-title"
      >
        <div
          class="rounded-2xl border p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-2xl"
          :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border-slate-200'"
        >
          <div class="flex items-center justify-between mb-6">
            <h3
              id="results-modal-title"
              class="text-2xl font-bold"
              :class="isDark() ? 'text-slate-200' : 'text-slate-800'"
            >
              Resultados de Escaneo
            </h3>
            <button
              @click="closeResultsModal"
              class="p-2 rounded-lg transition-colors"
              :class="isDark() ? 'hover:bg-slate-800' : 'hover:bg-slate-100'"
              aria-label="Cerrar modal"
            >
              <X class="w-6 h-6" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
            </button>
          </div>

          <!-- Loading -->
          <div v-if="loadingResults" class="text-center py-12">
            <div
              class="w-8 h-8 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            ></div>
            <p :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Cargando resultados...</p>
          </div>

          <!-- No Results -->
          <div
            v-else-if="!currentResults || !currentResults.has_results"
            class="text-center py-12"
          >
            <Database class="w-16 h-16 mx-auto mb-4" :class="isDark() ? 'text-slate-600' : 'text-slate-300'" />
            <p class="text-lg" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">No hay resultados disponibles</p>
            <p class="text-sm mt-2" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
              Ejecuta el escaneo para ver los resultados
            </p>
          </div>

          <!-- Results Content -->
          <div v-else class="space-y-4">
            <!-- Metadata -->
            <div
              class="rounded-xl p-4 border"
              :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'"
            >
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Tipo de Acción</p>
                  <p class="font-semibold" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                    {{ currentResults.results.action_type === 'shutdown' ? 'Apagado' : currentResults.results.action_type === 'both' ? 'Escaneo + Apagado' : getScanTypeName(currentResults.results.scan_type) }}
                  </p>
                </div>
                <div>
                  <p :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Estado</p>
                  <span
                    class="px-2 py-1 text-xs font-semibold rounded-full"
                    :class="
                      currentResults.results.status === 'success'
                        ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                        : 'bg-red-500/20 text-red-400 border border-red-500/50'
                    "
                  >
                    {{
                      currentResults.results.status === "success"
                        ? "Exitoso"
                        : "Error"
                    }}
                  </span>
                </div>
                <div>
                  <p :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Targets Escaneados</p>
                  <p class="font-semibold" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                    {{ currentResults.results.targets_count }}
                  </p>
                </div>
                <div>
                  <p :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Fecha</p>
                  <p class="font-semibold" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                    {{ formatTimestamp(currentResults.results.timestamp) }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Scan Results -->
            <div
              v-if="
                currentResults.results.scan_results &&
                currentResults.results.scan_results.length > 0
              "
              class="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50"
            >
              <h4 class="text-lg font-bold text-slate-200 mb-4">
                Resultados del Escaneo
              </h4>
              <div class="overflow-x-auto">
                <div class="max-h-96 overflow-y-auto">
                  <pre
                    class="text-xs text-slate-300 bg-slate-900/50 p-4 rounded-lg"
                    >{{
                      JSON.stringify(
                        currentResults.results.scan_results,
                        null,
                        2
                      )
                    }}</pre
                  >
                </div>
              </div>
            </div>

            <!-- Shutdown Results -->
            <div
              v-if="
                currentResults.results.shutdown_results &&
                typeof currentResults.results.shutdown_results === 'object' &&
                !Array.isArray(currentResults.results.shutdown_results)
              "
              class="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50"
            >
              <h4 class="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
                <Power class="w-5 h-5 text-red-400" />
                Resultados de Apagado
              </h4>

              <!-- Resumen de apagado -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
                <div class="bg-slate-900/50 rounded-lg p-3 border border-slate-700/30 text-center">
                  <p class="text-2xl font-bold text-cyan-400">{{ currentResults.results.shutdown_results.total_active || 0 }}</p>
                  <p class="text-xs text-slate-400 mt-1">IPs Activas</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-3 border border-green-700/30 text-center">
                  <p class="text-2xl font-bold text-green-400">{{ currentResults.results.shutdown_results.total_success || 0 }}</p>
                  <p class="text-xs text-slate-400 mt-1">Apagadas</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-3 border border-red-700/30 text-center">
                  <p class="text-2xl font-bold text-red-400">{{ currentResults.results.shutdown_results.total_failed || 0 }}</p>
                  <p class="text-xs text-slate-400 mt-1">Fallidas</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-3 border border-slate-700/30 text-center">
                  <p class="text-2xl font-bold text-slate-500">{{ currentResults.results.shutdown_results.total_inactive || 0 }}</p>
                  <p class="text-xs text-slate-400 mt-1">Inactivas (omitidas)</p>
                </div>
              </div>

              <!-- IPs apagadas exitosamente -->
              <div v-if="currentResults.results.shutdown_results.success_ips && currentResults.results.shutdown_results.success_ips.length > 0" class="mb-4">
                <h5 class="text-sm font-semibold text-green-400 mb-2 flex items-center gap-2">
                  <CheckCircle class="w-4 h-4" />
                  IPs Apagadas Exitosamente ({{ currentResults.results.shutdown_results.success_ips.length }})
                </h5>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  <div
                    v-for="ip in currentResults.results.shutdown_results.success_ips"
                    :key="'ok-' + ip"
                    class="flex items-center gap-2 px-3 py-2 bg-green-900/20 border border-green-700/30 rounded-lg"
                  >
                    <div class="w-2 h-2 rounded-full bg-green-400"></div>
                    <span class="text-sm font-mono text-green-300">{{ ip }}</span>
                  </div>
                </div>
              </div>

              <!-- IPs que fallaron -->
              <div v-if="currentResults.results.shutdown_results.failed_ips && currentResults.results.shutdown_results.failed_ips.length > 0" class="mb-4">
                <h5 class="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
                  <X class="w-4 h-4" />
                  IPs que No se Apagaron ({{ currentResults.results.shutdown_results.failed_ips.length }})
                </h5>
                <div class="space-y-2">
                  <div
                    v-for="(result, index) in currentResults.results.shutdown_results.failed_ips"
                    :key="'fail-' + index"
                    class="flex items-center justify-between px-3 py-2 bg-red-900/20 border border-red-700/30 rounded-lg"
                  >
                    <div class="flex items-center gap-2">
                      <div class="w-2 h-2 rounded-full bg-red-400"></div>
                      <span class="text-sm font-mono text-red-300">{{ result.host }}</span>
                    </div>
                    <span class="text-xs text-red-400/70 max-w-[200px] truncate" :title="result.error">
                      {{ result.error || 'Error desconocido' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Mensaje si no hay IPs activas -->
              <div v-if="currentResults.results.shutdown_results.total_active === 0" class="text-center py-4">
                <p class="text-slate-400">No se encontraron IPs activas para apagar</p>
              </div>
            </div>

            <!-- Error Message -->
            <div
              v-if="
                currentResults.results.status === 'error' &&
                currentResults.results.error
              "
              class="bg-red-500/10 border border-red-500/50 rounded-xl p-4"
            >
              <p class="text-red-400 font-semibold mb-2">
                Error en la Ejecución
              </p>
              <p class="text-red-300 text-sm">
                {{ currentResults.results.error }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Confirmation Modal -->
    <teleport to="body">
      <div
        v-if="showConfirmModal"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="showConfirmModal = false"
      >
        <div
          class="rounded-2xl shadow-2xl border p-6 max-w-md w-full transform transition-all"
          :class="isDark() ? 'bg-gray-900 border-gray-700' : 'bg-white border-slate-200'"
        >
          <div class="flex items-start gap-4 mb-6">
            <div
              :class="[
                'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0',
                confirmModalData.type === 'danger'
                  ? (isDark() ? 'bg-red-500/20' : 'bg-red-100')
                  : (isDark() ? 'bg-yellow-500/20' : 'bg-yellow-100'),
              ]"
            >
              <svg
                v-if="confirmModalData.type === 'danger'"
                class="w-6 h-6 text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <svg
                v-else
                class="w-6 h-6 text-yellow-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <div class="flex-1">
              <h3 class="text-xl font-bold mb-2" :class="isDark() ? 'text-white' : 'text-slate-900'">
                {{ confirmModalData.title }}
              </h3>
              <p
                class="text-sm whitespace-pre-line leading-relaxed"
                :class="isDark() ? 'text-gray-300' : 'text-slate-600'"
              >
                {{ confirmModalData.message }}
              </p>
            </div>
          </div>

          <div class="flex gap-3">
            <button
              @click="showConfirmModal = false"
              class="flex-1 px-4 py-3 rounded-xl font-semibold transition-colors duration-200"
              :class="isDark() ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'"
            >
              {{ confirmModalData.cancelText }}
            </button>
            <button
              @click="
                () => {
                  confirmModalData.onConfirm?.();
                  showConfirmModal = false;
                }
              "
              :class="[
                'flex-1 px-4 py-3 rounded-xl font-semibold transition-all duration-200',
                confirmModalData.type === 'danger'
                  ? 'bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-500/30'
                  : 'bg-yellow-600 hover:bg-yellow-700 text-white shadow-lg shadow-yellow-500/30',
              ]"
            >
              {{ confirmModalData.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Result Modal -->
    <teleport to="body">
      <div
        v-if="showResultModal"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="showResultModal = false"
      >
        <div
          class="rounded-2xl shadow-2xl border p-6 max-w-md w-full transform transition-all"
          :class="isDark() ? 'bg-gray-900 border-gray-700' : 'bg-white border-slate-200'"
        >
          <div class="flex items-start gap-4 mb-6">
            <div
              :class="[
                'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0',
                resultModalData.type === 'success'
                  ? (isDark() ? 'bg-emerald-500/20' : 'bg-emerald-100')
                  : resultModalData.type === 'error'
                    ? (isDark() ? 'bg-red-500/20' : 'bg-red-100')
                    : (isDark() ? 'bg-yellow-500/20' : 'bg-yellow-100'),
              ]"
            >
              <svg
                v-if="resultModalData.type === 'success'"
                class="w-6 h-6 text-emerald-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <svg
                v-else-if="resultModalData.type === 'error'"
                class="w-6 h-6 text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
              <svg
                v-else
                class="w-6 h-6 text-yellow-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <div class="flex-1">
              <h3 class="text-xl font-bold mb-2" :class="isDark() ? 'text-white' : 'text-slate-900'">
                {{ resultModalData.title }}
              </h3>
              <p
                class="text-sm whitespace-pre-line leading-relaxed"
                :class="isDark() ? 'text-gray-300' : 'text-slate-600'"
              >
                {{ resultModalData.message }}
              </p>
            </div>
          </div>

          <button
            @click="showResultModal = false"
            class="w-full px-4 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-xl font-semibold transition-colors duration-200"
          >
            Cerrar
          </button>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import {
  Calendar,
  Plus,
  Power,
  Edit,
  Trash2,
  Tag,
  Activity,
  X,
  Wifi,
  Server,
  Monitor,
  Search,
  Shield,
  Database,
  Play,
  CheckCircle,
  RefreshCw,
  User,
  Key,
  FolderOpen,
} from "lucide-vue-next";
import { useToast } from "../composables/useToast";
import { scannerAPI } from "../api/scanner";
import { useGlobalWebSocket } from "../composables/useWebSocket";
import { useTheme } from "../composables/useTheme";
import { usePermissions } from "../composables/usePermissions";

const toast = useToast();
const ws = useGlobalWebSocket();
const { isDark } = useTheme();
const { canManageSchedulers, canRunSchedulers, canDeleteResources } = usePermissions();

const schedules = ref([]);
const loading = ref(false);
const showScheduleModal = ref(false);
const editingSchedule = ref(null);
const showResultsModal = ref(false);
const loadingResults = ref(false);
const currentResults = ref(null);
const showConfirmModal = ref(false);
const showResultModal = ref(false);
const confirmModalData = ref({});
const resultModalData = ref({});
const targetType = ref("subnet"); // 'subnet', 'range', 'hosts'
let pollingInterval = null; // Variable para el intervalo de actualización

// Saved SSH credentials
const savedSSHCredentials = ref([]);

const loadSavedSSHCredentials = async () => {
  try {
    savedSSHCredentials.value = await scannerAPI.getSSHCredentials();
  } catch {
    savedSSHCredentials.value = [];
  }
};

const applySavedSSHCredential = async (cred) => {
  try {
    const full = await scannerAPI.getSSHCredential(cred.id);
    formData.value.sshUsername = full.username;
    formData.value.sshPassword = full.password || '';
    toast.success(`Credenciales "${cred.name}" aplicadas`, 'SSH');
  } catch {
    toast.error('Error al cargar credencial', 'SSH');
  }
};

// History state
const historyItems = ref([]);
const historyTotal = ref(0);
const historyPage = ref(0);
const historyLimit = 20;
const loadingHistory = ref(false);
const showHistoryDetailModal = ref(false);
const loadingHistoryDetail = ref(false);
const historyDetail = ref(null);

// Obtener hora local actual en formato HH:MM
const getCurrentTime = () => {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
};

// Custom time picker state
const selectedHour = ref(0);
const selectedMinute = ref(0);
const showTimePicker = ref(false);

const syncTimeFromForm = () => {
  const parts = (formData.value?.time || '00:00').split(':');
  selectedHour.value = parseInt(parts[0]) || 0;
  selectedMinute.value = parseInt(parts[1]) || 0;
};

const updateFormTime = () => {
  const h = String(selectedHour.value).padStart(2, '0');
  const m = String(selectedMinute.value).padStart(2, '0');
  formData.value.time = `${h}:${m}`;
};

const adjustHour = (delta) => {
  selectedHour.value = (selectedHour.value + delta + 24) % 24;
  updateFormTime();
};

const adjustMinute = (delta) => {
  selectedMinute.value = (selectedMinute.value + delta + 60) % 60;
  updateFormTime();
};

const formattedTime = computed(() => {
  const h = String(selectedHour.value).padStart(2, '0');
  const m = String(selectedMinute.value).padStart(2, '0');
  return `${h}:${m}`;
});

const hourHandAngle = computed(() => {
  return (selectedHour.value % 12) * 30 + selectedMinute.value * 0.5;
});

const minuteHandAngle = computed(() => {
  return selectedMinute.value * 6;
});

const formData = ref({
  name: "",
  actionType: "scan",
  scanType: "ping",
  frequency: "daily",
  time: getCurrentTime(),
  dayOfWeek: "1",
  dayOfMonth: 1,
  enabled: true,
  targetSubnet: "",
  targetRange: "",
  targetHosts: "",
  autoShutdown: false,
  shutdownAfterScan: false,
  shutdownTargets: "",
  sshUsername: "",
  sshPassword: "",
  sshSudoPassword: "",
});

const getScanTypeIcon = (type) => {
  const icons = {
    ping: Wifi,
    ports: Server,
    services: Server,
    os: Monitor,
    mac: Search,
    full: Database,
  };
  return icons[type] || Database;
};

const getScanTypeName = (type) => {
  const names = {
    ping: "Ping",
    ports: "Puertos",
    services: "Servicios",
    os: "Detección de SO",
    mac: "Dirección MAC",
    full: "Escaneo Completo",
  };
  return names[type] || type;
};

const getScanTypeColor = (type) => {
  const colors = {
    ping: "bg-cyan-500/20 text-cyan-400",
    ports: "bg-blue-500/20 text-blue-400",
    services: "bg-purple-500/20 text-purple-400",
    os: "bg-green-500/20 text-green-400",
    mac: "bg-yellow-500/20 text-yellow-400",
    full: "bg-red-500/20 text-red-400",
  };
  return colors[type] || "bg-slate-500/20 text-slate-400";
};

const getScheduleDescription = (schedule) => {
  const descriptions = {
    hourly: "Cada hora",
    daily: `Diario a las ${schedule.time}`,
    weekly: `Semanal (${getDayName(schedule.day_of_week)}) a las ${schedule.time}`,
    monthly: `Mensual (día ${schedule.day_of_month}) a las ${schedule.time}`,
  };
  return descriptions[schedule.frequency] || schedule.frequency;
};

const getDayName = (day) => {
  const days = [
    "Domingo",
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
  ];
  return days[day] || "";
};

const formatNextRun = (date) => {
  return new Date(date).toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// Verificar si hay resultados disponibles para un schedule
const hasResults = (scheduleId) => {
  // Verifica si el schedule tiene last_run (fue ejecutado al menos una vez)
  const schedule = schedules.value.find(s => s.id === scheduleId);
  return schedule && schedule.last_run;
};

// ==================== API CALLS ====================

const loadSchedules = async (showToast = true) => {
  // No mostrar loading en actualizaciones automáticas
  if (showToast) {
    loading.value = true;
  }

  try {
    const newSchedules = await scannerAPI.getSchedules();

    // Si es la primera carga, reemplazar todo
    if (schedules.value.length === 0) {
      schedules.value = newSchedules;
    } else {
      // Actualizar solo schedules existentes sin reemplazar el array
      newSchedules.forEach((newSchedule) => {
        const index = schedules.value.findIndex((s) => s.id === newSchedule.id);

        if (index !== -1) {
          // Actualizar solo campos individuales para mantener reactividad sin re-render
          const existing = schedules.value[index];
          if (existing.last_run !== newSchedule.last_run)
            existing.last_run = newSchedule.last_run;
          if (existing.next_run !== newSchedule.next_run)
            existing.next_run = newSchedule.next_run;
          if (existing.execution_count !== newSchedule.execution_count)
            existing.execution_count = newSchedule.execution_count;
          if (existing.enabled !== newSchedule.enabled)
            existing.enabled = newSchedule.enabled;
          if (existing.name !== newSchedule.name)
            existing.name = newSchedule.name;
        } else {
          // Schedule nuevo, agregarlo
          schedules.value.push(newSchedule);
        }
      });

      // Eliminar schedules que ya no existen
      schedules.value = schedules.value.filter((s) =>
        newSchedules.some((ns) => ns.id === s.id)
      );
    }

    if (showToast) {
      toast.success(`${schedules.value.length} schedules cargados`);
    }
  } catch (err) {
    if (showToast) {
      toast.error("Error cargando escaneos programados");
    }
  } finally {
    if (showToast) {
      loading.value = false;
    }
  }
};

const saveSchedule = async () => {
  loading.value = true;
  try {
    // Mapear campos del frontend al formato del backend
    const scheduleData = {
      name: formData.value.name,
      action_type: formData.value.actionType,
      scan_type:
        formData.value.actionType === "shutdown"
          ? null
          : formData.value.scanType,
      frequency: formData.value.frequency,
      time: formData.value.time,
      day_of_week:
        formData.value.frequency === "weekly"
          ? parseInt(formData.value.dayOfWeek)
          : null,
      day_of_month:
        formData.value.frequency === "monthly"
          ? parseInt(formData.value.dayOfMonth)
          : null,
      enabled: formData.value.enabled,
      target_subnet: formData.value.targetSubnet || null,
      target_range: formData.value.targetRange || null,
      target_hosts: formData.value.targetHosts || null,
      auto_shutdown:
        formData.value.actionType === "shutdown" ||
        formData.value.actionType === "both",
      shutdown_after_scan:
        formData.value.actionType === "both"
          ? formData.value.shutdownAfterScan
          : false,
      shutdown_targets: null, // Se usarán los mismos objetivos configurados arriba
      ssh_username: formData.value.sshUsername || null,
      ssh_password: formData.value.sshPassword || null,
      ssh_sudo_password: formData.value.sshSudoPassword || null,
    };

    if (editingSchedule.value) {
      // Actualizar
      await scannerAPI.updateSchedule(editingSchedule.value.id, scheduleData);
      toast.success("Escaneo programado actualizado");
    } else {
      // Crear
      await scannerAPI.createSchedule(scheduleData);
      toast.success("Escaneo programado creado");
    }

    await loadSchedules();
    closeModal();
  } catch (err) {
    toast.error("Error guardando escaneo programado");
  } finally {
    loading.value = false;
  }
};

const editSchedule = (schedule) => {
  editingSchedule.value = schedule;
  // Mapear campos del backend al formato del frontend
  formData.value = {
    name: schedule.name,
    actionType: schedule.action_type || "scan",
    scanType: schedule.scan_type || "ping",
    frequency: schedule.frequency,
    time: schedule.time || "00:00",
    dayOfWeek: schedule.day_of_week?.toString() || "1",
    dayOfMonth: schedule.day_of_month || 1,
    enabled: schedule.enabled,
    targetSubnet: schedule.target_subnet || "",
    targetRange: schedule.target_range || "",
    targetHosts: schedule.target_hosts || "",
    autoShutdown: schedule.auto_shutdown || false,
    shutdownAfterScan: schedule.shutdown_after_scan || false,
    shutdownTargets: schedule.shutdown_targets || "",
    sshUsername: schedule.ssh_username || "",
    sshPassword: schedule.ssh_password || "",
    sshSudoPassword: schedule.ssh_sudo_password || "",
  };
  showScheduleModal.value = true;
};

const deleteSchedule = async (id, name) => {
  confirmModalData.value = {
    title: "Confirmar Eliminación",
    message: `¿Estás seguro de que deseas eliminar el escaneo "${name}"?\n\nEsta acción no se puede deshacer.`,
    confirmText: "Eliminar",
    cancelText: "Cancelar",
    type: "danger",
    onConfirm: async () => {
      loading.value = true;
      try {
        await scannerAPI.deleteSchedule(id);
        await loadSchedules();
        showResultModal.value = true;
        resultModalData.value = {
          title: "Escaneo Eliminado",
          message: `El escaneo programado "${name}" ha sido eliminado exitosamente.`,
          type: "success",
        };
      } catch (err) {
        showResultModal.value = true;
        resultModalData.value = {
          title: "Error",
          message:
            "No se pudo eliminar el escaneo programado. Intenta nuevamente.",
          type: "error",
        };
      } finally {
        loading.value = false;
      }
    },
  };
  showConfirmModal.value = true;
};

const toggleSchedule = async (id) => {
  loading.value = true;
  try {
    const updatedSchedule = await scannerAPI.toggleSchedule(id);
    toast.info(
      updatedSchedule.enabled ? "Escaneo activado" : "Escaneo desactivado"
    );
    await loadSchedules();
  } catch (err) {
    toast.error("Error activando/desactivando escaneo");
  } finally {
    loading.value = false;
  }
};

const runScheduleNow = async (id) => {
  loading.value = true;
  try {
    await scannerAPI.runScheduleNow(id);
    toast.success("Escaneo iniciado en segundo plano");
    await loadSchedules();
  } catch (err) {
    toast.error("Error ejecutando escaneo");
  } finally {
    loading.value = false;
  }
};

const closeModal = () => {
  showScheduleModal.value = false;
  editingSchedule.value = null;
  formData.value = {
    name: "",
    actionType: "scan",
    scanType: "ping",
    frequency: "daily",
    time: getCurrentTime(),
    dayOfWeek: "1",
    dayOfMonth: 1,
    enabled: true,
    targetSubnet: "",
    targetRange: "",
    targetHosts: "",
    autoShutdown: false,
    shutdownAfterScan: false,
    shutdownTargets: "",
    sshUsername: "",
    sshPassword: "",
    sshSudoPassword: "",
  };
};

const viewResults = async (scheduleId) => {
  showResultsModal.value = true;
  loadingResults.value = true;
  currentResults.value = null;

  try {
    const results = await scannerAPI.getScheduleResults(scheduleId);
    currentResults.value = results;
  } catch (err) {
    toast.error("Error cargando resultados del escaneo");
  } finally {
    loadingResults.value = false;
  }
};

const closeResultsModal = () => {
  showResultsModal.value = false;
  currentResults.value = null;
};

const formatTimestamp = (timestamp) => {
  if (!timestamp) return "N/A";
  return new Date(timestamp).toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

// ==================== HISTORY FUNCTIONS ====================

const loadHistory = async () => {
  loadingHistory.value = true;
  try {
    const data = await scannerAPI.getAllScanHistory(historyPage.value * historyLimit, historyLimit);
    historyItems.value = data.items || [];
    historyTotal.value = data.total || 0;
  } catch (err) {
    toast.error("Error cargando historial de ejecuciones");
  } finally {
    loadingHistory.value = false;
  }
};

const viewHistoryDetail = async (historyId) => {
  showHistoryDetailModal.value = true;
  loadingHistoryDetail.value = true;
  historyDetail.value = null;
  
  try {
    const data = await scannerAPI.getHistoryDetail(historyId);
    historyDetail.value = data;
  } catch (err) {
    toast.error("Error cargando detalle de ejecución");
  } finally {
    loadingHistoryDetail.value = false;
  }
};

const deleteHistory = async (historyId) => {
  confirmModalData.value = {
    title: "Eliminar Registro",
    message: "¿Estás seguro de que deseas eliminar este registro del historial?",
    confirmText: "Eliminar",
    cancelText: "Cancelar",
    type: "danger",
    onConfirm: async () => {
      try {
        await scannerAPI.deleteHistoryEntry(historyId);
        toast.success("Registro eliminado");
        await loadHistory();
      } catch (err) {
        toast.error("Error eliminando registro");
      }
    },
  };
  showConfirmModal.value = true;
};

const formatDuration = (seconds) => {
  if (!seconds && seconds !== 0) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (mins < 60) return `${mins}m ${secs}s`;
  const hours = Math.floor(mins / 60);
  const remainMins = mins % 60;
  return `${hours}h ${remainMins}m`;
};

// Cargar schedules al montar el componente
onMounted(() => {
  loadSchedules(true); // Mostrar toast en la carga inicial
  loadHistory(); // Cargar historial
  loadSavedSSHCredentials(); // Cargar credenciales SSH guardadas

  // Escuchar eventos WebSocket para actualizaciones en tiempo real
  ws.on('schedule_update', (data) => {
    handleScheduleUpdate(data);
  });
});

// Limpiar al desmontar el componente
onBeforeUnmount(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }
});

// Manejar actualizaciones de schedules por WebSocket
const handleScheduleUpdate = (data) => {
  const { action, schedule, schedule_id } = data;
  
  switch (action) {
    case 'created':
      // Agregar nuevo schedule
      schedules.value.push(schedule);
      toast.success(`Nuevo schedule "${schedule.name}" creado`);
      break;
      
    case 'updated':
    case 'toggled':
    case 'executed':
      // Actualizar schedule existente
      const index = schedules.value.findIndex(s => s.id === schedule.id);
      if (index !== -1) {
        // Actualizar solo campos específicos
        const existing = schedules.value[index];
        Object.keys(schedule).forEach(key => {
          if (existing[key] !== schedule[key]) {
            existing[key] = schedule[key];
          }
        });
        
        if (action === 'executed') {
          // Refrescar historial cuando se ejecuta un scan
          loadHistory();
          
          // Mostrar notificación con detalle de apagado si aplica
          if (data.shutdown_results && data.shutdown_results.total_active !== undefined) {
            const sr = data.shutdown_results
            if (sr.total_success > 0 || sr.total_failed > 0) {
              const msgs = []
              if (sr.total_success > 0) msgs.push(`${sr.total_success} apagada(s)`)
              if (sr.total_failed > 0) msgs.push(`${sr.total_failed} fallida(s)`)
              toast.info(`Apagado programado: ${msgs.join(', ')} de ${sr.total_active} activa(s)`)
            } else if (sr.total_active === 0) {
              toast.info('Apagado programado: No se encontraron IPs activas')
            }
          }
        }
      }
      break;
      
    case 'deleted':
      // Eliminar schedule
      const deleteIndex = schedules.value.findIndex(s => s.id === schedule_id);
      if (deleteIndex !== -1) {
        const deletedName = schedules.value[deleteIndex].name;
        schedules.value.splice(deleteIndex, 1);
        toast.success(`Schedule "${deletedName}" eliminado`);
      }
      break;
  }
};

</script>
