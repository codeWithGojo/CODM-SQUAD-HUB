import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const runtimeEnv = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env;
export const API_BASE_URL = (runtimeEnv?.EXPO_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');
const TOKEN_KEY = 'codm-squad-hub.access-token';

let memoryToken: string | null = null;

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly payload: unknown,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function setAccessToken(token: string | null): Promise<void> {
  memoryToken = token;
  if (Platform.OS === 'web') {
    if (token) await AsyncStorage.setItem(TOKEN_KEY, token);
    else await AsyncStorage.removeItem(TOKEN_KEY);
    return;
  }
  if (token) await SecureStore.setItemAsync(TOKEN_KEY, token);
  else await SecureStore.deleteItemAsync(TOKEN_KEY);
  await AsyncStorage.removeItem(TOKEN_KEY);
}

export async function getAccessToken(): Promise<string | null> {
  if (memoryToken) return memoryToken;
  if (Platform.OS === 'web') {
    memoryToken = await AsyncStorage.getItem(TOKEN_KEY);
    return memoryToken;
  }
  memoryToken = await SecureStore.getItemAsync(TOKEN_KEY);
  if (!memoryToken) {
    const legacyToken = await AsyncStorage.getItem(TOKEN_KEY);
    if (legacyToken) {
      await SecureStore.setItemAsync(TOKEN_KEY, legacyToken);
      await AsyncStorage.removeItem(TOKEN_KEY);
      memoryToken = legacyToken;
    }
  }
  return memoryToken;
}

export async function api<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json');
  if (token && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get('content-type') ?? '';
  const payload: unknown = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof payload === 'object' && payload && 'detail' in payload ? String((payload as { detail: unknown }).detail) : `Request failed (${response.status})`;
    throw new ApiError(response.status, payload, detail);
  }
  return payload as T;
}

function json(method: string, body?: unknown): RequestInit {
  return { method, body: body === undefined ? undefined : JSON.stringify(body) };
}

export type UUID = string;
export type Mode = 'MP' | 'BR';

export interface Region {
  id: UUID;
  code: string;
  name: string;
  zone: string;
}

export interface CurrentUser {
  id: UUID;
  shid: string;
  phone: string;
  email: string | null;
  gamertag: string;
  preferred_mode: Mode | null;
  region_id: UUID | null;
  is_platform_admin: boolean;
  reputation_score: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  is_new_user: boolean;
}

export interface Tournament {
  id: UUID;
  organizer_id: UUID;
  season_id: UUID | null;
  name: string;
  slug: string;
  mode: Mode;
  format: string;
  status: string;
  tier: string;
  starts_at: string;
  prize_pool_naira: number;
  max_teams: number;
  ranking_weight: number;
  entry_fee_kobo: number;
}

export interface Season {
  id: UUID;
  name: string;
  code: string;
  starts_on: string;
  ends_on: string;
  is_active: boolean;
}

export interface RankingRow {
  id: UUID;
  entity_id: UUID;
  entity_name: string;
  entity_type: 'player' | 'team' | 'organization';
  scope: 'national' | 'regional' | 'continental';
  scope_code: string;
  mode: Mode;
  rating: number;
  points: number;
  rank: number;
  movement: number;
  matches_played: number;
}

export interface TransferOffer {
  id: UUID;
  player_id: UUID;
  from_team_id: UUID | null;
  to_team_id: UUID;
  offer_type: 'permanent' | 'loan' | 'free_signing';
  status: string;
  transfer_fee_naira: number | null;
  proposed_salary_naira: number | null;
  expires_at: string;
}

