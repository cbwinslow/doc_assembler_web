import { apiClient } from './api';
import { User, LoginCredentials, RegisterCredentials, ApiResponse } from '@/types';

export interface AuthResponse {
  user: User;
  token: string;
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    
    if (response.success && response.data) {
      apiClient.setAuthToken(response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    
    return response.data;
  }

  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', credentials);
    
    if (response.success && response.data) {
      apiClient.setAuthToken(response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Even if the API call fails, we should clear local storage
      console.error('Logout API call failed:', error);
    } finally {
      apiClient.clearAuthToken();
    }
  }

  async refreshToken(): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/refresh');
    
    if (response.success && response.data) {
      apiClient.setAuthToken(response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    
    if (response.success && response.data) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    
    return response.data;
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await apiClient.patch<User>('/auth/profile', data);
    
    if (response.success && response.data) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    
    return response.data;
  }

  async changePassword(data: { currentPassword: string; newPassword: string }): Promise<void> {
    await apiClient.post('/auth/change-password', data);
  }

  async forgotPassword(email: string): Promise<void> {
    await apiClient.post('/auth/forgot-password', { email });
  }

  async resetPassword(data: { token: string; password: string }): Promise<void> {
    await apiClient.post('/auth/reset-password', data);
  }

  async verifyEmail(token: string): Promise<void> {
    await apiClient.post('/auth/verify-email', { token });
  }

  async resendVerificationEmail(): Promise<void> {
    await apiClient.post('/auth/resend-verification');
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = apiClient.getAuthToken();
    const user = this.getStoredUser();
    return !!(token && user);
  }

  // Get stored user from localStorage
  getStoredUser(): User | null {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Error parsing stored user:', error);
      return null;
    }
  }

  // Get stored token
  getStoredToken(): string | null {
    return apiClient.getAuthToken();
  }

  // Clear all auth data
  clearAuthData(): void {
    apiClient.clearAuthToken();
  }
}

export const authService = new AuthService();
export default authService;

