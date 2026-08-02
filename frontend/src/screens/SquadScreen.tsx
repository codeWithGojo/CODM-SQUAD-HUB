import React, { useState } from 'react';
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
import { TrophyCard } from '../components/TrophyCard';
import {
  MOCK_PLAYERS,
  MOCK_USER,
  MOCK_TEAM_TROPHIES,
} from '../constants/mock';

type SquadTab = 'roster' | 'trophies';

export function SquadScreen() {
  const [tab, setTab] = useState<SquadTab>('roster');
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
            <Text style={styles.orgSub}>
              {MOCK_PLAYERS.length} players · {MOCK_TEAM_TROPHIES.length} team trophies
            </Text>
          </View>
          <TierBadge tier={MOCK_USER.orgTier} />
        </View>

        {/* Actions */}
        <View style={styles.actions}>
          <TouchableOpacity style={styles.actionBtn} activeOpacity={0.8}>
            <Text style={styles.actionText}>+ Invite</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionBtn, styles.actionOutline]}
            activeOpacity={0.8}
          >
            <Text style={[styles.actionText, styles.actionOutlineText]}>
              Manage
            </Text>
          </TouchableOpacity>
        </View>

        {/* Tabs: Roster | Team Trophies */}
        <View style={styles.tabs}>
          <TouchableOpacity
            style={[styles.tab, tab === 'roster' && styles.tabActive]}
            onPress={() => setTab('roster')}
            activeOpacity={0.8}
          >
            <Text
              style={[styles.tabText, tab === 'roster' && styles.tabTextActive]}
            >
              Roster
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, tab === 'trophies' && styles.tabActive]}
            onPress={() => setTab('trophies')}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.tabText,
                tab === 'trophies' && styles.tabTextActive,
              ]}
            >
              Team Trophies
            </Text>
          </TouchableOpacity>
        </View>

        {/* ── Roster ───────────────────────────────────────────────── */}
        {tab === 'roster' && (
          <>
            <Text style={styles.section}>Starters</Text>
            {starters.map((p) => (
              <PlayerCard key={p.id} player={p} />
            ))}

            <Text style={[styles.section, { marginTop: theme.spacing.lg }]}>
              Bench
            </Text>
            {bench.map((p) => (
              <PlayerCard key={p.id} player={p} />
            ))}
          </>
        )}

        {/* ── Team Trophy Cabinet ──────────────────────────────────── */}
        {tab === 'trophies' && (
          <>
            <View style={styles.cabinetHeader}>
              <Text style={styles.cabinetTitle}>Team Trophy Cabinet</Text>
              <Text style={styles.cabinetSub}>
                Tournament titles & seasonal achievements for{' '}
                {MOCK_USER.orgName}
              </Text>
            </View>

            {MOCK_TEAM_TROPHIES.length === 0 ? (
              <View style={styles.empty}>
                <Text style={styles.emptyTitle}>No team trophies yet</Text>
                <Text style={styles.emptySub}>
                  Win official tournaments to fill the cabinet
                </Text>
              </View>
            ) : (
              MOCK_TEAM_TROPHIES.map((t) => (
                <TrophyCard key={t.id} trophy={t} />
              ))
            )}
          </>
        )}
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
    marginBottom: theme.spacing.lg,
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

  // Tabs
  tabs: {
    flexDirection: 'row',
    backgroundColor: colors.blackCard,
    borderRadius: theme.radius.md,
    padding: 4,
    marginBottom: theme.spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: theme.radius.sm,
  },
  tabActive: {
    backgroundColor: colors.blue,
  },
  tabText: {
    color: colors.gray300,
    fontSize: 13,
    fontWeight: '600',
  },
  tabTextActive: {
    color: colors.white,
  },

  section: {
    color: colors.white,
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.semibold,
    marginBottom: theme.spacing.md,
  },

  cabinetHeader: {
    marginBottom: theme.spacing.lg,
  },
  cabinetTitle: {
    color: colors.white,
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.bold,
  },
  cabinetSub: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
    marginTop: 4,
  },
  empty: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyTitle: {
    color: colors.white,
    fontSize: theme.fontSize.md,
    fontWeight: '600',
  },
  emptySub: {
    color: colors.gray500,
    fontSize: theme.fontSize.sm,
    marginTop: 6,
  },
});
