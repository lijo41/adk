import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { cleanupApi } from '../api/cleanup';
import { useAppStore } from './appStore';

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  company_name: string;
  gstin: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User | null) => void;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (token: string, user: User | null) =>
        set({ token, user, isAuthenticated: true }),
      logout: async () => {
        try {
          // Clear all session data from backend (chunks, documents, etc.)
          await cleanupApi.clearUserSessionData();
          
          // Clear frontend app store data
          useAppStore.getState().clearAllData();
          
          // Clear auth store
          set({ token: null, user: null, isAuthenticated: false });
          
          // Clear localStorage manually to ensure complete cleanup
          localStorage.removeItem('auth-storage');
          localStorage.removeItem('adk-app-storage');
          localStorage.removeItem('token');
          
        } catch (error) {
          console.error('Error during logout cleanup (continuing with local logout):', error);
          // Still proceed with local logout even if backend cleanup fails
          useAppStore.getState().clearAllData();
          set({ token: null, user: null, isAuthenticated: false });
          localStorage.removeItem('auth-storage');
          localStorage.removeItem('adk-app-storage');
          localStorage.removeItem('token');
        }
      },
      setUser: (user: User) => set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
