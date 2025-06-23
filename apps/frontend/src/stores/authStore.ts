import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient, endpoints } from '../services/api';
import type { AuthStore, User, LoginCredentials, RegisterData } from '../types';

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true });
        
        try {
          const response = await apiClient.post<{
            user: User;
            token: string;
          }>(endpoints.auth.login, credentials);

          if (response.success && response.data) {
            const { user, token } = response.data;
            
            // Store token in localStorage for API calls
            localStorage.setItem('auth_token', token);
            
            set({
              user,
              token,
              isAuthenticated: true,
              isLoading: false,
            });
          } else {
            throw new Error(response.error || 'Login failed');
          }
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true });
        
        try {
          const response = await apiClient.post<{
            user: User;
            token: string;
          }>(endpoints.auth.register, data);

          if (response.success && response.data) {
            const { user, token } = response.data;
            
            // Store token in localStorage for API calls
            localStorage.setItem('auth_token', token);
            
            set({
              user,
              token,
              isAuthenticated: true,
              isLoading: false,
            });
          } else {
            throw new Error(response.error || 'Registration failed');
          }
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        // Clear token from localStorage
        localStorage.removeItem('auth_token');
        
        // Clear state
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });

        // Optional: Call logout endpoint to invalidate token on server
        try {
          apiClient.post(endpoints.auth.logout);
        } catch (error) {
          console.warn('Failed to logout on server:', error);
        }
      },

      refreshToken: async () => {
        const { token } = get();
        
        if (!token) {
          throw new Error('No token available');
        }

        try {
          const response = await apiClient.post<{
            user: User;
            token: string;
          }>(endpoints.auth.refresh);

          if (response.success && response.data) {
            const { user, token: newToken } = response.data;
            
            // Update token in localStorage
            localStorage.setItem('auth_token', newToken);
            
            set({
              user,
              token: newToken,
              isAuthenticated: true,
            });
          } else {
            // If refresh fails, logout user
            get().logout();
            throw new Error(response.error || 'Token refresh failed');
          }
        } catch (error) {
          get().logout();
          throw error;
        }
      },

      updateProfile: async (data: Partial<User>) => {
        const { user } = get();
        
        if (!user) {
          throw new Error('No user logged in');
        }

        set({ isLoading: true });

        try {
          const response = await apiClient.put<User>(
            endpoints.users.update(user.id),
            data
          );

          if (response.success && response.data) {
            set({
              user: response.data,
              isLoading: false,
            });
          } else {
            throw new Error(response.error || 'Profile update failed');
          }
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

