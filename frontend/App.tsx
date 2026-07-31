import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, DarkTheme } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PhoneScreen } from './src/screens/auth/PhoneScreen';
import { OtpScreen } from './src/screens/auth/OtpScreen';
import { MainTabs } from './src/navigation/MainTabs';
import { colors } from './src/theme';

type AuthScreen = 'phone' | 'otp' | 'app';

const navTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: colors.black,
    card: colors.blackSoft,
    primary: colors.blue,
    text: colors.white,
    border: colors.border,
  },
};

export default function App() {
  const [screen, setScreen] = useState<AuthScreen>('phone');
  const [phone, setPhone] = useState('');

  const logout = () => {
    setPhone('');
    setScreen('phone');
  };

  if (screen === 'phone') {
    return (
      <SafeAreaProvider>
        <StatusBar style="light" />
        <PhoneScreen
          onContinue={(p) => {
            setPhone(p);
            setScreen('otp');
          }}
        />
      </SafeAreaProvider>
    );
  }

  if (screen === 'otp') {
    return (
      <SafeAreaProvider>
        <StatusBar style="light" />
        <OtpScreen
          phone={phone}
          onBack={() => setScreen('phone')}
          onVerify={() => setScreen('app')}
        />
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <NavigationContainer theme={navTheme}>
        <MainTabs onLogout={logout} />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
