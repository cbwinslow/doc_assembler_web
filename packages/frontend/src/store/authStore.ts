import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, AuthState } from '@/types';
import { authService } from '@/services/auth';
import { socketService } from '@/services/socket';

interface AuthStore extends AuthState {
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
  setLoading: (isLoading: boolean) => void;
  clearError: () => void;
  initializeAuth: () => Promise<void>;
  
  // Error state
  error: string | null;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await authService.login({ email, password });
          
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          // Connect to socket with the new token
          socketService.connect(response.token);
        } catch (error: any) {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: error.message || 'Login failed',
          });
          throw error;
        }
      },

      register: async (email: string, password: string, name: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await authService.register({ email, password, name });
          
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          // Connect to socket with the new token
          socketService.connect(response.token);
        } catch (error: any) {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: error.message || 'Registration failed',
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        
        try {
          await authService.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          // Always clear state regardless of API call success
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });

          // Disconnect socket
          socketService.disconnect();
        }
      },

      refreshToken: async () => {
        const currentToken = get().token;
        if (!currentToken) return;

        try {
          const response = await authService.refreshToken();
          
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            error: null,
          });

          // Reconnect socket with new token
          socketService.disconnect();
          socketService.connect(response.token);
        } catch (error: any) {
          // Token refresh failed, logout user
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            error: error.message || 'Session expired',
          });
          
          socketService.disconnect();
          throw error;
        }
      },

      updateUser: (userData: Partial<User>) => {
        const currentUser = get().user;
        if (currentUser) {
          const updatedUser = { ...currentUser, ...userData };
          set({ user: updatedUser });
          
          // Update localStorage
          localStorage.setItem('user', JSON.stringify(updatedUser));
        }
      },

      setLoading: (isLoading: boolean) => {
        set({ isLoading });
      },

      clearError: () => {
        set({ error: null });
      },

      initializeAuth: async () => {
        const storedToken = authService.getStoredToken();
        const storedUser = authService.getStoredUser();

        if (storedToken && storedUser) {
          set({
            user: storedUser,
            token: storedToken,
            isAuthenticated: true,
            isLoading: false,
          });

          try {
            // Verify token is still valid by fetching current user
            const currentUser = await authService.getCurrentUser();
            set({ user: currentUser });
            
            // Connect socket
            socketService.connect(storedToken);
          } catch (error) {
            console.error('Token validation failed:', error);
            // Token is invalid, clear auth state
            set({
              user: null,
              token: null,
              isAuthenticated: false,
              isLoading: false,
            });
            authService.clearAuthData();
          }
        } else {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Selectors for easier component consumption
export const useAuth = () => {
  const store = useAuthStore();
  return {
    user: store.user,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
  };
};

export const useAuthActions = () => {
  const store = useAuthStore();
  return {
    login: store.login,
    register: store.register,
    logout: store.logout,
    updateUser: store.updateUser,
    clearError: store.clearError,
    initializeAuth: store.initializeAuth,
  };
};