export interface NotificationItem {
  id: UUID;
  type: string;
  title: string;
  body: string;
  action_url: string | null;
  data: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

export interface ChatMessage {
  id: UUID;
  thread_id: UUID;
  sender_user_id: UUID;
  body: string;
  attachments: Record<string, unknown>[];
  reply_to_message_id: UUID | null;
  created_at: string;
}

export interface HillOutputPlayer {
  user_id: UUID;
  gamertag: string;
  in_game_role: string | null;
  kills: number;
  hill_output: {
    map_name: string;
    hill_labels: string[];
    kills_by_hill: number[];
    shared_scale: number;
    role_profile: Record<string, number> | null;
  };
  summary: {
    hill_kills: number;
    average_per_hill: number;
    peak_kills: number;
    peak_hill_index: number;
    consistency: number;
  };
}

export interface HillOutputResponse {
  match_id: UUID;
  team_id: UUID;
  status: string;
  players: HillOutputPlayer[];
}

export const platformApi = {
  auth: {
    requestOtp: (phone: string) => api<{ expires_in_seconds: number; dev_code?: string }>('/auth/request-otp', json('POST', { phone })),
    verifyOtp: async (phone: string, code: string) => {
      const result = await api<TokenResponse>('/auth/verify-otp', json('POST', { phone, code }));
      if (!result.is_new_user) await setAccessToken(result.access_token);
      return result;
    },
    completeSignup: async (signupToken: string, profile: Record<string, unknown>) => {
      const result = await api<TokenResponse>('/auth/complete-signup', {
        ...json('POST', profile),
        headers: { Authorization: `Bearer ${signupToken}`, 'Content-Type': 'application/json' },
      });
      await setAccessToken(result.access_token);
      return result;
    },
    me: () => api<CurrentUser>('/auth/me'),
    logout: () => setAccessToken(null),
  },
  identity: {
    regions: (zone?: string) => api<Region[]>(`/regions${zone ? `?zone=${encodeURIComponent(zone)}` : ''}`),
  },
  tournaments: {
    list: (mode?: Mode) => api<Tournament[]>(`/tournaments${mode ? `?mode=${mode}` : ''}`),
    get: (id: UUID) => api<Tournament>(`/tournaments/${id}`),
    standings: (id: UUID) => api<Record<string, unknown>[]>(`/tournaments/${id}/standings`),
    hillOutput: (tournamentId: UUID, matchId: UUID, teamId: UUID) =>
      api<HillOutputResponse>(`/tournaments/${tournamentId}/matches/${matchId}/hill-output?team_id=${encodeURIComponent(teamId)}`),
    register: (id: UUID, input: Record<string, unknown>) => api(`/tournaments/${id}/registrations`, json('POST', input)),
  },
  rankings: {
    table: (seasonId: UUID, mode: Mode, entityType = 'team', scope = 'continental', scopeCode = 'AFRICA') =>
      api<RankingRow[]>(`/rankings?season_id=${seasonId}&mode=${mode}&entity_type=${entityType}&scope=${scope}&scope_code=${encodeURIComponent(scopeCode)}`),
    seasons: () => api<Season[]>('/seasons'),
  },
  transfers: {
    offers: (status?: string) => api<TransferOffer[]>(`/transfers/offers${status ? `?status=${encodeURIComponent(status)}` : ''}`),
    submit: (input: Record<string, unknown>) => api<TransferOffer>('/transfers/offers', json('POST', input)),
    clubDecision: (id: UUID, input: Record<string, unknown>) => api<TransferOffer>(`/transfers/offers/${id}/club-decision`, json('POST', input)),
    playerDecision: (id: UUID, accept: boolean) => api<TransferOffer>(`/transfers/offers/${id}/player-decision`, json('POST', { accept })),
    complete: (id: UUID) => api(`/transfers/offers/${id}/complete`, json('POST')),
    watchlist: (teamId: UUID) => api<Record<string, unknown>[]>(`/transfers/watchlists/${teamId}`),
    marketValue: (playerId: UUID) => api<Record<string, unknown>>(`/transfers/market-values/${playerId}`),
  },
  performance: {
    analytics: (days = 30) => api<Record<string, number>>(`/performance/me/analytics?days=${days}`),
    logMatch: (input: Record<string, unknown>) => api('/performance/matches', json('POST', input)),
    runWeeklyReview: (weekStart: string, force = false) => api('/ai/weekly-reviews/run', json('POST', { week_start: weekStart, force })),
    reviews: () => api<Record<string, unknown>[]>('/ai/weekly-reviews/me'),
    trainingPlan: (weekStart?: string) => api<Record<string, unknown>>(`/ai/training-plans/me${weekStart ? `?week_start=${weekStart}` : ''}`),
  },
  mapGuides: {
    curated: (mode?: Mode) => api<Record<string, unknown>[]>(`/map-guides${mode ? `?mode=${mode}` : ''}`),
    team: (teamId: UUID) => api<Record<string, unknown>[]>(`/map-guides/teams/${teamId}`),
  },
  commerce: {
    plans: () => api<Record<string, unknown>>('/commerce/plans'),
    subscriptionCheckout: (input: Record<string, unknown>) => api('/commerce/subscriptions/checkout', json('POST', input)),
    campaigns: () => api<Record<string, unknown>[]>('/commerce/campaigns'),
    products: (organizationId: UUID) => api<Record<string, unknown>[]>(`/commerce/products?organization_id=${organizationId}`),
    order: (input: Record<string, unknown>) => api('/commerce/orders', json('POST', input)),
    myOrders: () => api<Record<string, unknown>[]>('/commerce/orders/me'),
    storeOrders: (organizationId: UUID, status?: string) =>
      api<Record<string, unknown>[]>(`/commerce/orders?organization_id=${organizationId}${status ? `&status=${encodeURIComponent(status)}` : ''}`),
  },
  notifications: {
    list: (unreadOnly = false) => api<NotificationItem[]>(`/notifications?unread_only=${unreadOnly}`),
    unreadCount: () => api<{ unread_count: number }>('/notifications/unread-count'),
    read: (id: UUID) => api<NotificationItem>(`/notifications/${id}/read`, json('POST')),
    readAll: () => api<{ updated: number }>('/notifications/read-all', json('POST')),
    registerDevice: (token: string | null) => api<void>('/notifications/device-token', json('PUT', { token })),
  },
  chat: {
    threads: () => api<Record<string, unknown>[]>('/chat/threads'),
    createThread: (input: Record<string, unknown>) => api('/chat/threads', json('POST', input)),
    messages: (threadId: UUID) => api<ChatMessage[]>(`/chat/threads/${threadId}/messages`),
    send: (threadId: UUID, body: string, attachments: Record<string, unknown>[] = []) =>
      api<ChatMessage>(`/chat/threads/${threadId}/messages`, json('POST', { body, attachments })),
  },
};

export type RealtimeEvent = { type: string; [key: string]: unknown };

export class RealtimeClient {
  private socket: WebSocket | null = null;
  private listeners = new Set<(event: RealtimeEvent) => void>();
  private channels = new Set<string>();
  private closedByUser = false;
  private retry = 0;
  private connectionVersion = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  async connect(): Promise<void> {
    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) return;
    this.closedByUser = false;
    const version = ++this.connectionVersion;
    const token = await getAccessToken();
    if (!token) throw new Error('Sign in before opening realtime updates.');
    if (this.closedByUser || version !== this.connectionVersion) return;
    const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/ws';
    this.socket = new WebSocket(wsUrl);
    this.socket.onopen = () => this.socket?.send(JSON.stringify({ type: 'auth', token }));
    this.socket.onmessage = ({ data }) => {
      try {
        const event = JSON.parse(String(data)) as RealtimeEvent;
        if (event.type === 'auth.ok') {
          this.retry = 0;
          this.channels.forEach((channel) => this.send({ type: 'subscribe', channel }));
        }
        this.listeners.forEach((listener) => listener(event));
      } catch {
        // Ignore malformed server frames; protocol errors are reported as valid JSON events.
      }
    };
    this.socket.onclose = () => {
      this.socket = null;
      if (!this.closedByUser) {
        const delay = Math.min(30_000, 1_000 * 2 ** this.retry++);
        this.reconnectTimer = setTimeout(() => {
          this.reconnectTimer = null;
          void this.connect().catch(() => {
            // A later screen focus or network transition can reconnect.
          });
        }, delay);
      }
    };
  }

  subscribe(channel: string): () => void {
    this.channels.add(channel);
    this.send({ type: 'subscribe', channel });
    return () => {
      this.channels.delete(channel);
      this.send({ type: 'unsubscribe', channel });
    };
  }

  onEvent(listener: (event: RealtimeEvent) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  close(): void {
    this.closedByUser = true;
    this.connectionVersion += 1;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    this.socket?.close();
    this.socket = null;
  }

  private send(event: RealtimeEvent): void {
    if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(JSON.stringify(event));
  }
}

export const realtimeClient = new RealtimeClient();
