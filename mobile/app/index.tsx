import { useEffect } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { useProfileStore } from '../src/store/profileStore';

export default function Index() {
  const router = useRouter();
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const { profile, fetchProfile, hasCompletedOnboarding } = useProfileStore();

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.replace('/(auth)/login');
      } else {
        // Try to fetch profile (will fail until backend adds /me endpoint)
        fetchProfile().then(() => {
          if (!hasCompletedOnboarding()) {
            router.replace('/onboarding');
          } else {
            router.replace('/(tabs)/home');
          }
        }).catch(() => {
          // Backend doesn't have /me endpoint yet, go to onboarding
          router.replace('/onboarding');
        });
      }
    }
  }, [isLoading, isAuthenticated]);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#007AFF" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
});

