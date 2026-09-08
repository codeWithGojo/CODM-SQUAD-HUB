import type { CurrentUser, TokenResponse } from './api';

export type SessionState =
  | { status: 'checking' }
  | { status: 'phone'; notice?: string }
  | { status: 'otp'; phone: string; devCode?: string }
  | { status: 'signup'; phone: string; signupToken: string }
  | { status: 'ready'; user: CurrentUser }
  | { status: 'retry'; message: string };

export interface SessionDependencies {
  readToken: () => Promise<string | null>;
  saveToken: (token: string | null) => Promise<void>;
  me: () => Promise<CurrentUser>;
  requestOtp: (phone: string) => Promise<{ dev_code?: string | null }>;
  verifyOtp: (phone: string, code: string) => Promise<TokenResponse>;
  signup: (token: string, profile: Record<string, unknown>) => Promise<TokenResponse>;
  closeRealtime: () => void;
}

export function normalizePhone(value: string): string {
  const cleaned = value.replace(/[\s()-]/g, '');
  const phone = /^0\d{10}$/.test(cleaned) ? `+234${cleaned.slice(1)}` : cleaned;
  if (!/^\+[1-9]\d{9,14}$/.test(phone)) {
    throw new Error('Use a country code, such as +2348012345678, or an 11-digit Nigerian number.');
  }
  return phone;
}

export function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function denied(error: unknown): boolean {
  const status = (error as { status?: number } | null)?.status;
  return status === 401 || status === 403;
}

// A generation prevents a delayed request from reopening a session after sign-out/back.
export class SessionController {
  private dependencies: SessionDependencies;
  private generation = 0;
  private state: SessionState = { status: 'checking' };
  private listeners = new Set<() => void>();

  constructor(dependencies: SessionDependencies) { this.dependencies = dependencies; }
  getSnapshot = (): SessionState => this.state;
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  };
  private update(state: SessionState) {
    this.state = state;
    this.listeners.forEach(listener => listener());
  }

  restore = async () => {
    const version = ++this.generation;
    if (this.state.status !== 'ready') this.update({ status: 'checking' });
    try {
      const token = await this.dependencies.readToken();
      if (version !== this.generation) return;
      if (!token) { this.update({ status: 'phone' }); return; }
      const user = await this.dependencies.me();
      if (version === this.generation) this.update({ status: 'ready', user });
    } catch (error) {
      if (version !== this.generation) return;
      if (denied(error)) {
        await this.signOut((error as { status?: number }).status === 403
          ? errorMessage(error, 'This account is unavailable.') : 'Your session expired. Sign in again.');
      } else {
        // An outage must not delete a valid stored session or show a mock logged-in user.
        this.update({ status: 'retry', message: errorMessage(error, 'Could not restore your session. Try again.') });
      }
    }
  };

  requestOtp = async (input: string) => {
    const phone = normalizePhone(input);
    const version = ++this.generation;
    const result = await this.dependencies.requestOtp(phone);
    if (version === this.generation) this.update({ status: 'otp', phone, devCode: result.dev_code ?? undefined });
  };

  resend = async () => {
    if (this.state.status !== 'otp') return;
    const { phone } = this.state;
    const version = this.generation;
    const result = await this.dependencies.requestOtp(phone);
    if (version === this.generation) {
      this.update({ status: 'otp', phone, devCode: result.dev_code ?? undefined });
      return result.dev_code ?? undefined;
    }
  };

  verify = async (code: string) => {
    if (this.state.status !== 'otp') return;
    const { phone } = this.state;
    const version = this.generation;
    const result = await this.dependencies.verifyOtp(phone, code);
    if (version !== this.generation) return;
    if (result.is_new_user) {
      // Signup credentials only live in memory; they cannot restore a player session.
      this.update({ status: 'signup', phone, signupToken: result.access_token });
    } else {
      await this.finish(result.access_token, version);
    }
  };

  signup = async (profile: Record<string, unknown>) => {
    if (this.state.status !== 'signup') return;
    const { phone, signupToken } = this.state;
    const version = this.generation;
    const result = await this.dependencies.signup(signupToken, { ...profile, phone });
    if (version === this.generation) await this.finish(result.access_token, version);
  };

  private async finish(token: string, version: number) {
    try {
      await this.dependencies.saveToken(token);
    } catch {
      if (version === this.generation) await this.signOut('Could not save your session securely. Sign in again.');
      return;
    }
    if (version === this.generation) await this.restore();
  }

  signOut = async (notice?: string) => {
    const version = ++this.generation;
    this.dependencies.closeRealtime();
    this.update({ status: 'checking' });
    try {
      await this.dependencies.saveToken(null);
      if (version === this.generation) this.update({ status: 'phone', notice });
    } catch {
      if (version === this.generation) this.update({ status: 'retry', message: 'Could not clear the saved session. Try signing out again.' });
    }
  };
}
