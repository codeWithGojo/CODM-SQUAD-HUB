import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { usePlayerSession } from '../components/AuthGate';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { ApiError, Mode, OrganizationRecord, OrgTier, platformApi, PlayerLookup, Region, RosterEvent, RosterMember, SquadRecord } from '../services/api';
import { errorMessage } from '../services/session';
import { colors } from '../theme/colors';

const tiers: { value: OrgTier; label: string }[] = [
  { value: 'T1', label: 'First team' }, { value: 'T2', label: 'Second team' },
  { value: 'T3', label: 'Academy' }, { value: 'T4', label: 'Development' },
];
type Form = 'org' | 'squad' | 'add' | 'move' | 'remove' | null;

export function OrganizationScreen({ onBack }: { onBack: () => void }) {
  const { user } = usePlayerSession();
  const [orgs, setOrgs] = useState<OrganizationRecord[]>([]);
  const [squads, setSquads] = useState<SquadRecord[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [orgId, setOrgId] = useState('');
  const [teamId, setTeamId] = useState('');
  const [members, setMembers] = useState<RosterMember[]>([]);
  const [history, setHistory] = useState<RosterEvent[]>([]);
  const [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(true);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [rosterError, setRosterError] = useState('');
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState<Form>(null);
  const [formError, setFormError] = useState('');
  const [name, setName] = useState('');
  const [tier, setTier] = useState<OrgTier>('T1');
  const [mode, setMode] = useState<Mode>('MP');
  const [country, setCountry] = useState('NG');
  const [shid, setShid] = useState('');
  const [found, setFound] = useState<PlayerLookup | null>(null);
  const [role, setRole] = useState<'player' | 'substitute'>('player');
  const [selected, setSelected] = useState<RosterMember | null>(null);
  const [destination, setDestination] = useState('');
  const live = useRef(true);
  const selectedIds = useRef({ orgId, teamId });
  selectedIds.current = { orgId, teamId };
  const operation = useRef(false);
  const currentTeam = squads.find(row => row.id === teamId);
  const currentOrg = orgs.find(row => row.id === orgId);
  const visibleSquads = squads.filter(row => (row.organization_id ?? '') === orgId);
  const canCreate = !orgId || currentOrg?.can_manage_roster;

  async function load(preferred?: { orgId: string; teamId: string }) {
    const [organizations, teams, directory] = await Promise.all([
      platformApi.organizations.mine(), platformApi.squads.mine(), platformApi.identity.regions(),
    ]);
    if (!live.current) return;
    setOrgs(organizations); setSquads(teams); setRegions(directory);
    const desired = preferred ?? selectedIds.current;
    const nextOrg = desired.orgId && organizations.some(row => row.id === desired.orgId)
      ? desired.orgId : desired.teamId || !organizations.length ? '' : organizations[0].id;
    const available = teams.filter(row => (row.organization_id ?? '') === nextOrg);
    setOrgId(nextOrg);
    setTeamId(available.find(row => row.id === desired.teamId)?.id ?? available[0]?.id ?? '');
    setRefresh(value => value + 1); setError('');
  }

  async function reload() {
    setLoading(true);
    try { await load(); }
    catch (error) { if (live.current) setError(errorMessage(error, 'Could not load your squads.')); }
    finally { if (live.current) setLoading(false); }
  }
  useEffect(() => {
    live.current = true;
    void reload();
    return () => { live.current = false; };
  }, []);
  useEffect(() => {
    let active = true;
    setMembers([]); setHistory([]); setRosterError('');
    if (!teamId) { setRosterLoading(false); return; }
    setRosterLoading(true);
    Promise.all([platformApi.squads.members(teamId), platformApi.squads.timeline(teamId).catch(error => {
      if (error instanceof ApiError && error.status === 403) return [];
      throw error;
    })]).then(([people, events]) => { if (active) { setMembers(people); setHistory(events); } })
      .catch(error => { if (active) setRosterError(errorMessage(error, 'Could not load this roster.')); })
      .finally(() => { if (active) setRosterLoading(false); });
    return () => { active = false; };
  }, [teamId, refresh]);

  function open(next: Form, member?: RosterMember) {
    setFormError(''); setNotice(''); setName(''); setShid(''); setFound(null); setDestination('');
    setSelected(member ?? null); setRole(member?.role === 'substitute' ? 'substitute' : 'player');
    setCountry(regions.find(row => row.id === user.region_id)?.code ?? 'NG');
    setMode(currentTeam?.primary_mode ?? user.preferred_mode ?? 'MP'); setForm(next);
  }
  async function save() {
    if (operation.current) return;
    operation.current = true; setBusy(true); setFormError('');
    let preferred: { orgId: string; teamId: string } | undefined;
    let saved = false;
    try {
      if (form === 'org') {
        if (name.trim().length < 2) throw new Error('Enter an organization name.');
        const org = await platformApi.organizations.create(name.trim());
        preferred = { orgId: org.id, teamId: '' };
      } else if (form === 'squad') {
        const region = regions.find(row => row.code === country.trim().toUpperCase());
        if (name.trim().length < 2 || !region) throw new Error('Enter a squad name and a valid country code.');
        const team = await platformApi.squads.create({ name: name.trim(), region_id: region.id,
          organization_id: orgId || null, org_tier: orgId ? tier : null, primary_mode: mode });
        preferred = { orgId, teamId: team.id };
      } else if (form === 'add' && found && currentTeam) {
        await platformApi.squads.add(currentTeam.id, found.id, role);
      } else if (form === 'move' && selected && currentTeam) {
        if (!destination) throw new Error('Choose a destination squad.');
        await platformApi.squads.move(currentTeam.id, selected.user_id, destination, role);
      } else if (form === 'remove' && selected && currentTeam) {
        await platformApi.squads.remove(currentTeam.id, selected.user_id);
      } else throw new Error('Select a player first.');
      saved = true;
      if (!live.current) return;
      setForm(null); setNotice('Saved.');
      await load(preferred);
    } catch (error) {
      if (live.current) {
        const message = errorMessage(error, 'Could not save this change.');
        if (saved) setError(`Change saved, but refresh failed. ${message}`); else setFormError(message);
      }
    } finally { operation.current = false; if (live.current) setBusy(false); }
  }
  async function lookup() {
    if (operation.current) return;
    operation.current = true; setBusy(true); setFormError(''); setFound(null);
    try {
      const player = await platformApi.squads.findPlayer(shid);
      if (live.current) setFound(player);
    } catch (error) { if (live.current) setFormError(errorMessage(error, 'Player not found.')); }
    finally { operation.current = false; if (live.current) setBusy(false); }
  }

  return <View style={s.screen}>
    <View style={s.header}><Button title="Back" variant="ghost" onPress={onBack} disabled={busy} />
      <Text style={s.heading}>Organizations & squads</Text></View>
    <ScrollView contentContainerStyle={s.content}>
      {loading ? <ActivityIndicator color={colors.white} accessibilityLabel="Loading organizations" /> : null}
      {error ? <Text style={s.error} accessibilityRole="alert">{error}</Text> : null}
      <View style={s.row}><Button title="Refresh" variant="outline" disabled={loading || busy} onPress={() => { void reload(); }} />
        <Button title="Create organization" disabled={loading || busy || !!error} onPress={() => open('org')} /></View>
      {notice ? <Text style={s.copy} accessibilityLiveRegion="polite">{notice}</Text> : null}
      <ScrollView horizontal contentContainerStyle={s.choices}>
        {[{ id: '', name: 'Standalone squads' }, ...orgs].map(org => <Choice key={org.id} label={org.name}
          selected={orgId === org.id} disabled={busy || loading} onPress={() => {
            setOrgId(org.id); setTeamId(squads.find(team => (team.organization_id ?? '') === org.id)?.id ?? '');
          }} />)}
      </ScrollView>
      <View style={s.row}><Text style={s.title}>{currentOrg?.name ?? 'Standalone squads'}</Text>
        {canCreate ? <Button title="Create squad" disabled={loading || busy || !!error} onPress={() => open('squad')} /> : null}</View>
      {!loading && !visibleSquads.length && !error ? <Text style={s.copy}>No squads yet.</Text> : null}
      <View style={s.choices}>{visibleSquads.map(team => <Choice key={team.id}
        label={`${team.org_tier ? `${team.org_tier} · ` : ''}${team.name} · ${team.primary_mode ?? 'MP / BR'}`}
        selected={team.id === teamId} disabled={busy} onPress={() => setTeamId(team.id)} />)}</View>
      {currentTeam ? <>
        <View style={s.row}><Text style={s.title}>{currentTeam.name}</Text>
          {currentTeam.can_manage_roster ? <Button title="Add player" disabled={busy || rosterLoading || !!rosterError} onPress={() => open('add')} /> : null}</View>
        {rosterLoading ? <ActivityIndicator color={colors.white} accessibilityLabel="Loading roster" /> : null}
        {rosterError ? <><Text style={s.error} accessibilityRole="alert">{rosterError}</Text>
          <Button title="Retry roster" onPress={() => setRefresh(value => value + 1)} /></> : null}
        {members.map(member => <View key={member.id} style={s.card}>
          <Text style={s.title}>{member.gamertag}</Text><Text style={s.copy}>{member.shid} · {member.role}</Text>
          {currentTeam.can_manage_roster && member.role !== 'manager' ? <View style={s.row}>
            {currentTeam.organization_id ? <Button title="Move roster" variant="outline" disabled={busy} onPress={() => open('move', member)} /> : null}
            <Button title="Remove" variant="ghost" disabled={busy} onPress={() => open('remove', member)} />
          </View> : null}
        </View>)}
        <Text style={s.title}>Roster history</Text>
        {!rosterLoading && !rosterError && !history.length ? <Text style={s.copy}>No roster history available.</Text> : null}
        {history.map(event => <View style={s.card} key={event.id}><Text style={s.copy}>{event.description}</Text>
          <Text style={s.meta}>{event.event_type} · {new Date(event.created_at).toLocaleString()}</Text></View>)}
      </> : null}
    </ScrollView>
    <Modal visible={form !== null} animationType="slide" onRequestClose={() => { if (!busy) setForm(null); }}>
      <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={[s.content, { paddingTop: 48 }]} keyboardShouldPersistTaps="handled">
          <Button title="Cancel" variant="ghost" disabled={busy} onPress={() => setForm(null)} />
          <Text style={s.heading}>{form === 'org' ? 'Create organization' : form === 'squad' ? 'Create squad' : form === 'add' ? 'Add existing player' : form === 'move' ? 'Move player' : 'Remove player'}</Text>
          {form === 'org' || form === 'squad' ? <Input label="Name" value={name} onChangeText={setName} maxLength={100} editable={!busy} accessibilityLabel="Name" /> : null}
          {form === 'squad' ? <>
            {orgId ? <><Text style={s.copy}>Organization structure</Text><View style={s.choices}>{tiers.map(item => <Choice key={item.value}
              label={`${item.value} · ${item.label}`} selected={tier === item.value} disabled={busy} onPress={() => setTier(item.value)} />)}</View></> : null}
            <Input label="Country code" value={country} onChangeText={setCountry} maxLength={2} autoCapitalize="characters" editable={!busy} accessibilityLabel="Country code" />
            <Text style={s.meta}>{regions.find(row => row.code === country.toUpperCase())?.name ?? 'Use an African country code, e.g. NG.'}</Text>
            <View style={s.choices}>{(['MP', 'BR'] as Mode[]).map(value => <Choice key={value} label={value} selected={mode === value} disabled={busy} onPress={() => setMode(value)} />)}</View>
          </> : null}
          {form === 'add' ? <>
            <Input label="Squad Hub ID" placeholder="SH-…" value={shid} onChangeText={value => { setShid(value); setFound(null); }} editable={!busy} autoCapitalize="characters" accessibilityLabel="Player Squad Hub ID" />
            <Button title="Find player" variant="outline" onPress={() => { void lookup(); }} disabled={busy || !shid.trim()} />
            {found ? <Text style={s.title}>{found.gamertag} · {found.shid}</Text> : null}
            <Text style={s.copy}>Adds this existing account directly to the roster. This does not send an invitation or create a contract.</Text>
          </> : null}
          {form === 'move' ? <><Text style={s.copy}>Move {selected?.gamertag} to:</Text><View style={s.choices}>
            {squads.filter(team => team.id !== teamId && team.organization_id === currentTeam?.organization_id && team.can_manage_roster).map(team =>
              <Choice key={team.id} label={`${team.org_tier} · ${team.name}`} selected={destination === team.id} disabled={busy} onPress={() => setDestination(team.id)} />)}
          </View><Text style={s.copy}>The move is saved to the player’s timeline. Competitive results stay unchanged.</Text></> : null}
          {form === 'add' || form === 'move' ? <View style={s.choices}>{(['player', 'substitute'] as const).map(value =>
            <Choice key={value} label={value === 'player' ? 'Player' : 'Substitute'} selected={role === value} disabled={busy} onPress={() => setRole(value)} />)}</View> : null}
          {form === 'remove' ? <Text style={s.copy}>Remove {selected?.gamertag} from {currentTeam?.name}? A release event will be saved. Contracted players must use the contract workflow.</Text> : null}
          {formError ? <Text style={s.error} accessibilityRole="alert">{formError}</Text> : null}
          <Button title={form === 'remove' ? 'Confirm removal' : 'Save'} loading={busy} disabled={form === 'add' && !found}
            onPress={() => { void save(); }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  </View>;
}

function Choice({ label, selected, disabled, onPress }: { label: string; selected: boolean; disabled?: boolean; onPress: () => void }) {
  return <Pressable accessibilityRole="button" accessibilityState={{ selected, disabled }} disabled={disabled} onPress={onPress}
    style={[s.choice, selected && s.selected, disabled && { opacity: 0.5 }]}><Text style={s.copy}>{label}</Text></Pressable>;
}
const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  header: { padding: 12, borderBottomWidth: 1, borderBottomColor: colors.border },
  content: { padding: 16, paddingBottom: 40, gap: 14 },
  heading: { color: colors.white, fontSize: 22, fontWeight: '700' },
  title: { color: colors.white, fontSize: 17, fontWeight: '600', flexShrink: 1 },
  copy: { color: colors.white, fontSize: 15, lineHeight: 22 },
  meta: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  error: { color: colors.error, fontSize: 15, lineHeight: 22 },
  row: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 10 },
  choices: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 12, paddingVertical: 8, borderWidth: 1, borderColor: colors.border, borderRadius: 8 },
  selected: { borderColor: colors.magenta, backgroundColor: colors.redSoft },
  card: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 14, gap: 8 },
});
