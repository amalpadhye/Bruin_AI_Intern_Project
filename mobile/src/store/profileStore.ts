import { create } from 'zustand';
import { apiClient } from '../lib/api';

export interface UserProfile {
  height_cm?: number;
  weight_kg?: number;
  exercise_level?: string;
  goal?: 'gain' | 'lose' | 'maintain';
  dietary_restrictions?: string[];
  dorm?: string;
  meal_plan?: string;
  has_completed_onboarding?: boolean;
}

interface ProfileState {
  profile: UserProfile | null;
  isLoading: boolean;
  fetchProfile: () => Promise<void>;
  updateProfile: (updates: Partial<UserProfile>) => Promise<void>;
  hasCompletedOnboarding: () => boolean;
}

/**
 * Profile Store - Manages user profile state
 * 
 * NOTE: Backend GET /me and PUT /me endpoints are pending (STATUS.md line 122-128).
 * This store will work automatically when endpoints are added.
 */
export const useProfileStore = create<ProfileState>((set, get) => ({
  profile: null,
  isLoading: false,

  fetchProfile: async () => {
    try {
      set({ isLoading: true });
      // This will work when backend adds GET /me endpoint
      const profile = await apiClient.getProfile();
      set({ profile, isLoading: false });
    } catch (error: any) {
      // Expected until backend endpoint is added
      if (error.response?.status === 404 || error.response?.status === 501) {
        console.log('Profile endpoint not available yet');
      }
      set({ isLoading: false });
    }
  },

  updateProfile: async (updates: Partial<UserProfile>) => {
    try {
      const currentProfile = get().profile || {};
      const updatedProfile = { ...currentProfile, ...updates };
      
      // This will work when backend adds PUT /me endpoint
      await apiClient.updateProfile(updates);
      set({ profile: updatedProfile });
    } catch (error: any) {
      // Expected until backend endpoint is added
      if (error.response?.status === 404 || error.response?.status === 501) {
        // Still update local state even if backend doesn't have endpoint yet
        const currentProfile = get().profile || {};
        set({ profile: { ...currentProfile, ...updates } });
        console.log('Profile endpoint not available yet, updated locally');
      } else {
        throw error;
      }
    }
  },

  hasCompletedOnboarding: () => {
    const profile = get().profile;
    return profile?.has_completed_onboarding ?? false;
  },
}));

