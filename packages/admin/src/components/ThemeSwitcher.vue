<template>
  <div class="dropdown dropdown-end">
    <!-- Theme Switcher Button -->
    <div tabindex="0" role="button" class="btn btn-ghost btn-circle tooltip tooltip-bottom" data-tip="Change Theme">
      <!-- Theme Icon -->
      <svg v-if="isDarkTheme()" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <!-- Moon Icon -->
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>
      </svg>
      <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <!-- Sun Icon -->
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>
      </svg>
    </div>

    <!-- Theme Options Dropdown -->
    <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow-lg border border-base-300">
      <!-- Light Themes Section -->
      <li class="menu-title">
        <span class="text-base-content/60">Light Themes</span>
      </li>
      <li v-for="theme in lightThemes" :key="theme.value">
        <input
          type="radio"
          name="theme-dropdown"
          class="theme-controller btn btn-sm btn-block btn-ghost justify-start"
          :aria-label="theme.label"
          :value="theme.value"
          :checked="currentTheme === theme.value"
          @change="setTheme(theme.value)"
        />
      </li>

      <!-- Divider -->
      <li><div class="divider my-1"></div></li>

      <!-- Dark Themes Section -->
      <li class="menu-title">
        <span class="text-base-content/60">Dark Themes</span>
      </li>
      <li v-for="theme in darkThemes" :key="theme.value">
        <input
          type="radio"
          name="theme-dropdown"
          class="theme-controller btn btn-sm btn-block btn-ghost justify-start"
          :aria-label="theme.label"
          :value="theme.value"
          :checked="currentTheme === theme.value"
          @change="setTheme(theme.value)"
        />
      </li>

    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { currentTheme, availableThemes, setTheme, isDarkTheme } = useTheme()

// Organize themes by category
const lightThemes = computed(() => availableThemes.filter(t => t.category === 'light'))
const darkThemes = computed(() => availableThemes.filter(t => t.category === 'dark'))
</script>

<style scoped>
/* Ensure dropdown appears above other elements */
.dropdown-content {
  z-index: 1000;
}
</style>