import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, theme } from '../theme';

interface Props {
  title: string;
  subtitle?: string;
}

export function EmptyState({ title, subtitle }: Props) {
  return (
    <View style={styles.wrap}>
      <Text style={styles.title}>{title}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    paddingVertical: theme.spacing.xxl,
    alignItems: 'center',
  },
  title: {
    color: colors.gray300,
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.medium,
    marginBottom: 4,
  },
  subtitle: {
    color: colors.gray500,
    fontSize: theme.fontSize.sm,
    textAlign: 'center',
    paddingHorizontal: theme.spacing.xl,
  },
});
