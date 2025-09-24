import axios from 'axios'

export interface LineUser {
  id: string
  userId: string
  displayName: string | null
  pictureUrl: string | null
  statusMessage: string | null
  language: string | null
  isFollowing: boolean
  isBlocked: boolean
  profileLastUpdated: string | null
  firstSeenAt: string
  lastSeenAt: string
  lastMessageAt: string | null
  createdAt: string
  updatedAt: string
}

export interface UserWithStats extends LineUser {
  messageCount: number
}

export interface PaginatedUsersResponse {
  users: LineUser[]
  total: number
  limit: number
  offset: number
  hasMore: boolean
}

export interface UserListOptions {
  limit?: number
  offset?: number
  search?: string
  isFollowing?: boolean
  sortBy?: 'displayName' | 'lastSeenAt' | 'firstSeenAt' | 'lastMessageAt'
  sortOrder?: 'asc' | 'desc'
}

export interface ApiResponse<T> {
  success: boolean
  data: T
}

export interface ApiError {
  error: string
}

export class UsersApiClient {
  private baseURL = '/api/admin'

  async getUsers(options: UserListOptions = {}): Promise<PaginatedUsersResponse> {
    try {
      const params = new URLSearchParams()

      if (options.limit) params.append('limit', options.limit.toString())
      if (options.offset) params.append('offset', options.offset.toString())
      if (options.search) params.append('search', options.search)
      if (typeof options.isFollowing === 'boolean') {
        params.append('isFollowing', options.isFollowing.toString())
      }
      if (options.sortBy) params.append('sortBy', options.sortBy)
      if (options.sortOrder) params.append('sortOrder', options.sortOrder)

      const response = await axios.get<ApiResponse<PaginatedUsersResponse>>(
        `${this.baseURL}/users?${params.toString()}`
      )

      if (response.data.success) {
        return response.data.data
      } else {
        throw new Error('Failed to fetch users')
      }
    } catch (error: any) {
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error)
      }
      throw new Error('Failed to fetch users')
    }
  }

  async getUserById(userId: string): Promise<UserWithStats> {
    try {
      const response = await axios.get<ApiResponse<{ user: UserWithStats }>>(
        `${this.baseURL}/users/${encodeURIComponent(userId)}`
      )

      if (response.data.success) {
        return response.data.data.user
      } else {
        throw new Error('Failed to fetch user')
      }
    } catch (error: any) {
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error)
      }
      throw new Error('Failed to fetch user')
    }
  }

  async searchUsers(query: string, limit = 10): Promise<LineUser[]> {
    try {
      const response = await axios.get<ApiResponse<{ users: LineUser[] }>>(
        `${this.baseURL}/users/search/${encodeURIComponent(query)}?limit=${limit}`
      )

      if (response.data.success) {
        return response.data.data.users
      } else {
        throw new Error('Failed to search users')
      }
    } catch (error: any) {
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error)
      }
      throw new Error('Failed to search users')
    }
  }
}

// Export singleton instance
export const usersApi = new UsersApiClient()