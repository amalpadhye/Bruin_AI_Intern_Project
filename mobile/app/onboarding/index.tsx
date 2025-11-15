import { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput } from 'react-native';
import { useRouter } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useProfileStore } from '../../src/store/profileStore';

const onboardingSchema = z.object({
  height_cm: z.number().min(100).max(250),
  weight_kg: z.number().min(30).max(300),
  exercise_level: z.enum(['sedentary', 'light', 'moderate', 'active', 'very_active']),
  goal: z.enum(['gain', 'lose', 'maintain']),
  dietary_restrictions: z.array(z.string()).optional(),
  dorm: z.string().min(1),
  meal_plan: z.string().min(1),
});

type OnboardingForm = z.infer<typeof onboardingSchema>;

const DORMS = [
  'Hedrick Hall',
  'Rieber Hall',
  'Sproul Hall',
  'De Neve Plaza',
  'Sunset Village',
  'Hitch Suites',
  'Other',
];

const MEAL_PLANS = [
  '19P - 19 meals per week',
  '14P - 14 meals per week',
  '11P - 11 meals per week',
  '19R - 19 meals + $65 flex',
  '14R - 14 meals + $65 flex',
  '11R - 11 meals + $65 flex',
];

const DIETARY_RESTRICTIONS = [
  'Vegetarian',
  'Vegan',
  'Gluten-Free',
  'Dairy-Free',
  'Nut-Free',
  'Halal',
  'Kosher',
  'No Restrictions',
];

