import type { RealChickenCopy } from '@chirpcoop/real-chicken-ui/types';

// RealChickenShell renders only these two of RealChickenCopy's fields, so the
// prototype carries just them and casts at the call site.
export type ShellCopy = Pick<RealChickenCopy, 'appTitle' | 'appSubtitle'>;

export function asShellCopy(copy: ShellCopy): RealChickenCopy {
  return copy as RealChickenCopy;
}
