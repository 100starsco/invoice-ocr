<template>
  <div class="drawer lg:drawer-open" data-testid="admin-layout">
    <!-- Drawer Toggle -->
    <input id="drawer-toggle" type="checkbox" class="drawer-toggle" />

    <!-- Page Content -->
    <div class="drawer-content flex flex-col">
      <!-- Enhanced Navbar -->
      <div class="navbar bg-base-100 shadow-lg border-b border-base-300">
        <div class="navbar-start">
          <!-- Mobile Menu Toggle (responsive) -->
          <label for="drawer-toggle" class="btn btn-square btn-ghost lg:hidden">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
          </label>

          <!-- Sidebar Toggle (always visible) -->
          <div class="hidden lg:block">
            <SidebarToggle />
          </div>

          <!-- App Title -->
          <h1 class="text-xl font-bold text-primary ml-2 lg:ml-4">Invoice OCR Admin</h1>
        </div>

        <div class="navbar-center hidden lg:flex">
          <!-- Optional: Add breadcrumb or search here -->
        </div>

        <div class="navbar-end">
          <div class="flex items-center gap-2">
            <!-- Notifications (placeholder for future) -->
            <button class="btn btn-ghost btn-circle" title="Notifications">
              <div class="indicator">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
                </svg>
                <span class="badge badge-xs badge-primary indicator-item"></span>
              </div>
            </button>

            <!-- Profile Dropdown -->
            <ProfileDropdown />
          </div>
        </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1 p-8 bg-base-200">
        <router-view />
      </div>
    </div>

    <!-- Enhanced Sidebar -->
    <div class="drawer-side">
      <label for="drawer-toggle" class="drawer-overlay"></label>
      <aside :class="[
        'min-h-full bg-base-100 shadow-lg border-r border-base-300 transition-all duration-300 ease-in-out',
        getSidebarWidthClass()
      ]">
        <!-- Sidebar Header -->
        <div class="p-4 border-b border-base-300">
          <div :class="[
            'flex items-center transition-all duration-300',
            shouldShowLabels() ? 'justify-start' : 'justify-center'
          ]">
            <div class="avatar placeholder">
              <div class="bg-primary text-primary-content rounded-full w-8 h-8">
                <span class="text-sm">IO</span>
              </div>
            </div>
            <span
              v-if="shouldShowLabels()"
              class="ml-3 font-semibold text-lg transition-opacity duration-300"
            >
              Admin
            </span>
          </div>
        </div>

        <!-- Navigation Menu -->
        <ul class="menu p-0 w-full min-h-full">
          <!-- Dashboard -->
          <li>
            <router-link :class="[
                'flex items-center p-4 transition-all duration-200',
                shouldShowLabels() ? 'justify-start' : 'justify-center',
                shouldShowTooltips() ? 'tooltip tooltip-right' : '',
                { 'active': $route.name === 'Dashboard' }
              ]"
               :data-tip="shouldShowTooltips() ? 'Dashboard' : ''"
               to="/">
              <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 21l4-4 4 4"></path>
              </svg>
              <span
                v-if="shouldShowLabels()"
                class="ml-3 transition-opacity duration-300"
              >
                Dashboard
              </span>
            </router-link>
          </li>

          <!-- Users -->
          <li>
            <router-link :class="[
                'flex items-center p-4 transition-all duration-200',
                shouldShowLabels() ? 'justify-start' : 'justify-center',
                shouldShowTooltips() ? 'tooltip tooltip-right' : '',
                { 'active': $route.name === 'Users' }
              ]"
               :data-tip="shouldShowTooltips() ? 'Users' : ''"
               to="/users">
              <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
              </svg>
              <span
                v-if="shouldShowLabels()"
                class="ml-3 transition-opacity duration-300"
              >
                Users
              </span>
            </router-link>
          </li>

          <!-- Invoices -->
          <li>
            <a :class="[
                'flex items-center p-4 transition-all duration-200',
                shouldShowLabels() ? 'justify-start' : 'justify-center',
                shouldShowTooltips() ? 'tooltip tooltip-right' : ''
              ]"
               :data-tip="shouldShowTooltips() ? 'Invoices' : ''"
               href="#">
              <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <span
                v-if="shouldShowLabels()"
                class="ml-3 transition-opacity duration-300"
              >
                Invoices
              </span>
            </a>
          </li>

          <!-- Jobs -->
          <li>
            <a :class="[
                'flex items-center p-4 transition-all duration-200',
                shouldShowLabels() ? 'justify-start' : 'justify-center',
                shouldShowTooltips() ? 'tooltip tooltip-right' : ''
              ]"
               :data-tip="shouldShowTooltips() ? 'Jobs' : ''"
               href="#">
              <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
              </svg>
              <span
                v-if="shouldShowLabels()"
                class="ml-3 transition-opacity duration-300"
              >
                Jobs
              </span>
            </a>
          </li>

          <!-- Messages -->
          <li>
            <a :class="[
                'flex items-center p-4 transition-all duration-200',
                shouldShowLabels() ? 'justify-start' : 'justify-center',
                shouldShowTooltips() ? 'tooltip tooltip-right' : ''
              ]"
               :data-tip="shouldShowTooltips() ? 'Messages' : ''"
               href="#">
              <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
              <span
                v-if="shouldShowLabels()"
                class="ml-3 transition-opacity duration-300"
              >
                Messages
              </span>
            </a>
          </li>

          <!-- Divider -->
          <li v-if="shouldShowLabels()" class="my-2">
            <div class="divider mx-4"></div>
          </li>

          <!-- Settings -->
          <li>
            <a :class="[
                'flex items-center p-4 transition-all duration-200',
                shouldShowLabels() ? 'justify-start' : 'justify-center',
                shouldShowTooltips() ? 'tooltip tooltip-right' : ''
              ]"
               :data-tip="shouldShowTooltips() ? 'Settings' : ''"
               href="#">
              <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
              <span
                v-if="shouldShowLabels()"
                class="ml-3 transition-opacity duration-300"
              >
                Settings
              </span>
            </a>
          </li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import ProfileDropdown from '@/components/ProfileDropdown.vue'
import SidebarToggle from '@/components/SidebarToggle.vue'
import { useSidebar } from '@/composables/useSidebar'

const { getSidebarWidthClass, shouldShowLabels, shouldShowTooltips } = useSidebar()
</script>