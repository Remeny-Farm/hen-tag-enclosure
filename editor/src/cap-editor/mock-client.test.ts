import { expect, test } from 'vitest';

import catalog from './data/catalog.json';
import { createMockClient } from './mock-client.js';
import { defaultColours, type CapDesign } from './types.js';

const dc = defaultColours(catalog);
const hen: CapDesign = {
  henId: 'h1', serial: 67, scheme: 'pasture', icon: 'heart', centre: null, band: null, colours: dc,
  status: 'draft', designHash: '', proofUrl: null,
};
const client = (balance = 1000n, status: CapDesign['status'] = 'draft') =>
  createMockClient({ hens: [{ ...hen, status }], balance, catalog });

test('lock on the free scheme with free decor charges nothing and recomputes the hash', async () => {
  const c = client();
  const d = await c.lock('h1');
  expect(d.status).toBe('locked');
  expect(d.designHash).toHaveLength(16);
  expect((await c.getWallet()).balance).toBe(1000n);
});

test('lock charges scheme + icon + band from the catalog packs', async () => {
  const c = client(1000n);
  await c.save('h1', { scheme: 'bluedye', icon: 'skull', centre: null, band: 'checker', colours: dc });
  await c.lock('h1');
  expect((await c.getWallet()).balance).toBe(1000n - 100n - 80n - 30n);
});

test('lock refuses when grain is short and leaves the draft untouched', async () => {
  const c = client(10n);
  await c.save('h1', { scheme: 'gold', icon: null, centre: 'rings', band: null, colours: dc });
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

test('save rejects an icon with a centre pattern, unknown ids and clashing zone colours', async () => {
  await expect(client().save('h1', { scheme: 'pasture', icon: 'heart', centre: 'rings', band: null, colours: dc }))
    .rejects.toMatchObject({ code: 'CATALOG_MISMATCH' });
  await expect(client().save('h1', { scheme: 'pasture', icon: 'unicorn', centre: null, band: null, colours: dc }))
    .rejects.toMatchObject({ code: 'CATALOG_MISMATCH' });
  await expect(client().save('h1', { scheme: 'pasture', icon: 'heart', centre: null, band: null, colours: { ...dc, number: 'base' } }))
    .rejects.toMatchObject({ code: 'CATALOG_MISMATCH' });
});

test('zone colours are free otherwise: base number on a coloured ring is fine', async () => {
  const d = await client().save('h1', { scheme: 'pasture', icon: 'heart', centre: null, band: 'arc', colours: { ring: 'a', number: 'base', disc: 'b', centre: 'a', band: 'b' } });
  expect(d.colours.ring).toBe('a');
});

test('clear is a fourth colour for any zone, but never for both the number and its ring', async () => {
  const d = await client().save('h1', { scheme: 'pasture', icon: 'heart', centre: null, band: null, colours: { ...dc, number: 'clear', disc: 'clear' } });
  expect(d.colours.number).toBe('clear');
  await expect(client().save('h1', { scheme: 'pasture', icon: 'heart', centre: null, band: null, colours: { ...dc, ring: 'clear', number: 'clear' } }))
    .rejects.toMatchObject({ code: 'CATALOG_MISMATCH' });
});

test('save on a locked design is refused', async () => {
  await expect(client(0n, 'locked').save('h1', { scheme: 'pasture', icon: null, centre: null, band: null, colours: dc }))
    .rejects.toMatchObject({ code: 'NOT_EDITABLE' });
});
