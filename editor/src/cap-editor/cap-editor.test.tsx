import { expect, test } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
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

const tab = (name: string) => screen.getByRole('tab', { name: new RegExp(name) });

test('opens on the palette step with the cap on stage, the wallet and the summary', async () => {
  setup();
  expect(await screen.findByRole('img', { name: 'Cap 67' })).toBeInTheDocument();
  expect(screen.getByLabelText('1,000 Golden Grain')).toBeInTheDocument();
  expect(screen.getByRole('tablist', { name: en.capEditor.stepsLabel })).toBeInTheDocument();
  expect(tab('Palette')).toHaveAttribute('aria-selected', 'true');
  expect(screen.getByRole('radio', { name: 'Blue-dye' })).toBeInTheDocument();
  expect(screen.getByText(en.capEditor.hints.palette)).toBeInTheDocument();
  expect(screen.getByText(en.capEditor.summaryLabel)).toBeInTheDocument();
});

test('the steps are a keyboard tablist and Next walks through them', async () => {
  setup();
  const user = userEvent.setup();
  await screen.findByRole('img', { name: 'Cap 67' });
  await user.click(screen.getByRole('button', { name: en.capEditor.continueLabel }));
  expect(tab('Motif')).toHaveAttribute('aria-selected', 'true');
  expect(screen.getByRole('tabpanel', { name: /Motif/ })).toBeVisible();
  tab('Motif').focus();
  await user.keyboard('{ArrowRight}');
  expect(tab('Colours')).toHaveAttribute('aria-selected', 'true');
  expect(screen.getByRole('radiogroup', { name: 'Outer ring' })).toBeInTheDocument();
});

test('locking a paid scheme with a Drop icon and a Vibe band charges the itemised total and celebrates', async () => {
  const client = setup(1000n);
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: 'Gold' }));
  await user.click(tab('Motif'));
  await user.click(screen.getByRole('radio', { name: 'Skull' }));
  await user.click(screen.getByRole('radio', { name: 'Checker' }));
  expect(screen.getAllByRole('region', { name: 'Drop' })[0]).toHaveTextContent(en.capEditor.limited);
  await user.click(screen.getByRole('button', { name: en.capEditor.lock }));
  const dialog = screen.getByRole('dialog');
  expect(dialog).toHaveTextContent('Total');
  expect(dialog).toHaveTextContent(en.capEditor.hints.lock);
  await user.click(within(dialog).getByRole('button', { name: en.capEditor.lockConfirm }));
  await waitFor(() => expect(screen.getByText(en.capEditor.status.locked)).toBeInTheDocument());
  expect((await client.getWallet()).balance).toBe(1000n - 500n - 80n - 30n);
  expect(screen.getByRole('status')).toHaveTextContent(en.capEditor.celebrate);
  expect(screen.getByRole('button', { name: /Edit again/ })).toBeInTheDocument();
});

test('insufficient grain shows the mapped error and stays a draft', async () => {
  setup(10n);
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: 'Blue-dye' }));
  await user.click(screen.getByRole('button', { name: en.capEditor.lock }));
  await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: en.capEditor.lockConfirm }));
  expect(await screen.findByRole('alert')).toHaveTextContent(en.capEditor.errors.INSUFFICIENT_GRAIN);
  expect(screen.getByText(en.capEditor.status.draft)).toBeInTheDocument();
});

test('the icon colour sits right under the icon rail, clear allowed, the disc colour blocked and explained', async () => {
  const client = setup();
  const user = userEvent.setup();
  await screen.findByRole('img', { name: 'Cap 67' });
  await user.click(tab('Motif'));
  const row = screen.getByRole('radiogroup', { name: 'Icon / centre pattern: Heart' });
  expect(row.querySelector('input[aria-label^="Colour B"]')).toBeDisabled(); // the disc is colour b
  expect(row.querySelector('input[aria-label^="Colour B"]')?.getAttribute('aria-label')).toContain(en.capEditor.hints.numberRule);
  await user.click(row.querySelector('label:nth-child(4)') as Element);           // clear
  await waitFor(() => expect(client.state().hens[0].colours.centre).toBe('clear'));
  expect(screen.getByText(en.capEditor.hints.motifColour)).toBeInTheDocument();
});

test('the number cannot take the ring colour; moving the ring moves the number away and says so', async () => {
  const client = setup();
  const user = userEvent.setup();
  await screen.findByRole('img', { name: 'Cap 67' });
  await user.click(tab('Colours'));
  const number = screen.getByRole('radiogroup', { name: 'Number' });
  expect(number.querySelector('input[aria-label^="Base colour"]')).toBeDisabled();
  const ring = screen.getByRole('radiogroup', { name: 'Outer ring' });
  await user.click(ring.querySelector('label:nth-child(2)') as Element);          // colour A on the ring
  await waitFor(() => expect(client.state().hens[0].colours.ring).toBe('a'));
  expect(client.state().hens[0].colours.number).not.toBe('a');
  expect(screen.getByRole('status')).toHaveTextContent('Number');
});

test('choosing a centre pattern clears the icon and the band gets its own colour row', async () => {
  setup();
  const user = userEvent.setup();
  await screen.findByRole('img', { name: 'Cap 67' });
  await user.click(tab('Motif'));
  await user.click(screen.getByRole('radio', { name: 'Rings' }));
  expect(screen.getByRole('radio', { name: 'Heart' })).not.toBeChecked();
  expect(screen.getByRole('img', { name: 'Cap 67' }).querySelector('[data-part="centre"]')).not.toBeNull();
  await user.click(screen.getByRole('radio', { name: 'Stripes' }));
  expect(screen.getByRole('radiogroup', { name: 'Band pattern: Stripes' })).toBeInTheDocument();
});

test('a locked design is frozen with an explanation; re-editing takes two taps and the fee', async () => {
  const client = setup(1000n, 'locked');
  const user = userEvent.setup();
  const button = await screen.findByRole('button', { name: /Edit again/ });
  expect(screen.getByText(en.capEditor.hints.readOnly)).toBeInTheDocument();
  expect(screen.getByRole('radio', { name: 'Blue-dye' })).toBeDisabled();
  await user.click(button);
  await user.click(screen.getByRole('button', { name: en.capEditor.confirmAgain }));
  await waitFor(() => expect(screen.getByText(en.capEditor.status.draft)).toBeInTheDocument());
  expect((await client.getWallet()).balance).toBe(950n);
});

test('installed caps offer a replacement for the fee and no lock button', async () => {
  setup(1000n, 'installed');
  expect(await screen.findByRole('button', { name: /Request a replacement/ })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: en.capEditor.lock })).toBeNull();
});
