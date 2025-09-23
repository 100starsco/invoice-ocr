import { ref, watch, onMounted, readonly } from 'vue'

export type Theme = 'light' | 'dark' | 'cupcake' | 'corporate' | 'business' | 'synthwave' | 'retro' | 'cyberpunk'

export const AVAILABLE_THEMES: Array<{ value: Theme; label: string; category: 'light' | 'dark' }> = [
  { value: 'light', label: 'Light', category: 'light' },
  { value: 'cupcake', label: 'Cupcake', category: 'light' },
  { value: 'corporate', label: 'Corporate', category: 'light' },
  { value: 'retro', label: 'Retro', category: 'light' },
  { value: 'dark', label: 'Dark', category: 'dark' },
  { value: 'business', label: 'Business', category: 'dark' },
  { value: 'synthwave', label: 'Synthwave', category: 'dark' },
  { value: 'cyberpunk', label: 'Cyberpunk', category: 'dark' }
]

const THEME_STORAGE_KEY = 'admin-theme'

// Reactive theme state
const currentTheme = ref<Theme>('light')

// Get theme from localStorage or system preference
function getInitialTheme(): Theme {
  if (typeof window === 'undefined') return 'light'

  const stored = localStorage.getItem(THEME_STORAGE_KEY) as Theme | null
  if (stored && AVAILABLE_THEMES.some(t => t.value === stored)) {
    return stored
  }

  // Detect system preference
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }

  return 'light'
}

// Apply theme to document
function applyTheme(theme: Theme) {
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', theme)
  }
}

// Save theme to localStorage
function saveTheme(theme: Theme) {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  }
}

export function useTheme() {
  // Set theme and persist
  const setTheme = (theme: Theme) => {
    currentTheme.value = theme
    applyTheme(theme)
    saveTheme(theme)
  }

  // Get current theme info
  const getCurrentThemeInfo = () => {
    return AVAILABLE_THEMES.find(t => t.value === currentTheme.value) || AVAILABLE_THEMES[0]
  }

  // Check if current theme is dark
  const isDarkTheme = () => {
    return getCurrentThemeInfo().category === 'dark'
  }

  // Toggle between light and dark themes
  const toggleTheme = () => {
    const currentInfo = getCurrentThemeInfo()
    if (currentInfo.category === 'light') {
      setTheme('dark')
    } else {
      setTheme('light')
    }
  }

  // Initialize theme on mount
  onMounted(() => {
    const initialTheme = getInitialTheme()
    currentTheme.value = initialTheme
    applyTheme(initialTheme)
  })

  // Watch for theme changes and apply them
  watch(currentTheme, (newTheme) => {
    applyTheme(newTheme)
    saveTheme(newTheme)
  })

  return {
    currentTheme: readonly(currentTheme),
    availableThemes: AVAILABLE_THEMES,
    setTheme,
    toggleTheme,
    getCurrentThemeInfo,
    isDarkTheme
  }
}