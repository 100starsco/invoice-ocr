import { ref } from 'vue';
import { imageProcessor } from '@/utils';
import type { ResizeOptions } from '@/utils';

export function useImageProcessing() {
  const isProcessing = ref(false);
  const error = ref<string | null>(null);

  const resizeImage = async (
    source: HTMLImageElement | HTMLCanvasElement,
    options: ResizeOptions = {}
  ) => {
    isProcessing.value = true;
    error.value = null;

    try {
      const result = await imageProcessor.resizeImage(source, options);
      return result;
    } catch (err: any) {
      error.value = err.message || 'Failed to resize image';
      throw err;
    } finally {
      isProcessing.value = false;
    }
  };

  const loadImage = async (src: string) => {
    isProcessing.value = true;
    error.value = null;

    try {
      const image = await imageProcessor.loadImage(src);
      return image;
    } catch (err: any) {
      error.value = err.message || 'Failed to load image';
      throw err;
    } finally {
      isProcessing.value = false;
    }
  };

  const processImage = async (canvas: HTMLCanvasElement, operations: {
    grayscale?: boolean;
    contrast?: number;
    brightness?: number;
    rotate?: number;
  }) => {
    isProcessing.value = true;
    error.value = null;

    try {
      if (operations.grayscale) {
        imageProcessor.applyGrayscale(canvas);
      }
      if (operations.contrast !== undefined) {
        imageProcessor.adjustContrast(canvas, operations.contrast);
      }
      if (operations.brightness !== undefined) {
        imageProcessor.adjustBrightness(canvas, operations.brightness);
      }
      if (operations.rotate !== undefined) {
        return imageProcessor.rotateImage(canvas, operations.rotate);
      }
      return canvas;
    } catch (err: any) {
      error.value = err.message || 'Failed to process image';
      throw err;
    } finally {
      isProcessing.value = false;
    }
  };

  return {
    isProcessing,
    error,
    resizeImage,
    loadImage,
    processImage,
  };
}