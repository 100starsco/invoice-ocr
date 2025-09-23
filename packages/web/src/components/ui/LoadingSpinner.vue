<template>
  <div :class="containerClasses">
    <span :class="spinnerClasses"></span>
    <span v-if="text" class="ml-2">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  size?: 'xs' | 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'accent' | 'neutral' | 'info' | 'success' | 'warning' | 'error';
  text?: string;
  fullscreen?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  color: 'primary',
  fullscreen: false,
});

const containerClasses = computed(() => {
  if (props.fullscreen) {
    return 'fixed inset-0 flex items-center justify-center bg-base-100 bg-opacity-75 z-50';
  }
  return 'flex items-center';
});

const spinnerClasses = computed(() => {
  const classes = ['loading', 'loading-spinner'];

  const sizeMap = {
    xs: 'loading-xs',
    sm: 'loading-sm',
    md: 'loading-md',
    lg: 'loading-lg',
  };

  if (props.size) classes.push(sizeMap[props.size]);
  if (props.color) classes.push(`text-${props.color}`);

  return classes.join(' ');
});
</script>