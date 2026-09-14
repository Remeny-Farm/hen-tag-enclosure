import { expect, test } from 'vitest';
import { render } from '@testing-library/react';

import { CapPreview } from './cap-preview.js';
import catalog from './data/catalog.json';
import layout from './data/layout.json';
import { defaultColours } from './types.js';

const dc = defaultColours(catalog);
const base = { serial: 67, scheme: 'gold', icon: 'heart', centre: null, band: 'stripes', colours: dc };

test('draws every zone in the colour the design assigns', () => {
  const { container } = render(<CapPreview design={base} catalog={catalog} layout={layout} title="cap 67" />);
  const fillOf = (part: string) => container.querySelector(`[data-part="${part}"]`)?.getAttribute('fill');
  expect(container.querySelector('svg')).toHaveAttribute('aria-label', 'cap 67');
  expect(container.querySelectorAll('[data-glyph]')).toHaveLength(2);
  expect(fillOf('ring')).toBe('#1C1B20');
  expect(fillOf('icon')).toBe('#E2A72E');
  expect(fillOf('band')).toBe('#F2F2EE');
  expect(fillOf('disc')).toBe('#F2F2EE');
  expect(container.querySelector('[data-part="window"]')).not.toBeNull();
});

test('a recoloured ring and number follow the assignment', () => {
  const { container } = render(
    <CapPreview design={{ ...base, colours: { ...dc, ring: 'a', number: 'base' } }} catalog={catalog} layout={layout} title="cap" />,
  );
  expect(container.querySelector('[data-part="ring"]')?.getAttribute('fill')).toBe('#E2A72E');
  expect(container.querySelector('[data-glyph] path')?.getAttribute('fill')).toBe('#1C1B20');
});

test('a centre pattern replaces the icon, the barcode band is drawn per serial', () => {
  const { container } = render(
    <CapPreview design={{ ...base, serial: 12345, icon: null, centre: 'rings', band: 'barcode' }} catalog={catalog} layout={layout} title="cap" />,
  );
  expect(container.querySelectorAll('[data-glyph]')).toHaveLength(5);
  expect(container.querySelector('[data-part="icon"]')).toBeNull();
  expect(container.querySelector('[data-part="centre"]')).not.toBeNull();
  expect(container.querySelector('[data-part="band"]')?.getAttribute('d')).toMatch(/^M /);
});

test('is deterministic', () => {
  const a = render(<CapPreview design={base} catalog={catalog} layout={layout} title="t" />).container.innerHTML;
  const b = render(<CapPreview design={base} catalog={catalog} layout={layout} title="t" />).container.innerHTML;
  expect(a).toBe(b);
});
