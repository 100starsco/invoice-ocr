<template>
  <div :class="cardClasses">
    <div v-if="$slots.header" class="card-header">
      <slot name="header" />
    </div>
    <div class="card-body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="card-actions">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  bordered?: boolean;
  compact?: boolean;
  shadow?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

const props = withDefaults(defineProps<Props>(), {
  bordered: false,
  compact: false,
  shadow: 'md',
});

const cardClasses = computed(() => {
  const classes = ['card', 'bg-base-100'];

  if (props.bordered) classes.push('card-bordered');
  if (props.compact) classes.push('card-compact');
  if (props.shadow) classes.push(`shadow-${props.shadow}`);

  return classes.join(' ');
});
</script>