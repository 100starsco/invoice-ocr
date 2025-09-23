import { apiClient } from './api';
import type { OcrResult } from '@/stores';

export interface OcrProcessRequest {
  imageBase64?: string;
  imageUrl?: string;
  userId?: string;
  metadata?: Record<string, any>;
}

export interface OcrCorrection {
  fieldName: string;
  oldValue: string | number;
  newValue: string | number;
  confidence?: number;
}

export class OcrService {
  private static instance: OcrService;

  private constructor() {}

  public static getInstance(): OcrService {
    if (!OcrService.instance) {
      OcrService.instance = new OcrService();
    }
    return OcrService.instance;
  }

  async processImage(request: OcrProcessRequest): Promise<OcrResult> {
    const response = await apiClient.post<OcrResult>('/ocr/process', request);
    return response.data;
  }

  async getResult(resultId: string): Promise<OcrResult> {
    const response = await apiClient.get<OcrResult>(`/ocr/results/${resultId}`);
    return response.data;
  }

  async getResults(userId?: string): Promise<OcrResult[]> {
    const params = userId ? { userId } : {};
    const response = await apiClient.get<OcrResult[]>('/ocr/results', { params });
    return response.data;
  }

  async submitCorrections(
    resultId: string,
    corrections: OcrCorrection[]
  ): Promise<OcrResult> {
    const response = await apiClient.put<OcrResult>(
      `/ocr/results/${resultId}/corrections`,
      { corrections }
    );
    return response.data;
  }

  async deleteResult(resultId: string): Promise<void> {
    await apiClient.delete(`/ocr/results/${resultId}`);
  }

  async getReviewLink(resultId: string): Promise<{ url: string }> {
    const response = await apiClient.get<{ url: string }>(
      `/ocr/results/${resultId}/review-link`
    );
    return response.data;
  }
}

export const ocrService = OcrService.getInstance();