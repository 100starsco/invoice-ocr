<template>
  <div data-testid="users-page">
    <!-- Page Header -->
    <div class="mb-6 flex flex-col lg:flex-row gap-4 justify-between items-start lg:items-center">
      <div>
        <h1 class="text-3xl font-bold text-base-content">User Management</h1>
        <p class="text-base-content/70 mt-1">Manage and monitor LINE users</p>
      </div>

      <!-- Search Bar -->
      <div class="form-control">
        <div class="input-group">
          <input
            type="text"
            placeholder="Search users..."
            class="input input-bordered w-64"
            :value="searchQuery"
            @input="handleSearch($event)"
          />
          <button class="btn btn-square btn-primary">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
        <!-- Filters & Stats -->
        <div class="mb-6 flex flex-col lg:flex-row gap-4 justify-between items-start lg:items-center">
          <!-- Stats Cards -->
          <div class="stats shadow bg-base-100">
            <div class="stat">
              <div class="stat-title">Total Users</div>
              <div class="stat-value text-primary">{{ total.toLocaleString() }}</div>
              <div class="stat-desc">{{ hasUsers ? 'Active users in system' : 'No users found' }}</div>
            </div>
            <div class="stat">
              <div class="stat-title">Following</div>
              <div class="stat-value text-success">{{ followingCount }}</div>
              <div class="stat-desc">Users following bot</div>
            </div>
          </div>

          <!-- Filters -->
          <div class="flex flex-wrap gap-2">
            <!-- Following Filter -->
            <div class="dropdown dropdown-end">
              <label tabindex="0" class="btn btn-outline btn-sm">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.707A1 1 0 013 7V4z"></path>
                </svg>
                Following: {{ followingFilterText }}
              </label>
              <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-40">
                <li><a @click="setFollowingFilter(undefined)" :class="{ 'active': followingFilter === undefined }">All Users</a></li>
                <li><a @click="setFollowingFilter(true)" :class="{ 'active': followingFilter === true }">Following</a></li>
                <li><a @click="setFollowingFilter(false)" :class="{ 'active': followingFilter === false }">Not Following</a></li>
              </ul>
            </div>

            <!-- Sort Options -->
            <div class="dropdown dropdown-end">
              <label tabindex="0" class="btn btn-outline btn-sm">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"></path>
                </svg>
                Sort: {{ sortText }}
              </label>
              <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
                <li><a @click="setSorting('lastSeenAt', 'desc')" :class="{ 'active': sortBy === 'lastSeenAt' && sortOrder === 'desc' }">Last Seen (Recent)</a></li>
                <li><a @click="setSorting('lastSeenAt', 'asc')" :class="{ 'active': sortBy === 'lastSeenAt' && sortOrder === 'asc' }">Last Seen (Oldest)</a></li>
                <li><a @click="setSorting('displayName', 'asc')" :class="{ 'active': sortBy === 'displayName' && sortOrder === 'asc' }">Name (A-Z)</a></li>
                <li><a @click="setSorting('displayName', 'desc')" :class="{ 'active': sortBy === 'displayName' && sortOrder === 'desc' }">Name (Z-A)</a></li>
                <li><a @click="setSorting('firstSeenAt', 'desc')" :class="{ 'active': sortBy === 'firstSeenAt' && sortOrder === 'desc' }">Joined (Recent)</a></li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Error Alert -->
        <div v-if="error" class="alert alert-error mb-6">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span>{{ error }}</span>
          <button class="btn btn-sm btn-ghost" @click="clearError">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading && !hasUsers" class="flex justify-center items-center py-12">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>

        <!-- Empty State -->
        <div v-else-if="isEmpty" class="hero bg-base-100 rounded-lg shadow-lg py-12">
          <div class="hero-content text-center">
            <div class="max-w-md">
              <svg class="w-24 h-24 mx-auto text-base-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
              </svg>
              <h3 class="text-2xl font-bold mb-2">No Users Found</h3>
              <p class="text-base-content/70 mb-4">
                {{ searchQuery ? 'Try adjusting your search or filters.' : 'No users have been registered yet.' }}
              </p>
              <button v-if="searchQuery || followingFilter !== undefined" class="btn btn-primary" @click="clearFilters">
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        <!-- Users Table -->
        <div v-else class="bg-base-100 rounded-box shadow-lg border border-base-300">
          <table class="table table-zebra table-sm table-pin-rows w-full">
              <thead>
                <tr class="bg-base-300 text-base-content border-b border-base-300">
                  <th class="w-16">#</th>
                  <th>User</th>
                  <th>Status</th>
                  <th>Activity</th>
                  <th class="hidden lg:table-cell">Joined</th>
                  <th class="hidden xl:table-cell">Messages</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(user, index) in users" :key="user.id" class="hover:bg-base-200 transition-colors duration-200 cursor-pointer" @click="viewUserDetails(user.userId)">
                  <!-- Row Number -->
                  <td class="font-mono text-sm text-base-content/60">
                    {{ offset + index + 1 }}
                  </td>

                  <!-- User Info -->
                  <td class="min-w-0">
                    <div class="flex items-center gap-3">
                      <div class="avatar placeholder">
                        <div class="mask mask-squircle w-10 h-10 bg-base-300">
                          <img
                            v-if="user.pictureUrl"
                            :src="user.pictureUrl"
                            :alt="getUserDisplayName(user)"
                            class="object-cover w-full h-full"
                            loading="lazy"
                          />
                          <div v-else class="bg-primary text-primary-content text-sm font-bold flex items-center justify-center">
                            {{ getUserDisplayName(user).charAt(0).toUpperCase() }}
                          </div>
                        </div>
                      </div>
                      <div class="min-w-0 flex-1">
                        <div class="font-semibold text-base-content truncate">{{ getUserDisplayName(user) }}</div>
                        <div class="text-xs text-base-content/60 font-mono truncate">
                          {{ user.userId.substring(0, 16) }}...
                        </div>
                        <div v-if="user.statusMessage" class="text-xs text-base-content/50 mt-0.5 truncate max-w-40">
                          {{ user.statusMessage }}
                        </div>
                      </div>
                    </div>
                  </td>

                  <!-- Status -->
                  <td>
                    <div class="flex flex-col gap-1.5">
                      <div class="badge badge-xs" :class="getUserStatusColor(user)">
                        <div class="w-1.5 h-1.5 rounded-full mr-1" :class="user.isFollowing ? 'bg-success-content' : 'bg-error-content'"></div>
                        {{ user.isFollowing ? 'Following' : 'Unfollowed' }}
                      </div>
                      <div v-if="user.isBlocked" class="badge badge-error badge-xs">
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728"></path>
                        </svg>
                        Blocked
                      </div>
                    </div>
                  </td>

                  <!-- Activity -->
                  <td>
                    <div class="space-y-1">
                      <div class="text-xs font-medium text-base-content">
                        <span class="text-base-content/60">Last seen:</span>
                        {{ formatLastSeen(user.lastSeenAt) }}
                      </div>
                      <div v-if="user.lastMessageAt" class="text-xs text-success">
                        <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                        </svg>
                        {{ formatLastSeen(user.lastMessageAt) }}
                      </div>
                      <div v-else class="text-xs text-base-content/40">
                        <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                        </svg>
                        No messages
                      </div>
                    </div>
                  </td>

                  <!-- Joined Date -->
                  <td class="hidden lg:table-cell">
                    <div class="text-xs space-y-0.5">
                      <div class="font-medium text-base-content">
                        {{ new Date(user.firstSeenAt).toLocaleDateString() }}
                      </div>
                      <div class="text-base-content/60">
                        {{ new Date(user.firstSeenAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                      </div>
                    </div>
                  </td>

                  <!-- Message Count -->
                  <td class="hidden xl:table-cell">
                    <div class="stat">
                      <div class="stat-value text-sm text-primary">N/A</div>
                      <div class="stat-desc text-xs">messages</div>
                    </div>
                  </td>

                  <!-- Actions -->
                  <td class="relative">
                    <div class="dropdown dropdown-end dropdown-bottom" @click.stop>
                      <label tabindex="0" class="btn btn-ghost btn-xs btn-circle">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path>
                        </svg>
                      </label>
                      <ul tabindex="0" class="dropdown-content menu menu-sm p-2 shadow-lg bg-base-100 rounded-box w-44 border border-base-300 z-[1000]">
                        <li>
                          <a @click="viewUserDetails(user.userId)" class="text-xs">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                            </svg>
                            View Details
                          </a>
                        </li>
                        <li>
                          <a class="text-xs">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                            </svg>
                            View Messages
                          </a>
                        </li>
                        <li>
                          <a class="text-xs">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            Export Data
                          </a>
                        </li>
                      </ul>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="flex justify-center items-center p-6 bg-base-200 border-t">
            <div class="join">
              <button class="join-item btn btn-sm" @click="prevPage" :disabled="currentPage === 1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                </svg>
              </button>

              <template v-for="page in visiblePages" :key="page">
                <button
                  v-if="page !== '...'"
                  class="join-item btn btn-sm"
                  :class="{ 'btn-active': page === currentPage }"
                  @click="goToPage(page as number)"
                >
                  {{ page }}
                </button>
                <span v-else class="join-item btn btn-sm btn-disabled">...</span>
              </template>

              <button class="join-item btn btn-sm" @click="nextPage" :disabled="currentPage === totalPages">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </button>
            </div>

            <div class="ml-4 text-sm text-base-content/70">
              Page {{ currentPage }} of {{ totalPages }} ({{ total.toLocaleString() }} users)
            </div>
          </div>
    </div>

    <!-- Action Bar -->
    <div class="mb-6 flex flex-wrap gap-2 items-center justify-between">
      <!-- Refresh Button -->
      <button class="btn btn-ghost btn-sm" @click="refresh" :disabled="isLoading" title="Refresh">
        <svg class="w-4 h-4 mr-2" :class="{ 'animate-spin': isLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
        Refresh
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useUsers } from '@/composables/useUsers'

// Composables
const {
  users,
  isLoading,
  error,
  total,
  currentPage,
  totalPages,
  hasUsers,
  isEmpty,
  searchQuery,
  followingFilter,
  sortBy,
  sortOrder,
  offset,
  fetchUsers,
  searchUsers,
  setFollowingFilter,
  setSorting,
  goToPage,
  nextPage,
  prevPage,
  refresh,
  clearError,
  formatLastSeen,
  getUserDisplayName,
  getUserStatusColor
} = useUsers()

// Computed properties
const followingCount = computed(() =>
  users.value.filter(user => user.isFollowing).length
)

const followingFilterText = computed(() => {
  if (followingFilter.value === true) return 'Following'
  if (followingFilter.value === false) return 'Not Following'
  return 'All'
})

const sortText = computed(() => {
  const sortNames = {
    'lastSeenAt': 'Last Seen',
    'displayName': 'Name',
    'firstSeenAt': 'Joined',
    'lastMessageAt': 'Last Message'
  }
  const order = sortOrder.value === 'desc' ? '↓' : '↑'
  return `${sortNames[sortBy.value]} ${order}`
})

const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const current = currentPage.value
  const total = totalPages.value

  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    pages.push(1)

    if (current > 4) pages.push('...')

    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    if (current < total - 3) pages.push('...')

    pages.push(total)
  }

  return pages
})

// Methods
function handleSearch(event: Event) {
  const target = event.target as HTMLInputElement
  searchUsers(target.value)
}

function clearFilters() {
  searchUsers('')
  setFollowingFilter(undefined)
  setSorting('lastSeenAt', 'desc')
}

function viewUserDetails(userId: string) {
  // TODO: Implement user details modal or page
  console.log('View user details:', userId)
}

// Lifecycle
onMounted(() => {
  fetchUsers(true)
})
</script>