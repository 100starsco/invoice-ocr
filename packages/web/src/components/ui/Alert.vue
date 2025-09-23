<template>
  <div :class="alertClasses" role="alert">
    <component :is="iconComponent" v-if="showIcon" class="w-6 h-6 shrink-0" />
    <div class="flex-1">
      <slot />
    </div>
    <button
      v-if="closable"
      @click="handleClose"
      class="btn btn-ghost btn-sm btn-circle"
      aria-label="Close"
    >
      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path
          fill-rule="evenodd"
          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
          clip-rule="evenodd"
        />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
} from '@heroicons/vue/24/outline';

interface Props {
  type?: 'info' | 'success' | 'warning' | 'error';
  closable?: boolean;
  showIcon?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'info',
  closable: false,
  showIcon: true,
});

const emit = defineEmits<{
  close: [];
}>();

const alertClasses = computed(() => {
  const classes = ['alert'];

  if (props.type) classes.push(`alert-${props.type}`);

  return classes.join(' ');
});

const iconComponent = computed(() => {
  const iconMap = {
    info: InformationCircleIcon,
    success: CheckCircleIcon,
    warning: ExclamationTriangleIcon,
    error: XCircleIcon,
  };
  return iconMap[props.type];
});

const handleClose = () => {
  emit('close');
};
</script>