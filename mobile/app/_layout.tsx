import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '../src/store/authStore';
import { offlineCache } from '../src/lib/offlineCache';
import { notificationService } from '../src/lib/notifications';

const queryClient = new QueryClient();

export default function RootLayout() {
  const { checkAuth } = useAuthStore();

  useEffect(() => {
    // Initialize offline cache
    offlineCache.init().catch(console.error);
    
    // Check auth status on app start
    checkAuth();

    // Register for push notifications
    notificationService.registerForPushNotifications().catch(console.error);

    // Set up notification listeners
    const cleanup = notificationService.setupNotificationListeners(
      (notification) => {
        console.log('Notification received:', notification);
      },
      (response) => {
        console.log('Notification tapped:', response);
      }
    );

    // Schedule meal reminders
    notificationService.scheduleMealReminders().catch(console.error);

    return cleanup;
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="onboarding" />
      </Stack>
    </QueryClientProvider>
  );
}

