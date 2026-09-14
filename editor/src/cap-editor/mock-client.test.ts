import { expect, test } from 'vitest';

import catalog from './data/catalog.json';
import { createMockClient } from './mock-client.js';
import type { CapDesign } from './types.js';

const hen: CapDesign = {
  henId: 'h1', serial: 67, scheme: 'classic', icon: 'heart', centre: null, band: null,
  status: 'draft', designHash: '', proofUrl: null,
};
const client = (balance = 1000n, status: CapDesign['status'] = 'draft') =>
  createMockClient({ hens: [{ ...hen, status }], balance, catalog });

test('lock on a free scheme charges nothing and recomputes the hash', async () => {
  const c = client();
  const d = await c.lock('h1');
  expect(d.status).toBe('locked');
  expect(d.designHash).toHaveLength(16);
  expect((await c.getWallet()).balance).toBe(1000n);
});

test('lock on a paid scheme charges its catalog price', async () => {
  const c = client(200n);
  await c.save('h1', { scheme: 'meadow', icon: 'star', centre: null, band: 'dots' });
  await c.lock('h1');
  expect((await c.getWallet()).balance).toBe(50n);
});

test('lock refuses when grain is short and leaves the draft untouched', async () => {
  const c = client(10n);
  await c.save('h1', { scheme: 'sunset', icon: null, centre: 'rings', band: null });
  await expect(c.lock('h1')).rejects.toMatchObject({ code: 'INSUFFICIENT_GRAIN' });
  expect((await c.load('h1')).status).toBe('draft');
});

test('re-edit costs the fee and returns to draft; batched designs cannot be unlocked', async () => {
  const c = client(100n);
  await c.lock('h1');
  expect((await c.unlockForEdit('h1')).status).toBe('draft');
  expect((await c.getWallet()).balance).toBe(50n);
  await c.lock('h1');
  c.state().hens[0].status = 'batched';
  await expect(c.unlockForEdit('h1')).rejects.toMatchObject({ code: 'DESIGN_BATCHED' });
});

test('replacement from installed opens a new draft and charges the fee', async () => {
  const c = client(600n, 'installed');
  const d = await c.requestReplacement('h1');
  expect(d.status).toBe('draft');
  expect(d.proofUrl).toBeNull();
  expect((await c.getWallet()).balance).toBe(100n);
});

test('save rejects an icon together with a centre pattern and unknown ids', async () => {
  await expect(client().save('h1', { scheme: 'classic', icon: 'heart', centre: 'rings', band: null }))
    .rejects.toMatchObject({ code: 'CATALOG_MISMATCH' });
  await expect(client().save('h1', { scheme: 'classic', icon: 'unicorn', centre: null, band: null }))
    .rejects.toMatchObject({ code: 'CATALOG_MISMATCH' });
});

test('save on a locked design is refused', async () => {
  await expect(client(0n, 'locked').save('h1', { scheme: 'classic', icon: null, centre: null, band: null }))
    .rejects.toMatchObject({ code: 'NOT_EDITABLE' });
});
