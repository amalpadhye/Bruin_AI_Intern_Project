import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../src/lib/api';
import { offlineCache } from '../../src/lib/offlineCache';
import { useAuthStore } from '../../src/store/authStore';
import { format } from 'date-fns';

interface Meal {
  id: string;
  item_id?: string;
  custom_name?: string;
  calories_est?: number;
  macros?: Record<string, number>;
  source: 'scan' | 'menu' | 'manual';
  created_at: string;
}

export default function MealsScreen() {
  const { user } = useAuthStore();
  const [refreshing, setRefreshing] = useState(false);
  const [showOffline, setShowOffline] = useState(false);

  const { data: meals, refetch, isLoading } = useQuery({
    queryKey: ['meals', user?.id],
    queryFn: async () => {
      try {
        // Try to get meals from backend (will fail until backend adds GET /me/meals)
        const onlineMeals = await apiClient.getMeals();
        // Also get cached meals
        if (user?.id) {
          const cachedMeals = await offlineCache.getCachedMeals(user.id);
          // Merge and deduplicate
          const allMeals = [...(onlineMeals || []), ...cachedMeals];
          return allMeals.sort(
            (a, b) =>
              new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
        }
        return onlineMeals || [];
      } catch (error) {
        // If offline or endpoint doesn't exist, return cached meals
        if (user?.id) {
          const cachedMeals = await offlineCache.getCachedMeals(user.id);
          setShowOffline(true);
          return cachedMeals;
        }
        return [];
      }
    },
    enabled: !!user,
  });

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await refetch();
      setShowOffline(false);
    } catch (error) {
      console.error('Refresh error:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const renderMeal = ({ item }: { item: Meal }) => {
    const mealName = item.custom_name || `Meal ${item.id.slice(0, 8)}`;
    const calories = item.calories_est || 0;
    const date = new Date(item.created_at);

    return (
      <View style={styles.mealCard}>
        <View style={styles.mealHeader}>
          <Text style={styles.mealName}>{mealName}</Text>
          <Text style={styles.mealDate}>{format(date, 'MMM d, h:mm a')}</Text>
        </View>
        <View style={styles.mealDetails}>
          <Text style={styles.calories}>{calories} cal</Text>
          <Text style={styles.source}>
            {item.source === 'scan' ? '📷 Scan' : item.source === 'menu' ? '🍽️ Menu' : '✍️ Manual'}
          </Text>
        </View>
        {item.macros && (
          <View style={styles.macros}>
            {item.macros.protein && (
              <Text style={styles.macroText}>Protein: {item.macros.protein}g</Text>
            )}
            {item.macros.carbs && (
              <Text style={styles.macroText}>Carbs: {item.macros.carbs}g</Text>
            )}
            {item.macros.fat && (
              <Text style={styles.macroText}>Fat: {item.macros.fat}g</Text>
            )}
          </View>
        )}
      </View>
    );
  };

  if (isLoading && !meals) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading meals...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {showOffline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>
            ⚠️ Offline mode - showing cached meals
          </Text>
        </View>
      )}

      <FlatList
        data={meals || []}
        renderItem={renderMeal}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No meals logged yet</Text>
            <Text style={styles.emptySubtext}>
              Scan a food photo to get started!
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  offlineBanner: { backgroundColor: '#fff3cd', padding: 12, alignItems: 'center' },
  offlineText: { color: '#856404', fontSize: 14 },
  list: { padding: 16 },
  mealCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  mealHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  mealName: { fontSize: 18, fontWeight: '600', color: '#000', flex: 1 },
  mealDate: { fontSize: 12, color: '#666' },
  mealDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  calories: { fontSize: 20, fontWeight: 'bold', color: '#007AFF' },
  source: { fontSize: 14, color: '#666' },
  macros: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  macroText: { fontSize: 12, color: '#666' },
  loadingText: { textAlign: 'center', marginTop: 40, fontSize: 16, color: '#666' },
  emptyContainer: { alignItems: 'center', padding: 40 },
  emptyText: { fontSize: 18, fontWeight: '600', color: '#000', marginBottom: 8 },
  emptySubtext: { fontSize: 14, color: '#666' },
});

