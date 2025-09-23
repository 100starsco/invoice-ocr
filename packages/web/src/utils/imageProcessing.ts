const Pica = require('pica');

export interface ResizeOptions {
  width?: number;
  height?: number;
  quality?: 1 | 2 | 3;
  unsharpAmount?: number;
  unsharpRadius?: number;
  unsharpThreshold?: number;
}

export interface ProcessingResult {
  dataUrl: string;
  blob: Blob;
  width: number;
  height: number;
}

export class ImageProcessor {
  private pica: any;

  constructor() {
    this.pica = new Pica();
  }

  async resizeImage(
    source: HTMLImageElement | HTMLCanvasElement,
    options: ResizeOptions = {}
  ): Promise<ProcessingResult> {
    const sourceWidth = source instanceof HTMLImageElement ? source.naturalWidth : source.width;
    const sourceHeight = source instanceof HTMLImageElement ? source.naturalHeight : source.height;

    const targetWidth = options.width || sourceWidth;
    const targetHeight = options.height || sourceHeight;

    const canvas = document.createElement('canvas');
    canvas.width = targetWidth;
    canvas.height = targetHeight;

    await this.pica.resize(source, canvas, {
      quality: options.quality || 2,
      unsharpAmount: options.unsharpAmount || 0,
      unsharpRadius: options.unsharpRadius || 0,
      unsharpThreshold: options.unsharpThreshold || 0,
    });

    const blob = await this.pica.toBlob(canvas, 'image/jpeg', 0.92);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);

    return {
      dataUrl,
      blob,
      width: targetWidth,
      height: targetHeight,
    };
  }

  async loadImage(src: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });
  }

  detectEdges(canvas: HTMLCanvasElement): ImageData | null {
    const context = canvas.getContext('2d');
    if (!context) return null;

    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    return imageData;
  }

  applyGrayscale(canvas: HTMLCanvasElement): void {
    const context = canvas.getContext('2d');
    if (!context) return;

    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    for (let i = 0; i < data.length; i += 4) {
      const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
      data[i] = gray;
      data[i + 1] = gray;
      data[i + 2] = gray;
    }

    context.putImageData(imageData, 0, 0);
  }

  adjustContrast(canvas: HTMLCanvasElement, amount: number): void {
    const context = canvas.getContext('2d');
    if (!context) return;

    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    const factor = (259 * (amount + 255)) / (255 * (259 - amount));

    for (let i = 0; i < data.length; i += 4) {
      data[i] = factor * (data[i] - 128) + 128;
      data[i + 1] = factor * (data[i + 1] - 128) + 128;
      data[i + 2] = factor * (data[i + 2] - 128) + 128;
    }

    context.putImageData(imageData, 0, 0);
  }

  adjustBrightness(canvas: HTMLCanvasElement, amount: number): void {
    const context = canvas.getContext('2d');
    if (!context) return;

    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    for (let i = 0; i < data.length; i += 4) {
      data[i] += amount;
      data[i + 1] += amount;
      data[i + 2] += amount;
    }

    context.putImageData(imageData, 0, 0);
  }

  cropImage(
    canvas: HTMLCanvasElement,
    x: number,
    y: number,
    width: number,
    height: number
  ): HTMLCanvasElement {
    const newCanvas = document.createElement('canvas');
    const context = newCanvas.getContext('2d');

    if (!context) return canvas;

    newCanvas.width = width;
    newCanvas.height = height;
    context.drawImage(canvas, x, y, width, height, 0, 0, width, height);

    return newCanvas;
  }

  rotateImage(canvas: HTMLCanvasElement, degrees: number): HTMLCanvasElement {
    const radians = (degrees * Math.PI) / 180;
    const newCanvas = document.createElement('canvas');
    const context = newCanvas.getContext('2d');

    if (!context) return canvas;

    const width = canvas.width;
    const height = canvas.height;

    newCanvas.width = Math.abs(width * Math.cos(radians)) + Math.abs(height * Math.sin(radians));
    newCanvas.height = Math.abs(width * Math.sin(radians)) + Math.abs(height * Math.cos(radians));

    context.translate(newCanvas.width / 2, newCanvas.height / 2);
    context.rotate(radians);
    context.drawImage(canvas, -width / 2, -height / 2);

    return newCanvas;
  }
}

export const imageProcessor = new ImageProcessor();