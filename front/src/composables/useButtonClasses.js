import { computed } from 'vue'
import { useTheme } from './useTheme'

/**
 * Shared button class helpers — consistent design system across all components.
 * Cyber/outlined CTAs: transparent fill, neon border + glow, fast transitions.
 */
export function useButtonClasses() {
  const { isDark } = useTheme()

  /** Primary CTA for short forms (e.g. "Nuevo Schedule", "Aplicar filtros") */
  const btnPrimaryClass = computed(() =>
    [
      'group isolate relative inline-flex items-center gap-2 px-4 py-2 rounded-md bg-transparent',
      'text-cyan-400 hover:text-cyan-300 font-bold tracking-widest uppercase text-xs',
      'border border-cyan-500/50 hover:border-cyan-500',
      'transition-all duration-300 ease-in-out',
      'shadow-[0_0_20px_rgba(34,211,238,0.25)] hover:shadow-[0_0_15px_rgba(34,211,238,0.28)]',
      'active:translate-y-1 active:shadow-[0_0_15px_rgba(34,211,238,0.45)] active:scale-[0.98]',
      "before:content-[''] before:absolute before:inset-0 before:-z-10 before:bg-gradient-to-r before:from-cyan-600/25 before:to-blue-600/25 before:opacity-0 hover:before:opacity-50 before:transition-opacity before:duration-300 before:blur-xl before:rounded-md",
      "after:content-[''] after:absolute after:-inset-1 after:-z-10 after:bg-gradient-to-r after:from-cyan-600 after:to-blue-600 after:opacity-20 hover:after:opacity-15 after:blur-xl hover:after:blur-xl after:rounded-md after:transition-all after:duration-300",
      'disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:active:translate-y-0 disabled:active:scale-100',
    ].join(' ')
  )

  /** Secondary/ghost button (e.g. "Cancelar", "Exportar", "Actualizar") */
  const btnSecondaryClass = computed(() =>
    isDark()
      ? [
          'group relative inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-transparent',
          'text-slate-300 hover:text-cyan-300 font-bold tracking-widest uppercase text-[11px]',
          'border border-slate-600/70 hover:border-cyan-500/40',
          'transition-all duration-300 ease-in-out',
          'hover:shadow-[0_0_16px_rgba(34,211,238,0.14)]',
          'active:translate-y-0.5 active:scale-[0.99]',
          'disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none',
        ].join(' ')
      : [
          'group relative inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-transparent',
          'text-slate-700 hover:text-cyan-600 font-bold tracking-widest uppercase text-[11px]',
          'border border-slate-300 hover:border-cyan-500/40',
          'transition-all duration-300 ease-in-out',
          'hover:shadow-[0_0_16px_rgba(34,211,238,0.10)]',
          'active:translate-y-0.5 active:scale-[0.99]',
          'disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none',
        ].join(' ')
  )

  /** Base class for small icon-only action buttons */
  const btnIconBaseClass = computed(() =>
    isDark()
      ? 'p-2 rounded-lg border transition-all duration-200 active:scale-95 border-slate-600/70 bg-slate-800/80'
      : 'p-2 rounded-lg border transition-all duration-200 active:scale-95 border-slate-300 bg-white'
  )

  /** Full-width main action CTA (emerald — "Iniciar Escaneo", "Iniciar Ping"…) */
  const btnCTAClass = computed(() =>
    [
      'group isolate relative w-full px-10 py-5 rounded-md bg-transparent',
      'text-cyan-400 hover:text-cyan-300 font-bold tracking-widest uppercase text-sm',
      'border border-cyan-500/50 hover:border-cyan-500',
      'transition-all duration-300 ease-in-out',
      'shadow-[0_0_20px_rgba(34,211,238,0.25)] hover:shadow-[0_0_28px_rgba(34,211,238,0.32)]',
      'active:translate-y-1 active:shadow-[0_0_15px_rgba(34,211,238,0.45)] active:scale-[0.98]',
      'flex items-center justify-center gap-3',
      "before:content-[''] before:absolute before:inset-0 before:-z-10 before:bg-gradient-to-r before:from-cyan-600/25 before:to-blue-600/25 before:opacity-0 hover:before:opacity-80 before:transition-opacity before:duration-300 before:blur-xl before:rounded-md",
      "after:content-[''] after:absolute after:-inset-1 after:-z-10 after:bg-gradient-to-r after:from-cyan-600 after:to-blue-600 after:opacity-20 hover:after:opacity-25 after:blur-xl hover:after:blur-xl after:rounded-md after:transition-all after:duration-300",
      'disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:active:translate-y-0 disabled:active:scale-100',
    ].join(' ')
  )

  /** Small danger/outlined button (red) for toolbars and forms (e.g. "Apagar", "Eliminar") */
  const btnDangerClass = computed(() =>
    [
      'group isolate relative inline-flex items-center gap-2 px-4 py-2 rounded-md bg-transparent',
      'text-red-400 hover:text-red-300 font-bold tracking-widest uppercase text-xs',
      'border border-red-500/50 hover:border-red-500',
      'transition-all duration-300 ease-in-out',
      'shadow-[0_0_20px_rgba(248,113,113,0.25)] hover:shadow-[0_0_28px_rgba(248,113,113,0.32)]',
      'active:translate-y-1 active:shadow-[0_0_15px_rgba(248,113,113,0.45)] active:scale-[0.98]',
      "before:content-[''] before:absolute before:inset-0 before:-z-10 before:bg-gradient-to-r before:from-red-600/25 before:to-rose-600/25 before:opacity-0 hover:before:opacity-80 before:transition-opacity before:duration-300 before:blur-xl before:rounded-md",
      "after:content-[''] after:absolute after:-inset-1 after:-z-10 after:bg-gradient-to-r after:from-red-600 after:to-rose-600 after:opacity-20 hover:after:opacity-25 after:blur-xl hover:after:blur-xl after:rounded-md after:transition-all after:duration-300",
      'disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:active:translate-y-0 disabled:active:scale-100',
    ].join(' ')
  )

  /** Full-width cancel/danger CTA (red — "Cancelar Escaneo") */
  const btnDangerCTAClass = computed(() =>
    [
      'group isolate relative w-full px-10 py-5 rounded-md bg-transparent',
      'text-red-400 hover:text-red-300 font-bold tracking-widest uppercase text-sm',
      'border border-red-500/50 hover:border-red-500',
      'transition-all duration-300 ease-in-out',
      'shadow-[0_0_20px_rgba(248,113,113,0.25)] hover:shadow-[0_0_28px_rgba(248,113,113,0.32)]',
      'active:translate-y-1 active:shadow-[0_0_15px_rgba(248,113,113,0.45)] active:scale-[0.98]',
      'flex items-center justify-center gap-3',
      "before:content-[''] before:absolute before:inset-0 before:-z-10 before:bg-gradient-to-r before:from-red-600/25 before:to-rose-600/25 before:opacity-0 hover:before:opacity-80 before:transition-opacity before:duration-300 before:blur-xl before:rounded-md",
      "after:content-[''] after:absolute after:-inset-1 after:-z-10 after:bg-gradient-to-r after:from-red-600 after:to-rose-600 after:opacity-20 hover:after:opacity-25 after:blur-xl hover:after:blur-xl after:rounded-md after:transition-all after:duration-300",
      'disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:active:translate-y-0 disabled:active:scale-100',
    ].join(' ')
  )

  /**
   * Tone class for icon-only buttons (combine with btnIconBaseClass).
   * @param {'cyan'|'purple'|'green'|'blue'|'red'|'amber'|'slate'} tone
   * @param {boolean} disabled
   */
  const getIconToneClass = (tone = 'slate', disabled = false) => {
    if (disabled) {
      return isDark()
        ? 'text-slate-500 border-slate-700/60 bg-slate-800/40 cursor-not-allowed'
        : 'text-slate-400 border-slate-200 bg-slate-100 cursor-not-allowed'
    }

    const tonesDark = {
      cyan:   'text-cyan-300   hover:text-cyan-200   hover:border-cyan-400/50   hover:bg-cyan-500/15',
      purple: 'text-purple-300 hover:text-purple-200 hover:border-purple-400/50 hover:bg-purple-500/15',
      green:  'text-emerald-300 hover:text-emerald-200 hover:border-emerald-400/50 hover:bg-emerald-500/15',
      blue:   'text-blue-300   hover:text-blue-200   hover:border-blue-400/50   hover:bg-blue-500/15',
      red:    'text-red-300    hover:text-red-200    hover:border-red-400/50    hover:bg-red-500/15',
      amber:  'text-amber-300  hover:text-amber-200  hover:border-amber-400/50  hover:bg-amber-500/15',
      slate:  'text-slate-300  hover:text-white      hover:border-slate-500     hover:bg-slate-700/80',
    }

    const tonesLight = {
      cyan:   'text-cyan-700   hover:text-cyan-800   hover:border-cyan-400   hover:bg-cyan-50',
      purple: 'text-purple-700 hover:text-purple-800 hover:border-purple-400 hover:bg-purple-50',
      green:  'text-emerald-700 hover:text-emerald-800 hover:border-emerald-400 hover:bg-emerald-50',
      blue:   'text-blue-700   hover:text-blue-800   hover:border-blue-400   hover:bg-blue-50',
      red:    'text-red-700    hover:text-red-800    hover:border-red-400    hover:bg-red-50',
      amber:  'text-amber-700  hover:text-amber-800  hover:border-amber-400  hover:bg-amber-50',
      slate:  'text-slate-700  hover:text-slate-900  hover:border-slate-400  hover:bg-slate-50',
    }

    return isDark() ? (tonesDark[tone] ?? tonesDark.slate) : (tonesLight[tone] ?? tonesLight.slate)
  }

  /**
   * Pagination prev/next button class.
   * @param {boolean} disabled
   */
  const getPaginationButtonClass = (disabled) => {
    if (disabled) {
      return isDark()
        ? 'px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-700/60 bg-slate-800/40 text-slate-500 cursor-not-allowed'
        : 'px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed'
    }
    return isDark()
      ? 'px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700 transition-all duration-200'
      : 'px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 transition-all duration-200'
  }

  /**
   * Confirm modal button (danger=red, else=amber).
   * @param {'danger'|'confirm'} type
   */
  const getConfirmButtonClass = (type) => {
    if (type === 'danger') {
      return isDark()
        ? 'flex-1 px-4 py-3 rounded-xl font-semibold border border-red-500/40 bg-red-600 hover:bg-red-500 text-white transition-all duration-200'
        : 'flex-1 px-4 py-3 rounded-xl font-semibold border border-red-500/30 bg-red-600 hover:bg-red-700 text-white transition-all duration-200'
    }
    return isDark()
      ? 'flex-1 px-4 py-3 rounded-xl font-semibold border border-amber-500/40 bg-amber-600 hover:bg-amber-500 text-white transition-all duration-200'
      : 'flex-1 px-4 py-3 rounded-xl font-semibold border border-amber-500/30 bg-amber-600 hover:bg-amber-700 text-white transition-all duration-200'
  }

  /**
   * Modal footer cancel button (outlined secondary).
   */
  const btnModalCancelClass = computed(() =>
    isDark()
      ? 'flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all border bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
      : 'flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all border bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
  )

  /**
   * Modal footer primary submit button (cyan).
   */
  const btnModalSubmitClass = computed(() =>
    [
      'group isolate relative flex-1 px-4 py-2.5 rounded-md bg-transparent',
      'text-cyan-400 hover:text-cyan-300 font-bold tracking-widest uppercase text-xs',
      'border border-cyan-500/50 hover:border-cyan-500',
      'transition-all duration-300 ease-in-out',
      'shadow-[0_0_20px_rgba(34,211,238,0.25)] hover:shadow-[0_0_28px_rgba(34,211,238,0.32)]',
      'active:translate-y-1 active:shadow-[0_0_15px_rgba(34,211,238,0.45)] active:scale-[0.98]',
      "before:content-[''] before:absolute before:inset-0 before:-z-10 before:bg-gradient-to-r before:from-cyan-600/25 before:to-blue-600/25 before:opacity-0 hover:before:opacity-80 before:transition-opacity before:duration-300 before:blur-xl before:rounded-md",
      "after:content-[''] after:absolute after:-inset-1 after:-z-10 after:bg-gradient-to-r after:from-cyan-600 after:to-blue-600 after:opacity-20 hover:after:opacity-25 after:blur-xl hover:after:blur-xl after:rounded-md after:transition-all after:duration-300",
      'disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none disabled:active:translate-y-0 disabled:active:scale-100',
    ].join(' ')
  )

  return {
    btnPrimaryClass,
    btnSecondaryClass,
    btnIconBaseClass,
    btnCTAClass,
    btnDangerClass,
    btnDangerCTAClass,
    btnModalCancelClass,
    btnModalSubmitClass,
    getPaginationButtonClass,
    getConfirmButtonClass,
    getIconToneClass,
  }
}
