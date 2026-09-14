import { expect, test } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { en } from '../copy/en.js';
import { CapEditor } from './cap-editor.js';
import catalog from './data/catalog.json';
import layout from './data/layout.json';
import { createMockClient } from './mock-client.js';
import type { CapDesign } from './types.js';

const hen: CapDesign = {
  henId: 'h1', serial: 67, scheme: 'classic', icon: 'heart', centre: null, band: null,
  status: 'draft', designHash: '', proofUrl: null,
};

function setup(balance = 1000n, status: CapDesign['status'] = 'draft') {
  const client = createMockClient({ hens: [{ ...hen, status }], balance, catalog });
  render(
    <CapEditor henId="h1" client={client} catalog={catalog} layout={layout} copy={en.capEditor} walletCopy={en.wallet} locale="en-US" />,
  );
  return client;
}

test('shows the preview, the wallet and the scheme options', async () => {
  setup();
  expect(await screen.findByRole('img', { name: 'Cap 67' })).toBeInTheDocument();
  expect(screen.getByLabelText('1,000 Golden Grain')).toBeInTheDocument();
  expect(screen.getByRole('radio', { name: 'Meadow' })).toBeInTheDocument();
  expect(screen.getByRole('radio', { name: 'Heart' })).toBeChecked();
});

test('locking a paid scheme asks for confirmation, charges, and locks', async () => {
  const client = setup(500n);
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: 'Sunset' }));
  await user.click(screen.getByRole('button', { name: /Lock design/ }));
  await user.click(screen.getByRole('button', { name: en.capEditor.lockConfirm }));
  await waitFor(() => expect(screen.getByText(en.capEditor.status.locked)).toBeInTheDocument());
  expect((await client.getWallet()).balance).toBe(200n);
  expect(screen.getByRole('button', { name: /Edit again/ })).toBeInTheDocument();
  expect(screen.queryByRole('dialog')).toBeNull();
});

test('insufficient grain shows the mapped error and stays a draft', async () => {
  setup(10n);
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: 'Meadow' }));
  await user.click(screen.getByRole('button', { name: /Lock design/ }));
  await user.click(screen.getByRole('button', { name: en.capEditor.lockConfirm }));
  expect(await screen.findByRole('alert')).toHaveTextContent(en.capEditor.errors.INSUFFICIENT_GRAIN);
  expect(screen.getByText(en.capEditor.status.draft)).toBeInTheDocument();
});

test('choosing a centre pattern clears the icon and redraws the preview', async () => {
  setup();
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: 'Rings' }));
  expect(screen.getByRole('radio', { name: 'Heart' })).not.toBeChecked();
  expect(screen.getByRole('img', { name: 'Cap 67' }).querySelector('[data-part="centre"]')).not.toBeNull();
  await user.click(screen.getByRole('radio', { name: 'Stripes' }));
  expect(screen.getByRole('img', { name: 'Cap 67' }).querySelector('[data-part="band"]')).not.toBeNull();
});

test('a locked design is read-only and re-editing takes two taps and the fee', async () => {
  const client = setup(1000n, 'locked');
  const user = userEvent.setup();
  const button = await screen.findByRole('button', { name: /Edit again/ });
  expect(screen.getByRole('radio', { name: 'Meadow' })).toBeDisabled();
  await user.click(button);
  expect(screen.getByRole('button', { name: en.capEditor.confirmAgain })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: en.capEditor.confirmAgain }));
  await waitFor(() => expect(screen.getByText(en.capEditor.status.draft)).toBeInTheDocument());
  expect((await client.getWallet()).balance).toBe(950n);
});

test('installed caps offer a replacement for the fee and no lock button', async () => {
  setup(1000n, 'installed');
  expect(await screen.findByRole('button', { name: /Request a replacement/ })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /Lock design/ })).toBeNull();
});
