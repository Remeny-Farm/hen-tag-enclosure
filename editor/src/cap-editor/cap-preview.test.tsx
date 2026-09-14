import { expect, test } from 'vitest';
import { render } from '@testing-library/react';

import { CapPreview } from './cap-preview.js';
import catalog from './data/catalog.json';
import layout from './data/layout.json';

const base = { serial: 67, scheme: 'gold', icon: 'heart', centre: null, band: 'stripes' };

test('draws the digits, the icon and the band pattern in the scheme colours', () => {
  const { container } = render(<CapPreview design={base} catalog={catalog} layout={layout} title="cap 67" />);
  expect(container.querySelector('svg')).toHaveAttribute('aria-label', 'cap 67');
  expect(container.querySelectorAll('[data-glyph]')).toHaveLength(2);
  expect(container.querySelector('[data-part="icon"]')?.getAttribute('fill')).toBe('#E2A72E');
  expect(container.querySelector('[data-part="band"]')?.getAttribute('fill')).toBe('#F2F2EE');
  expect(container.querySelector('[data-part="core"]')?.getAttribute('fill')).toBe('#F2F2EE');
  expect(container.querySelector('[data-part="base"]')?.getAttribute('fill')).toBe('#1C1B20');
  expect(container.querySelector('[data-part="window"]')).not.toBeNull();
});

test('a centre pattern replaces the icon and a 5-digit serial has five glyphs', () => {
  const { container } = render(
    <CapPreview design={{ ...base, serial: 12345, icon: null, centre: 'rings' }} catalog={catalog} layout={layout} title="cap" />,
  );
  expect(container.querySelectorAll('[data-glyph]')).toHaveLength(5);
  expect(container.querySelector('[data-part="icon"]')).toBeNull();
  expect(container.querySelector('[data-part="centre"]')).not.toBeNull();
});

test('no band and no decor leaves only the core disc', () => {
  const { container } = render(
    <CapPreview design={{ ...base, icon: null, band: null }} catalog={catalog} layout={layout} title="cap" />,
  );
  expect(container.querySelector('[data-part="band"]')).toBeNull();
  expect(container.querySelector('[data-part="icon"]')).toBeNull();
  expect(container.querySelector('[data-part="core"]')).not.toBeNull();
});

test('is deterministic', () => {
  const a = render(<CapPreview design={base} catalog={catalog} layout={layout} title="t" />).container.innerHTML;
  const b = render(<CapPreview design={base} catalog={catalog} layout={layout} title="t" />).container.innerHTML;
  expect(a).toBe(b);
});
