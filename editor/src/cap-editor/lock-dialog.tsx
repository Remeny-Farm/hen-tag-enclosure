import { useEffect, useId, useRef, type KeyboardEvent, type MouseEvent } from 'react';
import { wrapDialogTabFocus } from '@chirpcoop/real-chicken-ui/dialog-focus';
import { formatGoldenGrain, GoldenGrainGlyph } from '@chirpcoop/real-chicken-ui/golden-grain';
import { GoldenGrainPill, type GoldenGrainPillCopy } from '@chirpcoop/real-chicken-ui/wallet-pill';

import type { CapEditorCopy } from './types.js';

type Props = {
  copy: CapEditorCopy;
  walletCopy: GoldenGrainPillCopy;
  locale: string;
  price: bigint;
  balance: bigint;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

// Confirmation before the one irreversible patron action. Same accessible
// shape as the web app's rename modal: role=dialog + aria-modal, Tab wrapped
// by the package helper, Escape and the overlay both cancel, focus lands on
// the confirm button and returns to the trigger on unmount.
export function LockDialog({ copy, walletCopy, locale, price, balance, busy, onCancel, onConfirm }: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    confirmRef.current?.focus();
    return () => previouslyFocused?.focus();
  }, []);

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape') {
      event.stopPropagation();
      onCancel();
      return;
    }
    wrapDialogTabFocus(dialogRef.current, event);
  }

  function handleOverlayMouseDown(event: MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget) onCancel();
  }

  return (
    <div className="rc-cap-dialog__overlay" onMouseDown={handleOverlayMouseDown}>
      <div
        ref={dialogRef}
        className="rc-cap-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        onKeyDown={handleKeyDown}
      >
        <h2 className="rc-cap-dialog__title" id={titleId}>{copy.lockTitle}</h2>
        <p className="rc-cap-dialog__desc" id={descId}>{copy.lockBody}</p>
        <dl className="rc-cap-dialog__facts">
          <dt>{copy.schemeLabel}</dt>
          <dd className="rc-cap-price">
            {price === 0n ? copy.free : (<><GoldenGrainGlyph /> {formatGoldenGrain(price, locale)}</>)}
          </dd>
          <dt>{walletCopy.label}</dt>
          <dd><GoldenGrainPill balance={balance} copy={walletCopy} locale={locale} variant="compact" /></dd>
        </dl>
        <div className="rc-cap-dialog__actions">
          <button type="button" className="rc-cap-btn rc-cap-btn--ghost" onClick={onCancel} disabled={busy}>
            {copy.cancel}
          </button>
          <button
            ref={confirmRef}
            type="button"
            className="rc-cap-btn rc-cap-btn--primary"
            onClick={onConfirm}
            disabled={busy}
          >
            {copy.lockConfirm}
          </button>
        </div>
      </div>
    </div>
  );
}
