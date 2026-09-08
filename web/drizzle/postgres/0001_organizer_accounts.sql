CREATE TABLE IF NOT EXISTS organizer_accounts (
  id TEXT PRIMARY KEY NOT NULL,
  email TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  display_name TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS organizer_accounts_email_unique ON organizer_accounts (email);
