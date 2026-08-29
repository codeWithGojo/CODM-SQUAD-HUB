import React, { memo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import Svg, { Circle, Line, Polygon, Polyline, Text as SvgText } from 'react-native-svg';
import { colors } from '../theme/colors';

type RoleMetric = 'Objective pressure' | 'Trades' | 'Survival' | 'Kills' | 'Objective' | 'Consistency';

type HillPlayer = {
  id: string;
  name: string;
  role: string;
  grade: string;
  hillKills: number[];
  profile: Record<RoleMetric, number>;
};

const HILL_LABELS = ['P1', 'P2', 'P3', 'P4', 'P1', 'P2', 'P3', 'P4', 'P1'];
const SHARED_SCALE = 12;

const PLAYERS: HillPlayer[] = [
  {
    id: 'gojo',
    name: 'N¡M・GOJO',
    role: 'Support / OBJ',
    grade: 'A+',
    hillKills: [4, 4, 6, 5, 6, 7, 8, 4, 2],
    profile: { 'Objective pressure': 88, Trades: 84, Survival: 72, Kills: 79, Objective: 94, Consistency: 86 },
  },
  {
    id: 'ares',
    name: 'NIM・ARES',
    role: 'Main slayer',
    grade: 'B+',
    hillKills: [4, 2, 7, 4, 4, 6, 2, 3, 4],
    profile: { 'Objective pressure': 62, Trades: 78, Survival: 69, Kills: 87, Objective: 51, Consistency: 73 },
  },
  {
    id: 'kairo',
    name: 'NIM・KAIRO',
    role: 'Flex',
    grade: 'A−',
    hillKills: [6, 3, 3, 5, 5, 4, 5, 4, 5],
    profile: { 'Objective pressure': 76, Trades: 81, Survival: 75, Kills: 82, Objective: 73, Consistency: 89 },
  },
  {
    id: 'zen',
    name: 'NIM・ZEN',
    role: 'IGL / flex',
    grade: 'B',
    hillKills: [2, 5, 4, 8, 3, 1, 5, 4, 3],
    profile: { 'Objective pressure': 80, Trades: 76, Survival: 77, Kills: 70, Objective: 81, Consistency: 64 },
  },
  {
    id: 'flux',
    name: 'NIM・FLUX',
    role: 'Entry slayer',
    grade: 'A',
    hillKills: [4, 11, 4, 2, 2, 4, 3, 1, 4],
    profile: { 'Objective pressure': 68, Trades: 71, Survival: 58, Kills: 92, Objective: 55, Consistency: 48 },
  },
];

function sum(values: number[]) {
  return values.reduce((total, value) => total + value, 0);
}

function playerStats(player: HillPlayer) {
  const total = sum(player.hillKills);
  const average = total / player.hillKills.length;
  const peak = Math.max(...player.hillKills);
  const peakIndex = player.hillKills.indexOf(peak);
  const variance = sum(player.hillKills.map(value => (value - average) ** 2)) / player.hillKills.length;
  const deviation = Math.sqrt(variance);
  const consistency = Math.max(0, Math.min(100, Math.round(100 - deviation * 16)));
  return { total, average, peak, peakIndex, consistency };
}

const TEAM_KILLS = sum(PLAYERS.map(player => sum(player.hillKills)));
const STREAKIEST = PLAYERS.reduce((current, player) => {
  const stats = playerStats(player);
  const currentStats = playerStats(current);
  return stats.peak - stats.average > currentStats.peak - currentStats.average ? player : current;
});
const STREAK_STATS = playerStats(STREAKIEST);
const STREAK_PEAK_SHARE = Math.round((STREAK_STATS.peak / STREAK_STATS.total) * 100);

function chartPoints(values: number[], width: number, height: number) {
  const left = 27;
  const right = 8;
  const top = 13;
  const bottom = 24;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  return values.map((value, index) => ({
    x: left + (plotWidth * index) / Math.max(1, values.length - 1),
    y: top + plotHeight - (Math.min(SHARED_SCALE, value) / SHARED_SCALE) * plotHeight,
  }));
}

const HillTrendChart = memo(function HillTrendChart({ player, width }: { player: HillPlayer; width: number }) {
  const height = 142;
  const points = chartPoints(player.hillKills, width, height);
  const baseline = height - 24;
  const linePoints = points.map(point => `${point.x},${point.y}`).join(' ');
  const fillPoints = `${points[0].x},${baseline} ${linePoints} ${points[points.length - 1]?.x ?? width - 8},${baseline}`;
  const stats = playerStats(player);

  return (
    <View
      accessible
      accessibilityRole="image"
      accessibilityLabel={`${player.name} hill output: ${player.hillKills.join(', ')} kills across nine active hills, ${stats.total} total kills.`}
    >
      <Svg width={width} height={height}>
        {[0, 6, 12].map(value => {
          const y = 13 + (SHARED_SCALE - value) * ((height - 37) / SHARED_SCALE);
          return (
            <React.Fragment key={value}>
              <Line x1="27" x2={width - 8} y1={y} y2={y} stroke="#282B34" strokeWidth="1" />
              <SvgText x="2" y={y + 3} fill="#747986" fontSize="8">{value}</SvgText>
            </React.Fragment>
          );
        })}
        <Polygon points={fillPoints} fill="#DA373C" opacity="0.12" />
        <Polyline points={linePoints} fill="none" stroke="#F04A50" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        {points.map((point, index) => (
          <React.Fragment key={`${HILL_LABELS[index]}-${index}`}>
            <Circle cx={point.x} cy={point.y} r="3.4" fill="#FF9EA2" stroke="#DA373C" strokeWidth="1.5" />
            <SvgText x={point.x} y={height - 7} fill="#747986" fontSize="7" textAnchor="middle">{HILL_LABELS[index]}</SvgText>
            {index === stats.peakIndex ? (
              <SvgText x={point.x} y={Math.max(9, point.y - 8)} fill="#FFFFFF" fontSize="9" fontWeight="700" textAnchor="middle">{stats.peak}</SvgText>
            ) : null}
          </React.Fragment>
        ))}
      </Svg>
    </View>
  );
});

const PlayerOutputCard = memo(function PlayerOutputCard({
  player,
  width,
  selected,
  onSelect,
}: {
  player: HillPlayer;
  width: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const stats = playerStats(player);
  return (
    <Pressable
      onPress={onSelect}
      style={[styles.playerCard, { width }, selected ? styles.playerCardSelected : null]}
      accessibilityRole="button"
      accessibilityState={{ selected }}
      accessibilityLabel={`Select ${player.name}, ${stats.total} kills, grade ${player.grade}`}
    >
      <View style={styles.cardTop}>
        <View>
          <Text style={styles.playerName}>{player.name}</Text>
          <Text style={styles.role}>{player.role}</Text>
        </View>
        <View style={styles.totalWrap}>
          <Text style={styles.total}>{stats.total}</Text>
          <Text style={styles.totalLabel}>KILLS</Text>
        </View>
      </View>
      <HillTrendChart player={player} width={width - 22} />
      <View style={styles.cardStats}>
        <Text style={styles.cardStat}>Peak <Text style={styles.cardStatValue}>{stats.peak} · {HILL_LABELS[stats.peakIndex]}</Text></Text>
        <Text style={styles.cardStat}>Avg <Text style={styles.cardStatValue}>{stats.average.toFixed(1)}</Text></Text>
        <Text style={styles.cardStat}>Consistency <Text style={styles.cardStatValue}>{stats.consistency}</Text></Text>
      </View>
    </Pressable>
  );
});

function polarPoint(centerX: number, centerY: number, radius: number, index: number, total: number) {
  const angle = -Math.PI / 2 + (index * Math.PI * 2) / total;
  return { x: centerX + Math.cos(angle) * radius, y: centerY + Math.sin(angle) * radius };
}

const RoleRadar = memo(function RoleRadar({ player, width }: { player: HillPlayer; width: number }) {
  const height = 238;
  const centerX = width / 2;
  const centerY = 111;
  const radius = Math.min(72, width * 0.24);
  const metrics = Object.entries(player.profile) as [RoleMetric, number][];
  const ring = (ratio: number) => metrics.map((_, index) => {
    const point = polarPoint(centerX, centerY, radius * ratio, index, metrics.length);
    return `${point.x},${point.y}`;
  }).join(' ');
  const valuePoints = metrics.map(([, value], index) => {
    const point = polarPoint(centerX, centerY, radius * value / 100, index, metrics.length);
    return `${point.x},${point.y}`;
  }).join(' ');

  return (
    <View accessible accessibilityRole="image" accessibilityLabel={`${player.name} role profile. ${metrics.map(([label, value]) => `${label} ${value}`).join(', ')}.`}>
      <Svg width={width} height={height}>
        {[0.33, 0.66, 1].map(ratio => <Polygon key={ratio} points={ring(ratio)} fill="none" stroke="#343844" strokeWidth="1" />)}
        {metrics.map(([label], index) => {
          const edge = polarPoint(centerX, centerY, radius, index, metrics.length);
          const text = polarPoint(centerX, centerY, radius + 27, index, metrics.length);
          return (
            <React.Fragment key={label}>
              <Line x1={centerX} y1={centerY} x2={edge.x} y2={edge.y} stroke="#2B2F39" strokeWidth="1" />
              <SvgText x={text.x} y={text.y + 3} fill="#8C919D" fontSize="7" fontWeight="600" textAnchor="middle">{label.toUpperCase()}</SvgText>
            </React.Fragment>
          );
        })}
        <Polygon points={valuePoints} fill="#DA373C" fillOpacity="0.2" stroke="#F04A50" strokeWidth="2" />
        {metrics.map(([, value], index) => {
          const point = polarPoint(centerX, centerY, radius * value / 100, index, metrics.length);
          return <Circle key={index} cx={point.x} cy={point.y} r="3" fill="#FFB0B3" stroke="#DA373C" strokeWidth="1" />;
        })}
        <SvgText x={centerX} y={centerY + 3} fill="#FFFFFF" fontSize="12" fontWeight="800" textAnchor="middle">{player.grade}</SvgText>
      </Svg>
    </View>
  );
});

export function HillByHillAnalytics() {
  const { width: viewportWidth } = useWindowDimensions();
  const cardWidth = Math.max(260, Math.min(342, viewportWidth - 58));
  const [selectedId, setSelectedId] = useState(PLAYERS[0].id);
  const selected = PLAYERS.find(player => player.id === selectedId) ?? PLAYERS[0];
  const selectedStats = playerStats(selected);

  return (
    <View>
      <View style={styles.hero}>
        <View style={styles.heroTop}>
          <View style={styles.flex}>
            <Text style={styles.eyebrow}>HARDPOINT INTELLIGENCE</Text>
            <Text style={styles.title}>Hill-by-hill output</Text>
            <Text style={styles.copy}>Kills during each of nine active hills on a shared 0–12 scale.</Text>
          </View>
          <View style={styles.livePill}><Text style={styles.liveText}>ANALYZED</Text></View>
        </View>
        <View style={styles.teamMetrics}>
          <View><Text style={styles.metricValue}>{TEAM_KILLS}</Text><Text style={styles.metricLabel}>TEAM KILLS</Text></View>
          <View><Text style={styles.metricValue}>9</Text><Text style={styles.metricLabel}>ACTIVE HILLS</Text></View>
          <View><Text style={styles.metricValue}>0–12</Text><Text style={styles.metricLabel}>SHARED SCALE</Text></View>
        </View>
      </View>

      <Text style={styles.sectionTitle}>PLAYER OUTPUT · TAP TO INSPECT</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        snapToInterval={cardWidth + 10}
        decelerationRate="fast"
        contentContainerStyle={styles.cardRail}
      >
        {PLAYERS.map(player => (
          <PlayerOutputCard
            key={player.id}
            player={player}
            width={cardWidth}
            selected={selected.id === player.id}
            onSelect={() => setSelectedId(player.id)}
          />
        ))}
      </ScrollView>

      <View style={styles.profileCard}>
        <View style={styles.profileTop}>
          <View>
            <Text style={styles.eyebrow}>SELECTED PROFILE</Text>
            <Text style={styles.profileName}>{selected.name}</Text>
            <Text style={styles.role}>{selected.role}</Text>
          </View>
          <View style={styles.grade}><Text style={styles.gradeText}>{selected.grade}</Text></View>
        </View>
        <RoleRadar player={selected} width={cardWidth - 4} />
        <View style={styles.profileMetrics}>
          <View style={styles.profileMetric}><Text style={styles.profileMetricValue}>{selectedStats.total}</Text><Text style={styles.profileMetricLabel}>KILLS</Text></View>
          <View style={styles.profileMetric}><Text style={styles.profileMetricValue}>{selectedStats.peak}</Text><Text style={styles.profileMetricLabel}>PEAK HILL</Text></View>
          <View style={styles.profileMetric}><Text style={styles.profileMetricValue}>{selectedStats.consistency}</Text><Text style={styles.profileMetricLabel}>CONSISTENCY</Text></View>
        </View>
      </View>

      <View style={styles.insightCard}>
        <Text style={styles.insightTag}>AI MATCH NOTE</Text>
        <Text style={styles.insightTitle}>{STREAKIEST.name} produced the sharpest spike.</Text>
        <Text style={styles.insightCopy}>{STREAK_PEAK_SHARE}% of {STREAKIEST.name}'s eliminations came on {HILL_LABELS[STREAK_STATS.peakIndex]}. Review the setup before that hill to separate repeatable positioning from a one-off heater.</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  hero: { backgroundColor: '#15171C', borderWidth: 1, borderColor: '#353840', borderRadius: 12, padding: 14, marginBottom: 16 },
  heroTop: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  eyebrow: { color: colors.redBright, fontSize: 7.5, fontWeight: '800', letterSpacing: 1.2 },
  title: { color: colors.white, fontSize: 20, fontWeight: '800', marginTop: 5 },
  copy: { color: colors.muted, fontSize: 8.5, lineHeight: 13, marginTop: 4 },
  livePill: { backgroundColor: '#26382E', borderWidth: 1, borderColor: '#347B54', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 6 },
  liveText: { color: '#68D99C', fontSize: 6.5, fontWeight: '800', letterSpacing: 0.7 },
  teamMetrics: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 16, paddingTop: 13, borderTopWidth: 1, borderTopColor: '#2A2D34' },
  metricValue: { color: colors.white, fontSize: 17, fontWeight: '800' },
  metricLabel: { color: colors.subtle, fontSize: 6.5, fontWeight: '700', marginTop: 3 },
  sectionTitle: { color: colors.subtle, fontSize: 7.5, fontWeight: '800', letterSpacing: 1.1, marginBottom: 9 },
  cardRail: { gap: 10, paddingRight: 12, paddingBottom: 16 },
  playerCard: { backgroundColor: '#1B1D22', borderWidth: 1, borderColor: '#30333B', borderRadius: 12, padding: 11 },
  playerCardSelected: { borderColor: '#A72E36', backgroundColor: '#201A1D' },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  playerName: { color: colors.white, fontSize: 11, fontWeight: '800' },
  role: { color: colors.muted, fontSize: 7.5, marginTop: 3 },
  totalWrap: { alignItems: 'flex-end' },
  total: { color: colors.white, fontSize: 16, fontWeight: '800' },
  totalLabel: { color: colors.subtle, fontSize: 6.5, fontWeight: '700' },
  cardStats: { flexDirection: 'row', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: '#2A2D34', paddingTop: 9 },
  cardStat: { color: colors.subtle, fontSize: 7 },
  cardStatValue: { color: colors.white, fontWeight: '700' },
  profileCard: { backgroundColor: '#15171C', borderWidth: 1, borderColor: '#353840', borderRadius: 12, padding: 13, marginBottom: 12, alignItems: 'center' },
  profileTop: { alignSelf: 'stretch', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  profileName: { color: colors.white, fontSize: 14, fontWeight: '800', marginTop: 5 },
  grade: { width: 38, height: 38, borderRadius: 8, borderWidth: 1, borderColor: '#3B9B67', backgroundColor: '#20362A', alignItems: 'center', justifyContent: 'center' },
  gradeText: { color: '#69D99A', fontSize: 14, fontWeight: '900' },
  profileMetrics: { alignSelf: 'stretch', flexDirection: 'row', gap: 8 },
  profileMetric: { flex: 1, backgroundColor: '#1D2026', borderRadius: 8, padding: 10, alignItems: 'center' },
  profileMetricValue: { color: colors.white, fontSize: 16, fontWeight: '800' },
  profileMetricLabel: { color: colors.subtle, fontSize: 6.5, fontWeight: '700', marginTop: 3 },
  insightCard: { backgroundColor: '#211719', borderLeftWidth: 3, borderLeftColor: colors.redBright, borderRadius: 10, padding: 13, marginBottom: 8 },
  insightTag: { color: colors.redBright, fontSize: 7, fontWeight: '800', letterSpacing: 1 },
  insightTitle: { color: colors.white, fontSize: 12, fontWeight: '800', marginTop: 6 },
  insightCopy: { color: colors.muted, fontSize: 8.5, lineHeight: 13, marginTop: 5 },
});
