import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { TimelineEvent } from '../constants/mock';
import { colors, theme } from '../theme';

export function TimelineItem({ event, isLast }: { event: TimelineEvent; isLast: boolean }) {
  return (
    <View style={styles.row}>
      <View style={styles.rail}>
        <View style={styles.dot} />
        {!isLast && <View style={styles.line} />}
      </View>
      <View style={styles.content}>
        <Text style={styles.date}>{event.date}</Text>
        <Text style={styles.title}>{event.title}</Text>
        <Text style={styles.description}>{event.description}</Text>
        {event.meta ? <Text style={styles.meta}>{event.meta}</Text> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', minHeight: 86 },
  rail: { width: 24, alignItems: 'center' },
  dot: { width: 10, height: 10, borderRadius: 5, backgroundColor: colors.magenta, marginTop: 4 },
  line: { width: 1, flex: 1, backgroundColor: colors.border, marginVertical: 4 },
  content: { flex: 1, paddingBottom: theme.spacing.md },
  date: { color: colors.gray500, fontSize: 10 },
  title: { color: colors.white, fontSize: theme.fontSize.sm, fontWeight: theme.fontWeight.bold, marginTop: 3 },
  description: { color: colors.gray300, fontSize: theme.fontSize.xs, marginTop: 3 },
  meta: { color: colors.blueBright, fontSize: 10, fontWeight: theme.fontWeight.semibold, marginTop: 4 },
});
