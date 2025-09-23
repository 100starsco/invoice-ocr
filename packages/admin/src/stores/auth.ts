import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

interface User {
  id: string
  email: string
  name: string
}

interface LoginResponse {
  token: string
  user: User
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('admin_token'))
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  // Set axios default headers if token exists
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  async function login(email: string, password: string) {
    isLoading.value = true
    error.value = null

    try {
      const response = await axios.post<{ success: boolean; data: LoginResponse }>('/api/admin/login', {
        email,
        password
      })

      if (response.data.success) {
        const { token: newToken, user: userData } = response.data.data

        // Store token
        token.value = newToken
        localStorage.setItem('admin_token', newToken)

        // Store user data
        user.value = userData

        // Set axios default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`

        return true
      }
    } catch (err: any) {
      error.value = err.response?.data?.error || 'Login failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      await axios.post('/api/admin/logout')
    } catch {
      // Ignore logout errors
    } finally {
      // Clear local data
      token.value = null
      user.value = null
      localStorage.removeItem('admin_token')
      delete axios.defaults.headers.common['Authorization']
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return false

    isLoading.value = true
    error.value = null

    try {
      const response = await axios.get<{ success: boolean; data: { user: User } }>('/api/admin/me')

      if (response.data.success) {
        user.value = response.data.data.user
        return true
      }
    } catch (err: any) {
      // Token might be invalid
      if (err.response?.status === 401) {
        await logout()
      }
      error.value = err.response?.data?.error || 'Failed to fetch user'
      return false
    } finally {
      isLoading.value = false
    }
  }

  return {
    token: computed(() => token.value),
    user: computed(() => user.value),
    isAuthenticated,
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    login,
    logout,
    fetchCurrentUser
  }
})