import { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../src/lib/api';
import { offlineCache } from '../../src/lib/offlineCache';
import { useAuthStore } from '../../src/store/authStore';
import { syncService } from '../../src/lib/sync';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';

interface Post {
  id: string;
  user_id: string;
  title: string;
  body: string;
  image_key?: string;
  created_at: string;
  tags?: string[];
  upvotes?: number;
  user_vote?: number;
}

export default function FeedScreen() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);
  const [sortBy, setSortBy] = useState<'new' | 'top'>('new');

  const { data: posts, refetch, isLoading } = useQuery({
    queryKey: ['posts', sortBy],
    queryFn: async () => {
      try {
        // Try to get posts from backend (will fail until backend adds GET /posts)
        const onlinePosts = await apiClient.getPosts(sortBy);
        // Also get cached posts
        const cachedPosts = await offlineCache.getCachedPosts();
        // Merge and deduplicate
        const allPosts = [...(onlinePosts || []), ...cachedPosts];
        return allPosts.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      } catch (error) {
        // If offline or endpoint doesn't exist, return cached posts
        const cachedPosts = await offlineCache.getCachedPosts();
        return cachedPosts;
      }
    },
  });

  const voteMutation = useMutation({
    mutationFn: async ({ postId, value }: { postId: string; value: 1 | -1 }) => {
      try {
        await apiClient.votePost(postId, value);
        return { postId, value };
      } catch (error) {
        // Cache vote for offline sync (will work when backend adds POST /posts/:id/vote)
        if (user) {
          await offlineCache.cacheVote({
            user_id: user.id,
            post_id: postId,
            value,
            synced: false,
          });
          syncService.syncWhenOnline(user.id).catch(console.error);
        }
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });

  const handleVote = (postId: string, currentVote: number) => {
    const newValue = currentVote === 1 ? -1 : 1;
    voteMutation.mutate({ postId, value: newValue as 1 | -1 });
  };

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await refetch();
    } catch (error) {
      console.error('Refresh error:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const renderPost = ({ item }: { item: Post }) => {
    const date = new Date(item.created_at);
    const upvotes = item.upvotes || 0;
    const userVote = item.user_vote || 0;

    return (
      <View style={styles.postCard}>
        <View style={styles.postHeader}>
          <Text style={styles.postTitle}>{item.title}</Text>
          <Text style={styles.postDate}>{format(date, 'MMM d, h:mm a')}</Text>
        </View>
        <Text style={styles.postBody}>{item.body}</Text>
        {item.tags && item.tags.length > 0 && (
          <View style={styles.tagsContainer}>
            {item.tags.map((tag, index) => (
              <View key={index} style={styles.tag}>
                <Text style={styles.tagText}>#{tag}</Text>
              </View>
            ))}
          </View>
        )}
        <View style={styles.postFooter}>
          <TouchableOpacity
            style={styles.voteButton}
            onPress={() => handleVote(item.id, userVote)}
          >
            <Ionicons
              name={userVote === 1 ? 'arrow-up' : 'arrow-up-outline'}
              size={20}
              color={userVote === 1 ? '#007AFF' : '#666'}
            />
            <Text
              style={[
                styles.voteCount,
                userVote === 1 && styles.voteCountActive,
              ]}
            >
              {upvotes}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.sortButtons}>
          <TouchableOpacity
            style={[styles.sortButton, sortBy === 'new' && styles.sortButtonActive]}
            onPress={() => setSortBy('new')}
          >
            <Text
              style={[
                styles.sortButtonText,
                sortBy === 'new' && styles.sortButtonTextActive,
              ]}
            >
              New
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.sortButton, sortBy === 'top' && styles.sortButtonActive]}
            onPress={() => setSortBy('top')}
          >
            <Text
              style={[
                styles.sortButtonText,
                sortBy === 'top' && styles.sortButtonTextActive,
              ]}
            >
              Top
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <FlatList
        data={posts || []}
        renderItem={renderPost}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No posts yet</Text>
            <Text style={styles.emptySubtext}>
              Be the first to share your meal!
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  sortButtons: { flexDirection: 'row', gap: 8 },
  sortButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
  },
  sortButtonActive: { backgroundColor: '#007AFF' },
  sortButtonText: { fontSize: 14, fontWeight: '600', color: '#666' },
  sortButtonTextActive: { color: '#fff' },
  list: { padding: 16 },
  postCard: {
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
  postHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  postTitle: { fontSize: 18, fontWeight: '600', color: '#000', flex: 1 },
  postDate: { fontSize: 12, color: '#666', marginLeft: 12 },
  postBody: { fontSize: 14, color: '#333', lineHeight: 20, marginBottom: 12 },
  tagsContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  tag: { backgroundColor: '#e3f2fd', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  tagText: { fontSize: 12, color: '#007AFF' },
  postFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  voteButton: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  voteCount: { fontSize: 14, color: '#666', marginLeft: 4 },
  voteCountActive: { color: '#007AFF', fontWeight: '600' },
  emptyContainer: { alignItems: 'center', padding: 40 },
  emptyText: { fontSize: 18, fontWeight: '600', color: '#000', marginBottom: 8 },
  emptySubtext: { fontSize: 14, color: '#666' },
});

