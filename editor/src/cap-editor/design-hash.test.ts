import { expect, test } from 'vitest';

import { designHash } from './design-hash.js';

test('matches the Python test vectors in cad/test_cap_marking.py', async () => {
  expect(await designHash({ serial: 67, scheme: 'classic', icon: 'heart', centre: null, band: 'stripes' })).toBe(
    '05dcdb796b921b25',
  );
  expect(await designHash({ serial: 8, scheme: 'meadow', icon: null, centre: 'rings', band: null })).toBe(
    '0371884d05cc4f6b',
  );
  expect(await designHash({ serial: 12345, scheme: 'classic', icon: 'star', centre: null, band: 'dots' })).toBe(
    '8fc7c9f4fcdb32c0',
  );
});
