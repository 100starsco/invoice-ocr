<template>
  <div class="min-h-screen bg-gray-900 relative overflow-hidden">
    <!-- Camera Stream -->
    <video
      ref="videoRef"
      class="w-full h-full object-cover absolute inset-0"
      :class="{ 'scale-x-[-1]': isUsingFrontCamera }"
      autoplay
      playsinline
      muted
    ></video>

    <!-- Canvas for capturing -->
    <canvas
      ref="canvasRef"
      class="hidden"
    ></canvas>

    <!-- Invoice Guide Overlay -->
    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div class="relative">
        <!-- Guide Frame -->
        <div
          class="border-2 border-white rounded-lg"
          :style="{
            width: guideWidth + 'px',
            height: guideHeight + 'px',
            opacity: 0.8
          }"
        >
          <!-- Corner markers -->
          <div class="absolute -top-1 -left-1 w-6 h-6 border-t-4 border-l-4 border-primary rounded-tl-lg"></div>
          <div class="absolute -top-1 -right-1 w-6 h-6 border-t-4 border-r-4 border-primary rounded-tr-lg"></div>
          <div class="absolute -bottom-1 -left-1 w-6 h-6 border-b-4 border-l-4 border-primary rounded-bl-lg"></div>
          <div class="absolute -bottom-1 -right-1 w-6 h-6 border-b-4 border-r-4 border-primary rounded-br-lg"></div>

        </div>

        <!-- Guide Text -->
        <div class="absolute -top-12 left-1/2 transform -translate-x-1/2">
          <div class="bg-black bg-opacity-60 px-3 py-2 rounded-lg">
            <p class="text-white text-sm font-medium text-center">
              {{ guideText }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Top Status Bar -->
    <div class="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/50 to-transparent">
      <div class="flex justify-between items-center text-white">
        <button
          @click="router.go(-1)"
          class="btn btn-ghost btn-sm btn-circle"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>

        <div class="flex items-center space-x-2">
          <div v-if="cameraStore.isProcessing" class="loading loading-spinner loading-sm"></div>
          <span class="text-sm font-medium">{{ statusText }}</span>
        </div>

        <div class="w-10"></div>
      </div>
    </div>

    <!-- Bottom Controls -->
    <div class="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/70 to-transparent">
      <div class="flex items-center justify-between">
        <!-- Flash Toggle (Left) -->
        <button
          v-if="hasFlash"
          @click="toggleFlash"
          class="btn btn-ghost btn-circle text-white"
          :class="{ 'btn-active': isFlashOn }"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
        </button>
        <div v-else class="w-12"></div>

        <!-- Capture Button (Center) -->
        <button
          @click="captureImage"
          :disabled="!cameraStore.hasPermission || cameraStore.isProcessing"
          class="btn btn-circle btn-primary btn-lg relative"
          :class="{ 'btn-disabled': !cameraStore.hasPermission || cameraStore.isProcessing }"
        >
          <div v-if="cameraStore.isProcessing" class="loading loading-spinner loading-md"></div>
          <svg v-else class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
        </button>

        <!-- Right spacer for layout balance -->
        <div class="w-12"></div>
      </div>
    </div>

    <!-- Permission Request Modal -->
    <div v-if="showPermissionModal" class="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 m-4 max-w-sm">
        <div class="text-center">
          <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          <h3 class="text-lg font-semibold mb-2">Camera Access Required</h3>
          <p class="text-gray-600 mb-4">To capture invoices, we need access to your camera. Please allow camera permissions.</p>
          <div class="flex space-x-3">
            <button @click="requestCameraPermission" class="btn btn-primary flex-1">Allow Camera</button>
            <button @click="router.go(-1)" class="btn btn-ghost flex-1">Cancel</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="absolute top-20 left-4 right-4 z-40">
      <div class="alert alert-error">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
        </svg>
        <span>{{ errorMessage }}</span>
        <button @click="errorMessage = ''" class="btn btn-ghost btn-sm">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useCameraStore } from '@/stores';

const cameraStore = useCameraStore();
const router = useRouter();

// Refs
const videoRef = ref<HTMLVideoElement>();
const canvasRef = ref<HTMLCanvasElement>();
const showPermissionModal = ref(false);
const errorMessage = ref('');
const isFlashOn = ref(false);
const hasFlash = ref(false);
const currentStream = ref<MediaStream | null>(null);


// Guide dimensions (responsive) - optimized for vertical receipts
const guideWidth = ref(320);
const guideHeight = ref(480);

