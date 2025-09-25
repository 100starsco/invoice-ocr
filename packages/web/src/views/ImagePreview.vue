<template>
  <div class="min-h-screen bg-gray-900 flex flex-col">
    <!-- Header -->
    <div class="bg-black bg-opacity-50 p-4">
      <div class="flex justify-between items-center text-white">
        <button
          @click="goBack"
          class="btn btn-ghost btn-sm btn-circle"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
          </svg>
        </button>

        <h1 class="text-lg font-semibold">Preview</h1>

        <div class="w-10"></div>
      </div>
    </div>

    <!-- Image Preview -->
    <div class="flex-1 flex items-center justify-center p-4">
      <div class="w-full max-w-md">
        <!-- Loading State -->
        <div v-if="isProcessing" class="text-center text-white">
          <div class="loading loading-spinner loading-lg mb-4"></div>
          <p>Processing image...</p>
        </div>

        <!-- Image Display -->
        <div v-else-if="processedImageUrl" class="space-y-4">
          <!-- Cropped Image -->
          <div class="bg-white rounded-lg p-4">
            <img
              :src="processedImageUrl"
              :alt="'Cropped invoice'"
              class="w-full h-auto rounded border border-gray-200 shadow-lg"
              :style="`max-height: ${maxImageHeight}px`"
            />
          </div>

          <!-- Image Info -->
          <div class="bg-black bg-opacity-50 rounded-lg p-3 text-white text-sm">
            <div class="flex justify-between">
              <span>Size:</span>
              <span>{{ imageWidth }} × {{ imageHeight }}px</span>
            </div>
            <div class="flex justify-between mt-1">
              <span>Quality:</span>
              <span>{{ quality }}%</span>
            </div>
          </div>

        </div>

        <!-- Error State -->
        <div v-else class="text-center text-white">
          <svg class="w-16 h-16 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
          </svg>
          <p>Unable to load image</p>
          <p class="text-sm text-gray-400 mt-2">Please try capturing again</p>
        </div>
      </div>
    </div>

    <!-- Bottom Controls -->
    <div class="bg-black bg-opacity-50 p-4">
      <div class="flex space-x-3">
        <!-- Retake Button -->
        <button
          @click="retakePhoto"
          class="btn btn-outline btn-sm flex-1"
          :disabled="isProcessing"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 616 0z"></path>
          </svg>
          Retake
        </button>

        <!-- Send to Chat Button -->
        <button
          @click="sendToChat"
          :disabled="!processedImageUrl || isProcessing || isSending"
          class="btn btn-primary btn-sm flex-1"
        >
          <div v-if="isSending" class="loading loading-spinner loading-sm mr-2"></div>
          <svg v-else class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
          </svg>
          {{ isSending ? 'Sending...' : 'Send to Chat' }}
        </button>
      </div>
    </div>

    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 m-4 max-w-sm text-center">
        <div class="mb-4">
          <svg class="w-16 h-16 text-green-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <h3 class="text-lg font-semibold mb-2">Image Sent!</h3>
        <p class="text-gray-600 mb-4">Your invoice has been sent to the LINE chat successfully.</p>
        <div class="flex space-x-3">
          <button @click="closeAndReturn" class="btn btn-primary flex-1">Done</button>
          <button @click="retakePhoto" class="btn btn-outline flex-1">Take Another</button>
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
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { imageProcessor } from '@/utils/imageProcessing';
import { liffManager } from '@/utils/liff';

const route = useRoute();
const router = useRouter();

// Refs
const processedImageUrl = ref<string>('');
const originalImageUrl = ref<string>('');
const isProcessing = ref(false);
const isSending = ref(false);
const showSuccessModal = ref(false);
const errorMessage = ref('');
const imageWidth = ref(0);
const imageHeight = ref(0);
const quality = ref(92);

// Computed
const maxImageHeight = computed(() => {
  return Math.min(window.innerHeight * 0.6, 500);
});

// Methods
const goBack = () => {
  // Clean up blob URLs
  if (originalImageUrl.value) {
    URL.revokeObjectURL(originalImageUrl.value);
  }
  if (processedImageUrl.value && processedImageUrl.value !== originalImageUrl.value) {
    URL.revokeObjectURL(processedImageUrl.value);
  }
  router.go(-1);
};


const retakePhoto = () => {
  // Clean up blob URLs
  if (originalImageUrl.value) {
    URL.revokeObjectURL(originalImageUrl.value);
  }
  if (processedImageUrl.value && processedImageUrl.value !== originalImageUrl.value) {
    URL.revokeObjectURL(processedImageUrl.value);
  }
  router.push({ name: 'camera' });
};

