import type { ReactNode } from 'react';
import { formatGoldenGrain, GoldenGrainGlyph } from '@chirpcoop/real-chicken-ui/golden-grain';

// A Golden Grain amount with its glyph; `free` swaps in the free label.
export function Price({ amount, locale, free }: { amount: bigint; locale: string; free?: string }): ReactNode {
  if (amount === 0n && free) return <span className="rc-cap-price rc-cap-price--free">{free}</span>;
  return (
    <span className="rc-cap-price">
      <GoldenGrainGlyph /> {formatGoldenGrain(amount, locale)}
    </span>
  );
}
