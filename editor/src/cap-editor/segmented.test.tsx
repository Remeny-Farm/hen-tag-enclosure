import { expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { Segmented } from './segmented.js';

const items = [{ id: 'a', title: 'One' }, { id: 'b', title: 'Two' }, { id: 'c', title: 'Three' }] as const;

test('is a tablist with one tab stop and arrow-key navigation that wraps', async () => {
  const onChange = vi.fn();
  render(<Segmented label="Steps" idPrefix="s" numbered items={[...items]} value="a" onChange={onChange} />);
  const tabs = screen.getAllByRole('tab');
  expect(tabs).toHaveLength(3);
  expect(tabs[0]).toHaveAttribute('aria-selected', 'true');
  expect(tabs[1]).toHaveAttribute('tabindex', '-1');
  tabs[0].focus();
  await userEvent.keyboard('{ArrowLeft}');
  expect(onChange).toHaveBeenLastCalledWith('c');
  await userEvent.keyboard('{End}');
  expect(onChange).toHaveBeenLastCalledWith('c');
});