// Helper function to resize image for LINE compatibility
const resizeImageForLine = async (imageUrl: string, maxDimension = 800): Promise<Blob> => {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      let { width, height } = img;

      if (width > maxDimension || height > maxDimension) {
        if (width > height) {
          height = (height * maxDimension) / width;
          width = maxDimension;
        } else {
          width = (width * maxDimension) / height;
          height = maxDimension;
        }
      }

      canvas.width = width;
      canvas.height = height;
      ctx?.drawImage(img, 0, 0, width, height);

      canvas.toBlob((resizedBlob) => {
        resolve(resizedBlob!);
      }, 'image/jpeg', 0.7); // Even lower quality for smaller size
    };
    img.src = imageUrl;
  });
};

const sendToChat = async () => {
  if (!processedImageUrl.value || isSending.value) return;

  try {
    isSending.value = true;
    errorMessage.value = '';

    console.log('=== Starting sendToChat with shareTargetPicker ===');

    // Initialize LIFF if not already done
    await liffManager.init();

    // Check if we're in LINE client
    if (!liffManager.isInClient()) {
      // For development/testing purposes, create a mock user
      if (import.meta.env.VITE_ENV === 'development') {
        console.warn('LIFF not available - using mock user for development');
        const mockProfile = {
          userId: 'dev_user_' + Date.now(),
          displayName: 'Development User',
          pictureUrl: '',
          statusMessage: ''
        };

        // Continue with upload using mock profile
        const resizedBlob = await resizeImageForLine(processedImageUrl.value);

        const formData = new FormData();
        formData.append('image', resizedBlob, 'invoice.jpg');
        formData.append('userId', mockProfile.userId);

        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3002';

        const uploadResponse = await fetch(`${apiUrl}/api/liff/upload-image`, {
          method: 'POST',
          body: formData
        });

        if (!uploadResponse.ok) {
          const errorText = await uploadResponse.text();
          console.error('Development upload error:', uploadResponse.status, errorText);
          throw new Error(`Upload failed: ${uploadResponse.status}`);
        }

        const uploadData = await uploadResponse.json();
        console.log('Development mode: Image uploaded successfully', uploadData);

        showSuccessModal.value = true;
        return;
      } else {
        throw new Error('This feature is only available in LINE app');
      }
    }

    // Ensure user is authenticated
    await liffManager.ensureAuthenticated();
    console.log('✓ User authenticated');

    // Get LINE user profile
    const profile = await liffManager.getProfile();
    console.log('✓ Got user profile:', profile?.displayName);

    if (!profile?.userId) {
      throw new Error('Unable to get user profile');
    }

    console.log('=== Starting image upload ===');

    // Resize image for LINE compatibility
    const resizedBlob = await resizeImageForLine(processedImageUrl.value, 800);
    console.log('✓ Image resized for LINE compatibility, size:', resizedBlob.size, 'bytes');

    // Create FormData for upload
    const formData = new FormData();
    formData.append('image', resizedBlob, `invoice_${Date.now()}.jpg`);
    formData.append('userId', profile.userId);

    // Use correct API URL based on environment
    const isDev = import.meta.env.VITE_ENV === 'development';
    const apiUrl = isDev ? import.meta.env.VITE_API_URL : import.meta.env.VITE_PRODUCTION_API_URL;
    const uploadUrl = `${apiUrl}/api/liff/upload-image`;

    const uploadResponse = await fetch(uploadUrl, {
      method: 'POST',
      body: formData,
    });

    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text();
      console.error('Upload failed:', uploadResponse.status, errorText);
      throw new Error(`Upload failed: ${uploadResponse.status} ${errorText}`);
    }

    const uploadResult = await uploadResponse.json();
    console.log('✓ Upload successful:', uploadResult);

    // Use direct Spaces URL for LINE messaging
    const imageUrl = uploadResult.url;
    console.log('Using image URL for LINE:', imageUrl);

    // === PRIMARY METHOD: shareTargetPicker with Image ===
    console.log('=== Using shareTargetPicker (Primary Method) ===');

    const imageMessage = {
      type: 'image',
      originalContentUrl: imageUrl,
      previewImageUrl: imageUrl
    };

    try {
      await liffManager.shareTargetPicker([imageMessage]);
      console.log('✓ shareTargetPicker with image sent successfully!');
      showSuccessModal.value = true;
      return;
    } catch (shareError: any) {
      console.error('shareTargetPicker with image failed:', shareError.message);

      // Try with smaller image if size might be the issue
      if (shareError.message.includes('size') || shareError.code === 400) {
        console.log('=== Trying shareTargetPicker with smaller image ===');

        const smallerBlob = await resizeImageForLine(processedImageUrl.value, 600);
        console.log('Smaller image size:', smallerBlob.size, 'bytes');

        const smallerFormData = new FormData();
        smallerFormData.append('image', smallerBlob, `invoice_small_${Date.now()}.jpg`);
        smallerFormData.append('userId', profile.userId);

        const smallerUploadResponse = await fetch(uploadUrl, {
          method: 'POST',
          body: smallerFormData,
        });

        if (smallerUploadResponse.ok) {
          const smallerUploadResult = await smallerUploadResponse.json();
          const smallerImageUrl = smallerUploadResult.url;

          const smallerImageMessage = {
            type: 'image',
            originalContentUrl: smallerImageUrl,
            previewImageUrl: smallerImageUrl
          };

          try {
            await liffManager.shareTargetPicker([smallerImageMessage]);
            console.log('✓ shareTargetPicker with smaller image sent successfully!');
            showSuccessModal.value = true;
            return;
          } catch (smallerError: any) {
            console.error('shareTargetPicker with smaller image also failed:', smallerError.message);
          }
        }
      }

      // Fallback to text message with image link
      console.log('=== Fallback: shareTargetPicker with text message ===');
      try {
        const textMessage = {
          type: 'text',
          text: `📸 Invoice uploaded successfully!\nView image: ${imageUrl}`
        };

        await liffManager.shareTargetPicker([textMessage]);
        console.log('✓ shareTargetPicker with text sent successfully!');
        showSuccessModal.value = true;
        return;
      } catch (textError: any) {
        console.error('shareTargetPicker with text also failed:', textError.message);

        // Final fallback to sendMessages if shareTargetPicker completely fails
        console.log('=== Final fallback: sendMessages ===');
        try {
          await liffManager.sendMessages([imageMessage]);
          console.log('✓ sendMessages fallback successful!');
          showSuccessModal.value = true;
          return;
        } catch (sendError: any) {
          console.error('sendMessages fallback also failed:', sendError.message);
          throw shareError; // Throw the original shareTargetPicker error
        }
      }
    }

  } catch (error: any) {
    console.error('=== sendToChat Error ===');
    console.error('Error message:', error.message);
    console.error('Error code:', error.code);
    console.error('Error detail:', error.detail);

    if (error.message === 'REDIRECTING_TO_LOGIN') {
      console.log('Redirecting to LINE login...');
      return;
    }

    errorMessage.value = `LINE Error: ${error.message || 'Failed to send image to chat'}`;
  } finally {
    isSending.value = false;
  }
};