export default function OnboardingScreen() {
  const router = useRouter();
  const { updateProfile } = useProfileStore();
  const [step, setStep] = useState(1);
  const [selectedRestrictions, setSelectedRestrictions] = useState<string[]>([]);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
  } = useForm<OnboardingForm>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      dietary_restrictions: [],
    },
  });

  const onSubmit = async (data: OnboardingForm) => {
    try {
      await updateProfile({
        ...data,
        has_completed_onboarding: true,
      });
      router.replace('/(tabs)/home');
    } catch (error) {
      console.error('Onboarding error:', error);
    }
  };

  const toggleRestriction = (restriction: string) => {
    if (restriction === 'No Restrictions') {
      setSelectedRestrictions(['No Restrictions']);
      setValue('dietary_restrictions', ['No Restrictions']);
    } else {
      const updated = selectedRestrictions.includes(restriction)
        ? selectedRestrictions.filter((r) => r !== restriction)
        : [...selectedRestrictions.filter((r) => r !== 'No Restrictions'), restriction];
      setSelectedRestrictions(updated);
      setValue('dietary_restrictions', updated);
    }
  };

  const renderStep1 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Height & Weight</Text>
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Height (cm)</Text>
        <Controller
          control={control}
          name="height_cm"
          render={({ field: { onChange, value } }) => (
            <TextInput
              style={styles.input}
              placeholder="170"
              keyboardType="numeric"
              value={value?.toString()}
              onChangeText={(text) => onChange(parseInt(text) || 0)}
            />
          )}
        />
      </View>
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Weight (kg)</Text>
        <Controller
          control={control}
          name="weight_kg"
          render={({ field: { onChange, value } }) => (
            <TextInput
              style={styles.input}
              placeholder="70"
              keyboardType="numeric"
              value={value?.toString()}
              onChangeText={(text) => onChange(parseFloat(text) || 0)}
            />
          )}
        />
      </View>
      <TouchableOpacity style={styles.nextButton} onPress={() => setStep(2)}>
        <Text style={styles.nextButtonText}>Next</Text>
      </TouchableOpacity>
    </View>
  );

  const renderStep2 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Activity Level</Text>
      {['sedentary', 'light', 'moderate', 'active', 'very_active'].map((level) => (
        <Controller
          key={level}
          control={control}
          name="exercise_level"
          render={({ field: { onChange, value } }) => (
            <TouchableOpacity
              style={[styles.optionButton, value === level && styles.optionButtonSelected]}
              onPress={() => onChange(level)}
            >
              <Text style={[styles.optionText, value === level && styles.optionTextSelected]}>
                {level.replace('_', ' ').toUpperCase()}
              </Text>
            </TouchableOpacity>
          )}
        />
      ))}
      <TouchableOpacity style={styles.nextButton} onPress={() => setStep(3)}>
        <Text style={styles.nextButtonText}>Next</Text>
      </TouchableOpacity>
    </View>
  );

  const renderStep3 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Goal</Text>
      {(['gain', 'lose', 'maintain'] as const).map((goal) => (
        <Controller
          key={goal}
          control={control}
          name="goal"
          render={({ field: { onChange, value } }) => (
            <TouchableOpacity
              style={[styles.optionButton, value === goal && styles.optionButtonSelected]}
              onPress={() => onChange(goal)}
            >
              <Text style={[styles.optionText, value === goal && styles.optionTextSelected]}>
                {goal.toUpperCase()}
              </Text>
            </TouchableOpacity>
          )}
        />
      ))}
      <TouchableOpacity style={styles.nextButton} onPress={() => setStep(4)}>
        <Text style={styles.nextButtonText}>Next</Text>
      </TouchableOpacity>
    </View>
  );

  const renderStep4 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Dietary Restrictions</Text>
      <View style={styles.restrictionsGrid}>
        {DIETARY_RESTRICTIONS.map((restriction) => (
          <TouchableOpacity
            key={restriction}
            style={[
              styles.restrictionChip,
              selectedRestrictions.includes(restriction) && styles.restrictionChipSelected,
            ]}
            onPress={() => toggleRestriction(restriction)}
          >
            <Text
              style={[
                styles.restrictionText,
                selectedRestrictions.includes(restriction) && styles.restrictionTextSelected,
              ]}
            >
              {restriction}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <TouchableOpacity style={styles.nextButton} onPress={() => setStep(5)}>
        <Text style={styles.nextButtonText}>Next</Text>
      </TouchableOpacity>
    </View>
  );

  const renderStep5 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Dorm & Meal Plan</Text>
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Dorm</Text>
        <Controller
          control={control}
          name="dorm"
          render={({ field: { onChange, value } }) => (
            <View>
              {DORMS.map((dorm) => (
                <TouchableOpacity
                  key={dorm}
                  style={[styles.optionButton, value === dorm && styles.optionButtonSelected]}
                  onPress={() => onChange(dorm)}
                >
                  <Text style={[styles.optionText, value === dorm && styles.optionTextSelected]}>
                    {dorm}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        />
      </View>
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Meal Plan</Text>
        <Controller
          control={control}
          name="meal_plan"
          render={({ field: { onChange, value } }) => (
            <View>
              {MEAL_PLANS.map((plan) => (
                <TouchableOpacity
                  key={plan}
                  style={[styles.optionButton, value === plan && styles.optionButtonSelected]}
                  onPress={() => onChange(plan)}
                >
                  <Text style={[styles.optionText, value === plan && styles.optionTextSelected]}>
                    {plan}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        />
      </View>
      <TouchableOpacity
        style={[styles.nextButton, isSubmitting && styles.buttonDisabled]}
        onPress={handleSubmit(onSubmit)}
        disabled={isSubmitting}
      >
        <Text style={styles.nextButtonText}>
          {isSubmitting ? 'Saving...' : 'Complete Setup'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      <View style={styles.progressBar}>
        <View style={[styles.progressFill, { width: `${(step / 5) * 100}%` }]} />
      </View>
      {step === 1 && renderStep1()}
      {step === 2 && renderStep2()}
      {step === 3 && renderStep3()}
      {step === 4 && renderStep4()}
      {step === 5 && renderStep5()}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  progressBar: { height: 4, backgroundColor: '#e0e0e0' },
  progressFill: { height: '100%', backgroundColor: '#007AFF' },
  stepContainer: { padding: 20, minHeight: '100%' },
  stepTitle: { fontSize: 28, fontWeight: 'bold', marginBottom: 32, color: '#000' },
  inputGroup: { marginBottom: 24 },
  label: { fontSize: 16, fontWeight: '600', marginBottom: 8, color: '#000' },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  optionButton: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    backgroundColor: '#fff',
  },
  optionButtonSelected: { borderColor: '#007AFF', backgroundColor: '#e3f2fd' },
  optionText: { fontSize: 16, color: '#000' },
  optionTextSelected: { color: '#007AFF', fontWeight: '600' },
  restrictionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 24 },
  restrictionChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ddd',
    backgroundColor: '#fff',
    marginBottom: 8,
  },
  restrictionChipSelected: { borderColor: '#007AFF', backgroundColor: '#e3f2fd' },
  restrictionText: { fontSize: 14, color: '#000' },
  restrictionTextSelected: { color: '#007AFF', fontWeight: '600' },
  nextButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 'auto',
    marginBottom: 20,
  },
  nextButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  buttonDisabled: { opacity: 0.6 },
});

