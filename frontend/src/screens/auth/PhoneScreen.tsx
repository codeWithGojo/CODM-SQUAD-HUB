import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { errorMessage } from '../../services/session';
import { Button } from '../../components/Button';
import { Input } from '../../components/Input';
import { colors, theme } from '../../theme';

interface Props {
  onContinue: (phone: string) => Promise<void>;
  notice?: string;
}

export function PhoneScreen({ onContinue, notice }: Props) {
  const [phone, setPhone] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleContinue = async () => {
    if (loading) return;
    setError('');
    setLoading(true);
    try {
      await onContinue(phone);
    } catch (error) {
      setError(errorMessage(error, 'Could not request a code. Try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" backgroundColor={colors.black} />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <View style={styles.logoMark}>
              <Text style={styles.logoText}>CS</Text>
            </View>
            <Text style={styles.title}>CoDM Squad Hub</Text>
            <Text style={styles.subtitle}>
              Competitive scene for African squads
            </Text>
          </View>

          <View style={styles.form}>
            <Text style={styles.sectionTitle}>Sign in with phone</Text>
            {notice ? <Text style={{ color: colors.gray300, marginBottom: 16 }} accessibilityRole="alert">{notice}</Text> : null}
            <Input
              label="Phone number"
              placeholder="+234 801 234 5678"
              keyboardType="phone-pad"
              value={phone}
              onChangeText={setPhone}
              error={error}
              autoComplete="tel"
              accessibilityLabel="Phone number with country code"
              editable={!loading}
              autoFocus
            />
            <Button
              title="Continue"
              onPress={handleContinue}
              loading={loading}
            />
          </View>

          <Text style={styles.footer}>
            By continuing you agree to our Terms & Privacy Policy
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.black,
  },
  flex: {
    flex: 1,
  },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.xl,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: theme.spacing.xxl,
  },
  logoMark: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: colors.blue,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.md,
  },
  logoText: {
    color: colors.white,
    fontSize: 28,
    fontWeight: '700',
  },
  title: {
    color: colors.white,
    fontSize: theme.fontSize.xxl,
    fontWeight: theme.fontWeight.bold,
    marginBottom: theme.spacing.xs,
  },
  subtitle: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
    textAlign: 'center',
  },
  form: {
    marginBottom: theme.spacing.xl,
  },
  sectionTitle: {
    color: colors.white,
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.semibold,
    marginBottom: theme.spacing.md,
  },
  footer: {
    color: colors.gray500,
    fontSize: theme.fontSize.xs,
    textAlign: 'center',
  },
});
