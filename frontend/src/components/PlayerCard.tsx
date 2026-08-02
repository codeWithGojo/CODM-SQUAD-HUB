import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { colors, theme } from '../theme';
import { TierBadge } from './TierBadge';

export interface Player {
  id: string;
  gamertag: string;
  role: string;
  isStarter: boolean;
  competitiveTier?: string;
  marketValueNgn?: number;
  trophyCount?: number;
}

interface Props {
  player: Player;
  onPress?: () => void;
}

export function PlayerCard({ player, onPress }: Props) {
  const initials = player.gamertag.slice(0, 2).toUpperCase();

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.8}
      disabled={!onPress}
    >
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{initials}</Text>
      </View>

      <View style={styles.info}>
        <Text style={styles.name}>{player.gamertag}</Text>
        <Text style={styles.role}>
          {player.role} · {player.isStarter ? 'Starter' : 'Bench'}
        </Text>

        {/* Extra meta row */}
        <View style={styles.metaRow}>
          {player.marketValueNgn != null && (
            <Text style={styles.meta}>
              ₦{player.marketValueNgn.toLocaleString()}
            </Text>
          )}
          {player.trophyCount != null && player.trophyCount > 0 && (
            <Text style={styles.metaTrophy}>
              🏆 {player.trophyCount}
            </Text>
          )}
        </View>
      </View>

      {player.competitiveTier ? (
        <TierBadge tier={player.competitiveTier} size="sm" />
      ) : null}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.blackCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: theme.spacing.sm,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.blue,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: theme.spacing.md,
  },
  avatarText: {
    color: colors.white,
    fontWeight: '700',
    fontSize: 14,
  },
  info: {
    flex: 1,
  },
  name: {
    color: colors.white,
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
  },
  role: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
    marginTop: 2,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 4,
  },
  meta: {
    color: colors.blueBright,
    fontSize: 12,
    fontWeight: '600',
  },
  metaTrophy: {
    color: '#F59E0B',
    fontSize: 12,
    fontWeight: '600',
  },
});
