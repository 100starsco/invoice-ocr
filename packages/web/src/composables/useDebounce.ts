import { ref, customRef } from 'vue';

export function useDebounce<T>(value: T, delay: number = 300) {
  let timeout: NodeJS.Timeout;

  return customRef((track, trigger) => {
    return {
      get() {
        track();
        return value;
      },
      set(newValue: T) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          value = newValue;
          trigger();
        }, delay);
      },
    };
  });
}

export function useDebouncedRef<T>(initialValue: T, delay: number = 300) {
  const state = ref(initialValue);
  const debouncedState = useDebounce(state.value, delay);

  return {
    state,
    debouncedState,
  };
}