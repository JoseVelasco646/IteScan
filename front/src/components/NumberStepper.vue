<template>
  <div class="number-stepper-wrapper">
    <!-- Label -->
    <div v-if="label" class="flex items-center gap-2 mb-2.5">
      <slot name="icon" />
      <label class="text-sm font-semibold"
        :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
        {{ label }}
      </label>
    </div>

    <div class="flex items-center gap-3 flex-wrap">
      <!-- Stepper control -->
      <div class="inline-flex items-stretch rounded-xl overflow-hidden border transition-all"
        :class="[
          isDark()
            ? 'bg-slate-900/60 border-slate-600 hover:border-slate-500'
            : 'bg-white border-slate-300 hover:border-slate-400'
        ]"
        :style="focused ? `box-shadow: 0 0 0 3px ${accentRgba}; border-color: ${accentHex}` : ''">

        <!-- Minus button -->
        <button
          @mousedown="startDecrement" @mouseup="stopRepeat" @mouseleave="stopRepeat"
          @touchstart.prevent="startDecrement" @touchend="stopRepeat"
          :disabled="modelValue <= min"
          class="stepper-btn flex items-center justify-center w-11 transition-all duration-150 select-none"
          :class="[
            modelValue <= min
              ? (isDark() ? 'text-slate-600 cursor-not-allowed' : 'text-slate-300 cursor-not-allowed')
              : (isDark() ? 'text-slate-300' : 'text-slate-500'),
            isDark() ? 'border-r border-slate-700' : 'border-r border-slate-200'
          ]"
          :style="modelValue > min ? `--stepper-hover: ${accentRgba}; --stepper-text: ${accentHex}` : ''">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
            <path stroke-linecap="round" d="M5 12h14" />
          </svg>
        </button>

        <!-- Value display -->
        <div class="relative flex items-center">
          <input
            :value="modelValue"
            @input="onInput"
            @focus="focused = true"
            @blur="focused = false"
            type="number"
            :min="min"
            :max="max"
            :step="step"
            class="w-20 text-center py-2.5 font-mono text-lg font-semibold bg-transparent focus:outline-none appearance-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none [-moz-appearance:textfield]"
            :class="isDark() ? 'text-white' : 'text-slate-800'"
          />
          <span v-if="unit"
            class="absolute right-1.5 text-[10px] font-medium pointer-events-none"
            :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
            {{ unit }}
          </span>
        </div>

        <!-- Plus button -->
        <button
          @mousedown="startIncrement" @mouseup="stopRepeat" @mouseleave="stopRepeat"
          @touchstart.prevent="startIncrement" @touchend="stopRepeat"
          :disabled="modelValue >= max"
          class="stepper-btn flex items-center justify-center w-11 transition-all duration-150 select-none"
          :class="[
            modelValue >= max
              ? (isDark() ? 'text-slate-600 cursor-not-allowed' : 'text-slate-300 cursor-not-allowed')
              : (isDark() ? 'text-slate-300' : 'text-slate-500'),
            isDark() ? 'border-l border-slate-700' : 'border-l border-slate-200'
          ]"
          :style="modelValue < max ? `--stepper-hover: ${accentRgba}; --stepper-text: ${accentHex}` : ''">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
            <path stroke-linecap="round" d="M12 5v14M5 12h14" />
          </svg>
        </button>
      </div>

      <!-- Presets -->
      <div v-if="presets.length" class="flex gap-1.5 flex-wrap">
        <button v-for="val in presets" :key="val"
          @click="$emit('update:modelValue', val)"
          class="px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 border"
          :class="modelValue === val
            ? 'text-white shadow-sm'
            : isDark()
              ? 'bg-slate-800/60 text-slate-400 border-slate-700 hover:bg-slate-700/60 hover:text-slate-200 hover:border-slate-600'
              : 'bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100 hover:text-slate-700 hover:border-slate-300'"
          :style="modelValue === val ? `background-color: ${accentHex}; border-color: ${accentHex}; box-shadow: 0 2px 8px ${accentRgba}` : ''">
          {{ val }}
        </button>
      </div>

      <!-- Hint text -->
      <span v-if="hint" class="text-xs"
        :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
        {{ hint }}
      </span>
    </div>

    <!-- Range bar -->
    <div v-if="showRange" class="mt-2.5 px-1">
      <div class="relative h-1.5 rounded-full overflow-hidden"
        :class="isDark() ? 'bg-slate-800' : 'bg-slate-200'">
        <div class="absolute inset-y-0 left-0 rounded-full transition-all duration-300"
          :style="`width: ${rangePercent}%; background-color: ${accentHex}`"></div>
      </div>
      <div class="flex justify-between mt-1">
        <span class="text-[10px]" :class="isDark() ? 'text-slate-600' : 'text-slate-400'">{{ min }}</span>
        <span class="text-[10px]" :class="isDark() ? 'text-slate-600' : 'text-slate-400'">{{ max }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTheme } from '../composables/useTheme'

