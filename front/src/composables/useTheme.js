import { ref, watch } from 'vue'

const THEME_KEY = 'ite-scan-theme'
const theme = ref(localStorage.getItem(THEME_KEY) || 'dark')

export function useTheme() {
  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  const setTheme = (newTheme) => {
    if (['dark', 'light'].includes(newTheme)) {
      theme.value = newTheme
    }
  }

  // Aplicar tema al DOM
  watch(
    theme,
    (newTheme) => {
      localStorage.setItem(THEME_KEY, newTheme)
      document.documentElement.classList.remove('light', 'dark')
      document.documentElement.classList.add(newTheme)
    },
    { immediate: true }
  )

  return {
    theme,
    toggleTheme,
    setTheme,
    isDark: () => theme.value === 'dark',
    isLight: () => theme.value === 'light'
  }
}