// Computed
const isUsingFrontCamera = computed(() => {
  return cameraStore.deviceId?.includes('front') || cameraStore.deviceId?.includes('user');
});

const statusText = computed(() => {
  if (cameraStore.isProcessing) return 'Processing...';
  if (!cameraStore.hasPermission) return 'Camera access required';
  if (!cameraStore.isActive) return 'Starting camera...';
  return 'Align invoice within guide';
});

const guideText = computed(() => {
  if (!cameraStore.hasPermission) return 'Grant camera permission to continue';
  if (!cameraStore.isActive) return 'Initializing camera...';
  return 'Position receipt/invoice within the frame';
});


// Methods
const requestCameraPermission = async () => {
  try {
    console.log('Requesting camera permission...');
    await getCameraPermission();
    showPermissionModal.value = false;
  } catch (error: any) {
    console.error('Camera permission error:', error);
    handleCameraError(error);
  }
};

const getCameraPermission = async () => {
  try {
    // Step 1: First request basic camera access to get permission
    console.log('Step 1: Requesting basic camera access...');
    const basicStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' } // Prefer back camera
    });

    // Stop the basic stream immediately - we just needed permission
    basicStream.getTracks().forEach(track => track.stop());
    console.log('Basic camera permission granted');

    // Step 2: Now enumerate devices (should work with permission)
    console.log('Step 2: Enumerating camera devices...');
    const devices = await navigator.mediaDevices.enumerateDevices();
    const videoDevices = devices.filter(device => device.kind === 'videoinput');

    console.log('Found video devices:', videoDevices.length);
    videoDevices.forEach((device, index) => {
      console.log(`Camera ${index + 1}:`, device.label || `Camera ${index + 1}`, device.deviceId);
    });
    cameraStore.setAvailableDevices(videoDevices);

    // Step 3: Find preferred camera
    const backCamera = videoDevices.find(device =>
      device.label.toLowerCase().includes('back') ||
      device.label.toLowerCase().includes('rear') ||
      device.label.toLowerCase().includes('environment') ||
      device.label.toLowerCase().includes('facing back')
    );

    console.log('Back camera found:', backCamera?.label || 'None');

    // Step 4: Start camera with preferred device or fallback
    const preferredDeviceId = backCamera?.deviceId;
    await startCamera(preferredDeviceId);

    cameraStore.setPermission(true);
    cameraStore.setActive(true);
    console.log('Camera successfully initialized');

  } catch (error: any) {
    console.error('Camera permission error:', error);
    cameraStore.setPermission(false);
    throw error;
  }
};

const handleCameraError = (error: any) => {
  let message = 'Failed to access camera. ';

  if (error.name === 'NotAllowedError') {
    message += 'Permission denied. Please allow camera access and refresh the page.';
  } else if (error.name === 'NotFoundError') {
    message += 'No camera found on this device.';
  } else if (error.name === 'NotReadableError') {
    message += 'Camera is being used by another application.';
  } else if (error.name === 'OverconstrainedError') {
    message += 'Camera constraints could not be satisfied.';
  } else if (error.name === 'SecurityError') {
    message += 'Camera access blocked by security policy.';
  } else {
    message += 'Please check your camera settings and try again.';
  }

  errorMessage.value = message;
};

const startCamera = async (preferredDeviceId?: string) => {
  try {
    if (currentStream.value) {
      currentStream.value.getTracks().forEach(track => track.stop());
    }

    console.log('Starting camera with device:', preferredDeviceId || 'default');

    // Build constraints - start simple and stable
    let constraints: MediaStreamConstraints;

    if (preferredDeviceId) {
      // Try preferred device first
      constraints = {
        video: {
          deviceId: { ideal: preferredDeviceId },
          width: { ideal: 1920, max: 1920 },
          height: { ideal: 1080, max: 1080 }
        },
        audio: false
      };
    } else {
      // Fallback to basic constraints with facingMode
      constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 1920, max: 1920 },
          height: { ideal: 1080, max: 1080 }
        },
        audio: false
      };
    }

    let stream: MediaStream;

    try {
      console.log('Attempting camera with constraints:', constraints);
      stream = await navigator.mediaDevices.getUserMedia(constraints);
    } catch (error) {
      console.warn('Primary constraints failed, trying fallback:', error);

      try {
        // Basic fallback
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 }
          },
          audio: false
        });
        console.log('Fallback camera succeeded');
      } catch (fallbackError) {
        console.error('All camera attempts failed:', fallbackError);
        throw fallbackError;
      }
    }

    currentStream.value = stream;

    if (videoRef.value) {
      videoRef.value.srcObject = stream;
      await videoRef.value.play();
      console.log('Video element started successfully');
    }

    // Update device ID based on actual stream
    const videoTrack = stream.getVideoTracks()[0];
    const settings = videoTrack.getSettings();
    if (settings.deviceId) {
      cameraStore.setDeviceId(settings.deviceId);
    }

    // Check camera capabilities
    const capabilities = videoTrack.getCapabilities();

    // Flash capability
    hasFlash.value = 'torch' in capabilities;
    console.log('Flash available:', hasFlash.value);

    // Focus capabilities
    if (capabilities.focusMode) {
      supportedFocusModes.value = capabilities.focusMode;
      console.log('Supported focus modes:', capabilities.focusMode);
    }

    if (capabilities.focusDistance) {
      console.log('Focus distance range:', capabilities.focusDistance);
    }

    console.log('Camera capabilities:', capabilities);

  } catch (error: any) {
    console.error('Error starting camera:', error);
    handleCameraError(error);
    throw error;
  }
};