const { isDark } = useTheme()

const props = defineProps({
  modelValue: { type: Number, required: true },
  min: { type: Number, default: 1 },
  max: { type: Number, default: 999 },
  step: { type: Number, default: 1 },
  label: { type: String, default: '' },
  unit: { type: String, default: '' },
  hint: { type: String, default: '' },
  presets: { type: Array, default: () => [] },
  accentColor: { type: String, default: 'cyan' },
  showRange: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])
const focused = ref(false)

// Color mapping for inline styles (Tailwind can't do dynamic classes at build time)
const colorMap = {
  cyan: { hex: '#06b6d4', rgba: 'rgba(6,182,212,0.25)' },
  teal: { hex: '#14b8a6', rgba: 'rgba(20,184,166,0.25)' },
  purple: { hex: '#a855f7', rgba: 'rgba(168,85,247,0.25)' },
  indigo: { hex: '#6366f1', rgba: 'rgba(99,102,241,0.25)' },
  amber: { hex: '#f59e0b', rgba: 'rgba(245,158,11,0.25)' },
  emerald: { hex: '#10b981', rgba: 'rgba(16,185,129,0.25)' },
  blue: { hex: '#3b82f6', rgba: 'rgba(59,130,246,0.25)' },
  rose: { hex: '#f43f5e', rgba: 'rgba(244,63,94,0.25)' }
}

const accentHex = computed(() => colorMap[props.accentColor]?.hex || colorMap.cyan.hex)
const accentRgba = computed(() => colorMap[props.accentColor]?.rgba || colorMap.cyan.rgba)
const rangePercent = computed(() => ((props.modelValue - props.min) / (props.max - props.min)) * 100)

const clamp = (v) => Math.max(props.min, Math.min(props.max, v))

const onInput = (e) => {
  const v = parseFloat(e.target.value)
  if (!isNaN(v)) emit('update:modelValue', clamp(v))
}

const increment = () => {
  if (props.modelValue < props.max) emit('update:modelValue', clamp(props.modelValue + props.step))
}
const decrement = () => {
  if (props.modelValue > props.min) emit('update:modelValue', clamp(props.modelValue - props.step))
}

// Hold-to-repeat
let repeatTimer = null
let repeatInterval = null

const startIncrement = () => {
  increment()
  repeatTimer = setTimeout(() => {
    repeatInterval = setInterval(increment, 80)
  }, 400)
}
const startDecrement = () => {
  decrement()
  repeatTimer = setTimeout(() => {
    repeatInterval = setInterval(decrement, 80)
  }, 400)
}
const stopRepeat = () => {
  clearTimeout(repeatTimer)
  clearInterval(repeatInterval)
  repeatTimer = null
  repeatInterval = null
}
</script>

<style scoped>
/* Remove native number input spinners */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type="number"] {
  -moz-appearance: textfield;
}

/* Stepper button hover/active via CSS vars */
.stepper-btn:not(:disabled):hover {
  background-color: var(--stepper-hover, rgba(100,116,139,0.2));
  color: var(--stepper-text, inherit);
}
.stepper-btn:not(:disabled):active {
  background-color: var(--stepper-hover, rgba(100,116,139,0.3));
  color: var(--stepper-text, inherit);
  filter: brightness(0.9);
}
</style>
