import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export type ThemePreference = 'system' | 'light' | 'dark'

const STORAGE_KEY = 'cr_theme'
const media = window.matchMedia('(prefers-color-scheme: dark)')

function readPreference(): ThemePreference {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved === 'light' || saved === 'dark' || saved === 'system'
      ? saved
      : 'system'
  } catch {
    return 'system'
  }
}

export const useThemeStore = defineStore('theme', () => {
  const preference = ref<ThemePreference>(readPreference())
  const systemDark = ref(media.matches)
  const resolved = computed<'light' | 'dark'>(() => {
    if (preference.value === 'system') return systemDark.value ? 'dark' : 'light'
    return preference.value
  })

  let initialized = false
  let transitionTimer: ReturnType<typeof setTimeout> | undefined

  function apply(animate: boolean) {
    const root = document.documentElement
    if (animate) {
      root.classList.add('theme-transition')
      if (transitionTimer) clearTimeout(transitionTimer)
    }
    root.dataset.theme = resolved.value
    root.dataset.themePreference = preference.value
    try {
      localStorage.setItem(STORAGE_KEY, preference.value)
    } catch {
      // 浏览器禁用存储时仍允许当前页面切换主题。
    }
    if (animate) {
      void root.offsetHeight
      transitionTimer = setTimeout(() => {
        root.classList.remove('theme-transition')
      }, 420)
    }
  }

  function setPreference(value: ThemePreference) {
    if (preference.value === value) return
    preference.value = value
    apply(true)
  }

  function init() {
    if (initialized) return
    initialized = true
    apply(false)
    media.addEventListener('change', (event) => {
      systemDark.value = event.matches
      if (preference.value === 'system') apply(true)
    })
  }

  return { preference, resolved, init, setPreference }
})
