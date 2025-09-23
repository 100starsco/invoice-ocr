<template>
  <button
    :type="type"
    :class="buttonClasses"
    :disabled="disabled || loading"
    v-bind="$attrs"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  variant?: 'primary' | 'secondary' | 'accent' | 'ghost' | 'link';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  type?: 'button' | 'submit' | 'reset';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  loading: false,
  disabled: false,
  fullWidth: false,
});

const buttonClasses = computed(() => {
  const classes = ['btn'];

  if (props.variant) classes.push(`btn-${props.variant}`);
  if (props.size) classes.push(`btn-${props.size}`);
  if (props.fullWidth) classes.push('w-full');
  if (props.loading) classes.push('loading');

  return classes.join(' ');
});
</script>