const switchCamera = async () => {
  if (cameraStore.availableDevices.length <= 1) {
    console.log('Cannot switch camera: Only', cameraStore.availableDevices.length, 'device(s) available');
    return;
  }

  try {
    // Set processing state to show loading
    cameraStore.setProcessing(true);

    const currentDeviceId = cameraStore.deviceId;
    console.log('Current camera ID:', currentDeviceId);

    // Find front and back cameras specifically
    const backCamera = cameraStore.availableDevices.find(device =>
      device.label.toLowerCase().includes('back') ||
      device.label.toLowerCase().includes('rear') ||
      device.label.toLowerCase().includes('environment') ||
      device.label.toLowerCase().includes('facing back')
    );

    const frontCamera = cameraStore.availableDevices.find(device =>
      device.label.toLowerCase().includes('front') ||
      device.label.toLowerCase().includes('user') ||
      device.label.toLowerCase().includes('facing front') ||
      device.label.toLowerCase().includes('selfie')
    );

    console.log('Back camera found:', backCamera?.label || 'None');
    console.log('Front camera found:', frontCamera?.label || 'None');

    // Determine which camera to switch to
    let targetCamera;
    const isCurrentlyBack = currentDeviceId === backCamera?.deviceId;
    const isCurrentlyFront = currentDeviceId === frontCamera?.deviceId;

    if (isCurrentlyBack && frontCamera) {
      // Currently using back camera, switch to front
      targetCamera = frontCamera;
      console.log('Switching from back to front camera');
    } else if (isCurrentlyFront && backCamera) {
      // Currently using front camera, switch to back
      targetCamera = backCamera;
      console.log('Switching from front to back camera');
    } else {
      // If current camera is not clearly identified, prefer back camera
      targetCamera = backCamera || frontCamera;
      console.log('Current camera unclear, switching to:', targetCamera?.label);
    }

    if (!targetCamera) {
      console.log('No suitable camera found for switching');
      errorMessage.value = 'No other camera available for switching.';
      return;
    }

    console.log('Switching to camera:', targetCamera.label, 'ID:', targetCamera.deviceId);

    // Update device ID
    cameraStore.setDeviceId(targetCamera.deviceId);

    // Start the new camera
    await startCamera(targetCamera.deviceId);

    console.log('Camera switch successful');
  } catch (error) {
    console.error('Failed to switch camera:', error);
    errorMessage.value = 'Failed to switch camera. Using current camera.';
  } finally {
    // Always reset processing state
    cameraStore.setProcessing(false);
  }
};

const toggleFlash = async () => {
  if (!currentStream.value || !hasFlash.value) return;

  try {
    const videoTrack = currentStream.value.getVideoTracks()[0];
    await videoTrack.applyConstraints({
      advanced: [{ torch: !isFlashOn.value }] as any
    });
    isFlashOn.value = !isFlashOn.value;
  } catch (error) {
    console.error('Flash toggle error:', error);
  }
};

