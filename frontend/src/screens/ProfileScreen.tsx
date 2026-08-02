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
import { Button } from '../components/Button';
import { TrophyCard } from '../components/TrophyCard';
import { TimelineItem } from '../components/TimelineItem';
import {
  MOCK_USER,
  MOCK_PLAYER_TROPHIES,
  MOCK_CAREER_TIMELINE,
} from '../constants/mock';

type Tab = 'overview' | 'trophies' | 'career';

interface Props {
  onLogout?: () => void;
}

export function ProfileScreen({ onLogout }: Props) {
  const [tab, setTab] = useState<Tab>('overview');
  const initials = MOCK_USER.gamertag.slice(0, 2).toUpperCase();

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor={colors.black} />
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Profile header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initials}</Text>
          </View>
          <Text style={styles.gamertag}>{MOCK_USER.gamertag}</Text>
          <Text style={styles.displayName}>{MOCK_USER.displayName}</Text>
          <View style={styles.tierRow}>
            <TierBadge tier={MOCK_USER.competitiveTier} />
            <Text style={styles.roleTag}>{MOCK_USER.primaryRole}</Text>
          </View>
        </View>

        {/* Tabs */}
        <View style={styles.tabs}>
          {(['overview', 'trophies', 'career'] as Tab[]).map((t) => (
            <TouchableOpacity
              key={t}
              style={[styles.tab, tab === t && styles.tabActive]}
              onPress={() => setTab(t)}
              activeOpacity={0.8}
            >
              <Text style={[styles.tabText, tab === t && styles.tabTextActive]}>
                {t === 'overview' ? 'Overview' : t === 'trophies' ? 'Trophies' : 'Career'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* ── Overview ─────────────────────────────────────────────── */}
        {tab === 'overview' && (
          <>
            <View style={styles.card}>
              <View style={styles.statRow}>
                <Text style={styles.statLabel}>Market value</Text>
                <Text style={styles.statValue}>
                  ₦{MOCK_USER.marketValueNgn.toLocaleString()}
                </Text>
              </View>
              <View style={styles.divider} />
              <View style={styles.statRow}>
                <Text style={styles.statLabel}>Organization</Text>
                <Text style={styles.statValue}>{MOCK_USER.orgName}</Text>
              </View>
              <View style={styles.divider} />
              <View style={styles.statRow}>
                <Text style={styles.statLabel}>Preferred roles</Text>
                <Text style={styles.statValue}>
                  {MOCK_USER.preferredRoles.join(' · ')}
                </Text>
              </View>
              <View style={styles.divider} />
              <View style={styles.statRow}>
                <Text style={styles.statLabel}>Availability</Text>
                <Text
                  style={[
                    styles.statValue,
                    {
                      color:
                        MOCK_USER.availabilityStatus === 'Available'
                          ? colors.success
                          : colors.warning,
                    },
                  ]}
                >
                  {MOCK_USER.availabilityStatus}
                </Text>
              </View>
              <View style={styles.divider} />
              <View style={styles.statRow}>
                <Text style={styles.statLabel}>Region</Text>
                <Text style={styles.statValue}>{MOCK_USER.region}</Text>
              </View>
            </View>

            {/* Quick trophy preview */}
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Recent trophies</Text>
              <TouchableOpacity onPress={() => setTab('trophies')}>
                <Text style={styles.seeAll}>See all</Text>
              </TouchableOpacity>
            </View>
            {MOCK_PLAYER_TROPHIES.slice(0, 2).map((t) => (
              <TrophyCard key={t.id} trophy={t} />
            ))}

            <View style={{ height: theme.spacing.lg }} />
            <TouchableOpacity style={styles.menuItem} activeOpacity={0.7}>
              <Text style={styles.menuText}>Edit profile</Text>
              <Text style={styles.chevron}>›</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.menuItem} activeOpacity={0.7}>
              <Text style={styles.menuText}>Contract details</Text>
              <Text style={styles.chevron}>›</Text>
            </TouchableOpacity>

            <View style={{ height: theme.spacing.xl }} />
            <Button title="Log out" variant="outline" onPress={onLogout || (() => {})} />
          </>
        )}

        {/* ── Trophy Cabinet (Player) ──────────────────────────────── */}
        {tab === 'trophies' && (
          <>
            <View style={styles.cabinetHeader}>
              <Text style={styles.cabinetTitle}>Trophy Cabinet</Text>
              <Text style={styles.cabinetSub}>
                {MOCK_PLAYER_TROPHIES.length} trophies · Individual
              </Text>
            </View>

            {/* Rarity summary */}
            <View style={styles.rarityRow}>
              {(['legendary', 'epic', 'rare', 'common'] as const).map((r) => {
                const count = MOCK_PLAYER_TROPHIES.filter((t) => t.rarity === r).length;
                if (count === 0) return null;
                return (
                  <View key={r} style={styles.rarityChip}>
                    <Text style={styles.rarityCount}>{count}</Text>
                    <Text style={styles.rarityLabel}>{r}</Text>
                  </View>
                );
              })}
            </View>

            {MOCK_PLAYER_TROPHIES.map((t) => (
              <TrophyCard key={t.id} trophy={t} />
            ))}
          </>
        )}

        {/* ── Career Timeline ──────────────────────────────────────── */}
        {tab === 'career' && (
          <>
            <View style={styles.cabinetHeader}>
              <Text style={styles.cabinetTitle}>Career Timeline</Text>
              <Text style={styles.cabinetSub}>
                Promotions, transfers, trophies & milestones
              </Text>
            </View>

            <View style={styles.timelineWrap}>
              {MOCK_CAREER_TIMELINE.map((event, idx) => (
                <TimelineItem
                  key={event.id}
                  event={event}
                  isLast={idx === MOCK_CAREER_TIMELINE.length - 1}
                />
              ))}
            </View>
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
  profileHeader: {
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.blue,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.md,
  },
  avatarText: {
    color: colors.white,
    fontSize: 28,
    fontWeight: '700',
  },
  gamertag: {
    color: colors.white,
    fontSize: theme.fontSize.xl,
    fontWeight: theme.fontWeight.bold,
  },
  displayName: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
    marginTop: 2,
    marginBottom: theme.spacing.sm,
  },
  tierRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  roleTag: {
    color: colors.blueBright,
    fontSize: 13,
    fontWeight: '600',
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

  // Overview card
  card: {
    backgroundColor: colors.blackCard,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: theme.spacing.lg,
  },
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  statLabel: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
  },
  statValue: {
    color: colors.white,
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
  },

  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  sectionTitle: {
    color: colors.white,
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.semibold,
  },
  seeAll: {
    color: colors.blueBright,
    fontSize: 13,
    fontWeight: '600',
  },

  menuItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.blackCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: theme.spacing.sm,
  },
  menuText: {
    color: colors.white,
    fontSize: theme.fontSize.md,
  },
  chevron: {
    color: colors.gray500,
    fontSize: 22,
  },

  // Trophy cabinet
  cabinetHeader: {
    marginBottom: theme.spacing.md,
  },
  cabinetTitle: {
    color: colors.white,
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.bold,
  },
  cabinetSub: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
    marginTop: 2,
  },
  rarityRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: theme.spacing.lg,
  },
  rarityChip: {
    backgroundColor: colors.blackCard,
    borderRadius: theme.radius.sm,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    minWidth: 64,
  },
  rarityCount: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '700',
  },
  rarityLabel: {
    color: colors.gray500,
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
    marginTop: 2,
  },

  timelineWrap: {
    marginTop: theme.spacing.sm,
  },
});
