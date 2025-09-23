import liff from '@line/liff';
import { config } from '@/config';

export interface LiffProfile {
  userId: string;
  displayName: string;
  pictureUrl?: string;
  statusMessage?: string;
}

export class LiffManager {
  private initialized = false;

  async init(): Promise<void> {
    if (this.initialized) return;

    try {
      await liff.init({ liffId: config.liff.liffId });
      this.initialized = true;
    } catch (error) {
      console.error('LIFF initialization failed:', error);
      throw error;
    }
  }

  isLoggedIn(): boolean {
    return liff.isLoggedIn();
  }

  async login(redirectUri?: string): Promise<void> {
    if (!this.initialized) await this.init();
    liff.login({ redirectUri });
  }

  logout(): void {
    liff.logout();
  }

  async getProfile(): Promise<LiffProfile | null> {
    if (!this.initialized) await this.init();
    if (!this.isLoggedIn()) return null;

    try {
      const profile = await liff.getProfile();
      return profile;
    } catch (error) {
      console.error('Failed to get LIFF profile:', error);
      return null;
    }
  }

  async getAccessToken(): Promise<string | null> {
    if (!this.initialized) await this.init();
    return liff.getAccessToken();
  }

  async sendMessages(messages: any[]): Promise<void> {
    if (!this.initialized) await this.init();
    if (!liff.isInClient()) {
      throw new Error('This function is only available in LIFF browser');
    }

    await liff.sendMessages(messages);
  }

  isInClient(): boolean {
    return liff.isInClient();
  }

  getOS(): string | null {
    const os = liff.getOS();
    return os ?? null;
  }

  getLanguage(): string {
    return liff.getLanguage();
  }

  getVersion(): string {
    return liff.getVersion();
  }

  async shareTargetPicker(messages: any[]): Promise<void> {
    if (!this.initialized) await this.init();
    await liff.shareTargetPicker(messages);
  }

  closeWindow(): void {
    liff.closeWindow();
  }
}

export const liffManager = new LiffManager();