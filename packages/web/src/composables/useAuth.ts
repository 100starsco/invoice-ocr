import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores';
import { authService } from '@/services';
import type { LoginCredentials } from '@/services';

export function useAuth() {
  const router = useRouter();
  const userStore = useUserStore();

  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => userStore.isAuthenticated);
  const user = computed(() => userStore.user);

  const login = async (credentials: LoginCredentials) => {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await authService.login(credentials);
      userStore.setUser(response.user);
      await router.push('/');
    } catch (err: any) {
      error.value = err.message || 'Login failed';
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const logout = async () => {
    isLoading.value = true;

    try {
      await authService.logout();
      userStore.clearUser();
      await router.push('/login');
    } catch (err) {
      console.error('Logout failed:', err);
    } finally {
      isLoading.value = false;
    }
  };

  const checkAuth = async () => {
    if (!isAuthenticated.value) return false;

    try {
      const user = await authService.getCurrentUser();
      userStore.setUser(user);
      return true;
    } catch (err) {
      userStore.clearUser();
      return false;
    }
  };

  return {
    isAuthenticated,
    user,
    isLoading,
    error,
    login,
    logout,
    checkAuth,
  };
}