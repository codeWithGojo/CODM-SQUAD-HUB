import type { Database } from "./store.ts";
import { hashPassword, normalizeEmail, validateName, validatePassword, verifyPassword } from "./session.ts";

export type OrganizerAccount = {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
};

export class AccountError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function registerAccount(
  db: Database,
  input: { email: unknown; password: unknown; displayName: unknown },
): Promise<OrganizerAccount> {
  const email = normalizeEmail(input.email);
  const password = validatePassword(input.password);
  const displayName = validateName(input.displayName);
  if (!email) throw new AccountError("Enter a valid email address.", 400);
  if (!password) throw new AccountError("Password must be 10–200 characters.", 400);
  if (!displayName) throw new AccountError("Enter a display name up to 80 characters.", 400);
  const existing = await db.prepare("SELECT id FROM organizer_accounts WHERE email = ?").bind(email).first<{ id: string }>();
  if (existing) throw new AccountError("An organizer account already exists for this email.", 409);
  const account: OrganizerAccount = {
    id: crypto.randomUUID(),
    email,
    display_name: displayName,
    created_at: new Date().toISOString(),
  };
  const inserted = await db.prepare(
    "INSERT INTO organizer_accounts (id, email, password_hash, display_name, created_at) VALUES (?, ?, ?, ?, ?)",
  ).bind(account.id, email, await hashPassword(password), displayName, account.created_at).run();
  if (inserted.meta.changes !== 1) throw new AccountError("Could not create the organizer account.", 409);
  return account;
}

export async function authenticateAccount(
  db: Database,
  input: { email: unknown; password: unknown },
): Promise<OrganizerAccount> {
  const email = normalizeEmail(input.email);
  const password = validatePassword(input.password) ?? (typeof input.password === "string" ? input.password : "");
  if (!email || !password) throw new AccountError("Email or password is incorrect.", 401);
  const row = await db.prepare(
    "SELECT id, email, password_hash, display_name, created_at FROM organizer_accounts WHERE email = ?",
  ).bind(email).first<{ id: string; email: string; password_hash: string; display_name: string; created_at: string }>();
  if (!row || !(await verifyPassword(password, row.password_hash))) {
    throw new AccountError("Email or password is incorrect.", 401);
  }
  return { id: row.id, email: row.email, display_name: row.display_name, created_at: row.created_at };
}

export async function readAccount(db: Database, id: string): Promise<OrganizerAccount | null> {
  return db.prepare(
    "SELECT id, email, display_name, created_at FROM organizer_accounts WHERE id = ?",
  ).bind(id).first<OrganizerAccount>();
}
