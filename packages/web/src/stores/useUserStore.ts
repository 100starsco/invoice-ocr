import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export interface User {
  id: string;
  lineUserId?: string;
  displayName?: string;
  pictureUrl?: string;
  email?: string;
}

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null);
  const isAuthenticated = computed(() => !!user.value);

  const setUser = (userData: User | null) => {
    user.value = userData;
  };

  const clearUser = () => {
    user.value = null;
  };

  const updateUser = (updates: Partial<User>) => {
    if (user.value) {
      user.value = { ...user.value, ...updates };
    }
  };

  return {
    user,
    isAuthenticated,
    setUser,
    clearUser,
    updateUser,
  };
});