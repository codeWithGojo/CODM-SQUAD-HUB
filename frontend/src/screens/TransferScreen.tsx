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
import { OfferCard } from '../components/OfferCard';
import { EmptyState } from '../components/EmptyState';
import { MOCK_OFFERS } from '../constants/mock';

const TABS = ['Offers', 'Free Agents', 'My Listings', 'History'] as const;

export function TransferScreen() {
  const [tab, setTab] = useState<(typeof TABS)[number]>('Offers');

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor={colors.black} />
      <View style={styles.header}>
        <Text style={styles.title}>Transfer Centre</Text>
        <Text style={styles.sub}>Buy · Sell · Loan · All in ₦</Text>
      </View>

      {/* Tabs */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.tabs}
      >
        {TABS.map((t) => (
          <TouchableOpacity
            key={t}
            onPress={() => setTab(t)}
            style={[styles.tab, tab === t && styles.tabActive]}
          >
            <Text style={[styles.tabText, tab === t && styles.tabTextActive]}>{t}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView contentContainerStyle={styles.scroll}>
        {tab === 'Offers' &&
          MOCK_OFFERS.map((o) => (
            <OfferCard
              key={o.id}
              offer={o}
              onAccept={() => {}}
              onCounter={() => {}}
              onReject={() => {}}
            />
          ))}

        {tab === 'Free Agents' && (
          <EmptyState
            title="No free agents right now"
            subtitle="Players without contracts will appear here"
          />
        )}

        {tab === 'My Listings' && (
          <EmptyState
            title="No active listings"
            subtitle="List a player for sale or loan from Squad"
          />
        )}

        {tab === 'History' && (
          <EmptyState
            title="No transfer history yet"
            subtitle="Completed deals will show here"
          />
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
  header: {
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.md,
    paddingBottom: theme.spacing.sm,
  },
  title: {
    color: colors.white,
    fontSize: theme.fontSize.xl,
    fontWeight: theme.fontWeight.bold,
  },
  sub: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
    marginTop: 2,
  },
  tabs: {
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    gap: 8,
  },
  tab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: theme.radius.full,
    backgroundColor: colors.blackCard,
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: 8,
  },
  tabActive: {
    backgroundColor: colors.blue,
    borderColor: colors.blue,
  },
  tabText: {
    color: colors.gray300,
    fontSize: 13,
    fontWeight: '600',
  },
  tabTextActive: {
    color: colors.white,
  },
  scroll: {
    padding: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
});
