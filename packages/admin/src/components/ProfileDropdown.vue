<template>
  <div class="dropdown dropdown-end">
    <!-- Profile Avatar Button -->
    <div tabindex="0" role="button" class="btn btn-ghost btn-circle avatar">
      <div class="w-10 rounded-full">
        <div class="avatar placeholder">
          <div class="bg-primary text-primary-content rounded-full w-10">
            <span class="text-sm font-semibold">{{ userInitials }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Profile Dropdown Menu -->
    <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-64 p-2 shadow-lg border border-base-300">
      <!-- User Info Section -->
      <li class="menu-title px-4 py-2">
        <div class="flex items-center space-x-3">
          <div class="avatar placeholder">
            <div class="bg-primary text-primary-content rounded-full w-12">
              <span class="text-base font-semibold">{{ userInitials }}</span>
            </div>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-base-content truncate">{{ userName }}</p>
            <p class="text-xs text-base-content/60 truncate">{{ userEmail }}</p>
          </div>
          <div class="flex-shrink-0">
            <div class="w-3 h-3 bg-success rounded-full" title="Online"></div>
          </div>
        </div>
      </li>

      <!-- Divider -->
      <li><div class="divider my-1"></div></li>

      <!-- Profile Menu Items -->
      <li>
        <a href="#" class="flex items-center space-x-3 p-3 hover:bg-base-200">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
          </svg>
          <span>View Profile</span>
        </a>
      </li>

      <li>
        <a href="#" class="flex items-center space-x-3 p-3 hover:bg-base-200">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          <span>Account Settings</span>
        </a>
      </li>

      <li>
        <a href="#" class="flex items-center space-x-3 p-3 hover:bg-base-200">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span>Help & Support</span>
        </a>
      </li>

      <!-- Divider -->
      <li><div class="divider my-1"></div></li>

      <!-- Logout Option -->
      <li>
        <a @click="handleLogout" class="flex items-center space-x-3 p-3 hover:bg-error hover:text-error-content text-error">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
          </svg>
          <span>Sign Out</span>
        </a>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Generate user initials from name
const userInitials = computed(() => {
  if (!authStore.user?.name) return 'AD'

  const names = authStore.user.name.split(' ').filter(Boolean)
  if (names.length >= 2) {
    return (names[0][0] + names[names.length - 1][0]).toUpperCase()
  }
  return names[0]?.substring(0, 2).toUpperCase() || 'AD'
})

// User display information
const userName = computed(() => authStore.user?.name || 'Admin User')
const userEmail = computed(() => authStore.user?.email || 'admin@example.com')

// Handle logout action
async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
/* Ensure dropdown appears above other elements */
.dropdown-content {
  z-index: 1000;
}

/* Custom hover effects */
.menu li > a:hover {
  transition: all 0.2s ease;
}

/* Online status indicator animation */
.bg-success {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>