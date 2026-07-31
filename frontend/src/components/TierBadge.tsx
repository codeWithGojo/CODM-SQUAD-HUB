import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, theme } from '../theme';

const TIER_COLORS: Record<string, string> = {
  T1: colors.blueBright,
  T2: colors.blue,
  T3: '#5B8DEF',
  T4: colors.gray500,
};

interface Props {
  tier: string;
  size?: 'sm' | 'md';
}

export function TierBadge({ tier, size = 'md' }: Props) {
  const bg = TIER_COLORS[tier] || colors.gray500;
  return (
    <View style={[styles.badge, size === 'sm' && styles.sm, { backgroundColor: bg }]}>
      <Text style={[styles.text, size === 'sm' && styles.textSm]}>{tier}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: theme.radius.sm,
    alignSelf: 'flex-start',
  },
  sm: {
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  text: {
    color: colors.white,
    fontWeight: '700',
    fontSize: 13,
  },
  textSm: {
    fontSize: 11,
  },
});
