import { ref, watch, onMounted, readonly } from 'vue'

const SIDEBAR_STORAGE_KEY = 'admin-sidebar-collapsed'

// Global sidebar state - shared across all components
const isCollapsed = ref(false)
const isMobile = ref(false)

// Check if screen is mobile size
function checkMobileScreen() {
  if (typeof window === 'undefined') return false
  return window.innerWidth < 1024 // lg breakpoint
}

// Get initial sidebar state from localStorage
function getInitialSidebarState(): boolean {
  if (typeof window === 'undefined') return false

  const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY)
  if (stored !== null) {
    return stored === 'true'
  }

  // Default: collapsed on mobile, expanded on desktop
  return checkMobileScreen()
}

// Save sidebar state to localStorage
function saveSidebarState(collapsed: boolean) {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, collapsed.toString())
  }
}

// Handle window resize
function handleResize() {
  const mobile = checkMobileScreen()
  isMobile.value = mobile

  // On mobile, sidebar should be collapsed by default
  // But don't override user's manual preference on desktop
  if (mobile && !isCollapsed.value) {
    // Only auto-collapse if transitioning to mobile
    const wasDesktop = !isMobile.value
    if (wasDesktop) {
      isCollapsed.value = true
    }
  }
}

export function useSidebar() {
  // Toggle sidebar collapse state
  const toggleSidebar = () => {
    isCollapsed.value = !isCollapsed.value
    saveSidebarState(isCollapsed.value)
  }

  // Manually set sidebar state
  const setSidebarCollapsed = (collapsed: boolean) => {
    isCollapsed.value = collapsed
    saveSidebarState(collapsed)
  }

  // Get computed sidebar width classes
  const getSidebarWidthClass = () => {
    if (isMobile.value) {
      // On mobile, sidebar is overlay and full width when open
      return 'w-64'
    }
    // On desktop, width depends on collapsed state
    return isCollapsed.value ? 'w-16' : 'w-64'
  }

  // Check if sidebar should show text labels
  const shouldShowLabels = () => {
    if (isMobile.value) {
      // On mobile, always show labels when sidebar is open
      return true
    }
    // On desktop, show labels only when not collapsed
    return !isCollapsed.value
  }

  // Check if tooltips should be shown
  const shouldShowTooltips = () => {
    if (isMobile.value) {
      // No tooltips on mobile
      return false
    }
    // Show tooltips only when collapsed on desktop
    return isCollapsed.value
  }

  // Initialize sidebar state
  const initializeSidebar = () => {
    isMobile.value = checkMobileScreen()
    isCollapsed.value = getInitialSidebarState()

    // Add resize listener
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', handleResize)
    }
  }

  // Cleanup
  const destroySidebar = () => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('resize', handleResize)
    }
  }

  // Initialize on mount
  onMounted(() => {
    initializeSidebar()
  })

  // Watch for changes and save state
  watch(isCollapsed, (newValue) => {
    saveSidebarState(newValue)
  })

  return {
    isCollapsed: readonly(isCollapsed),
    isMobile: readonly(isMobile),
    toggleSidebar,
    setSidebarCollapsed,
    getSidebarWidthClass,
    shouldShowLabels,
    shouldShowTooltips,
    initializeSidebar,
    destroySidebar
  }
}