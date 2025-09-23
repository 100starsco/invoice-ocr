import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface OcrField {
  value: string | number | Date;
  confidence: number;
}

export interface OcrLineItem {
  description: OcrField;
  amount: OcrField;
}

export interface OcrResult {
  id: string;
  invoiceId: string;
  vendor: OcrField;
  invoiceNumber: OcrField;
  date: OcrField;
  totalAmount: OcrField;
  lineItems: OcrLineItem[];
  overallConfidence: number;
  originalImageUrl?: string;
  processedImageUrl?: string;
  createdAt: Date;
  updatedAt: Date;
}

export const useOcrStore = defineStore('ocr', () => {
  const currentResult = ref<OcrResult | null>(null);
  const results = ref<OcrResult[]>([]);
  const isProcessing = ref(false);
  const error = ref<string | null>(null);

  const setCurrentResult = (result: OcrResult | null) => {
    currentResult.value = result;
  };

  const addResult = (result: OcrResult) => {
    results.value.unshift(result);
  };

  const updateResult = (id: string, updates: Partial<OcrResult>) => {
    const index = results.value.findIndex(r => r.id === id);
    if (index !== -1) {
      results.value[index] = { ...results.value[index], ...updates };
    }
    if (currentResult.value?.id === id) {
      currentResult.value = { ...currentResult.value, ...updates };
    }
  };

  const setProcessing = (processing: boolean) => {
    isProcessing.value = processing;
  };

  const setError = (errorMessage: string | null) => {
    error.value = errorMessage;
  };

  const clearResults = () => {
    results.value = [];
    currentResult.value = null;
  };

  return {
    currentResult,
    results,
    isProcessing,
    error,
    setCurrentResult,
    addResult,
    updateResult,
    setProcessing,
    setError,
    clearResults,
  };
});