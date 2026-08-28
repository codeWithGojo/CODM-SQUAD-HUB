import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { Trophy } from '../constants/mock';
import { colors, theme } from '../theme';

const rarityColor: Record<Trophy['rarity'], string> = {
  common: colors.gray500,
  rare: colors.cyan,
  epic: colors.violet,
  legendary: colors.magenta,
};

export function TrophyCard({ trophy }: { trophy: Trophy }) {
  return (
    <View style={styles.card}>
      <View style={[styles.icon, { borderColor: rarityColor[trophy.rarity] }]}>
        <Text style={styles.iconText}>{trophy.icon}</Text>
      </View>
      <View style={styles.copy}>
        <Text style={styles.title}>{trophy.title}</Text>
        <Text style={styles.subtitle}>{trophy.subtitle}</Text>
        <Text style={[styles.rarity, { color: rarityColor[trophy.rarity] }]}>{trophy.rarity.toUpperCase()}</Text>
      </View>
      <Text style={styles.date}>{trophy.earnedAt}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { flexDirection: 'row', alignItems: 'center', gap: theme.spacing.md, padding: theme.spacing.md, marginBottom: theme.spacing.sm, backgroundColor: colors.blackCard, borderWidth: 1, borderColor: colors.border, borderRadius: theme.radius.md },
  icon: { width: 48, height: 48, borderRadius: theme.radius.md, alignItems: 'center', justifyContent: 'center', borderWidth: 1, backgroundColor: colors.blackElevated },
  iconText: { fontSize: 23 },
  copy: { flex: 1 },
  title: { color: colors.white, fontSize: theme.fontSize.sm, fontWeight: theme.fontWeight.bold },
  subtitle: { color: colors.gray300, fontSize: theme.fontSize.xs, marginTop: 3 },
  rarity: { fontSize: 9, fontWeight: theme.fontWeight.bold, marginTop: 5, letterSpacing: 1 },
  date: { color: colors.gray500, fontSize: 9 },
});
