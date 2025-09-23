import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface AppState {
  isLoading: boolean;
  theme: 'light' | 'dark' | 'cupcake';
  sidebarOpen: boolean;
  notification: {
    show: boolean;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
  } | null;
}

export const useAppStore = defineStore('app', () => {
  const isLoading = ref(false);
  const theme = ref<'light' | 'dark' | 'cupcake'>('light');
  const sidebarOpen = ref(false);
  const notification = ref<AppState['notification']>(null);

  const setLoading = (loading: boolean) => {
    isLoading.value = loading;
  };

  const setTheme = (newTheme: AppState['theme']) => {
    theme.value = newTheme;
  };

  const toggleSidebar = () => {
    sidebarOpen.value = !sidebarOpen.value;
  };

  const showNotification = (
    message: string,
    type: 'info' | 'success' | 'warning' | 'error' = 'info'
  ) => {
    notification.value = { show: true, message, type };
  };

  const hideNotification = () => {
    notification.value = null;
  };

  return {
    isLoading,
    theme,
    sidebarOpen,
    notification,
    setLoading,
    setTheme,
    toggleSidebar,
    showNotification,
    hideNotification,
  };
});