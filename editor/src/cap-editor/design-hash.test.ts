import { expect, test } from 'vitest';

import { designHash } from './design-hash.js';

test('matches the Python test vectors in cad/test_cap_marking.py', async () => {
  expect(await designHash({ serial: 67, scheme: 'pasture', icon: 'heart', centre: null, band: 'stripes' })).toBe(
    '0ea9d1eb0b0e95b6',
  );
  expect(await designHash({ serial: 8, scheme: 'bluedye', icon: null, centre: 'rings', band: null })).toBe(
    'baf8189d7242b555',
  );
  expect(await designHash({ serial: 12345, scheme: 'pasture', icon: 'star', centre: null, band: 'dots' })).toBe(
    'b8f357cf9a577818',
  );
});
