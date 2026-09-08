import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { platformApi, RosterEvent } from '../services/api';
import { errorMessage } from '../services/session';
import { colors } from '../theme/colors';
import { Button } from './Button';

export function RosterHistory() {
  const [events, setEvents] = useState<RosterEvent[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    platformApi.squads.myTimeline().then(rows => { if (active) setEvents(rows); })
      .catch(error => { if (active) setError(errorMessage(error, 'Could not load your roster history.')); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [attempt]);
  return <View style={{ gap: 14 }}>
    <Text style={{ color: colors.white, fontSize: 18, fontWeight: '600' }}>Your roster history</Text>
    {loading ? <ActivityIndicator color={colors.white} accessibilityLabel="Loading roster history" /> : null}
    {error ? <Text accessibilityRole="alert" style={{ color: colors.error, fontSize: 15 }}>{error}</Text> : null}
    {!loading && !error && !events.length ? <Text style={{ color: colors.muted, fontSize: 15 }}>No roster changes recorded yet.</Text> : null}
    {!error && events.map(event => <View key={event.id} style={{ paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: colors.border }}>
      <Text style={{ color: colors.white, fontSize: 16 }}>{event.description}</Text>
      <Text style={{ color: colors.muted, fontSize: 14, marginTop: 6 }}>{event.event_type} · {new Date(event.created_at).toLocaleString()}</Text>
    </View>)}
    <Button title="Refresh history" disabled={loading} variant="outline" onPress={() => setAttempt(value => value + 1)} />
  </View>;
}
