import React, { useEffect, useMemo, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Button } from '../../components/Button';
import { Input } from '../../components/Input';
import { ApiError, Mode, platformApi, Region } from '../../services/api';
import { colors, theme } from '../../theme';

interface Props {
  phone: string;
  signupToken: string;
  onComplete: () => Promise<void>;
  onBack: () => void;
}

export function SignupScreen({ phone, signupToken, onComplete, onBack }: Props) {
  const [regions, setRegions] = useState<Region[]>([]);
  const [gamertag, setGamertag] = useState('');
  const [email, setEmail] = useState('');
  const [countryCode, setCountryCode] = useState('NG');
  const [mode, setMode] = useState<Mode>('MP');
  const [isAdult, setIsAdult] = useState(true);
  const [parentalConsent, setParentalConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    platformApi.identity.regions()
      .then((rows) => {
        if (active) setRegions(rows);
      })
      .catch(() => {
        if (active) setError('Could not load the country directory. Check the API connection.');
      });
    return () => {
      active = false;
    };
  }, []);

  const selectedRegion = useMemo(
    () => regions.find((region) => region.code === countryCode.trim().toUpperCase()),
    [countryCode, regions],
  );

  const submit = async () => {
    if (gamertag.trim().length < 3) {
      setError('Gamertag must be at least 3 characters.');
      return;
    }
    if (!selectedRegion) {
      setError('Enter a valid African ISO country code, such as NG, GH, KE, or ZA.');
      return;
    }
    if (!isAdult && !parentalConsent) {
      setError('Confirmed parental consent is required for a minor account.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await platformApi.auth.completeSignup(signupToken, {
        phone,
        gamertag: gamertag.trim(),
        email: email.trim() || null,
        region_id: selectedRegion.id,
        preferred_mode: mode,
        is_adult: isAdult,
        parental_consent_confirmed: !isAdult && parentalConsent,
      });
      await onComplete();
    } catch (signupError) {
      setError(signupError instanceof ApiError ? signupError.message : 'Could not finish signup.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" backgroundColor={colors.black} />
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Pressable onPress={onBack} accessibilityRole="button">
            <Text style={styles.back}>← Use another number</Text>
          </Pressable>
          <Text style={styles.kicker}>PLAYER PASSPORT</Text>
          <Text style={styles.title}>Finish your profile</Text>
          <Text style={styles.subtitle}>Your verified phone is {phone}. Choose the identity used across rankings, teams, and tournaments.</Text>

          <Input
            label="Gamertag"
            placeholder="Your competitive name"
            value={gamertag}
            onChangeText={setGamertag}
            autoCapitalize="none"
            maxLength={50}
            accessibilityLabel="Gamertag"
          />
          <Input
            label="Email (optional, used for payments)"
            placeholder="you@example.com"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            autoComplete="email"
            accessibilityLabel="Email address"
          />
          <Input
            label="Country code"
            placeholder="NG"
            value={countryCode}
            onChangeText={(value) => setCountryCode(value.toUpperCase().slice(0, 2))}
            autoCapitalize="characters"
            maxLength={2}
            accessibilityLabel="Two-letter country code"
          />
          <Text style={styles.regionHint}>
            {selectedRegion ? `${selectedRegion.name} • ${selectedRegion.zone}` : regions.length ? 'Use a two-letter African country code.' : 'Loading countries…'}
          </Text>

          <Text style={styles.label}>Preferred mode</Text>
          <View style={styles.row}>
            {(['MP', 'BR'] as const).map((value) => (
              <Pressable
                key={value}
                onPress={() => setMode(value)}
                accessibilityRole="button"
                accessibilityState={{ selected: mode === value }}
                style={[styles.choice, mode === value ? styles.choiceActive : null]}
              >
                <Text style={[styles.choiceText, mode === value ? styles.choiceTextActive : null]}>{value}</Text>
              </Pressable>
            ))}
          </View>

          <Text style={styles.label}>Age declaration</Text>
          <View style={styles.row}>
            <Pressable
              onPress={() => setIsAdult(true)}
              accessibilityRole="button"
              accessibilityState={{ selected: isAdult }}
              style={[styles.choice, isAdult ? styles.choiceActive : null]}
            >
              <Text style={[styles.choiceText, isAdult ? styles.choiceTextActive : null]}>18 or older</Text>
            </Pressable>
            <Pressable
              onPress={() => setIsAdult(false)}
              accessibilityRole="button"
              accessibilityState={{ selected: !isAdult }}
              style={[styles.choice, !isAdult ? styles.choiceActive : null]}
            >
              <Text style={[styles.choiceText, !isAdult ? styles.choiceTextActive : null]}>Under 18</Text>
            </Pressable>
          </View>

          {!isAdult ? (
            <Pressable
              onPress={() => setParentalConsent((value) => !value)}
              accessibilityRole="checkbox"
              accessibilityState={{ checked: parentalConsent }}
              style={styles.consent}
            >
              <View style={[styles.checkbox, parentalConsent ? styles.checkboxActive : null]}>
                <Text style={styles.checkmark}>{parentalConsent ? '✓' : ''}</Text>
              </View>
              <Text style={styles.consentText}>A parent or guardian has consented to this account.</Text>
            </Pressable>
          ) : null}

          {error ? <Text style={styles.error} accessibilityRole="alert">{error}</Text> : null}
          <Button title="Create player passport" onPress={submit} loading={loading} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.black },
  flex: { flex: 1 },
  content: { flexGrow: 1, padding: theme.spacing.lg, paddingBottom: theme.spacing.xxl },
  back: { color: colors.blueBright, fontSize: theme.fontSize.sm, marginBottom: theme.spacing.xl },
  kicker: { color: colors.redBright, fontSize: theme.fontSize.xs, fontWeight: '700', letterSpacing: 1.5 },
  title: { color: colors.white, fontSize: theme.fontSize.xxl, fontWeight: '700', marginTop: theme.spacing.xs },
  subtitle: { color: colors.gray300, fontSize: theme.fontSize.sm, lineHeight: 20, marginTop: theme.spacing.sm, marginBottom: theme.spacing.xl },
  label: { color: colors.gray300, fontSize: theme.fontSize.sm, fontWeight: '500', marginBottom: theme.spacing.xs },
  regionHint: { color: colors.subtle, fontSize: theme.fontSize.xs, marginTop: -theme.spacing.sm, marginBottom: theme.spacing.md },
  row: { flexDirection: 'row', gap: theme.spacing.sm, marginBottom: theme.spacing.md },
  choice: { flex: 1, minHeight: 44, borderWidth: 1, borderColor: colors.border, borderRadius: theme.radius.md, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.blackCard },
  choiceActive: { borderColor: colors.blue, backgroundColor: colors.redSoft },
  choiceText: { color: colors.gray300, fontSize: theme.fontSize.sm, fontWeight: '600' },
  choiceTextActive: { color: colors.white },
  consent: { flexDirection: 'row', alignItems: 'center', gap: theme.spacing.sm, marginBottom: theme.spacing.lg },
  checkbox: { width: 24, height: 24, borderRadius: 6, borderWidth: 1, borderColor: colors.border, alignItems: 'center', justifyContent: 'center' },
  checkboxActive: { backgroundColor: colors.blue, borderColor: colors.blue },
  checkmark: { color: colors.white, fontWeight: '700' },
  consentText: { flex: 1, color: colors.gray300, fontSize: theme.fontSize.sm, lineHeight: 19 },
  error: { color: colors.error, fontSize: theme.fontSize.sm, textAlign: 'center', marginBottom: theme.spacing.md },
});
