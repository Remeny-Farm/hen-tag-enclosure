import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useArmedConfirm } from '@chirpcoop/real-chicken-ui/armed-confirm';
import { formatGoldenGrain, GoldenGrainGlyph } from '@chirpcoop/real-chicken-ui/golden-grain';
import { GoldenGrainPill, type GoldenGrainPillCopy } from '@chirpcoop/real-chicken-ui/wallet-pill';

import { CapPreview } from './cap-preview.js';
import { LockDialog } from './lock-dialog.js';
import { OptionGroup, type PickerOption } from './pickers.js';
import {
  isClientError,
  type CapDesign,
  type CapDesignClient,
  type CapDraft,
  type CapEditorCopy,
  type Catalog,
  type ClientErrorCode,
  type Layout,
} from './types.js';

export type CapEditorProps = {
  henId: string;
  client: CapDesignClient;
  catalog: Catalog;
  layout: Layout;
  copy: CapEditorCopy;
  walletCopy: GoldenGrainPillCopy;
  locale: string;
};

type Lang = 'hu' | 'en';
const langOf = (locale: string): Lang => (locale.toLowerCase().startsWith('hu') ? 'hu' : 'en');
const toDraft = (d: CapDesign): CapDraft => ({ scheme: d.scheme, icon: d.icon, centre: d.centre, band: d.band });
// The centre group mixes icons and patterns in one radio group; ids are
// prefixed so the two catalogs cannot collide (both have "dots").
const centreValue = (d: Pick<CapDesign, 'icon' | 'centre'>): string | null =>
  d.centre ? `centre:${d.centre}` : d.icon ? `icon:${d.icon}` : null;

