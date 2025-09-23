<template>
  <div class="drawer lg:drawer-open">
    <!-- Drawer Toggle -->
    <input id="drawer-toggle" type="checkbox" class="drawer-toggle" />

    <!-- Page Content -->
    <div class="drawer-content flex flex-col">
      <!-- Navbar -->
      <div class="navbar bg-base-100 shadow-lg">
        <div class="navbar-start">
          <label for="drawer-toggle" class="btn btn-square btn-ghost lg:hidden">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
          </label>
          <h1 class="text-xl font-bold text-primary ml-2">Invoice OCR Admin</h1>
        </div>
        <div class="navbar-end">
          <button @click="handleLogout" class="btn btn-ghost">
            Logout
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1 p-8 bg-base-200">
        <div class="hero bg-base-100 rounded-lg shadow-lg">
          <div class="hero-content text-center">
            <div class="max-w-md">
              <h1 class="text-5xl font-bold">Welcome!</h1>
              <p class="py-6 text-base-content/70">
                This is your admin dashboard. You can start building your features here.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sidebar -->
    <div class="drawer-side">
      <label for="drawer-toggle" class="drawer-overlay"></label>
      <aside class="min-h-full w-16 lg:w-64 bg-base-100 transition-all duration-300 shadow-lg">
        <!-- Sidebar Header -->
        <div class="p-4 border-b border-base-300">
          <div class="flex items-center justify-center lg:justify-start">
            <div class="avatar placeholder">
              <div class="bg-primary text-primary-content rounded-full w-8 h-8">
                <span class="text-sm">IO</span>
              </div>
            </div>
            <span class="ml-3 font-semibold text-lg hidden lg:block">Admin</span>
          </div>
        </div>

        <!-- Navigation Menu -->
        <ul class="menu p-0 w-full min-h-full">
          <!-- Dashboard -->
          <li>
            <a class="flex items-center justify-center lg:justify-start p-4 tooltip tooltip-right lg:tooltip-hidden"
               data-tip="Dashboard"
               :class="{ 'active': $route.name === 'Dashboard' }">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 21l4-4 4 4"></path>
              </svg>
              <span class="ml-3 hidden lg:block">Dashboard</span>
            </a>
          </li>

          <!-- Users -->
          <li>
            <a class="flex items-center justify-center lg:justify-start p-4 tooltip tooltip-right lg:tooltip-hidden"
               data-tip="Users">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
              </svg>
              <span class="ml-3 hidden lg:block">Users</span>
            </a>
          </li>

          <!-- Invoices -->
          <li>
            <a class="flex items-center justify-center lg:justify-start p-4 tooltip tooltip-right lg:tooltip-hidden"
               data-tip="Invoices">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <span class="ml-3 hidden lg:block">Invoices</span>
            </a>
          </li>

          <!-- Jobs -->
          <li>
            <a class="flex items-center justify-center lg:justify-start p-4 tooltip tooltip-right lg:tooltip-hidden"
               data-tip="Jobs">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
              </svg>
              <span class="ml-3 hidden lg:block">Jobs</span>
            </a>
          </li>

          <!-- Messages -->
          <li>
            <a class="flex items-center justify-center lg:justify-start p-4 tooltip tooltip-right lg:tooltip-hidden"
               data-tip="Messages">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
              <span class="ml-3 hidden lg:block">Messages</span>
            </a>
          </li>

          <!-- Divider -->
          <li class="my-2">
            <div class="divider mx-4 hidden lg:block"></div>
          </li>

          <!-- Settings -->
          <li>
            <a class="flex items-center justify-center lg:justify-start p-4 tooltip tooltip-right lg:tooltip-hidden"
               data-tip="Settings">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
              <span class="ml-3 hidden lg:block">Settings</span>
            </a>
          </li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>