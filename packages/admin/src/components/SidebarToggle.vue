<template>
  <button
    @click="handleToggle"
    class="btn btn-square btn-ghost tooltip tooltip-bottom"
    :data-tip="tooltipText"
    :aria-label="ariaLabel"
  >
    <!-- Hamburger/Close Icon with Animation -->
    <div class="w-6 h-6 flex flex-col justify-center items-center">
      <!-- Top Line -->
      <div
        class="w-5 h-0.5 bg-current transition-all duration-300 ease-in-out"
        :class="{
          'rotate-45 translate-y-1.5': isCollapsed && !isMobile,
          'mb-1': !isCollapsed || isMobile
        }"
      ></div>

      <!-- Middle Line -->
      <div
        class="w-5 h-0.5 bg-current transition-all duration-300 ease-in-out"
        :class="{
          'opacity-0': isCollapsed && !isMobile,
          'mb-1': !isCollapsed || isMobile
        }"
      ></div>

      <!-- Bottom Line -->
      <div
        class="w-5 h-0.5 bg-current transition-all duration-300 ease-in-out"
        :class="{
          '-rotate-45 -translate-y-1.5': isCollapsed && !isMobile
        }"
      ></div>
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSidebar } from '@/composables/useSidebar'

const { isCollapsed, isMobile, toggleSidebar } = useSidebar()

// Tooltip text based on current state
const tooltipText = computed(() => {
  if (isMobile.value) {
    return 'Toggle Menu'
  }
  return isCollapsed.value ? 'Expand Sidebar' : 'Collapse Sidebar'
})

// Aria label for accessibility
const ariaLabel = computed(() => {
  if (isMobile.value) {
    return 'Toggle navigation menu'
  }
  return isCollapsed.value ? 'Expand sidebar navigation' : 'Collapse sidebar navigation'
})

// Handle toggle click
function handleToggle() {
  toggleSidebar()
}
</script>

<style scoped>
/* Smooth transitions for all elements */
.transition-all {
  transition-property: all;
}

/* Ensure proper hover states */
.btn:hover {
  transform: scale(1.05);
  transition: transform 0.2s ease;
}

/* Responsive behavior for animation */
@media (max-width: 1024px) {
  /* On mobile, show standard hamburger menu */
  .w-5 {
    width: 1.25rem;
  }
}
</style>