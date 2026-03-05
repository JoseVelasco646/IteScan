<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :width="size"
    :height="size"
    :viewBox="os === 'linux' ? '3 0 18 24' : '0 0 24 24'"
    fill="none"
    :stroke="color"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="os-icon"
  >
    <!-- Windows -->
    <template v-if="os === 'windows'">
      <path d="M3 5.5l7.5-1.1v7.1H3z" fill="currentColor" stroke="none" />
      <path d="M11.5 4.2L21 3v8.5h-9.5z" fill="currentColor" stroke="none" />
      <path d="M3 12.5h7.5v7.1L3 18.5z" fill="currentColor" stroke="none" />
      <path d="M11.5 12.5H21V21l-9.5-1.2z" fill="currentColor" stroke="none" />
    </template>

    <!-- Linux (Tux penguin) -->
    <template v-else-if="os === 'linux'">
      <!-- Body (black) -->
      <path d="M7.5 10.5 Q7 14 6.5 17 Q6.5 20 9 20.5 L10.5 20.5 Q11 19 12 19 Q13 19 13.5 20.5 L15 20.5 Q17.5 20 17.5 17 Q17 14 16.5 10.5 Q16 8.5 14.5 7.5 Q13.5 7 12 7 Q10.5 7 9.5 7.5 Q8 8.5 7.5 10.5 Z" fill="#333" stroke="currentColor" :stroke-width="strokeWidth * 0.8" />
      <!-- Belly (white/yellow) -->
      <ellipse cx="12" cy="14.5" rx="3" ry="4.5" fill="#f5a623" stroke="none" opacity="0.35" />
      <ellipse cx="12" cy="14.5" rx="2.8" ry="4.2" fill="#fef3c7" stroke="currentColor" :stroke-width="strokeWidth * 0.5" />
      <!-- Head -->
      <circle cx="12" cy="5.5" r="4" fill="#333" stroke="currentColor" :stroke-width="strokeWidth * 0.8" />
      <!-- Eyes (white with black pupil) -->
      <ellipse cx="10.3" cy="5" rx="1.1" ry="1.3" fill="white" stroke="none" />
      <ellipse cx="13.7" cy="5" rx="1.1" ry="1.3" fill="white" stroke="none" />
      <circle cx="10.5" cy="5.1" r="0.55" fill="#111" stroke="none" />
      <circle cx="13.5" cy="5.1" r="0.55" fill="#111" stroke="none" />
      <!-- Beak -->
      <path d="M10.5 6.8 Q12 8.2 13.5 6.8 Q12 7.8 10.5 6.8 Z" fill="#f5a623" stroke="#d97706" :stroke-width="strokeWidth * 0.4" />
      <!-- Feet -->
      <path d="M9 20.5 L7.5 22 Q9 22.2 10.5 21.5 Z" fill="#f5a623" stroke="#d97706" :stroke-width="strokeWidth * 0.4" />
      <path d="M15 20.5 L16.5 22 Q15 22.2 13.5 21.5 Z" fill="#f5a623" stroke="#d97706" :stroke-width="strokeWidth * 0.4" />
      <!-- Wings -->
      <path d="M7.5 11 Q5.5 13.5 5 16.5 Q5.5 17 6.5 16.5 Q7 14 7.8 11.5 Z" fill="#333" stroke="currentColor" :stroke-width="strokeWidth * 0.6" />
      <path d="M16.5 11 Q18.5 13.5 19 16.5 Q18.5 17 17.5 16.5 Q17 14 16.2 11.5 Z" fill="#333" stroke="currentColor" :stroke-width="strokeWidth * 0.6" />
    </template>

    <!-- Apple / macOS -->
    <template v-else-if="os === 'apple'">
      <path d="M12.5 3.5 Q14 2 15 3.5" stroke="currentColor" :stroke-width="strokeWidth * 0.8" fill="none" />
      <path d="M16 7.5 Q19 7.5 19 11 Q19 15 16 18 Q14.5 20 13 20 Q12 20 11 19.5 Q10 20 9 20 Q7 20 5.5 17 Q4 14 5 11 Q5.5 7.5 8.5 7.5 Q10 7.5 11 8 Q12 7.5 13 7.5 Q14.5 7.5 16 7.5 Z" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
    </template>

    <!-- Android -->
    <template v-else-if="os === 'android'">
      <path d="M6 11v5a1 1 0 001 1h1v3a1 1 0 002 0v-3h4v3a1 1 0 002 0v-3h1a1 1 0 001-1v-5z" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M6 11a6 6 0 0112 0" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="9.5" cy="8" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="14.5" cy="8" r="0.8" fill="currentColor" stroke="none" />
      <path d="M8 3l1.5 2.5" stroke="currentColor" :stroke-width="strokeWidth * 0.8" fill="none" />
      <path d="M16 3l-1.5 2.5" stroke="currentColor" :stroke-width="strokeWidth * 0.8" fill="none" />
      <path d="M4 12v4a1 1 0 002 0v-4a1 1 0 00-2 0z" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M18 12v4a1 1 0 002 0v-4a1 1 0 00-2 0z" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
    </template>

    <!-- FreeBSD / BSD (daemon) -->
    <template v-else-if="os === 'bsd'">
      <circle cx="12" cy="10" r="7" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M7 6 L5 3" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M17 6 L19 3" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="9.5" cy="9" r="1" fill="currentColor" stroke="none" />
      <circle cx="14.5" cy="9" r="1" fill="currentColor" stroke="none" />
      <path d="M9 13 q3 3 6 0" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M8 17 L7 21" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M16 17 L17 21" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M11 17 v4" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M13 17 v4" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
    </template>

    <!-- Cisco / Router / Network -->
    <template v-else-if="os === 'network'">
      <circle cx="12" cy="6" r="3" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="5" cy="18" r="2.5" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <circle cx="19" cy="18" r="2.5" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M12 9v3" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M12 12 L5 15.5" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M12 12 L19 15.5" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
    </template>

    <!-- Default: Monitor -->
    <template v-else>
      <rect x="3" y="3" width="18" height="12" rx="2" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M8 21h8" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
      <path d="M12 15v6" stroke="currentColor" :stroke-width="strokeWidth" fill="none" />
    </template>
  </svg>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  name: { type: String, default: '' },
  size: { type: [Number, String], default: 16 },
  strokeWidth: { type: Number, default: 1.5 },
});

const color = computed(() => {
  switch (os.value) {
    case 'windows': return '#0078d4';
    case 'linux': return '#f5a623';
    case 'apple': return '#a3aaae';
    case 'android': return '#3ddc84';
    case 'bsd': return '#ab2b28';
    case 'network': return '#1ba0d7';
    default: return 'currentColor';
  }
});

const os = computed(() => {
  if (!props.name) return 'unknown';
  const l = props.name.toLowerCase();
  if (l.includes('windows')) return 'windows';
  if (l.includes('linux') || l.includes('ubuntu') || l.includes('debian') || l.includes('centos') || l.includes('fedora') || l.includes('red hat') || l.includes('suse') || l.includes('arch') || l.includes('mint')) return 'linux';
  if (l.includes('mac') || l.includes('apple') || l.includes('ios') || l.includes('darwin')) return 'apple';
  if (l.includes('android')) return 'android';
  if (l.includes('freebsd') || l.includes('openbsd') || l.includes('netbsd') || l.includes('bsd')) return 'bsd';
  if (l.includes('cisco') || l.includes('router') || l.includes('juniper') || l.includes('mikrotik') || l.includes('switch')) return 'network';
  return 'unknown';
});
</script>
