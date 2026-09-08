const encoder = new TextEncoder();
const COOKIE = "csh_session";
const MAX_AGE = 60 * 60 * 24 * 30;

export type SessionUser = {
  uid: string;
  email: string;
  name: string;
  exp: number;
};

function bytesToB64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function b64UrlToBytes(value: string): Uint8Array {
  const pad = (4 - (value.length % 4)) % 4;
  const padded = value.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat(pad);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function timingEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

export function sessionSecret(): string | null {
  const secret = process.env.SESSION_SECRET?.trim();
  return secret && secret.length >= 16 ? secret : null;
}

async function hmac(secret: string, payload: string): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return new Uint8Array(await crypto.subtle.sign("HMAC", key, encoder.encode(payload)));
}

export async function signSession(user: Omit<SessionUser, "exp">, now = Date.now()): Promise<string> {
  const secret = sessionSecret();
  if (!secret) throw new Error("SESSION_SECRET is not configured.");
  const payload = bytesToB64Url(encoder.encode(JSON.stringify({ ...user, exp: now + MAX_AGE * 1000 })));
  const signature = bytesToB64Url(await hmac(secret, payload));
  return `${payload}.${signature}`;
}

export async function readSessionToken(token: string, now = Date.now()): Promise<SessionUser | null> {
  const secret = sessionSecret();
  if (!secret) return null;
  const dot = token.lastIndexOf(".");
  if (dot <= 0) return null;
  const payload = token.slice(0, dot);
  const signature = token.slice(dot + 1);
  let expected: Uint8Array;
  let actual: Uint8Array;
  try {
    expected = await hmac(secret, payload);
    actual = b64UrlToBytes(signature);
  } catch {
    return null;
  }
  if (!timingEqual(expected, actual)) return null;
  try {
    const user = JSON.parse(new TextDecoder().decode(b64UrlToBytes(payload))) as SessionUser;
    if (!user?.uid || !user.email || typeof user.exp !== "number" || user.exp <= now) return null;
    return user;
  } catch {
    return null;
  }
}

export function cookieFromRequest(req: Request): string | null {
  const header = req.headers.get("cookie");
  if (!header) return null;
  for (const part of header.split(";")) {
    const [name, ...rest] = part.trim().split("=");
    if (name === COOKIE) return decodeURIComponent(rest.join("="));
  }
  return null;
}

export async function sessionFromRequest(req: Request): Promise<SessionUser | null> {
  const token = cookieFromRequest(req);
  if (!token) return null;
  return readSessionToken(token);
}

export function sessionCookie(token: string, req: Request, maxAge = MAX_AGE): string {
  const secure = new URL(req.url).protocol === "https:" || process.env.VERCEL === "1";
  return `${COOKIE}=${encodeURIComponent(token)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAge}${secure ? "; Secure" : ""}`;
}

export function clearSessionCookie(req: Request): string {
  return sessionCookie("deleted", req, 0);
}

async function pbkdf2(password: string, salt: Uint8Array, iterations: number): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey("raw", encoder.encode(password), "PBKDF2", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt, iterations },
    key,
    256,
  ));
}

export async function hashPassword(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await pbkdf2(password, salt, 210_000);
  return `pbkdf2$210000$${bytesToB64Url(salt)}$${bytesToB64Url(hash)}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const [scheme, iter, salt, hash] = stored.split("$");
  if (scheme !== "pbkdf2" || !iter || !salt || !hash) return false;
  const iterations = Number(iter);
  if (!Number.isInteger(iterations) || iterations < 10_000) return false;
  let actual: Uint8Array;
  let expected: Uint8Array;
  try {
    actual = await pbkdf2(password, b64UrlToBytes(salt), iterations);
    expected = b64UrlToBytes(hash);
  } catch {
    return false;
  }
  return timingEqual(actual, expected);
}

export function normalizeEmail(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const email = value.trim().toLowerCase();
  if (email.length < 5 || email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return null;
  return email;
}

export function validatePassword(value: unknown): string | null {
  if (typeof value !== "string" || value.length < 10 || value.length > 200) return null;
  return value;
}

export function validateName(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const name = value.trim();
  if (name.length < 1 || name.length > 80) return null;
  return name;
}
