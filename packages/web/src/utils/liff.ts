import liff from '@line/liff';

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

    console.log('=== LIFF Initialization Starting ===');
    console.log('Environment:', import.meta.env.VITE_ENV);
    console.log('Current URL:', window.location.href);
    console.log('User Agent:', navigator.userAgent);
    console.log('Running in LINE:', this.isRunningInLine());

    try {
      // Get LIFF ID from environment variable
      const liffId = import.meta.env.VITE_LIFF_ID || '2008146619-DbEmag6j';
      console.log('Using LIFF ID:', liffId);

      // In development mode outside LINE app, skip actual LIFF initialization
      if (import.meta.env.VITE_ENV === 'development' && !this.isRunningInLine()) {
        console.warn('LIFF initialization skipped - running in development mode outside LINE app');
        this.initialized = true;
        return;
      }

      console.log('Calling liff.init with LIFF ID:', liffId);
      await liff.init({ liffId });
      console.log('✓ LIFF initialization successful');

      // Log additional LIFF state after successful initialization
      console.log('LIFF state after init:');
      console.log('- isInClient:', liff.isInClient());
      console.log('- isLoggedIn:', liff.isLoggedIn());
      console.log('- getOS:', liff.getOS());
      console.log('- getLanguage:', liff.getLanguage());
      console.log('- getVersion:', liff.getVersion());

      this.initialized = true;
    } catch (error: any) {
      console.error('=== LIFF Initialization Error ===');
      console.error('Init error type:', typeof error);
      console.error('Init error message:', error.message);
      console.error('Init error name:', error.name);
      console.error('Init error code:', error.code);
      console.error('Init error detail:', error.detail);
      console.error('Init error stack:', error.stack);
      console.error('Init full error object:', JSON.stringify(error, Object.getOwnPropertyNames(error), 2));

      // In development mode, don't throw errors for LIFF init failures
      if (import.meta.env.VITE_ENV === 'development') {
        console.warn('LIFF initialization failed in development mode - continuing with mock functionality');
        this.initialized = true;
        return;
      }

      throw error;
    }
  }

  private isRunningInLine(): boolean {
    // Check if running inside LINE browser
    const userAgent = navigator.userAgent.toLowerCase();
    return userAgent.includes('line/') || userAgent.includes('liff/');
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

    // Check if user is logged in, if not, trigger login
    if (!this.isLoggedIn()) {
      throw new Error('USER_NOT_LOGGED_IN');
    }

    try {
      const profile = await liff.getProfile();
      return profile;
    } catch (error) {
      console.error('Failed to get LIFF profile:', error);
      throw error;
    }
  }

  async ensureAuthenticated(): Promise<void> {
    if (!this.initialized) await this.init();

    console.log('=== LIFF Authentication Check ===');
    console.log('LIFF initialized:', this.initialized);
    console.log('LIFF isLoggedIn:', this.isLoggedIn());
    console.log('LIFF isInClient:', this.isInClient());
    console.log('Current URL:', window.location.href);
    console.log('LIFF ID:', import.meta.env.VITE_LIFF_ID);

    if (!this.isLoggedIn()) {
      console.log('=== User not logged in, initiating login ===');

      // Clean redirect URI - remove query parameters that might cause issues
      const baseUrl = `${window.location.protocol}//${window.location.host}${window.location.pathname}`;
      console.log('Clean redirect URI:', baseUrl);

      try {
        console.log('Calling liff.login with redirect URI:', baseUrl);
        liff.login({ redirectUri: baseUrl });
        throw new Error('REDIRECTING_TO_LOGIN');
      } catch (loginError: any) {
        console.error('=== LIFF Login Error ===');
        console.error('Login error type:', typeof loginError);
        console.error('Login error message:', loginError.message);
        console.error('Login error name:', loginError.name);
        console.error('Login error code:', loginError.code);
        console.error('Login error detail:', loginError.detail);
        console.error('Login error stack:', loginError.stack);
        console.error('Login full error object:', JSON.stringify(loginError, Object.getOwnPropertyNames(loginError), 2));

        // If it's our expected redirect error, re-throw it
        if (loginError.message === 'REDIRECTING_TO_LOGIN') {
          throw loginError;
        }

        // Otherwise, it's a real login error
        throw new Error(`LINE Login failed: ${loginError.message || 'Unknown error'}`);
      }
    }

    console.log('✓ User is already authenticated');
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

    console.log('sendMessages called with:', messages);

    try {
      await liff.sendMessages(messages);
      console.log('sendMessages completed successfully');
    } catch (error: any) {
      console.error('sendMessages failed:', error);

      // Extract key error details
      if (error.code) {
        console.error('sendMessages error code:', error.code);
      }
      if (error.detail) {
        console.error('sendMessages error detail:', error.detail);
      }

      throw error;
    }
  }

  isInClient(): boolean {
    // In development mode, check if we're actually running in LINE
    if (import.meta.env.VITE_ENV === 'development' && !this.isRunningInLine()) {
      return false;
    }

    try {
      return liff.isInClient();
    } catch (error) {
      // If LIFF not initialized or available, return false
      console.warn('isInClient() failed - LIFF not available:', error);
      return false;
    }
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

    // Validate messages before sending
    if (!messages || messages.length === 0) {
      throw new Error('No messages provided to shareTargetPicker');
    }

    console.log('shareTargetPicker called with messages:', messages);

    // Validate message format
    for (const message of messages) {
      if (!message.type) {
        throw new Error('Message must have a type property');
      }

      if (message.type === 'image') {
        if (!message.originalContentUrl) {
          throw new Error('Image message must have originalContentUrl');
        }
        if (!message.previewImageUrl) {
          throw new Error('Image message must have previewImageUrl');
        }

        // Validate URLs are HTTPS
        if (!message.originalContentUrl.startsWith('https://')) {
          throw new Error('originalContentUrl must be HTTPS');
        }
        if (!message.previewImageUrl.startsWith('https://')) {
          throw new Error('previewImageUrl must be HTTPS');
        }
      }

      if (message.type === 'text') {
        if (!message.text || message.text.trim() === '') {
          throw new Error('Text message must have non-empty text property');
        }
      }
    }

    try {
      await liff.shareTargetPicker(messages);
      console.log('shareTargetPicker completed successfully');
    } catch (error: any) {
      console.error('shareTargetPicker failed:', error);

      // Enhanced error logging for shareTargetPicker
      if (error.code) {
        console.error('shareTargetPicker error code:', error.code);
      }
      if (error.detail) {
        console.error('shareTargetPicker error detail:', error.detail);
      }

      // Specific guidance for shareTargetPicker errors
      if (error.code === 400) {
        console.error('shareTargetPicker Bad Request - Common causes:');
        console.error('1. Invalid message format or structure');
        console.error('2. Image URLs not accessible or not HTTPS');
        console.error('3. Message content too large');
        console.error('4. LIFF app not properly configured for sharing');
      } else if (error.code === 403) {
        console.error('shareTargetPicker Forbidden - User may have denied permission');
      }

      throw error;
    }
  }

  closeWindow(): void {
    liff.closeWindow();
  }
}

export const liffManager = new LiffManager();