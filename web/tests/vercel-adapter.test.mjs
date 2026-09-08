import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {rewriteSql, wrapNodeSqlite} from '../lib/database.ts';
import {hashPassword, readSessionToken, signSession, verifyPassword} from '../lib/session.ts';
import {authenticateAccount, registerAccount} from '../lib/accounts.ts';
import {getIdentity} from '../lib/identity.ts';
import {saveCommand, readWorkspace} from '../lib/store.ts';

const previousSecret = process.env.SESSION_SECRET;
process.env.SESSION_SECRET = 'test-session-secret-value';
test.after(() => {
  if (previousSecret === undefined) delete process.env.SESSION_SECRET;
  else process.env.SESSION_SECRET = previousSecret;
});

function sqlite() {
  const db = new DatabaseSync(':memory:');
  db.exec(readFileSync(new URL('../drizzle/0000_public_skrulls.sql', import.meta.url), 'utf8'));
  db.exec(readFileSync(new URL('../drizzle/0001_organizer_accounts.sql', import.meta.url), 'utf8'));
  return wrapNodeSqlite(db);
}

test('postgres SQL rewrite converts placeholders and json_extract', () => {
  const sql = "SELECT game, json_extract(body, '$.rules.name') AS name, updated_at FROM workspaces WHERE owner = ? ORDER BY updated_at DESC LIMIT 100";
  assert.equal(
    rewriteSql(sql, 'postgres'),
    "SELECT game, body::jsonb #>> '{rules,name}' AS name, updated_at FROM workspaces WHERE owner = $1 ORDER BY updated_at DESC LIMIT 100",
  );
  assert.equal(
    rewriteSql('INSERT INTO workspaces (owner, game, body, version, updated_at) VALUES (?, ?, ?, 1, ?) ON CONFLICT(owner, game) DO NOTHING', 'postgres'),
    'INSERT INTO workspaces (owner, game, body, version, updated_at) VALUES ($1, $2, $3, 1, $4) ON CONFLICT(owner, game) DO NOTHING',
  );
  assert.equal(rewriteSql('SELECT body FROM workspaces WHERE owner = ? AND game = ?', 'sqlite'), 'SELECT body FROM workspaces WHERE owner = ? AND game = ?');
});

test('HMAC sessions round-trip and reject tampering or expiry', async () => {
  const token = await signSession({uid: 'org-1', email: 'a@example.com', name: 'Ada'}, 1_000);
  const user = await readSessionToken(token, 2_000);
  assert.equal(user.uid, 'org-1');
  assert.equal(user.email, 'a@example.com');
  const flipped = token.slice(0, -1) + (token.endsWith('a') ? 'b' : 'a');
  assert.equal(await readSessionToken(flipped, 2_000), null);
  assert.equal(await readSessionToken(token, 1_000 + 60 * 60 * 24 * 31 * 1000), null);
});

test('password hashes verify and reject the wrong secret', async () => {
  const stored = await hashPassword('correct-horse');
  assert.equal(await verifyPassword('correct-horse', stored), true);
  assert.equal(await verifyPassword('wrong-password', stored), false);
});

test('organizer accounts isolate workspaces and ignore a forged JSON owner', async () => {
  const db = sqlite();
  const ada = await registerAccount(db, {email: 'Ada@Example.com', password: 'correct-horse', displayName: 'Ada'});
  assert.equal(ada.email, 'ada@example.com');
  await assert.rejects(() => registerAccount(db, {email: 'ada@example.com', password: 'correct-horse', displayName: 'Ada'}), /already exists/);
  const login = await authenticateAccount(db, {email: 'ada@example.com', password: 'correct-horse'});
  assert.equal(login.id, ada.id);
  await assert.rejects(() => authenticateAccount(db, {email: 'ada@example.com', password: 'nope-nope-nope'}), /incorrect/);

  const cmd = {type: 'team.add', name: 'NIM', tier: 'First team'};
  await saveCommand(db, ada.id, 'codm', 0, cmd);
  assert.equal((await readWorkspace(db, ada.id, 'codm')).workspace.teams[0].name, 'NIM');
  assert.equal((await readWorkspace(db, 'forged-owner', 'codm')).workspace.teams.length, 0);

  const req = new Request('http://localhost/api/workspace', {
    method: 'POST',
    headers: {
      cookie: `csh_session=${encodeURIComponent(await signSession({uid: ada.id, email: ada.email, name: ada.display_name}))}`,
    },
  });
  const identity = await getIdentity(req);
  assert.equal(identity.owner, ada.id);
  assert.equal(identity.method, 'session');
});

test('ChatGPT dispatcher identity remains valid without a session cookie', async () => {
  const identity = await getIdentity(new Request('http://localhost/api/workspace', {
    headers: {'oai-authenticated-user-id': 'sites-organizer', 'oai-authenticated-user-email': 'sites@example.com'},
  }));
  assert.equal(identity.owner, 'sites-organizer');
  assert.equal(identity.method, 'chatgpt');
});

test('anonymous requests are unauthorized', async () => {
  await assert.rejects(() => getIdentity(new Request('http://localhost/api/workspace')), e => e.status === 401);
});
