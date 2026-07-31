import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { colors, theme } from '../theme';

export interface TransferOffer {
  id: string;
  playerName: string;
  fromOrg: string;
  offerType: 'buy' | 'sell' | 'loan';
  feeNgn: number;
  expiresIn: string;
  status: string;
}

interface Props {
  offer: TransferOffer;
  onAccept?: () => void;
  onCounter?: () => void;
  onReject?: () => void;
}

export function OfferCard({ offer, onAccept, onCounter, onReject }: Props) {
  const typeColor =
    offer.offerType === 'buy'
      ? colors.success
      : offer.offerType === 'loan'
      ? colors.warning
      : colors.blueBright;

  return (
    <View style={styles.card}>
      <View style={styles.top}>
        <View>
          <Text style={styles.player}>{offer.playerName}</Text>
          <Text style={styles.org}>from {offer.fromOrg}</Text>
        </View>
        <View style={[styles.typeBadge, { borderColor: typeColor }]}>
          <Text style={[styles.typeText, { color: typeColor }]}>
            {offer.offerType.toUpperCase()}
          </Text>
        </View>
      </View>

      <Text style={styles.fee}>₦{offer.feeNgn.toLocaleString()}</Text>
      <Text style={styles.expires}>Expires {offer.expiresIn}</Text>

      {(onAccept || onCounter || onReject) && (
        <View style={styles.actions}>
          {onReject && (
            <TouchableOpacity style={[styles.btn, styles.btnGhost]} onPress={onReject}>
              <Text style={styles.btnGhostText}>Reject</Text>
            </TouchableOpacity>
          )}
          {onCounter && (
            <TouchableOpacity style={[styles.btn, styles.btnOutline]} onPress={onCounter}>
              <Text style={styles.btnOutlineText}>Counter</Text>
            </TouchableOpacity>
          )}
          {onAccept && (
            <TouchableOpacity style={[styles.btn, styles.btnPrimary]} onPress={onAccept}>
              <Text style={styles.btnPrimaryText}>Accept</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.blackCard,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: theme.spacing.md,
  },
  top: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: theme.spacing.sm,
  },
  player: {
    color: colors.white,
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
  },
  org: {
    color: colors.gray300,
    fontSize: theme.fontSize.sm,
    marginTop: 2,
  },
  typeBadge: {
    borderWidth: 1,
    borderRadius: theme.radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  typeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  fee: {
    color: colors.blueBright,
    fontSize: theme.fontSize.xl,
    fontWeight: '700',
    marginBottom: 4,
  },
  expires: {
    color: colors.gray500,
    fontSize: theme.fontSize.xs,
    marginBottom: theme.spacing.md,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  btn: {
    flex: 1,
    height: 40,
    borderRadius: theme.radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnPrimary: {
    backgroundColor: colors.blue,
  },
  btnPrimaryText: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 13,
  },
  btnOutline: {
    borderWidth: 1,
    borderColor: colors.blue,
  },
  btnOutlineText: {
    color: colors.blueBright,
    fontWeight: '600',
    fontSize: 13,
  },
  btnGhost: {
    backgroundColor: colors.blackElevated,
  },
  btnGhostText: {
    color: colors.gray300,
    fontWeight: '600',
    fontSize: 13,
  },
});
