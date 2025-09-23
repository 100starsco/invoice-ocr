import { apiClient } from './api';

export interface ImagePreprocessRequest {
  imageBase64: string;
  operations?: {
    deskew?: boolean;
    removeDistortion?: boolean;
    perspectiveCorrection?: boolean;
    enhanceContrast?: boolean;
  };
}

export interface ImagePreprocessResponse {
  processedImageBase64: string;
  metadata: {
    originalSize: { width: number; height: number };
    processedSize: { width: number; height: number };
    operations: string[];
  };
}

export class ImageService {
  private static instance: ImageService;

  private constructor() {}

  public static getInstance(): ImageService {
    if (!ImageService.instance) {
      ImageService.instance = new ImageService();
    }
    return ImageService.instance;
  }

  async preprocessImage(request: ImagePreprocessRequest): Promise<ImagePreprocessResponse> {
    const response = await apiClient.post<ImagePreprocessResponse>(
      '/images/preprocess',
      request
    );
    return response.data;
  }

  async uploadImage(file: File): Promise<{ url: string; id: string }> {
    const formData = new FormData();
    formData.append('image', file);

    const response = await apiClient.post<{ url: string; id: string }>(
      '/images/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async getImageUrl(imageId: string): Promise<string> {
    const response = await apiClient.get<{ url: string }>(`/images/${imageId}/url`);
    return response.data.url;
  }

  convertFileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = (error) => reject(error);
    });
  }

  convertBase64ToBlob(base64: string, mimeType: string = 'image/jpeg'): Blob {
    const byteCharacters = atob(base64.split(',')[1]);
    const byteNumbers = new Array(byteCharacters.length);

    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }

    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  }
}

export const imageService = ImageService.getInstance();