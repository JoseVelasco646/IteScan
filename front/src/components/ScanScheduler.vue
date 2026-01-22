<template>
  <div
    class="rounded-3xl p-6 shadow-2xl"
    :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
  >
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <div
          class="p-3 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 rounded-xl border-2 border-cyan-500/50"
        >
          <Calendar class="w-6 h-6 text-cyan-400" />
        </div>
        <div>
          <h3 
            class="font-tagesschrift text-lg font-semibold mb-2 tracking-wide text-xl"
            :class="isDark() ? 'text-gray-200' : 'text-slate-800'"
          >
            Escaneos Programados
          </h3>
          <p 
            class="font-tagesschrift text-lg font-semibold mb-2 tracking-wide text-s"
            :class="isDark() ? 'text-gray-200' : 'text-slate-600'"
          >
            Automatiza tus escaneos de red
          </p>
        </div>
      </div>
      <button
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
      <p :class="isDark() ? 'text-slate-400' : 'text-slate-600'">Cargando schedules...</p>
    </div>

    <div v-else-if="schedules.length === 0" class="text-center py-12">
      <Clock :class="isDark() ? 'w-16 h-16 text-slate-600 mx-auto mb-4' : 'w-16 h-16 text-slate-400 mx-auto mb-4'" />
      <p 
        class="text-lg"
        :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
      >No hay escaneos programados</p>
      <p 
        class="text-sm mt-2"
        :class="isDark() ? 'text-slate-500' : 'text-slate-500'"
      >
        Crea tu primer escaneo automático
      </p>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="schedule in schedules"
        :key="schedule.id"
        class="rounded-xl p-4 transition-all duration-300 relative overflow-hidden"
        :class="[
          schedule.action_type === 'shutdown' || schedule.action_type === 'both'
            ? 'bg-gradient-to-br from-red-900/30 via-orange-900/20 to-red-900/30 border-2 border-red-500/50 hover:border-red-400/70 shadow-lg shadow-red-500/10'
            : 'bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50'
        ]"
      >
        <!-- Indicator de apagado automático -->
        <div
          v-if="schedule.action_type === 'shutdown' || schedule.action_type === 'both'"
          class="absolute top-0 right-0 bg-gradient-to-br from-red-500 to-orange-600 text-white text-xs font-bold px-3 py-1 rounded-bl-lg flex items-center gap-1"
        >
          <Power class="w-3 h-3" />
          {{ schedule.action_type === 'shutdown' ? 'APAGADO AUTO' : 'SCAN + APAGADO' }}
        </div>
        
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4 flex-1">
            <!-- Type Icon -->
            <div
              class="p-3 rounded-lg"
              :class="schedule.action_type === 'shutdown' || schedule.action_type === 'both'
                ? 'bg-gradient-to-br from-red-500/30 to-orange-500/30 border border-red-500/50'
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
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <h4 
                  class="font-semibold"
                  :class="schedule.action_type === 'shutdown' || schedule.action_type === 'both'
                    ? 'text-red-200'
                    : 'text-slate-200'"
                >
                  {{ schedule.name }}
                </h4>
                <span
                  class="px-2 py-1 text-xs font-semibold rounded-full"
                  :class="
                    schedule.enabled
                      ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                      : 'bg-slate-700/50 text-slate-400 border border-slate-600/50'
                  "
                >
                  {{ schedule.enabled ? "Activo" : "Inactivo" }}
                </span>
              </div>
              <div 
                class="flex items-center gap-4 text-sm"
                :class="schedule.action_type === 'shutdown' || schedule.action_type === 'both'
                  ? 'text-red-300/80'
                  : 'text-slate-400'"
              >
                <span class="flex items-center gap-1">
                  <Tag class="w-4 h-4" />
                  {{ getScanTypeName(schedule.scan_type) }}
                </span>
                <span class="flex items-center gap-1">
                  <Clock class="w-4 h-4" />
                  {{ getScheduleDescription(schedule) }}
                </span>
                <span v-if="schedule.next_run" class="flex items-center gap-1">
                  <Activity class="w-4 h-4" />
                  Próximo: {{ formatNextRun(schedule.next_run) }}
                </span>
                <span
                  v-if="schedule.last_run"
                  class="flex items-center gap-1 text-green-400"
                >
                  <CheckCircle class="w-4 h-4" />
                  Último: {{ formatNextRun(schedule.last_run) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2">
            <button
              v-if="schedule.last_run"
              @click="viewResults(schedule.id)"
              class="p-2 rounded-lg transition-all duration-300 flex items-center gap-1"
              :class="hasResults(schedule.id) ? 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30' : 'bg-slate-700/50 text-slate-500 cursor-not-allowed'"
              :aria-label="hasResults(schedule.id) ? 'Ver resultados' : 'Sin resultados'"
              :title="hasResults(schedule.id) ? 'Ver resultados de la última ejecución' : 'Ejecutado pero sin resultados disponibles'"
              :disabled="!hasResults(schedule.id)"
            >
              <Database class="w-5 h-5" />
              <span v-if="!hasResults(schedule.id)" class="text-xs">Sin datos</span>
            </button>
            <button
              @click="runScheduleNow(schedule.id)"
              class="p-2 bg-cyan-500/20 text-cyan-400 rounded-lg hover:bg-cyan-500/30 transition-all duration-300"
              aria-label="Ejecutar escaneo ahora"
            >
              <Play class="w-5 h-5" />
            </button>
            <button
              @click="toggleSchedule(schedule.id)"
              class="p-2 rounded-lg transition-all duration-300"
              :class="
                schedule.enabled
                  ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                  : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
              "
              :aria-label="
                schedule.enabled ? 'Desactivar escaneo' : 'Activar escaneo'
              "
            >
              <Power class="w-5 h-5" />
            </button>
            <button
              @click="editSchedule(schedule)"
              class="p-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-all duration-300"
              aria-label="Editar escaneo programado"
            >
              <Edit class="w-5 h-5" />
            </button>
            <button
              @click="deleteSchedule(schedule.id, schedule.name)"
              class="p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-all duration-300"
              aria-label="Eliminar escaneo programado"
            >
              <Trash2 class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>

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
          class="rounded-2xl p-6 max-w-2xl w-full shadow-2xl my-8 max-h-[calc(100vh-4rem)] overflow-y-auto"
          :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-gradient-to-br from-white via-slate-50 to-white border border-slate-200'"
        >
          <div class="flex items-center justify-between mb-4 sticky top-0 z-10 pb-3" 
               :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900' : 'bg-gradient-to-br from-white via-slate-50 to-white'">
            <h3
              id="schedule-modal-title"
              class="text-xl font-bold"
              :class="isDark() ? 'text-slate-200' : 'text-slate-800'"
            >
              {{ editingSchedule ? "Editar" : "Nuevo" }} Schedule
            </h3>
            <button
              @click="closeModal"
              class="p-1.5 rounded-lg transition-colors"
              :class="isDark() ? 'hover:bg-slate-800' : 'hover:bg-slate-200'"
              aria-label="Cerrar modal"
            >
              <X class="w-5 h-5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'" />
            </button>
          </div>

          <form @submit.prevent="saveSchedule" class="space-y-3">
            <!-- Name -->
            <div>
              <label
                for="schedule-name"
                class="block text-xs font-semibold mb-1.5 tracking-wide"
                :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
                >Nombre</label
              >
              <input
                id="schedule-name"
                v-model="formData.name"
                type="text"
                required
                class="w-full px-3 py-2.5 rounded-lg font-medium focus:outline-none focus:ring-2 shadow-sm transition-all duration-200 text-sm"
                :class="isDark() ? 'bg-slate-950/50 border border-slate-700/50 text-slate-100 placeholder:text-slate-500 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-600' : 'bg-white border border-slate-300 text-slate-800 placeholder:text-slate-400 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-400'"
                placeholder="Ej: Escaneo Diario de Red"
              />
            </div>

            <!-- Action Type and Frequency - 2 columns -->
            <div class="grid grid-cols-2 gap-3">
              <!-- Action Type -->
              <div>
                <label
                  for="action-type"
                  class="block text-xs font-semibold mb-1.5 tracking-wide"
                  :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
                  >Acción</label
                >
                <div class="relative">
                  <select
                    id="action-type"
                    v-model="formData.actionType"
                    required
                    class="w-full px-3 py-2.5 rounded-lg font-medium focus:outline-none focus:ring-2 shadow-sm transition-all duration-200 appearance-none cursor-pointer pr-8 text-sm"
                    :class="isDark() ? 'bg-slate-950/50 border border-slate-700/50 text-slate-100 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-600' : 'bg-white border border-slate-300 text-slate-800 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-400'"
                  >
                    <option value="scan" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                      Solo Escaneo
                    </option>
                    <option value="shutdown" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                      Solo Apagado
                    </option>
                    <option value="both" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                      Escaneo + Apagado
                    </option>
                  </select>
                  <div
                    class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none"
                  >
                    <svg
                      class="w-4 h-4"
                      :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>
              </div>

              <!-- Frequency -->
              <div>
                <label
                  for="frequency"
                  class="block text-xs font-semibold mb-1.5 tracking-wide"
                  :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
                  >Frecuencia</label
                >
                <div class="relative">
                  <select
                    id="frequency"
                    v-model="formData.frequency"
                    required
                    class="w-full px-3 py-2.5 rounded-lg font-medium focus:outline-none focus:ring-2 shadow-sm transition-all duration-200 appearance-none cursor-pointer pr-8 text-sm"
                    :class="isDark() ? 'bg-slate-950/50 border border-slate-700/50 text-slate-100 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-600' : 'bg-white border border-slate-300 text-slate-800 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-400'"
                  >
                    <option value="hourly" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                      Cada Hora
                    </option>
                    <option value="daily" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                      Diariamente
                    </option>
                    <option value="weekly" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                      Semanalmente
                    </option>
                    <option value="monthly" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                      Mensualmente
                    </option>
                  </select>
                  <div
                    class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none"
                  >
                    <svg
                      class="w-4 h-4"
                      :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            <!-- Scan Type -->
            <div
              v-if="
                formData.actionType === 'scan' || formData.actionType === 'both'
              "
            >
              <label
                for="scan-type"
                class="block text-xs font-semibold mb-1.5 tracking-wide"
                :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
                >Tipo de Escaneo</label
              >
              <div class="relative">
                <select
                  id="scan-type"
                  v-model="formData.scanType"
                  required
                  class="w-full px-3 py-2.5 rounded-lg font-medium focus:outline-none focus:ring-2 shadow-sm transition-all duration-200 appearance-none cursor-pointer pr-8 text-sm"
                  :class="isDark() ? 'bg-slate-950/50 border border-slate-700/50 text-slate-100 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-600' : 'bg-white border border-slate-300 text-slate-800 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-400'"
                >
                  <option value="ping" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                    Ping
                  </option>
                  <option value="ports" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                    Puertos
                  </option>
                  <option value="services" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                    Servicios
                  </option>
                  <option value="os" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                    Detección de SO
                  </option>
                  <option value="mac" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                    MAC Address
                  </option>
                  <option value="full" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">
                    Escaneo Completo
                  </option>
                </select>
                <div
                  class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none"
                >
                  <svg
                    class="w-4 h-4"
                    :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </div>
            </div>

            <!-- Time and Day fields in compact grid -->
            <div class="grid gap-3" :class="formData.frequency !== 'hourly' && (formData.frequency === 'weekly' || formData.frequency === 'monthly') ? 'grid-cols-2' : 'grid-cols-1'">
              <!-- Time -->
              <div v-if="formData.frequency !== 'hourly'">
                <label
                  for="schedule-time"
                  class="block text-xs font-semibold mb-1.5 tracking-wide"
                  :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
                  >Hora</label
                >
                <input
                  id="schedule-time"
                  v-model="formData.time"
                  type="time"
                  required
                  class="w-full px-3 py-2.5 rounded-lg font-medium focus:outline-none focus:ring-2 shadow-sm transition-all duration-200 text-sm"
                  :class="isDark() ? 'bg-slate-950/50 border border-slate-700/50 text-slate-100 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-600' : 'bg-white border border-slate-300 text-slate-800 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-400'"
                />
              </div>

              <!-- Day of Week (for weekly) -->
              <div v-if="formData.frequency === 'weekly'">
                <label
                  for="day-of-week"
                  class="block text-xs font-semibold mb-1.5 tracking-wide"
                  :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
                  >Día</label
                >
                <div class="relative">
                  <select
                    id="day-of-week"
                    v-model="formData.dayOfWeek"
                    required
                    class="w-full px-3 py-2.5 rounded-lg font-medium focus:outline-none focus:ring-2 shadow-sm transition-all duration-200 appearance-none cursor-pointer pr-8 text-sm"
                    :class="isDark() ? 'bg-slate-950/50 border border-slate-700/50 text-slate-100 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-600' : 'bg-white border border-slate-300 text-slate-800 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-400'"
                  >
                    <option value="1" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">Lunes</option>
                    <option value="2" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">Martes</option>
                    <option value="3" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">Miércoles</option>
                    <option value="4" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">Jueves</option>
                    <option value="5" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">Viernes</option>
                    <option value="6" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">Sábado</option>
                    <option value="0" :class="isDark() ? 'bg-slate-900 text-slate-100' : 'bg-white text-slate-800'">Domingo</option>
                  </select>
                  <div class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                    <svg class="w-4 h-4" :class="isDark() ? 'text-slate-400' : 'text-slate-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              <!-- Day of Month (for monthly) -->
              <div v-if="formData.frequency === 'monthly'">
                <label
                  for="day-of-month"
                  class="block text-xs font-semibold mb-1.5 tracking-wide"
                  :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
                  >Día del Mes</label
                >
                <input
                  id="day-of-month"
                  v-model.number="formData.dayOfMonth"
                  type="number"
                  min="1"
                  max="31"
                  required
                  class="w-full px-3 py-2.5 rounded-lg font-medium focus:outline-none focus:ring-2 shadow-sm transition-all duration-200 text-sm"
                  :class="isDark() ? 'bg-slate-950/50 border border-slate-700/50 text-slate-100 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-600' : 'bg-white border border-slate-300 text-slate-800 focus:border-cyan-500/70 focus:ring-cyan-500/20 hover:border-slate-400'"
                />
              </div>
            </div>

            <!-- Target Configuration -->
            <div class="border-t pt-3" :class="isDark() ? 'border-slate-700' : 'border-slate-300'">
              <h4 class="text-xs font-semibold mb-2" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
                Objetivos
              </h4>

              <!-- Tabs -->
              <div class="flex gap-1.5 mb-2">
                <button
                  type="button"
                  @click="targetType = 'subnet'"
                  :class="[
                    'flex-1 px-2 py-1.5 rounded-md text-xs font-semibold transition-all duration-200',
                    targetType === 'subnet'
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                      : isDark() ? 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:bg-slate-800' : 'bg-slate-100 text-slate-600 border border-slate-300 hover:bg-slate-200',
                  ]"
                >
                  Subred
                </button>
                <button
                  type="button"
                  @click="targetType = 'range'"
                  :class="[
                    'flex-1 px-2 py-1.5 rounded-md text-xs font-semibold transition-all duration-200',
                    targetType === 'range'
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                      : isDark() ? 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:bg-slate-800' : 'bg-slate-100 text-slate-600 border border-slate-300 hover:bg-slate-200',
                  ]"
                >
                  Rango
                </button>
                <button
                  type="button"
                  @click="targetType = 'hosts'"
                  :class="[
                    'flex-1 px-2 py-1.5 rounded-md text-xs font-semibold transition-all duration-200',
                    targetType === 'hosts'
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                      : isDark() ? 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:bg-slate-800' : 'bg-slate-100 text-slate-600 border border-slate-300 hover:bg-slate-200',
                  ]"
                >
                  Hosts
                </button>
              </div>

              <!-- Target Input -->
              <div>
                <input
                  v-if="targetType === 'subnet'"
                  id="target-subnet"
                  v-model="formData.targetSubnet"
                  type="text"
                  placeholder="Ej: 192.168.0.0/24"
                  class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all"
                  :class="isDark() ? 'bg-slate-800/50 border border-slate-700 text-slate-200 focus:border-cyan-500 focus:ring-cyan-500/50' : 'bg-white border border-slate-300 text-slate-800 focus:border-cyan-500 focus:ring-cyan-500/50'"
                />
                <input
                  v-else-if="targetType === 'range'"
                  id="target-range"
                  v-model="formData.targetRange"
                  type="text"
                  placeholder="Ej: 192.168.0.1-192.168.0.254"
                  class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all"
                  :class="isDark() ? 'bg-slate-800/50 border border-slate-700 text-slate-200 focus:border-cyan-500 focus:ring-cyan-500/50' : 'bg-white border border-slate-300 text-slate-800 focus:border-cyan-500 focus:ring-cyan-500/50'"
                />
                <input
                  v-else-if="targetType === 'hosts'"
                  id="target-hosts"
                  v-model="formData.targetHosts"
                  type="text"
                  placeholder="Ej: 192.168.0.10, 192.168.0.20"
                  class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all"
                  :class="isDark() ? 'bg-slate-800/50 border border-slate-700 text-slate-200 focus:border-cyan-500 focus:ring-cyan-500/50' : 'bg-white border border-slate-300 text-slate-800 focus:border-cyan-500 focus:ring-cyan-500/50'"
                />
              </div>
            </div>

            <!-- Auto Shutdown Configuration -->
            <div
              v-if="
                formData.actionType === 'shutdown' ||
                formData.actionType === 'both'
              "
              class="border-t pt-3"
              :class="isDark() ? 'border-slate-700' : 'border-slate-300'"
            >
              <h4 class="text-xs font-bold mb-2 flex items-center gap-2" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
                <Power class="w-3.5 h-3.5 text-red-400" />
                Configuración de Apagado
              </h4>

              <div class="space-y-2">
                
                <!-- Shutdown After Scan (only for 'both' mode) -->
                <div
                  v-if="formData.actionType === 'both'"
                  class="flex items-center gap-2 rounded-lg p-2"
                  :class="isDark() ? 'bg-yellow-500/10 border border-yellow-500/30' : 'bg-yellow-50 border border-yellow-300'"
                >
                  <label
                    for="shutdown-after-scan"
                    class="text-xs font-semibold"
                    :class="isDark() ? 'text-yellow-300' : 'text-yellow-700'"
                    >Apagar después del escaneo</label>
                  <input
                    id="shutdown-after-scan"
                    v-model="formData.shutdownAfterScan"
                    type="checkbox"
                    class="w-3.5 h-3.5 rounded text-red-500 focus:ring-red-500"
                    :class="isDark() ? 'border-slate-700 focus:ring-offset-slate-900' : 'border-slate-300'"
                  />
                  
                </div>

                <!-- SSH Credentials -->
                <div class="rounded-lg p-2.5 space-y-2" :class="isDark() ? 'bg-slate-800/30 border border-slate-700/50' : 'bg-slate-50 border border-slate-200'">
                  <p class="text-xs font-semibold mb-1.5" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">Credenciales SSH</p>
                  
                  <div>
                    <label
                      for="ssh-username"
                      class="block text-xs mb-1"
                      :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
                      >Usuario</label
                    >
                    <input
                      id="ssh-username"
                      v-model="formData.sshUsername"
                      type="text"
                      placeholder="usuario"
                      required
                      class="w-full px-2.5 py-1.5 rounded-md text-sm focus:outline-none focus:ring-1"
                      :class="isDark() ? 'bg-slate-950/50 border border-slate-700 text-slate-200 focus:border-red-500 focus:ring-red-500/50' : 'bg-white border border-slate-300 text-slate-800 focus:border-red-500 focus:ring-red-500/50'"
                    />
                  </div>

                  <div class="grid grid-cols-2 gap-2">
                    <div>
                      <label
                        for="ssh-password"
                        class="block text-xs mb-1"
                        :class="isDark() ? 'text-slate-400' : 'text-slate-600'"
                        >Contraseña</label
                      >
                      <input
                        id="ssh-password"
                        v-model="formData.sshPassword"
                        type="password"
                        placeholder="••••••••"
                        required
                        class="w-full px-2.5 py-1.5 rounded-md text-sm focus:outline-none focus:ring-1"
                        :class="isDark() ? 'bg-slate-950/50 border border-slate-700 text-slate-200 focus:border-red-500 focus:ring-red-500/50' : 'bg-white border border-slate-300 text-slate-800 focus:border-red-500 focus:ring-red-500/50'"
                      />
                    </div>
                    
                    <div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Enabled -->
            <div class="flex items-center gap-2 border-t pt-3" :class="isDark() ? 'border-slate-700' : 'border-slate-300'">
              <input
                id="schedule-enabled"
                v-model="formData.enabled"
                type="checkbox"
                class="w-4 h-4 rounded text-cyan-500 focus:ring-2 focus:ring-cyan-500/50"
                :class="isDark() ? 'border-slate-700' : 'border-slate-300'"
              />
              <label
                for="schedule-enabled"
                class="text-xs font-semibold"
                :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
                >Activar inmediatamente</label
              >
            </div>

            <!-- Actions -->
            <div class="flex gap-2 pt-3">
              <button
                type="submit"
                class="flex-1 px-4 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all duration-300 text-sm"
              >
                {{ editingSchedule ? "Actualizar" : "Crear" }}
              </button>
              <button
                type="button"
                @click="closeModal"
                class="px-4 py-2.5 rounded-lg font-semibold transition-all duration-300 text-sm"
                :class="isDark() ? 'bg-slate-800 text-slate-300 hover:bg-slate-700' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'"
              >
                Cancelar
              </button>
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
          class="bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 rounded-2xl border border-slate-700/50 p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-2xl"
        >
          <div class="flex items-center justify-between mb-6">
            <h3
              id="results-modal-title"
              class="text-2xl font-bold text-slate-200"
            >
              Resultados de Escaneo
            </h3>
            <button
              @click="closeResultsModal"
              class="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              aria-label="Cerrar modal"
            >
              <X class="w-6 h-6 text-slate-400" />
            </button>
          </div>

          <!-- Loading -->
          <div v-if="loadingResults" class="text-center py-12">
            <div
              class="w-8 h-8 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            ></div>
            <p class="text-slate-400">Cargando resultados...</p>
          </div>

          <!-- No Results -->
          <div
            v-else-if="!currentResults || !currentResults.has_results"
            class="text-center py-12"
          >
            <Database class="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p class="text-slate-400 text-lg">No hay resultados disponibles</p>
            <p class="text-slate-500 text-sm mt-2">
              Ejecuta el escaneo para ver los resultados
            </p>
          </div>

          <!-- Results Content -->
          <div v-else class="space-y-4">
            <!-- Metadata -->
            <div
              class="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50"
            >
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p class="text-slate-400">Tipo de Escaneo</p>
                  <p class="text-slate-200 font-semibold">
                    {{ getScanTypeName(currentResults.results.scan_type) }}
                  </p>
                </div>
                <div>
                  <p class="text-slate-400">Estado</p>
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
                  <p class="text-slate-400">Targets Escaneados</p>
                  <p class="text-slate-200 font-semibold">
                    {{ currentResults.results.targets_count }}
                  </p>
                </div>
                <div>
                  <p class="text-slate-400">Fecha</p>
                  <p class="text-slate-200 font-semibold">
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
                currentResults.results.shutdown_results.length > 0
              "
              class="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50"
            >
              <h4 class="text-lg font-bold text-slate-200 mb-4">
                Resultados de Apagado
              </h4>
              <div class="space-y-2">
                <div
                  v-for="(result, index) in currentResults.results
                    .shutdown_results"
                  :key="index"
                  class="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg"
                >
                  <span class="text-slate-300">{{ result.host }}</span>
                  <span
                    class="px-2 py-1 text-xs font-semibold rounded-full"
                    :class="
                      result.status === 'success'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    "
                  >
                    {{ result.status === "success" ? "Apagado" : "Error" }}
                  </span>
                </div>
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
          class="bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 p-6 max-w-md w-full transform transition-all"
        >
          <div class="flex items-start gap-4 mb-6">
            <div
              :class="[
                'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0',
                confirmModalData.type === 'danger'
                  ? 'bg-red-500/20'
                  : 'bg-yellow-500/20',
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
              <h3 class="text-xl font-bold text-white mb-2">
                {{ confirmModalData.title }}
              </h3>
              <p
                class="text-gray-300 text-sm whitespace-pre-line leading-relaxed"
              >
                {{ confirmModalData.message }}
              </p>
            </div>
          </div>

          <div class="flex gap-3">
            <button
              @click="showConfirmModal = false"
              class="flex-1 px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-semibold transition-colors duration-200"
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
          class="bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 p-6 max-w-md w-full transform transition-all"
        >
          <div class="flex items-start gap-4 mb-6">
            <div
              :class="[
                'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0',
                resultModalData.type === 'success'
                  ? 'bg-emerald-500/20'
                  : resultModalData.type === 'error'
                    ? 'bg-red-500/20'
                    : 'bg-yellow-500/20',
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
              <h3 class="text-xl font-bold text-white mb-2">
                {{ resultModalData.title }}
              </h3>
              <p
                class="text-gray-300 text-sm whitespace-pre-line leading-relaxed"
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
import { ref, onMounted, onBeforeUnmount } from "vue";
import {
  Calendar,
  Plus,
  Clock,
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
} from "lucide-vue-next";
import { useToast } from "../composables/useToast";
import { scannerAPI } from "../api/scanner";
import { useGlobalWebSocket } from "../composables/useWebSocket";
import { useTheme } from "../composables/useTheme";

const toast = useToast();
const ws = useGlobalWebSocket();
const { isDark } = useTheme();

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

// Obtener hora local actual en formato HH:MM
const getCurrentTime = () => {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
};

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
    mac: "MAC Address",
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
          title: "✕ Error",
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

// Cargar schedules al montar el componente
onMounted(() => {
  loadSchedules(true); // Mostrar toast en la carga inicial

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
