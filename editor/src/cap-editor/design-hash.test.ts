import { expect, test } from 'vitest';

import { designHash } from './design-hash.js';
import type { ZoneColours } from './types.js';

const dc: ZoneColours = { ring: 'base', number: 'a', disc: 'b', centre: 'a', band: 'b' };

test('matches the Python test vectors in cad/test_cap_marking.py', async () => {
  expect(await designHash({ serial: 67, scheme: 'pasture', icon: 'heart', centre: null, band: 'stripes', colours: dc })).toBe(
    '515bd1ffc394d597',
  );
  expect(
    await designHash({
      serial: 8, scheme: 'bluedye', icon: null, centre: 'rings', band: null,
      colours: { ring: 'a', number: 'base', disc: 'b', centre: 'a', band: 'b' },
    }),
  ).toBe('d6d6ead0fc97b830');
});
