import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { auth0Service, AuthResult } from '../lib/auth0';
import { apiClient } from '../lib/api';

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  token: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: User) => void;
}

const USER_KEY = '@forku:user';
const TOKEN_KEY = '@forku:auth_token';

/**
 * Auth Store - Manages authentication state
 * 
 * NOTE: Backend currently uses "temp_user" (STATUS.md line 119)
 * This store is ready for when backend adds proper auth support.
 */
export const useAuthStore = create<AuthState>((set, get) => ({
  isAuthenticated: false,
  isLoading: true,
  user: null,
  token: null,

  login: async () => {
    try {
      set({ isLoading: true });
      const result: AuthResult = await auth0Service.login();
      
      // Extract user info from token (for now, use temp until backend supports /me)
      // TODO: Call apiClient.getProfile() when backend adds GET /me endpoint
      const userProfile = { id: 'temp_user', email: '', name: 'User' };
      
      try {
        // Try to get profile from backend (will fail until backend implements /me)
        const profile = await apiClient.getProfile();
        userProfile.id = profile.id;
        userProfile.email = profile.email;
        userProfile.name = profile.name;
      } catch (error) {
        // Backend doesn't have /me endpoint yet, use temp user
        console.log('Backend profile endpoint not available yet, using temp user');
      }

      const user: User = {
        id: userProfile.id,
        email: userProfile.email,
        name: userProfile.name,
      };

      // Store in async storage
      await AsyncStorage.multiSet([
        [USER_KEY, JSON.stringify(user)],
        [TOKEN_KEY, result.accessToken],
      ]);

      set({
        isAuthenticated: true,
        user,
        token: result.accessToken,
        isLoading: false,
      });
    } catch (error) {
      console.error('Login error:', error);
      set({ isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await auth0Service.logout();
      await AsyncStorage.multiRemove([USER_KEY, TOKEN_KEY]);
      set({
        isAuthenticated: false,
        user: null,
        token: null,
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  },

  checkAuth: async () => {
    try {
      const [userStr, token] = await AsyncStorage.multiGet([USER_KEY, TOKEN_KEY]);
      
      if (userStr[1] && token[1]) {
        const user = JSON.parse(userStr[1]);
        await apiClient.setToken(token[1]);
        
        // Verify token is still valid by fetching profile
        try {
          const profile = await apiClient.getProfile();
          set({
            isAuthenticated: true,
            user: {
              id: profile.id,
              email: profile.email,
              name: profile.name,
            },
            token: token[1],
            isLoading: false,
          });
        } catch (error) {
          // Token invalid or backend doesn't have /me endpoint yet
          // For now, keep user logged in if we have token
          set({
            isAuthenticated: true,
            user,
            token: token[1],
            isLoading: false,
          });
        }
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      console.error('Auth check error:', error);
      set({ isLoading: false });
    }
  },

  setUser: (user: User) => {
    set({ user });
    AsyncStorage.setItem(USER_KEY, JSON.stringify(user));
  },
}));

