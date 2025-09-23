export interface CameraOptions {
  video?: boolean | MediaTrackConstraints;
  audio?: boolean;
  preferredDevice?: string;
}

export interface CaptureOptions {
  quality?: number;
  format?: 'jpeg' | 'png' | 'webp';
  maxWidth?: number;
  maxHeight?: number;
}

export class CameraManager {
  private stream: MediaStream | null = null;
  private videoElement: HTMLVideoElement | null = null;

  async requestPermission(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      console.error('Camera permission denied:', error);
      return false;
    }
  }

  async getAvailableDevices(): Promise<MediaDeviceInfo[]> {
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter(device => device.kind === 'videoinput');
  }

  async startCamera(
    videoElement: HTMLVideoElement,
    options: CameraOptions = {}
  ): Promise<void> {
    this.videoElement = videoElement;
    const constraints: MediaStreamConstraints = {
      video: options.video !== undefined ? options.video : true,
      audio: options.audio || false,
    };

    this.stream = await navigator.mediaDevices.getUserMedia(constraints);
    videoElement.srcObject = this.stream;
  }

  async stopCamera(): Promise<void> {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    if (this.videoElement) {
      this.videoElement.srcObject = null;
      this.videoElement = null;
    }
  }

  captureImage(options: CaptureOptions = {}): string | null {
    if (!this.videoElement) return null;

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (!context) return null;

    canvas.width = this.videoElement.videoWidth;
    canvas.height = this.videoElement.videoHeight;
    context.drawImage(this.videoElement, 0, 0, canvas.width, canvas.height);

    const format = `image/${options.format || 'jpeg'}`;
    const quality = options.quality || 0.92;

    return canvas.toDataURL(format, quality);
  }

  async switchCamera(deviceId: string): Promise<void> {
    if (!this.videoElement) return;

    await this.stopCamera();
    await this.startCamera(this.videoElement, {
      video: { deviceId: { exact: deviceId } },
    });
  }
}

export const cameraManager = new CameraManager();