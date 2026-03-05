<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke="color"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="device-icon"
  >
    <!-- PC / Desktop -->
    <template v-if="type === 'pc'">
      <rect x="2" y="3" width="20" height="13" rx="2" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M8 21h8" stroke="currentColor" :stroke-width="strokeWidth" />
      <path d="M12 16v5" stroke="currentColor" :stroke-width="strokeWidth" />
      <circle cx="12" cy="14" r="0.5" fill="currentColor" stroke="none" />
    </template>

    <!-- Laptop -->
    <template v-else-if="type === 'laptop'">
      <path d="M4 6a2 2 0 012-2h12a2 2 0 012 2v8H4V6z" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M2 16h20l-1.5 3H3.5L2 16z" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
    </template>

    <!-- Phone / Mobile -->
    <template v-else-if="type === 'phone'">
      <rect x="7" y="2" width="10" height="20" rx="2" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M11 18h2" stroke="currentColor" :stroke-width="strokeWidth" />
      <path d="M10 5h4" stroke="currentColor" :stroke-width="strokeWidth * 0.8" />
    </template>

    <!-- Printer -->
    <template v-else-if="type === 'printer'">
      <path d="M6 9V2h12v7" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <rect x="3" y="9" width="18" height="8" rx="1" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M6 17v4h12v-4" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="17" cy="12" r="0.8" fill="currentColor" stroke="none" />
    </template>

    <!-- Server -->
    <template v-else-if="type === 'server'">
      <rect x="4" y="2" width="16" height="6" rx="1.5" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <rect x="4" y="10" width="16" height="6" rx="1.5" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="7" cy="5" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="7" cy="13" r="0.8" fill="currentColor" stroke="none" />
      <path d="M11 5h5" stroke="currentColor" :stroke-width="strokeWidth * 0.7" />
      <path d="M11 13h5" stroke="currentColor" :stroke-width="strokeWidth * 0.7" />
      <path d="M12 18v3" stroke="currentColor" :stroke-width="strokeWidth" />
      <path d="M8 21h8" stroke="currentColor" :stroke-width="strokeWidth" />
    </template>

    <!-- Router -->
    <template v-else-if="type === 'router'">
      <ellipse cx="12" cy="14" rx="9" ry="3.5" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M12 3v7" stroke="currentColor" :stroke-width="strokeWidth" />
      <circle cx="12" cy="3" r="2" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M6 7l3.5 4" stroke="currentColor" :stroke-width="strokeWidth * 0.8" />
      <path d="M18 7l-3.5 4" stroke="currentColor" :stroke-width="strokeWidth * 0.8" />
      <circle cx="6" cy="7" r="1" fill="currentColor" stroke="none" />
      <circle cx="18" cy="7" r="1" fill="currentColor" stroke="none" />
    </template>

    <!-- Switch -->
    <template v-else-if="type === 'switch'">
      <rect x="2" y="8" width="20" height="8" rx="2" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="6" cy="12" r="1" fill="currentColor" stroke="none" />
      <circle cx="10" cy="12" r="1" fill="currentColor" stroke="none" />
      <circle cx="14" cy="12" r="1" fill="currentColor" stroke="none" />
      <circle cx="18" cy="12" r="1" fill="currentColor" stroke="none" />
      <path d="M6 8V5" stroke="currentColor" :stroke-width="strokeWidth * 0.8" />
      <path d="M10 8V4" stroke="currentColor" :stroke-width="strokeWidth * 0.8" />
      <path d="M14 8V5" stroke="currentColor" :stroke-width="strokeWidth * 0.8" />
      <path d="M18 8V4" stroke="currentColor" :stroke-width="strokeWidth * 0.8" />
    </template>

    <!-- Tablet -->
    <template v-else-if="type === 'tablet'">
      <rect x="4" y="2" width="16" height="20" rx="2" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="12" cy="19" r="0.8" fill="currentColor" stroke="none" />
      <path d="M10 4h4" stroke="currentColor" :stroke-width="strokeWidth * 0.7" />
    </template>

    <!-- Camera / IP Camera -->
    <template v-else-if="type === 'camera'">
      <circle cx="12" cy="12" r="7" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="12" cy="12" r="3.5" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
      <path d="M12 2v3" stroke="currentColor" :stroke-width="strokeWidth" />
      <rect x="10" y="1" width="4" height="2" rx="0.5" stroke="currentColor" :stroke-width="strokeWidth * 0.7" fill="none" />
    </template>

    <!-- Unknown / Default -->
    <template v-else>
      <circle cx="12" cy="12" r="9" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M9 9a3 3 0 015.12 1.5c0 1.5-2.12 2-2.12 3.5" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="12" cy="17" r="0.5" fill="currentColor" stroke="none" />
    </template>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'pc' },
  status: { type: String, default: 'grey' },
  size: { type: [Number, String], default: 32 },
  strokeWidth: { type: Number, default: 1.5 },
})

const color = computed(() => {
  switch (props.status) {
    case 'green': return '#22c55e'
    case 'red': return '#ef4444'
    case 'grey':
    default: return '#94a3b8'
  }
})
</script>
