import { expect, test } from 'vitest';

import { barcodeBars, barcodePath } from './barcode.js';
import layout from './data/layout.json';

test('reproduces the generator bars for the sample serial', () => {
  const sample = layout.barcode_sample;
  expect(barcodeBars(sample.serial, layout.band_window as [number, number])).toEqual(sample.bars);
});

test('different serials give different codes and a non-empty path', () => {
  expect(barcodeBars(67, [-10, 190])).not.toEqual(barcodeBars(68, [-10, 190]));
  expect(barcodePath(67, layout)).toMatch(/^M /);
});
