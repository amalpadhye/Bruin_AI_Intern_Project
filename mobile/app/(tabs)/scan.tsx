import { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Image,
  ScrollView,
} from 'react-native';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { apiClient } from '../../src/lib/api';
import { useAuthStore } from '../../src/store/authStore';
import { offlineCache } from '../../src/lib/offlineCache';
import { syncService } from '../../src/lib/sync';

/**
 * Scan Screen - Uses existing POST /scan endpoint
 * 
 * Matches backend implementation in app/api/scan.py:
 * - Accepts FormData with 'image' field (like test_ui.html)
 * - Backend handles S3 upload internally (scan.py line 44)
 * - Returns scan results with matched/unmatched foods
 * 
 * See STATUS.md for scan endpoint details.
 */
export default function ScanScreen() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, requestPermission] = useCameraPermissions();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const cameraRef = useRef<CameraView>(null);
  const { user } = useAuthStore();

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to use the camera</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const takePicture = async () => {
    if (cameraRef.current) {
      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.8,
          base64: false,
        });
        if (photo?.uri) {
          setImageUri(photo.uri);
          await processImage(photo.uri);
        }
      } catch (error) {
        console.error('Error taking picture:', error);
        Alert.alert('Error', 'Failed to take picture');
      }
    }
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setImageUri(result.assets[0].uri);
      await processImage(result.assets[0].uri);
    }
  };

  const processImage = async (uri: string) => {
    setIsScanning(true);
    setScanResult(null);

    try {
      // Use existing POST /scan endpoint - matches test_ui.html implementation
      // Backend expects FormData with 'image' field (app/api/scan.py line 20)
      // Backend handles S3 upload internally (scan.py line 44)
      const result = await apiClient.scanImage(uri);

      setScanResult(result);

      // Cache meal if scan successful (will sync when backend adds /me/meals endpoint)
      if (result.foods && result.foods.length > 0 && user) {
        const mealId = `meal_${Date.now()}`;
        await offlineCache.cacheMeal({
          id: mealId,
          user_id: user.id,
          source: 'scan',
          created_at: new Date().toISOString(),
          calories_est: result.totals?.chatgpt_estimate || result.totals?.menu_calories,
        });

        // Try to sync immediately (will work when backend adds /me/meals)
        syncService.syncWhenOnline(user.id).catch(console.error);
      }
    } catch (error: any) {
      console.error('Scan error:', error);
      Alert.alert(
        'Scan Failed',
        error.message || 'Failed to process image. Please try again.'
      );
    } finally {
      setIsScanning(false);
    }
  };

  const resetScan = () => {
    setImageUri(null);
    setScanResult(null);
  };

  return (
    <View style={styles.container}>
      {!imageUri ? (
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing={facing}
        >
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={styles.flipButton}
              onPress={() => setFacing(facing === 'back' ? 'front' : 'back')}
            >
              <Text style={styles.text}>Flip</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.captureButton} onPress={takePicture}>
              <View style={styles.captureButtonInner} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.pickButton} onPress={pickImage}>
              <Text style={styles.text}>Gallery</Text>
            </TouchableOpacity>
          </View>
        </CameraView>
      ) : (
        <ScrollView style={styles.resultContainer}>
          <Image source={{ uri: imageUri }} style={styles.previewImage} />

          {isScanning ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#007AFF" />
              <Text style={styles.loadingText}>Analyzing food...</Text>
            </View>
          ) : scanResult ? (
            <View style={styles.resultContent}>
              <Text style={styles.resultTitle}>Scan Results</Text>

              {scanResult.error ? (
                <View style={styles.errorBox}>
                  <Text style={styles.errorText}>{scanResult.message}</Text>
                </View>
              ) : (
                <>
                  <View style={styles.summaryBox}>
                    <Text style={styles.summaryText}>
                      Foods Found: {scanResult.total_foods}
                    </Text>
                    <Text style={styles.summaryText}>
                      Matched: {scanResult.matched_count}
                    </Text>
                    {scanResult.totals && (
                      <Text style={styles.summaryText}>
                        Total Calories: {scanResult.totals.menu_calories || scanResult.totals.chatgpt_estimate}
                      </Text>
                    )}
                  </View>

                  {scanResult.foods?.map((food: any, index: number) => (
                    <View key={index} style={styles.foodCard}>
                      {food.matched ? (
                        <>
                          <Text style={styles.foodName}>
                            {food.matched_item?.name}
                          </Text>
                          <Text style={styles.foodDetails}>
                            Calories: {food.calories?.menu_calories || food.calories?.chatgpt_estimate}
                          </Text>
                          {food.warn && (
                            <View style={styles.warningBox}>
                              <Text style={styles.warningText}>
                                ⚠️ {food.warning?.message}
                              </Text>
                            </View>
                          )}
                        </>
                      ) : (
                        <>
                          <Text style={styles.foodName}>
                            {food.suggestion?.suggested_name || 'Unknown Food'}
                          </Text>
                          <Text style={styles.foodDetails}>
                            Estimated Calories: {food.suggestion?.estimated_calories || food.chatgpt_original_estimate}
                          </Text>
                        </>
                      )}
                    </View>
                  ))}
                </>
              )}

              <View style={styles.actionButtons}>
                <TouchableOpacity
                  style={[styles.actionButton, styles.retryButton]}
                  onPress={resetScan}
                >
                  <Text style={styles.actionButtonText}>Scan Again</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.actionButton, styles.saveButton]}
                  onPress={() => {
                    Alert.alert('Success', 'Meal logged!');
                    resetScan();
                  }}
                >
                  <Text style={styles.actionButtonText}>Save Meal</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  buttonContainer: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: 'transparent',
    margin: 20,
    justifyContent: 'space-around',
    alignItems: 'flex-end',
  },
  flipButton: {
    alignSelf: 'flex-end',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    padding: 12,
    borderRadius: 8,
  },
  captureButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#007AFF',
  },
  captureButtonInner: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#007AFF',
  },
  pickButton: {
    alignSelf: 'flex-end',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    padding: 12,
    borderRadius: 8,
  },
  text: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  message: {
    textAlign: 'center',
    paddingBottom: 10,
    color: '#fff',
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  previewImage: {
    width: '100%',
    height: 300,
    resizeMode: 'cover',
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  resultContent: {
    padding: 20,
  },
  resultTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#000',
  },
  summaryBox: {
    backgroundColor: '#f0f0f0',
    padding: 16,
    borderRadius: 8,
    marginBottom: 20,
  },
  summaryText: {
    fontSize: 16,
    marginBottom: 4,
    color: '#000',
  },
  foodCard: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  foodName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    color: '#000',
  },
  foodDetails: {
    fontSize: 14,
    color: '#666',
  },
  warningBox: {
    backgroundColor: '#fff3cd',
    padding: 12,
    borderRadius: 6,
    marginTop: 8,
  },
  warningText: {
    fontSize: 14,
    color: '#856404',
  },
  errorBox: {
    backgroundColor: '#f8d7da',
    padding: 16,
    borderRadius: 8,
    marginBottom: 20,
  },
  errorText: {
    color: '#721c24',
    fontSize: 14,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  actionButton: {
    flex: 1,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  retryButton: {
    backgroundColor: '#6c757d',
  },
  saveButton: {
    backgroundColor: '#007AFF',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

