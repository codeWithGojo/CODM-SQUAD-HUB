import React, { createContext, useContext, useEffect, useSyncExternalStore } from 'react';
import { ActivityIndicator, AppState, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CurrentUser, getAccessToken, onSessionExpired, platformApi, realtimeClient, setAccessToken } from '../services/api';
import { SessionController } from '../services/session';
import { PhoneScreen } from '../screens/auth/PhoneScreen';
import { OtpScreen } from '../screens/auth/OtpScreen';
import { SignupScreen } from '../screens/auth/SignupScreen';
import { Button } from './Button';
import { colors } from '../theme/colors';

const session = new SessionController({
  readToken: getAccessToken,
  saveToken: setAccessToken,
  me: platformApi.auth.me,
  requestOtp: platformApi.auth.requestOtp,
  verifyOtp: platformApi.auth.verifyOtp,
  signup: platformApi.auth.completeSignup,
  closeRealtime: () => realtimeClient.close(),
});
const PlayerContext = createContext<{ user: CurrentUser; signOut: () => Promise<void> } | null>(null);
export function usePlayerSession() {
  const value = useContext(PlayerContext);
  if (!value) throw new Error('Player session is unavailable.');
  return value;
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const state = useSyncExternalStore(session.subscribe, session.getSnapshot);
  useEffect(() => {
    void session.restore();
    const unsubscribe = onSessionExpired(() => { void session.signOut('Your session expired. Sign in again.'); });
    let previous = AppState.currentState;
    const appState = AppState.addEventListener('change', next => {
      if (next === 'active' && previous !== 'active' && session.getSnapshot().status === 'ready') void session.restore();
      previous = next;
    });
    return () => { unsubscribe(); appState.remove(); };
  }, []);

  if (state.status === 'ready') {
    return <PlayerContext.Provider value={{ user: state.user, signOut: session.signOut }}>{children}</PlayerContext.Provider>;
  }
  if (state.status === 'phone') return <PhoneScreen onContinue={session.requestOtp} notice={state.notice} />;
  if (state.status === 'otp') return <OtpScreen key={state.phone} phone={state.phone} devCode={state.devCode}
    onVerify={session.verify} onResend={session.resend} onBack={() => { void session.signOut(); }} />;
  if (state.status === 'signup') return <SignupScreen phone={state.phone} onSubmit={session.signup}
    onBack={() => { void session.signOut(); }} />;
  return <SafeAreaView style={styles.safe}><View style={styles.content}>
    <Text style={styles.title}>CoDM Squad Hub</Text>
    {state.status === 'checking' ? <>
      <ActivityIndicator color={colors.white} accessibilityLabel="Checking your session" />
      <Text style={styles.message}>Checking your session…</Text>
    </> : <>
      <Text style={styles.message} accessibilityRole="alert">{state.message}</Text>
      <Button title="Retry connection" onPress={() => { void session.restore(); }} />
      <Button title="Sign out" variant="ghost" onPress={() => { void session.signOut(); }} />
    </>}
  </View></SafeAreaView>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { flex: 1, justifyContent: 'center', padding: 24, gap: 16 },
  title: { color: colors.white, fontSize: 24, fontWeight: '700', textAlign: 'center' },
  message: { color: colors.muted, fontSize: 16, lineHeight: 24, textAlign: 'center' },
});
