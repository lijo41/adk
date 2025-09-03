import axios from 'axios';
import type { User, UserLogin, UserRegistration, AuthResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear stored auth data on 401
      localStorage.removeItem('auth-storage');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API functions
export const authApi = {
  async login(credentials: UserLogin): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },

  async register(userData: UserRegistration): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  },

  async getProfile(): Promise<User> {
    const response = await apiClient.get('/auth/profile');
    return response.data;
  },

  async updateProfile(profileData: Partial<Pick<User, 'full_name' | 'phone' | 'company_name'>>): Promise<User> {
    const response = await apiClient.put('/auth/profile', profileData);
    return response.data;
  },

  async changePassword(passwordData: {
    current_password: string;
    new_password: string;
  }): Promise<{ message: string }> {
    const response = await apiClient.put('/auth/change-password', passwordData);
    return response.data;
  },

  async logout(): Promise<void> {
    // Clear local storage
    localStorage.removeItem('auth-storage');
    // Optionally call logout endpoint if it exists
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Ignore logout endpoint errors
    }
  }
};

export const getAuthToken = (): string | null => {
  // Try direct token first
  let token = localStorage.getItem('token');
  if (token) return token;

  // Try auth-storage format
  const authStorage = localStorage.getItem('auth-storage');
  if (authStorage) {
    try {
      const authData = JSON.parse(authStorage);
      return authData.state?.token || null;
    } catch (error) {
      console.error('Error parsing auth token:', error);
    }
  }
  
  return null;
};

