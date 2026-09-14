import { expect, test } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { en } from '../copy/en.js';
import { CapEditor } from './cap-editor.js';
import catalog from './data/catalog.json';
import layout from './data/layout.json';
import { createMockClient } from './mock-client.js';
import { defaultColours, type CapDesign } from './types.js';

const dc = defaultColours(catalog);
const hen: CapDesign = {
  henId: 'h1', serial: 67, scheme: 'pasture', icon: 'heart', centre: null, band: null, colours: dc,
  status: 'draft', designHash: '', proofUrl: null,
};

function setup(balance = 1000n, status: CapDesign['status'] = 'draft') {
  const client = createMockClient({ hens: [{ ...hen, status }], balance, catalog });
  render(
    <CapEditor henId="h1" client={client} catalog={catalog} layout={layout} copy={en.capEditor} walletCopy={en.wallet} locale="en-US" />,
  );
  return client;
}

test('shows the preview, the wallet, the schemes and the zone colour rows', async () => {
  setup();
  expect(await screen.findByRole('img', { name: 'Cap 67' })).toBeInTheDocument();
  expect(screen.getByLabelText('1,000 Golden Grain')).toBeInTheDocument();
  expect(screen.getByRole('radio', { name: 'Blue-dye' })).toBeInTheDocument();
  expect(screen.getByRole('radio', { name: 'Heart' })).toBeChecked();
  expect(screen.getByRole('radiogroup', { name: 'Outer ring' })).toBeInTheDocument();
  expect(screen.getByRole('radiogroup', { name: 'Number' })).toBeInTheDocument();
});

test('locking a paid scheme with a Drop icon and a Vibe band charges the itemised total', async () => {
  const client = setup(1000n);
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: 'Gold' }));
  await user.click(screen.getByRole('radio', { name: 'Skull' }));
  await user.click(screen.getByRole('radio', { name: 'Checker' }));
  await user.click(screen.getByRole('button', { name: /Lock design/ }));
  expect(screen.getByRole('dialog')).toHaveTextContent('Total');
  await user.click(screen.getByRole('button', { name: en.capEditor.lockConfirm }));
  await waitFor(() => expect(screen.getByText(en.capEditor.status.locked)).toBeInTheDocument());
  expect((await client.getWallet()).balance).toBe(1000n - 500n - 80n - 30n);
  expect(screen.getByRole('button', { name: /Edit again/ })).toBeInTheDocument();
});

test('insufficient grain shows the mapped error and stays a draft', async () => {
  setup(10n);
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: 'Blue-dye' }));
  await user.click(screen.getByRole('button', { name: /Lock design/ }));
  await user.click(screen.getByRole('button', { name: en.capEditor.lockConfirm }));
  expect(await screen.findByRole('alert')).toHaveTextContent(en.capEditor.errors.INSUFFICIENT_GRAIN);
  expect(screen.getByText(en.capEditor.status.draft)).toBeInTheDocument();
});

test('the number cannot take the ring colour; moving the ring moves the number away', async () => {
  const client = setup();
  const user = userEvent.setup();
  await screen.findByRole('img', { name: 'Cap 67' });
  const number = screen.getByRole('radiogroup', { name: 'Number' });
  const ring = screen.getByRole('radiogroup', { name: 'Outer ring' });
  expect(number.querySelector('input[aria-label^="Base colour"]')).toBeDisabled();
  await user.click(ring.querySelector('label[data-checked] ~ label, label:nth-child(2)') as Element); // colour A on the ring
  await waitFor(() => expect((client.state().hens[0].colours.ring)).toBe('a'));
  expect(client.state().hens[0].colours.number).not.toBe('a');
});

test('choosing a centre pattern clears the icon and shows its colour row; Drop tiles carry the limited tag', async () => {
  setup();
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: 'Rings' }));
  expect(screen.getByRole('radio', { name: 'Heart' })).not.toBeChecked();
  expect(screen.getByRole('img', { name: 'Cap 67' }).querySelector('[data-part="centre"]')).not.toBeNull();
  expect(screen.getByRole('radiogroup', { name: 'Icon / centre pattern' })).toBeInTheDocument();
  expect(screen.getAllByText(/Drop · limited/).length).toBeGreaterThan(5);
});

test('a locked design is read-only and re-editing takes two taps and the fee', async () => {
  const client = setup(1000n, 'locked');
  const user = userEvent.setup();
  const button = await screen.findByRole('button', { name: /Edit again/ });
  expect(screen.getByRole('radio', { name: 'Blue-dye' })).toBeDisabled();
  await user.click(button);
  await user.click(screen.getByRole('button', { name: en.capEditor.confirmAgain }));
  await waitFor(() => expect(screen.getByText(en.capEditor.status.draft)).toBeInTheDocument());
  expect((await client.getWallet()).balance).toBe(950n);
});

test('installed caps offer a replacement for the fee and no lock button', async () => {
  setup(1000n, 'installed');
  expect(await screen.findByRole('button', { name: /Request a replacement/ })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /Lock design/ })).toBeNull();
});