const closeAndReturn = () => {
  showSuccessModal.value = false;
  // Clean up blob URLs
  if (originalImageUrl.value) {
    URL.revokeObjectURL(originalImageUrl.value);
  }
  if (processedImageUrl.value && processedImageUrl.value !== originalImageUrl.value) {
    URL.revokeObjectURL(processedImageUrl.value);
  }
  // Navigate to home or close LIFF window
  if (liffManager.isInClient()) {
    liffManager.closeWindow();
  } else {
    router.push({ name: 'home' });
  }
};

// Lifecycle
onMounted(async () => {
  // Try to get image URL from route query first, then fall back to localStorage
  let imageUrl = route.query.image as string;
  let width = parseInt(route.query.width as string || '0');
  let height = parseInt(route.query.height as string || '0');

  // If not in query params, try localStorage
  if (!imageUrl) {
    imageUrl = localStorage.getItem('capturedImage') || '';
    width = parseInt(localStorage.getItem('capturedImageWidth') || '0');
    height = parseInt(localStorage.getItem('capturedImageHeight') || '0');
  }

  if (!imageUrl) {
    errorMessage.value = 'No image provided';
    console.error('No image URL found in query or localStorage');
    return;
  }

  originalImageUrl.value = imageUrl;
  processedImageUrl.value = imageUrl;
  imageWidth.value = width || 320;  // Default width
  imageHeight.value = height || 480; // Default height

  console.log('ImagePreview loaded with image:', {
    imageUrl,
    width: imageWidth.value,
    height: imageHeight.value
  });
});
</script>

<style scoped>
/* Prevent unwanted zoom on mobile */
.btn {
  touch-action: manipulation;
}

/* Image container styles */
img {
  object-fit: contain;
}

/* Range slider styling */
.range {
  background: rgba(255, 255, 255, 0.2);
}

/* Modal backdrop */
.absolute.inset-0 {
  backdrop-filter: blur(4px);
}
</style>