const captureImage = async () => {
  if (!videoRef.value || !canvasRef.value || cameraStore.isProcessing) return;

  try {
    cameraStore.setProcessing(true);

    const video = videoRef.value;
    const canvas = canvasRef.value;
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('Canvas context not available');
    }

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw the video frame to canvas
    if (isUsingFrontCamera.value) {
      // Flip front camera image horizontally
      ctx.scale(-1, 1);
      ctx.drawImage(video, -canvas.width, 0, canvas.width, canvas.height);
    } else {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    }

    // Calculate guide box coordinates relative to video dimensions
    const videoElement = video;
    const videoRect = videoElement.getBoundingClientRect();

    // Get the video's actual display dimensions
    const displayWidth = videoRect.width;
    const displayHeight = videoRect.height;

    // Calculate scaling factors between display and actual video resolution
    const scaleX = canvas.width / displayWidth;
    const scaleY = canvas.height / displayHeight;

    // Calculate guide box position in video coordinates
    const guideX = Math.round((displayWidth - guideWidth.value) / 2 * scaleX);
    const guideY = Math.round((displayHeight - guideHeight.value) / 2 * scaleY);
    const guideWidthScaled = Math.round(guideWidth.value * scaleX);
    const guideHeightScaled = Math.round(guideHeight.value * scaleY);

    // Create a new canvas for the cropped image
    const croppedCanvas = document.createElement('canvas');
    const croppedCtx = croppedCanvas.getContext('2d');

    if (!croppedCtx) {
      throw new Error('Cropped canvas context not available');
    }

    croppedCanvas.width = guideWidthScaled;
    croppedCanvas.height = guideHeightScaled;

    // Draw only the guided area to the cropped canvas
    croppedCtx.drawImage(
      canvas,
      guideX, guideY, guideWidthScaled, guideHeightScaled,
      0, 0, guideWidthScaled, guideHeightScaled
    );

    // Convert cropped canvas to blob
    croppedCanvas.toBlob(async (blob) => {
      if (blob) {
        const imageUrl = URL.createObjectURL(blob);
        cameraStore.setCapturedImage(imageUrl);

        console.log('Image captured and cropped successfully:', {
          imageUrl,
          width: guideWidthScaled,
          height: guideHeightScaled,
          blobSize: blob.size
        });

        // Reset processing state before navigation
        cameraStore.setProcessing(false);
        errorMessage.value = '';

        // Store the image URL in localStorage as backup
        localStorage.setItem('capturedImage', imageUrl);
        localStorage.setItem('capturedImageWidth', guideWidthScaled.toString());
        localStorage.setItem('capturedImageHeight', guideHeightScaled.toString());

        // Navigate to preview page
        try {
          await router.push({
            name: 'preview'
          });
        } catch (navError: any) {
          console.error('Navigation error details:', {
            error: navError,
            message: navError?.message,
            stack: navError?.stack
          });
          errorMessage.value = `Navigation failed: ${navError?.message || 'Unknown error'}`;
        }
      } else {
        console.error('Failed to create blob from canvas');
        errorMessage.value = 'Failed to process image. Please try again.';
        cameraStore.setProcessing(false);
      }
    }, 'image/jpeg', 0.92);

  } catch (error) {
    console.error('Capture error:', error);
    errorMessage.value = 'Failed to capture image. Please try again.';
    cameraStore.setProcessing(false);
  }
};

const updateGuideSize = () => {
  const width = window.innerWidth;
  const height = window.innerHeight;

  // Responsive guide sizing for vertical receipts (larger dimensions)
  if (width < 400) {
    // Mobile portrait - larger guide
    guideWidth.value = Math.min(width * 0.85, 340);
    guideHeight.value = Math.min(guideWidth.value * 1.5, height * 0.7);
  } else {
    // Desktop or wide mobile - much larger guide
    guideWidth.value = Math.min(380, width * 0.7);
    guideHeight.value = Math.min(guideWidth.value * 1.5, height * 0.8);
  }
};


// Lifecycle
onMounted(async () => {
  console.log('CameraCapture component mounted');
  updateGuideSize();
  window.addEventListener('resize', updateGuideSize);

  // Always show permission modal first for explicit user consent
  showPermissionModal.value = true;
  console.log('Permission modal shown');
});

onUnmounted(() => {
  window.removeEventListener('resize', updateGuideSize);

  // Stop camera stream
  if (currentStream.value) {
    currentStream.value.getTracks().forEach(track => track.stop());
  }

  // Reset store
  cameraStore.reset();
});
</script>

<style scoped>
/* Prevent unwanted zoom on mobile */
.btn {
  touch-action: manipulation;
}

/* Ensure video covers full screen */
video {
  object-fit: cover;
}

/* Guide frame animation */
@keyframes pulse-border {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 0.4;
  }
}

.guide-frame {
  animation: pulse-border 2s ease-in-out infinite;
}

/* Capture button press effect */
.btn-circle.btn-lg {
  transform-origin: center;
  transition: transform 0.1s ease;
}

.btn-circle.btn-lg:active {
  transform: scale(0.95);
}
</style>