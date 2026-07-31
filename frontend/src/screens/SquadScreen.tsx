import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  StatusBar,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, theme } from '../theme';
import { TierBadge } from '../components/TierBadge';
import { PlayerCard } from '../components/PlayerCard';
import { MOCK_PLAYERS, MOCK_USER } from '../constants/mock';

export function SquadScreen() {
  const starters = MOCK_PLAYERS.filter((p) => p.isStarter);
  const bench = MOCK_PLAYERS.filter((p) => !p.isStarter);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor={colors.black} />
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Org header */}
        <View style={styles.orgHeader}>
          <View>
            <Text style={styles.orgName}>{MOCK_USER.orgName}</Text>
            <Text style={styles.orgSub}>Your squad · {MOCK_PLAYERS.length} players</Text>
          </View>
          <TierBadge tier={MOCK_USER.orgTier} />
        </View>

        {/* Actions */}
        <View style={styles.actions}>
          <TouchableOpacity style={styles.actionBtn} activeOpacity={0.8}>
            <Text style={styles.actionText}>+ Invite</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.actionBtn, styles.actionOutline]} activeOpacity={0.8}>
            <Text style={[styles.actionText, styles.actionOutlineText]}>Manage</Text>
          </TouchableOpacity>
        </View>

        {/* Starters */}
        <Text style={styles.section}>Starters</Text>
        {starters.map((p) => (
          <PlayerCard key={p.id} player={p} />
        ))}

        {/* Bench */}
        <Text style={[styles.section, { marginTop: theme.spacing.lg }]}>Bench</Text>
        {bench.map((p) => (
          <PlayerCard key={p.id} player={p} />
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.black,
  },
  scroll: {
    padding: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  orgHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  orgName: {
    color: colors.white,
    fontSize: theme.fontSize.xl,
    fontWeight: theme.fontWeight.bold,
  },
  orgSub: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
    marginTop: 2,
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: theme.spacing.xl,
  },
  actionBtn: {
    flex: 1,
    height: 44,
    backgroundColor: colors.blue,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionOutline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: colors.blue,
  },
  actionText: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 14,
  },
  actionOutlineText: {
    color: colors.blueBright,
  },
  section: {
    color: colors.white,
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.semibold,
    marginBottom: theme.spacing.md,
  },
});
