import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface CameraState {
  isActive: boolean;
  hasPermission: boolean;
  deviceId: string | null;
  availableDevices: MediaDeviceInfo[];
  capturedImage: string | null;
  isProcessing: boolean;
}

export const useCameraStore = defineStore('camera', () => {
  const isActive = ref(false);
  const hasPermission = ref(false);
  const deviceId = ref<string | null>(null);
  const availableDevices = ref<MediaDeviceInfo[]>([]);
  const capturedImage = ref<string | null>(null);
  const isProcessing = ref(false);

  const setActive = (active: boolean) => {
    isActive.value = active;
  };

  const setPermission = (permission: boolean) => {
    hasPermission.value = permission;
  };

  const setDeviceId = (id: string | null) => {
    deviceId.value = id;
  };

  const setAvailableDevices = (devices: MediaDeviceInfo[]) => {
    availableDevices.value = devices;
  };

  const setCapturedImage = (image: string | null) => {
    capturedImage.value = image;
  };

  const setProcessing = (processing: boolean) => {
    isProcessing.value = processing;
  };

  const reset = () => {
    isActive.value = false;
    capturedImage.value = null;
    isProcessing.value = false;
  };

  return {
    isActive,
    hasPermission,
    deviceId,
    availableDevices,
    capturedImage,
    isProcessing,
    setActive,
    setPermission,
    setDeviceId,
    setAvailableDevices,
    setCapturedImage,
    setProcessing,
    reset,
  };
});