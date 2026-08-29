import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Button } from '../../components/Button';
import { colors, theme } from '../../theme';
import { ApiError } from '../../services/api';

interface Props {
  phone: string;
  devCode?: string;
  onVerify: (code: string) => Promise<void>;
  onResend: () => Promise<string | undefined>;
  onBack: () => void;
}

export function OtpScreen({ phone, devCode, onVerify, onResend, onBack }: Props) {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [localDevCode, setLocalDevCode] = useState(devCode);
  const inputs = useRef<(TextInput | null)[]>([]);

  const handleChange = (text: string, index: number) => {
    if (text.length > 1) {
      const digits = text.replace(/\D/g, '').slice(0, 6).split('');
      const next = [...code];
      digits.forEach((d, i) => {
        if (index + i < 6) next[index + i] = d;
      });
      setCode(next);
      const focusAt = Math.min(index + digits.length, 5);
      inputs.current[focusAt]?.focus();
      return;
    }

    const next = [...code];
    next[index] = text;
    setCode(next);

    if (text && index < 5) {
      inputs.current[index + 1]?.focus();
    }
  };

  const handleKeyPress = (key: string, index: number) => {
    if (key === 'Backspace' && !code[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  };

  const handleVerify = async () => {
    const full = code.join('');
    if (full.length < 6) return;
    setError('');
    setLoading(true);
    try {
      await onVerify(full);
    } catch (verifyError) {
      setError(verifyError instanceof ApiError ? verifyError.message : 'Could not verify this code.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setLoading(true);
    try {
      setLocalDevCode(await onResend());
      setCode(['', '', '', '', '', '']);
      inputs.current[0]?.focus();
    } catch (resendError) {
      setError(resendError instanceof ApiError ? resendError.message : 'Could not resend the code.');
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
        <View style={styles.content}>
          <Pressable onPress={onBack} accessibilityRole="button" style={styles.backButton}>
            <Text style={styles.back}>← Back</Text>
          </Pressable>

          <Text style={styles.title}>Enter code</Text>
          <Text style={styles.subtitle}>
            We sent a 6-digit code to{'\n'}
            <Text style={styles.phone}>{phone}</Text>
          </Text>

          <View style={styles.otpRow}>
            {code.map((digit, i) => (
              <TextInput
                key={i}
                ref={(ref) => {
                  inputs.current[i] = ref;
                }}
                style={[styles.otpBox, digit ? styles.otpFilled : null]}
                value={digit}
                onChangeText={(t) => handleChange(t, i)}
                onKeyPress={({ nativeEvent }) => handleKeyPress(nativeEvent.key, i)}
                keyboardType="number-pad"
                maxLength={i === 0 ? 6 : 1}
                selectTextOnFocus
                accessibilityLabel={`Verification code digit ${i + 1}`}
              />
            ))}
          </View>

          {localDevCode ? <Text style={styles.devCode}>Local development code: {localDevCode}</Text> : null}
          {error ? <Text style={styles.error} accessibilityRole="alert">{error}</Text> : null}

          <Button
            title="Verify"
            onPress={handleVerify}
            loading={loading}
            disabled={code.join('').length < 6}
          />

          <Pressable onPress={handleResend} disabled={loading} accessibilityRole="button">
            <Text style={styles.resend}>Didn't receive it? <Text style={styles.resendLink}>Resend</Text></Text>
          </Pressable>
        </View>
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
  content: {
    flex: 1,
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.lg,
    justifyContent: 'center',
  },
  back: {
    color: colors.blueBright,
    fontSize: theme.fontSize.md,
  },
  backButton: {
    position: 'absolute',
    top: theme.spacing.lg,
    left: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    paddingRight: theme.spacing.md,
  },
  title: {
    color: colors.white,
    fontSize: theme.fontSize.xxl,
    fontWeight: theme.fontWeight.bold,
    marginBottom: theme.spacing.sm,
  },
  subtitle: {
    color: colors.gray300,
    fontSize: theme.fontSize.md,
    marginBottom: theme.spacing.xl,
    lineHeight: 22,
  },
  phone: {
    color: colors.white,
    fontWeight: theme.fontWeight.semibold,
  },
  otpRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.xl,
  },
  otpBox: {
    width: 48,
    height: 56,
    borderRadius: theme.radius.md,
    backgroundColor: colors.blackCard,
    borderWidth: 1.5,
    borderColor: colors.border,
    color: colors.white,
    fontSize: 22,
    fontWeight: '700',
    textAlign: 'center',
  },
  otpFilled: {
    borderColor: colors.blue,
  },
  resend: {
    color: colors.gray500,
    textAlign: 'center',
    marginTop: theme.spacing.lg,
    fontSize: theme.fontSize.sm,
  },
  resendLink: {
    color: colors.blueBright,
    fontWeight: theme.fontWeight.semibold,
  },
  devCode: {
    color: colors.warning,
    fontSize: theme.fontSize.xs,
    textAlign: 'center',
    marginBottom: theme.spacing.md,
  },
  error: {
    color: colors.error,
    fontSize: theme.fontSize.xs,
    textAlign: 'center',
    marginBottom: theme.spacing.md,
  },
});
