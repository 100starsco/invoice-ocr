import { ref, onUnmounted } from 'vue';
import { useCameraStore } from '@/stores';
import { cameraManager } from '@/utils';

export function useCamera() {
  const cameraStore = useCameraStore();
  const videoElement = ref<HTMLVideoElement | null>(null);
  const error = ref<string | null>(null);

  const startCamera = async () => {
    if (!videoElement.value) {
      error.value = 'Video element not initialized';
      return;
    }

    try {
      const hasPermission = await cameraManager.requestPermission();
      cameraStore.setPermission(hasPermission);

      if (!hasPermission) {
        error.value = 'Camera permission denied';
        return;
      }

      await cameraManager.startCamera(videoElement.value);
      cameraStore.setActive(true);

      const devices = await cameraManager.getAvailableDevices();
      cameraStore.setAvailableDevices(devices);
    } catch (err: any) {
      error.value = err.message || 'Failed to start camera';
      cameraStore.setActive(false);
    }
  };

  const stopCamera = async () => {
    await cameraManager.stopCamera();
    cameraStore.setActive(false);
  };

  const captureImage = () => {
    const imageData = cameraManager.captureImage();
    if (imageData) {
      cameraStore.setCapturedImage(imageData);
    }
    return imageData;
  };

  const switchCamera = async (deviceId: string) => {
    await cameraManager.switchCamera(deviceId);
    cameraStore.setDeviceId(deviceId);
  };

  onUnmounted(() => {
    stopCamera();
  });

  return {
    videoElement,
    error,
    isActive: cameraStore.isActive,
    hasPermission: cameraStore.hasPermission,
    availableDevices: cameraStore.availableDevices,
    capturedImage: cameraStore.capturedImage,
    startCamera,
    stopCamera,
    captureImage,
    switchCamera,
  };
}