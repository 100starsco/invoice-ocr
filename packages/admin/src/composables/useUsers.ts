import { ref, computed, watch } from 'vue'
import { usersApi, type LineUser, type UserWithStats, type UserListOptions } from '@/api/users'

export function useUsers() {
  // State
  const users = ref<LineUser[]>([])
  const currentUser = ref<UserWithStats | null>(null)
  const isLoading = ref(false)
  const isLoadingUser = ref(false)
  const error = ref<string | null>(null)

  // Pagination
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const hasMore = ref(false)

  // Filters
  const searchQuery = ref('')
  const followingFilter = ref<boolean | undefined>(undefined)
  const sortBy = ref<'displayName' | 'lastSeenAt' | 'firstSeenAt' | 'lastMessageAt'>('lastSeenAt')
  const sortOrder = ref<'asc' | 'desc'>('desc')

  // Computed
  const offset = computed(() => (currentPage.value - 1) * pageSize.value)
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
  const hasUsers = computed(() => users.value.length > 0)
  const isEmpty = computed(() => !isLoading.value && users.value.length === 0)

  // Debounced search
  let searchTimeout: number | null = null

  // Methods
  async function fetchUsers(reset = false) {
    if (reset) {
      currentPage.value = 1
      users.value = []
    }

    isLoading.value = true
    error.value = null

    try {
      const options: UserListOptions = {
        limit: pageSize.value,
        offset: offset.value,
        sortBy: sortBy.value,
        sortOrder: sortOrder.value
      }

      if (searchQuery.value.trim()) {
        options.search = searchQuery.value.trim()
      }

      if (typeof followingFilter.value === 'boolean') {
        options.isFollowing = followingFilter.value
      }

      const response = await usersApi.getUsers(options)

      users.value = response.users
      total.value = response.total
      hasMore.value = response.hasMore

    } catch (err: any) {
      error.value = err.message || 'Failed to fetch users'
      users.value = []
      total.value = 0
      hasMore.value = false
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUserById(userId: string) {
    isLoadingUser.value = true
    error.value = null

    try {
      currentUser.value = await usersApi.getUserById(userId)
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch user'
      currentUser.value = null
    } finally {
      isLoadingUser.value = false
    }
  }

  async function searchUsers(query: string) {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }

    searchTimeout = window.setTimeout(() => {
      searchQuery.value = query
      fetchUsers(true)
    }, 300) // 300ms debounce
  }

  function setFollowingFilter(isFollowing: boolean | undefined) {
    followingFilter.value = isFollowing
    fetchUsers(true)
  }

  function setSorting(field: typeof sortBy.value, order: typeof sortOrder.value) {
    sortBy.value = field
    sortOrder.value = order
    fetchUsers(true)
  }

  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
      fetchUsers()
    }
  }

  function nextPage() {
    if (currentPage.value < totalPages.value) {
      currentPage.value++
      fetchUsers()
    }
  }

  function prevPage() {
    if (currentPage.value > 1) {
      currentPage.value--
      fetchUsers()
    }
  }

  function refresh() {
    fetchUsers(true)
  }

  function clearError() {
    error.value = null
  }

  function clearCurrentUser() {
    currentUser.value = null
  }

  // Format helpers
  function formatLastSeen(lastSeenAt: string): string {
    const date = new Date(lastSeenAt)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMinutes / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMinutes < 1) return 'Just now'
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`

    return date.toLocaleDateString()
  }

  function getUserDisplayName(user: LineUser): string {
    return user.displayName || `User ${user.userId.substring(0, 8)}`
  }

  function getUserStatusColor(user: LineUser): string {
    if (!user.isFollowing) return 'badge-ghost'

    const lastSeen = new Date(user.lastSeenAt)
    const now = new Date()
    const diffHours = (now.getTime() - lastSeen.getTime()) / (1000 * 60 * 60)

    if (diffHours < 1) return 'badge-success'
    if (diffHours < 24) return 'badge-warning'
    return 'badge-info'
  }

  // Watch for automatic refresh on filter changes
  watch([followingFilter, sortBy, sortOrder], () => {
    if (users.value.length > 0) {
      fetchUsers(true)
    }
  })

  return {
    // State
    users: computed(() => users.value),
    currentUser: computed(() => currentUser.value),
    isLoading: computed(() => isLoading.value),
    isLoadingUser: computed(() => isLoadingUser.value),
    error: computed(() => error.value),

    // Pagination
    total: computed(() => total.value),
    currentPage: computed(() => currentPage.value),
    pageSize: computed(() => pageSize.value),
    totalPages,
    hasMore: computed(() => hasMore.value),
    offset,

    // Filters
    searchQuery: computed(() => searchQuery.value),
    followingFilter: computed(() => followingFilter.value),
    sortBy: computed(() => sortBy.value),
    sortOrder: computed(() => sortOrder.value),

    // Computed
    hasUsers,
    isEmpty,

    // Methods
    fetchUsers,
    fetchUserById,
    searchUsers,
    setFollowingFilter,
    setSorting,
    goToPage,
    nextPage,
    prevPage,
    refresh,
    clearError,
    clearCurrentUser,

    // Helpers
    formatLastSeen,
    getUserDisplayName,
    getUserStatusColor
  }
}