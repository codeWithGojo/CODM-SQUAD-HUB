import { Player } from '../components/PlayerCard';
import { TransferOffer } from '../components/OfferCard';

export const MOCK_PLAYERS: Player[] = [
  { id: '1', gamertag: 'AceKillerNG', role: 'AR', isStarter: true, competitiveTier: 'T2', marketValueNgn: 450000 },
  { id: '2', gamertag: 'ShadowX', role: 'SMG', isStarter: true, competitiveTier: 'T2', marketValueNgn: 380000 },
  { id: '3', gamertag: 'NovaSniper', role: 'Sniper', isStarter: true, competitiveTier: 'T3', marketValueNgn: 220000 },
  { id: '4', gamertag: 'BlitzAR', role: 'AR', isStarter: false, competitiveTier: 'T3', marketValueNgn: 180000 },
  { id: '5', gamertag: 'GhostSMG', role: 'SMG', isStarter: false, competitiveTier: 'T4', marketValueNgn: 95000 },
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
  orgName: 'Phoenix Rising',
  orgTier: 'T2',
};
