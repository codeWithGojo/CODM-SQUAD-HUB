import test from 'node:test';
import assert from 'node:assert/strict';
import { SessionController, normalizePhone } from '../src/services/session.ts';
import { TokenStore } from '../src/services/tokenStore.ts';

const user = { id: 'player-1', gamertag: 'Gojo', shid: 'SH-1' };
function fixture(overrides = {}) {
  let saved = null;
  const deps = {
    readToken: async () => saved,
    saveToken: async token => { saved = token; },
    me: async () => user,
    requestOtp: async () => ({ dev_code: '123456' }),
    verifyOtp: async () => ({ is_new_user: false, access_token: 'access' }),
    signup: async () => ({ is_new_user: false, access_token: 'access' }),
    closeRealtime: () => {},
    ...overrides,
  };
  const session = new SessionController(deps);
  return { session, deps, saved: () => saved };
}
function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}

test('phone normalization preserves international numbers and handles Nigerian local numbers', () => {
  assert.equal(normalizePhone('0801 234 5678'), '+2348012345678');
  assert.equal(normalizePhone('+27 (82) 123-4567'), '+27821234567');
  assert.throws(() => normalizePhone('27123456789'));
  assert.throws(() => normalizePhone('invalid-number'));
});

test('first launch stays signed out; existing player verifies then restores /me', async () => {
  const f = fixture();
  await f.session.restore();
  assert.equal(f.session.getSnapshot().status, 'phone');
  await f.session.requestOtp('08012345678');
  assert.equal(f.session.getSnapshot().phone, '+2348012345678');
  await f.session.verify('123456');
  assert.equal(f.saved(), 'access');
  assert.equal(f.session.getSnapshot().user, user);
  assert.equal(f.session.getSnapshot().status, 'ready');
});

test('new player signup token stays in memory, verified phone cannot be replaced', async () => {
  let received;
  const f = fixture({
    verifyOtp: async () => ({ is_new_user: true, access_token: 'signup-only' }),
    signup: async (token, profile) => { received = { token, profile }; return { access_token: 'access' }; },
  });
  await f.session.requestOtp('+2348012345678');
  await f.session.verify('123456');
  assert.equal(f.session.getSnapshot().status, 'signup');
  assert.equal(f.saved(), null);
  await f.session.signup({ gamertag: 'Gojo', phone: 'forged' });
  assert.equal(received.token, 'signup-only');
  assert.equal(received.profile.phone, '+2348012345678');
  assert.equal(f.session.getSnapshot().status, 'ready');
});

test('invalid OTP stays on code entry and never saves a token', async () => {
  const f = fixture({ verifyOtp: async () => { throw new Error('Invalid or expired code.'); } });
  await f.session.requestOtp('+2348012345678');
  await assert.rejects(f.session.verify('000000'), /expired/);
  assert.equal(f.session.getSnapshot().status, 'otp');
  assert.equal(f.saved(), null);
});

test('expired and banned sessions close the gate and clear persisted credentials', async () => {
  for (const status of [401, 403]) {
    const f = fixture({ me: async () => { throw Object.assign(new Error('Account unavailable'), { status }); } });
    await f.deps.saveToken('expired');
    await f.session.restore();
    assert.equal(f.session.getSnapshot().status, 'phone');
    assert.equal(f.saved(), null);
    assert.ok(f.session.getSnapshot().notice);
  }
});

test('network failure retains the session and allows a successful retry', async () => {
  let offline = true;
  const f = fixture({ me: async () => { if (offline) throw new Error('Offline'); return user; } });
  await f.deps.saveToken('valid');
  await f.session.restore();
  assert.equal(f.saved(), 'valid');
  assert.equal(f.session.getSnapshot().status, 'retry');
  offline = false;
  await f.session.restore();
  assert.equal(f.session.getSnapshot().status, 'ready');
});

test('delayed verification cannot sign in after back/sign-out', async () => {
  const response = deferred();
  const f = fixture({ verifyOtp: () => response.promise });
  await f.session.requestOtp('+2348012345678');
  const verifying = f.session.verify('123456');
  await f.session.signOut();
  response.resolve({ is_new_user: false, access_token: 'late' });
  await verifying;
  assert.equal(f.saved(), null);
  assert.equal(f.session.getSnapshot().status, 'phone');
});

test('a stale /me response cannot reopen the app after sign-out', async () => {
  const response = deferred();
  const f = fixture({ me: () => response.promise });
  await f.deps.saveToken('valid');
  const restoring = f.session.restore();
  await Promise.resolve();
  await f.session.signOut();
  response.resolve(user);
  await restoring;
  assert.equal(f.session.getSnapshot().status, 'phone');
});

test('stored token read cannot resurrect credentials after a concurrent clear', async () => {
  const result = deferred();
  const store = new TokenStore({ read: () => result.promise, write: async () => {} });
  const reading = store.read();
  await store.write(null);
  result.resolve('old');
  assert.equal(await reading, null);
  assert.equal(await store.read(), null);
});

test('persistent token writes stay ordered when signing out during a save', async () => {
  const write = deferred();
  let persisted;
  const store = new TokenStore({ read: async () => null, write: async token => {
    if (token) await write.promise;
    persisted = token;
  } });
  const saving = store.write('access');
  const clearing = store.write(null);
  write.resolve();
  await Promise.all([saving, clearing]);
  assert.equal(persisted, null);
});

test('storage failure never opens the signed-in app', async () => {
  const f = fixture({ saveToken: async () => { throw new Error('Storage unavailable'); } });
  await f.session.requestOtp('+2348012345678');
  await f.session.verify('123456');
  assert.equal(f.session.getSnapshot().status, 'retry');
});
