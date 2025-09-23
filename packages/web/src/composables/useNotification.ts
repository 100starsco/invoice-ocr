import { ref } from 'vue';
import { useAppStore } from '@/stores';

export function useNotification() {
  const appStore = useAppStore();
  const notifications = ref<Array<{
    id: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
    duration?: number;
  }>>([]);

  const show = (
    message: string,
    type: 'info' | 'success' | 'warning' | 'error' = 'info',
    duration: number = 5000
  ) => {
    const id = Date.now().toString();
    const notification = { id, message, type, duration };

    notifications.value.push(notification);
    appStore.showNotification(message, type);

    if (duration > 0) {
      setTimeout(() => {
        dismiss(id);
      }, duration);
    }

    return id;
  };

  const dismiss = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id);
    if (index > -1) {
      notifications.value.splice(index, 1);
    }
    if (notifications.value.length === 0) {
      appStore.hideNotification();
    }
  };

  const clearAll = () => {
    notifications.value = [];
    appStore.hideNotification();
  };

  const success = (message: string, duration?: number) => {
    return show(message, 'success', duration);
  };

  const error = (message: string, duration?: number) => {
    return show(message, 'error', duration);
  };

  const warning = (message: string, duration?: number) => {
    return show(message, 'warning', duration);
  };

  const info = (message: string, duration?: number) => {
    return show(message, 'info', duration);
  };

  return {
    notifications,
    show,
    dismiss,
    clearAll,
    success,
    error,
    warning,
    info,
  };
}