// The patron's cap editor: pickers on the left, live preview and the one
// action the current status allows on the right. No data fetching of its
// own beyond the client it is handed; no string literals (copy in props).
export function CapEditor({ henId, client, catalog, layout, copy, walletCopy, locale }: CapEditorProps) {
  const [design, setDesign] = useState<CapDesign | null>(null);
  const [balance, setBalance] = useState<bigint | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ClientErrorCode | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const saveSeq = useRef(0);
  const lang = langOf(locale);
  const armed = useArmedConfirm();

  useEffect(() => {
    let alive = true;
    setDesign(null);
    setError(null);
    Promise.all([client.load(henId), client.getWallet()])
      .then(([d, w]) => {
        if (!alive) return;
        setDesign(d);
        setBalance(w.balance);
      })
      .catch((e: unknown) => alive && setError(codeOf(e)));
    return () => {
      alive = false;
    };
  }, [client, henId]);

  const scheme = useMemo(
    () => catalog.schemes.find((s) => s.id === design?.scheme) ?? catalog.schemes[0],
    [catalog, design?.scheme],
  );
  const price = BigInt(scheme.price_grain);
  const editable = design?.status === 'draft';

  async function refreshWallet(): Promise<void> {
    setBalance((await client.getWallet()).balance);
  }

  // Optimistic: the preview follows the tap at once, the server's answer
  // (or its refusal) lands afterwards; stale answers are dropped by sequence.
  async function change(patch: Partial<CapDraft>): Promise<void> {
    if (!design || !editable) return;
    const before = design;
    const next = { ...design, ...patch };
    setDesign(next);
    setError(null);
    const mine = ++saveSeq.current;
    try {
      const saved = await client.save(henId, toDraft(next));
      if (mine === saveSeq.current) setDesign(saved);
    } catch (e) {
      if (mine === saveSeq.current) {
        setDesign(before);
        setError(codeOf(e));
      }
    }
  }

  async function act(fn: () => Promise<CapDesign>): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      setDesign(await fn());
      await refreshWallet();
    } catch (e) {
      setError(codeOf(e));
    } finally {
      setBusy(false);
      setDialogOpen(false);
    }
  }

  const schemeOptions: PickerOption<string>[] = catalog.schemes.map((s) => ({
    id: s.id,
    title: s.name[lang],
    swatch: [s.text.hex, s.accent.hex],
    badge: s.price_grain === 0 ? copy.free : <Price amount={BigInt(s.price_grain)} locale={locale} />,
  }));
  const centreReach = layout.core_r;
  const bandReach = layout.band.r_max;
  const centreOptions: PickerOption<string | null>[] = [
    { id: null, title: copy.noneOption },
    ...catalog.icons.map((i) => ({
      id: `icon:${i.id}`,
      title: i.name[lang],
      glyph: { d: layout.icons[i.id as keyof typeof layout.icons], reach: centreReach },
    })),
    ...catalog.centre_patterns.map((p) => ({
      id: `centre:${p.id}`,
      title: p.name[lang],
      glyph: { d: layout.centre_patterns[p.id as keyof typeof layout.centre_patterns], reach: centreReach },
    })),
  ];
  const bandOptions: PickerOption<string | null>[] = [
    { id: null, title: copy.noneOption },
    ...catalog.band_patterns.map((p) => ({
      id: p.id,
      title: p.name[lang],
      glyph: { d: layout.band_patterns[p.id as keyof typeof layout.band_patterns], reach: bandReach },
    })),
  ];

  if (!design) {
    return (
      <section className="rc-panel rc-cap-editor" aria-busy="true">
        {error ? <p className="rc-inline-error" role="alert">{copy.errors[error]}</p> : <span className="rc-skeleton" />}
      </section>
    );
  }

  const title = copy.previewTitleTemplate.replace('{serial}', String(design.serial));
  const reeditFee = BigInt(catalog.fees.reedit_grain);
  const replacementFee = BigInt(catalog.fees.replacement_grain);

  return (
    <div className="rc-cap-editor">
      <section className="rc-panel rc-cap-editor__preview">
        <div className="rc-section-heading">
          <p className="rc-kicker">{copy.title}</p>
          <h2>{title}</h2>
        </div>
        <CapPreview design={design} catalog={catalog} layout={layout} title={title} />
        <p className="rc-cap-status" data-status={design.status}>{copy.status[design.status]}</p>
        {design.proofUrl ? <img className="rc-cap-proof" src={design.proofUrl} alt={copy.proofAlt} /> : null}
      </section>

      <section className="rc-panel rc-cap-editor__options">
        <OptionGroup
          label={copy.schemeLabel}
          name={`${henId}-scheme`}
          options={schemeOptions}
          value={design.scheme}
          onChange={(scheme) => void change({ scheme })}
          disabled={!editable}
        />
        <OptionGroup
          label={copy.centreLabel}
          name={`${henId}-centre`}
          options={centreOptions}
          value={centreValue(design)}
          onChange={(v) =>
            void change(
              v === null
                ? { icon: null, centre: null }
                : v.startsWith('icon:')
                  ? { icon: v.slice(5), centre: null }
                  : { icon: null, centre: v.slice(7) },
            )}
          disabled={!editable}
        />
        <OptionGroup
          label={copy.bandLabel}
          name={`${henId}-band`}
          options={bandOptions}
          value={design.band}
          onChange={(band) => void change({ band })}
          disabled={!editable}
        />

        <div className="rc-cap-actions">
          {balance !== null ? <GoldenGrainPill balance={balance} copy={walletCopy} locale={locale} /> : null}
          {design.status === 'draft' ? (
            <button type="button" className="rc-cap-btn rc-cap-btn--primary" onClick={() => setDialogOpen(true)} disabled={busy}>
              {copy.lock}
              {price > 0n ? <span className="rc-cap-btn__price"><Price amount={price} locale={locale} /></span> : null}
            </button>
          ) : null}
          {design.status === 'locked' ? (
            <button
              type="button"
              className="rc-cap-btn rc-cap-btn--ghost"
              onClick={() => armed.handleTap(() => void act(() => client.unlockForEdit(henId)))}
              onBlur={armed.disarm}
              disabled={busy}
            >
              {armed.armed ? copy.confirmAgain : copy.editAgainTemplate.replace('{amount}', formatGoldenGrain(reeditFee, locale))}
            </button>
          ) : null}
          {design.status === 'installed' ? (
            <button
              type="button"
              className="rc-cap-btn rc-cap-btn--ghost"
              onClick={() => armed.handleTap(() => void act(() => client.requestReplacement(henId)))}
              onBlur={armed.disarm}
              disabled={busy}
            >
              {armed.armed ? copy.confirmAgain : copy.requestReplacementTemplate.replace('{amount}', formatGoldenGrain(replacementFee, locale))}
            </button>
          ) : null}
        </div>
        {error ? <p className="rc-inline-error" role="alert">{copy.errors[error]}</p> : null}
      </section>

      {dialogOpen ? (
        <LockDialog
          copy={copy}
          walletCopy={walletCopy}
          locale={locale}
          price={price}
          balance={balance ?? 0n}
          busy={busy}
          onCancel={() => setDialogOpen(false)}
          onConfirm={() => void act(() => client.lock(henId))}
        />
      ) : null}
    </div>
  );
}

function Price({ amount, locale }: { amount: bigint; locale: string }): ReactNode {
  return (
    <span className="rc-cap-price">
      <GoldenGrainGlyph /> {formatGoldenGrain(amount, locale)}
    </span>
  );
}

function codeOf(e: unknown): ClientErrorCode {
  return isClientError(e) ? e.code : 'NOT_EDITABLE';
}
