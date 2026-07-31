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
import { MOCK_USER } from '../constants/mock';

export function HomeScreen() {
  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor={colors.black} />
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Welcome back</Text>
            <Text style={styles.name}>{MOCK_USER.gamertag}</Text>
          </View>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {MOCK_USER.gamertag.slice(0, 2).toUpperCase()}
            </Text>
          </View>
        </View>

        <View style={styles.tierCard}>
          <Text style={styles.tierLabel}>Competitive Tier</Text>
          <Text style={styles.tierValue}>{MOCK_USER.competitiveTier}</Text>
          <Text style={styles.tierSub}>
            {MOCK_USER.orgName} · Market value ₦
            {MOCK_USER.marketValueNgn.toLocaleString()}
          </Text>
        </View>

        <Text style={styles.sectionTitle}>Quick actions</Text>
        <View style={styles.actions}>
          {[
            { label: 'Transfer Centre', icon: '⇄' },
            { label: 'My Squad', icon: '◈' },
            { label: 'Challenges', icon: '⚔' },
            { label: 'Scrims', icon: '◎' },
          ].map((item) => (
            <TouchableOpacity
              key={item.label}
              style={styles.actionCard}
              activeOpacity={0.8}
            >
              <Text style={styles.actionIcon}>{item.icon}</Text>
              <Text style={styles.actionLabel}>{item.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.sectionTitle}>Recent</Text>
        <View style={styles.activityCard}>
          <Text style={styles.activityTitle}>No recent matches yet</Text>
          <Text style={styles.activitySub}>
            Official results and scrims will show up here
          </Text>
        </View>
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.xl,
  },
  greeting: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
  },
  name: {
    color: colors.white,
    fontSize: theme.fontSize.xl,
    fontWeight: theme.fontWeight.bold,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.blue,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.white,
    fontWeight: '700',
    fontSize: 16,
  },
  tierCard: {
    backgroundColor: colors.blackCard,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.lg,
    borderWidth: 1,
    borderColor: colors.blueMuted,
    marginBottom: theme.spacing.xl,
  },
  tierLabel: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
    marginBottom: 4,
  },
  tierValue: {
    color: colors.blueBright,
    fontSize: 36,
    fontWeight: '700',
  },
  tierSub: {
    color: colors.gray500,
    fontSize: theme.fontSize.sm,
    marginTop: 4,
  },
  sectionTitle: {
    color: colors.white,
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.semibold,
    marginBottom: theme.spacing.md,
  },
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.xl,
  },
  actionCard: {
    width: '48%',
    backgroundColor: colors.blackCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: theme.spacing.sm,
  },
  actionIcon: {
    fontSize: 22,
    marginBottom: 6,
    color: colors.blueBright,
  },
  actionLabel: {
    color: colors.white,
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.medium,
  },
  activityCard: {
    backgroundColor: colors.blackCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  activityTitle: {
    color: colors.gray300,
    fontSize: theme.fontSize.md,
    marginBottom: 4,
  },
  activitySub: {
    color: colors.gray500,
    fontSize: theme.fontSize.sm,
    textAlign: 'center',
  },
});
