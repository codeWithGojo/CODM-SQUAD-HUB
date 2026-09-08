CREATE TABLE IF NOT EXISTS workspaces (
  owner TEXT NOT NULL,
  game TEXT NOT NULL,
  body TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (owner, game)
);
