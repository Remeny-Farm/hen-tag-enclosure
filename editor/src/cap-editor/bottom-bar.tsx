import type { ReactNode } from 'react';
import { GoldenGrainPill, type GoldenGrainPillCopy } from '@chirpcoop/real-chicken-ui/wallet-pill';

import { Price } from './price.js';

type Props = {
  walletCopy: GoldenGrainPillCopy;
  locale: string;
  balance: bigint | null;
  total: bigint;
  totalLabel: string;
  free: string;
  // Announced politely: auto-fix notes, celebration, errors.
  message?: { text: string; tone: 'info' | 'success' | 'error' } | null;
  children: ReactNode;
};

// The persistent summary bar: what the cap costs, what you have, and the one
// thing to do next. Sticky above the home indicator on phones.
export function BottomBar({ walletCopy, locale, balance, total, totalLabel, free, message, children }: Props) {
  return (
    <div className="rc-cap-bar">
      {message ? (
        <p className="rc-cap-bar__message" data-tone={message.tone} role={message.tone === 'error' ? 'alert' : 'status'}>
          {message.text}
        </p>
      ) : null}
      <div className="rc-cap-bar__row">
        <div className="rc-cap-bar__sum" aria-live="polite">
          <span className="rc-cap-bar__label">{totalLabel}</span>
          <span className="rc-cap-bar__total"><Price amount={total} locale={locale} free={free} /></span>
        </div>
        {balance !== null ? <GoldenGrainPill balance={balance} copy={walletCopy} locale={locale} variant="compact" /> : null}
        <div className="rc-cap-bar__actions">{children}</div>
      </div>
    </div>
  );
}
