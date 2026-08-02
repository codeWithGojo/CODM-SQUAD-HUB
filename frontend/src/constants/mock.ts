import { Player } from '../components/PlayerCard';
import { TransferOffer } from '../components/OfferCard';

export const MOCK_PLAYERS: Player[] = [
  { id: '1', gamertag: 'AceKillerNG', role: 'AR', isStarter: true, competitiveTier: 'T2', marketValueNgn: 450000, trophyCount: 5 },
  { id: '2', gamertag: 'ShadowX', role: 'SMG', isStarter: true, competitiveTier: 'T2', marketValueNgn: 380000, trophyCount: 3 },
  { id: '3', gamertag: 'NovaSniper', role: 'Sniper', isStarter: true, competitiveTier: 'T3', marketValueNgn: 220000, trophyCount: 2 },
  { id: '4', gamertag: 'BlitzAR', role: 'AR', isStarter: false, competitiveTier: 'T3', marketValueNgn: 180000, trophyCount: 1 },
  { id: '5', gamertag: 'GhostSMG', role: 'SMG', isStarter: false, competitiveTier: 'T4', marketValueNgn: 95000, trophyCount: 0 },
];

export const MOCK_OFFERS: TransferOffer[] = [
  {
    id: 'o1',
    playerName: 'ViperAR',
    fromOrg: 'Night Wolves',
    offerType: 'buy',
    feeNgn: 650000,
    expiresIn: '2d 14h',
    status: 'pending',
  },
  {
    id: 'o2',
    playerName: 'FrostSMG',
    fromOrg: 'Lagos Elite',
    offerType: 'loan',
    feeNgn: 120000,
    expiresIn: '18h',
    status: 'pending',
  },
  {
    id: 'o3',
    playerName: 'AceKillerNG',
    fromOrg: 'Free Agent',
    offerType: 'sell',
    feeNgn: 500000,
    expiresIn: '5d',
    status: 'pending',
  },
];

export const MOCK_USER = {
  id: 'u1',
  gamertag: 'AceKillerNG',
  displayName: 'Ace Killer',
  role: 'player',
  region: 'NG',
  competitiveTier: 'T2',
  marketValueNgn: 450000,
  primaryRole: 'AR',
  preferredRoles: ['AR', 'SMG'],
  orgName: 'Phoenix Rising',
  orgTier: 'T2',
  availabilityStatus: 'Available',
  injuryStatus: null as string | null,
  retirementStatus: false,
};

// ─── Trophy Cabinet (Players + Teams) ───────────────────────────────────────

export type TrophyOwner = 'player' | 'team';

export interface Trophy {
  id: string;
  title: string;
  subtitle: string;
  type: 'tournament' | 'mvp' | 'seasonal' | 'achievement' | 'special';
  ownerType: TrophyOwner;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  earnedAt: string; // ISO or display date
  icon: string;
}

export const MOCK_PLAYER_TROPHIES: Trophy[] = [
  {
    id: 'pt1',
    title: 'West Africa Open MVP',
    subtitle: 'Best player · Season 3',
    type: 'mvp',
    ownerType: 'player',
    rarity: 'legendary',
    earnedAt: '2025-11-18',
    icon: '🏆',
  },
  {
    id: 'pt2',
    title: 'Lagos Invitational Champion',
    subtitle: 'Winner with Phoenix Rising',
    type: 'tournament',
    ownerType: 'player',
    rarity: 'epic',
    earnedAt: '2025-09-02',
    icon: '🥇',
  },
  {
    id: 'pt3',
    title: '100 Official Wins',
    subtitle: 'Career milestone',
    type: 'achievement',
    ownerType: 'player',
    rarity: 'rare',
    earnedAt: '2025-07-14',
    icon: '💯',
  },
  {
    id: 'pt4',
    title: 'Clutch Master',
    subtitle: '15 consecutive round clutches',
    type: 'achievement',
    ownerType: 'player',
    rarity: 'rare',
    earnedAt: '2025-05-22',
    icon: '🎯',
  },
  {
    id: 'pt5',
    title: 'Rising Star Award',
    subtitle: 'T3 → T2 promotion season',
    type: 'seasonal',
    ownerType: 'player',
    rarity: 'epic',
    earnedAt: '2025-03-30',
    icon: '⭐',
  },
];

export const MOCK_TEAM_TROPHIES: Trophy[] = [
  {
    id: 'tt1',
    title: 'Nigeria National Series',
    subtitle: 'Champions · 2025',
    type: 'tournament',
    ownerType: 'team',
    rarity: 'legendary',
    earnedAt: '2025-12-10',
    icon: '🏆',
  },
  {
    id: 'tt2',
    title: 'West Africa Club Cup',
    subtitle: 'Runners-up · Season 2',
    type: 'tournament',
    ownerType: 'team',
    rarity: 'epic',
    earnedAt: '2025-08-25',
    icon: '🥈',
  },
  {
    id: 'tt3',
    title: 'Regional Ladder #1',
    subtitle: 'Held for 6 consecutive weeks',
    type: 'seasonal',
    ownerType: 'team',
    rarity: 'rare',
    earnedAt: '2025-06-01',
    icon: '📊',
  },
];

// ─── Career Timeline ────────────────────────────────────────────────────────

export type TimelineEventType =
  | 'promotion'
  | 'demotion'
  | 'transfer'
  | 'trophy'
  | 'award'
  | 'injury'
  | 'return'
  | 'contract'
  | 'milestone';

export interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  title: string;
  description: string;
  date: string;
  meta?: string;
}

export const MOCK_CAREER_TIMELINE: TimelineEvent[] = [
  {
    id: 'e1',
    type: 'trophy',
    title: 'Won West Africa Open MVP',
    description: 'Individual award for outstanding performance',
    date: '2025-11-18',
    meta: 'Legendary',
  },
  {
    id: 'e2',
    type: 'promotion',
    title: 'Promoted to T2 First Team',
    description: 'Moved from Academy (T3) to First Team',
    date: '2025-10-05',
    meta: 'Phoenix Rising',
  },
  {
    id: 'e3',
    type: 'trophy',
    title: 'Lagos Invitational Champions',
    description: 'Team tournament victory',
    date: '2025-09-02',
    meta: 'Team Trophy',
  },
  {
    id: 'e4',
    type: 'transfer',
    title: 'Joined Phoenix Rising',
    description: 'Transferred from free agency',
    date: '2025-04-12',
    meta: '₦0 fee',
  },
  {
    id: 'e5',
    type: 'milestone',
    title: 'Reached 100 Official Wins',
    description: 'Career milestone unlocked',
    date: '2025-07-14',
  },
  {
    id: 'e6',
    type: 'contract',
    title: 'Signed 6-month contract',
    description: 'New deal with Phoenix Rising',
    date: '2025-04-12',
    meta: '₦180k / month',
  },
];
