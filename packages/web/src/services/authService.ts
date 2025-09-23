import { apiClient } from './api';
import type { User } from '@/stores';

export interface LoginCredentials {
  email?: string;
  password?: string;
  lineUserId?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export class AuthService {
  private static instance: AuthService;

  private constructor() {}

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  }

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  }

  async refreshToken(): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/refresh');
    return response.data;
  }

  async verifyLineToken(token: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/line/verify', { token });
    return response.data;
  }
}

export const authService = AuthService.getInstance();