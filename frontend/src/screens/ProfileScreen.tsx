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
import { Button } from '../components/Button';
import { MOCK_USER } from '../constants/mock';

interface Props {
  onLogout?: () => void;
}

export function ProfileScreen({ onLogout }: Props) {
  const initials = MOCK_USER.gamertag.slice(0, 2).toUpperCase();

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor={colors.black} />
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Avatar block */}
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

        {/* Stats card */}
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
            <Text style={styles.statLabel}>Region</Text>
            <Text style={styles.statValue}>{MOCK_USER.region}</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Account role</Text>
            <Text style={styles.statValue}>{MOCK_USER.role}</Text>
          </View>
        </View>

        {/* Actions */}
        <TouchableOpacity style={styles.menuItem} activeOpacity={0.7}>
          <Text style={styles.menuText}>Edit profile</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem} activeOpacity={0.7}>
          <Text style={styles.menuText}>Contract details</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem} activeOpacity={0.7}>
          <Text style={styles.menuText}>Notifications</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>

        <View style={{ height: theme.spacing.xl }} />
        <Button title="Log out" variant="outline" onPress={onLogout || (() => {})} />
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
    marginBottom: theme.spacing.xl,
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
});
