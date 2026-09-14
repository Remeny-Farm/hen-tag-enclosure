import { expect, test, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { PackRail } from './pickers.js';

const groups = [
  { id: 'basic', title: 'Basic', tiles: Array.from({ length: 8 }, (_, i) => ({ id: `t${i}`, title: `Tile ${i}` })) },
];

function overflow(rail: HTMLElement, scrollLeft: number) {
  Object.defineProperty(rail, 'scrollWidth', { configurable: true, value: 900 });
  Object.defineProperty(rail, 'clientWidth', { configurable: true, value: 300 });
  Object.defineProperty(rail, 'scrollLeft', { configurable: true, writable: true, value: scrollLeft });
  fireEvent.scroll(rail);
}

test('the arrows appear only towards more tiles and page the rail', () => {
  render(<PackRail label="Icons" name="i" groups={groups} value="t0" onChange={() => {}} arrows={{ prev: 'Previous options', next: 'More options' }} />);
  const rail = screen.getByRole('radio', { name: 'Tile 0' }).closest('.rc-cap-rail') as HTMLElement;
  // jsdom has no layout: nothing overflows, no arrow
  expect(screen.queryByRole('button', { name: 'More options' })).toBeNull();
  overflow(rail, 0);
  expect(screen.getByRole('button', { name: 'More options' })).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Previous options' })).toBeNull();
  const scrollBy = vi.fn();
  (rail as HTMLElement & { scrollBy: typeof scrollBy }).scrollBy = scrollBy;
  screen.getByRole('button', { name: 'More options' }).click();
  expect(scrollBy).toHaveBeenCalledWith({ left: 252, behavior: 'smooth' });
  overflow(rail, 600);
  expect(screen.queryByRole('button', { name: 'More options' })).toBeNull();
  expect(screen.getByRole('button', { name: 'Previous options' })).toBeVisible();
});
