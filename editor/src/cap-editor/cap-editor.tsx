import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useArmedConfirm } from '@chirpcoop/real-chicken-ui/armed-confirm';
import { formatGoldenGrain } from '@chirpcoop/real-chicken-ui/golden-grain';
import type { GoldenGrainPillCopy } from '@chirpcoop/real-chicken-ui/wallet-pill';

import { BottomBar } from './bottom-bar.js';
import { CapStage } from './cap-stage.js';
import { ColoursPanel } from './colours-panel.js';
import { LockDialog } from './lock-dialog.js';
import { ColourToggle, PackRail, SchemeCards, type ColourChoice, type RailGroup, type RailTile, type SchemeCard } from './pickers.js';
import { Price } from './price.js';
import { Segmented } from './segmented.js';
import {
  COLOUR_ROLES,
  findEntry,
  isClientError,
  lockPrice,
  pairedZone,
  type CapDesign,
  type CapDesignClient,
  type CapDraft,
  type CapEditorCopy,
  type Catalog,
  type CatalogEntry,
  type ClientErrorCode,
  type ColourRole,
  type Layout,
  type ZoneId,
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
type Step = 'palette' | 'motif' | 'colours';
type Message = { text: string; tone: 'info' | 'success' | 'error' };

const STEPS: Step[] = ['palette', 'motif', 'colours'];
const langOf = (locale: string): Lang => (locale.toLowerCase().startsWith('hu') ? 'hu' : 'en');
const toDraft = (d: CapDesign): CapDraft => ({ scheme: d.scheme, icon: d.icon, centre: d.centre, band: d.band, colours: d.colours });
// The centre rail mixes icons and patterns in one radio group; ids are
// prefixed so the two catalogs cannot collide (both have "dots").
const centreValue = (d: Pick<CapDesign, 'icon' | 'centre'>): string | null =>
  d.centre ? `centre:${d.centre}` : d.icon ? `icon:${d.icon}` : null;

// The patron's cap editor as a three-step game: Palette, Motif, Colours,
// with the cap on stage the whole time and a summary bar that always says
// what it costs and what to do next. No data fetching of its own beyond the
// client it is handed; no string literals (copy in props); every price and
// rule from the catalog.
export function CapEditor({ henId, client, catalog, layout, copy, walletCopy, locale }: CapEditorProps) {
  const [design, setDesign] = useState<CapDesign | null>(null);
  const [balance, setBalance] = useState<bigint | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [step, setStep] = useState<Step>('palette');
  const [celebrateKey, setCelebrateKey] = useState(0);
  const saveSeq = useRef(0);
  const messageTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lang = langOf(locale);
  const armed = useArmedConfirm();

  useEffect(() => {
    let alive = true;
    setDesign(null);
    setMessage(null);
    setStep('palette');
    Promise.all([client.load(henId), client.getWallet()])
      .then(([d, w]) => {
        if (!alive) return;
        setDesign(d);
        setBalance(w.balance);
      })
      .catch((e: unknown) => alive && say({ text: copy.errors[codeOf(e)], tone: 'error' }, 0));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, henId]);

  useEffect(() => () => {
    if (messageTimer.current) clearTimeout(messageTimer.current);
  }, []);

  function say(next: Message | null, ttlMs = 5000): void {
    if (messageTimer.current) clearTimeout(messageTimer.current);
    setMessage(next);
    if (next && ttlMs > 0) messageTimer.current = setTimeout(() => setMessage(null), ttlMs);
  }

  const scheme = useMemo(
    () => catalog.schemes.find((s) => s.id === design?.scheme) ?? catalog.schemes[0],
    [catalog, design?.scheme],
  );
  const editable = design?.status === 'draft';

  async function refreshWallet(): Promise<void> {
    setBalance((await client.getWallet()).balance);
  }

  // Optimistic: the stage answers the tap at once, the server's answer (or
  // refusal) lands afterwards; stale answers are dropped by sequence.
  async function change(patch: Partial<CapDraft>): Promise<void> {
    if (!design || !editable) return;
    const before = design;
    const next = { ...design, ...patch, colours: { ...design.colours, ...(patch.colours ?? {}) } };
    setDesign(next);
    const mine = ++saveSeq.current;
    try {
      const saved = await client.save(henId, toDraft(next));
      if (mine === saveSeq.current) setDesign(saved);
    } catch (e) {
      if (mine === saveSeq.current) {
        setDesign(before);
        say({ text: copy.errors[codeOf(e)], tone: 'error' });
      }
    }
  }

  // Zone colour with the visibility rule kept: when the paired zone takes
  // this zone's colour, this zone moves to the next free one, and we say so.
  function setColour(zone: ZoneId, role: ColourRole): void {
    if (!design) return;
    const colours = { ...design.colours, [zone]: role };
    const moved: ZoneId[] = [];
    for (const z of ['number', 'centre', 'band'] as ZoneId[]) {
      const other = pairedZone(catalog, z);
      if (other && colours[z] === colours[other]) {
        colours[z] = COLOUR_ROLES.find((r) => r !== colours[other]) ?? colours[z];
        moved.push(z);
      }
    }
    if (moved.length) say({ text: copy.autoFixTemplate.replace('{zone}', moved.map(zoneName).join(', ')), tone: 'info' });
    void change({ colours });
  }

  async function act(fn: () => Promise<CapDesign>, onDone?: () => void): Promise<void> {
    setBusy(true);
    try {
      setDesign(await fn());
      await refreshWallet();
      onDone?.();
    } catch (e) {
      say({ text: copy.errors[codeOf(e)], tone: 'error' });
    } finally {
      setBusy(false);
      setDialogOpen(false);
    }
  }

  const zoneName = (z: ZoneId) => (catalog.zones as Record<string, { name: { hu: string; en: string } }>)[z].name[lang];
  const priceOf = (e: CatalogEntry | null): bigint => BigInt(e?.price_grain ?? 0);
  const packOf = (id: string | undefined) => catalog.packs.find((p) => p.id === (id ?? 'basic'));
  const badgeOf = (e: CatalogEntry): ReactNode => (e.price_grain === 0 ? null : <Price amount={priceOf(e)} locale={locale} />);

  const schemeCards: SchemeCard[] = catalog.schemes.map((s) => ({
    id: s.id,
    title: s.name[lang],
    blurb: copy.schemeBlurbs[s.id],
    price: <Price amount={BigInt(s.price_grain)} locale={locale} free={copy.free} />,
    swatch: [s.base.hex, s.a.hex, s.b.hex],
  }));

  const groupsOf = <T extends string | null>(entries: readonly CatalogEntry[], tile: (e: CatalogEntry) => RailTile<T>, none: RailTile<T>): RailGroup<T>[] =>
    catalog.packs.map((p) => {
      const items = entries.filter((e) => (e.pack ?? 'basic') === p.id);
      const price = items[0]?.price_grain ?? 0;
      return {
        id: p.id,
        title: p.name[lang],
        note: price === 0 ? copy.free : copy.perItemTemplate.replace('{amount}', formatGoldenGrain(BigInt(price), locale)),
        limited: p.limited ? copy.limited : undefined,
        tiles: [...(p.id === 'basic' ? [none] : []), ...items.map(tile)],
      };
    }).filter((g) => g.tiles.length > 0);

  const centreGroups = groupsOf<string | null>(
    [...catalog.icons, ...catalog.centre_patterns.map((c) => ({ ...c, kind: 'centre' }))] as CatalogEntry[],
    (e) => ({
      id: (e as CatalogEntry & { kind?: string }).kind === 'centre' ? `centre:${e.id}` : `icon:${e.id}`,
      title: e.name[lang],
      glyph: {
        d: (e as CatalogEntry & { kind?: string }).kind === 'centre'
          ? layout.centre_patterns[e.id as keyof typeof layout.centre_patterns]
          : layout.icons[e.id as keyof typeof layout.icons],
        reach: layout.core_r,
      },
      badge: badgeOf(e),
    }),
    { id: null, title: copy.noneOption },
  );
  const bandGroups = groupsOf<string | null>(
    catalog.band_patterns,
    (e) => ({
      id: e.id,
      title: e.name[lang],
      glyph: {
        d: e.id === 'barcode' ? layout.band_patterns.stripes : layout.band_patterns[e.id as keyof typeof layout.band_patterns],
        reach: layout.band.r_max,
      },
      badge: badgeOf(e),
    }),
    { id: null, title: copy.noneOption },
  );
  const colourChoices: ColourChoice[] = [
    { role: 'base', hex: scheme.base.hex, title: `${copy.colourRoles.base}: ${scheme.base.filament}` },
    { role: 'a', hex: scheme.a.hex, title: `${copy.colourRoles.a}: ${scheme.a.filament}` },
    { role: 'b', hex: scheme.b.hex, title: `${copy.colourRoles.b}: ${scheme.b.filament}` },
    { role: 'clear', hex: catalog.window.hex, title: `${copy.colourRoles.clear}: ${catalog.window.filament}` },
  ];

  if (!design) {
    return (
      <div className="rc-cap-editor" aria-busy="true">
        <div className="rc-cap-stage rc-cap-stage--skeleton" aria-label={copy.loading}>
          <div className="rc-cap-stage__cap"><span className="rc-cap-skeleton rc-cap-skeleton--disc" /></div>
          <span className="rc-cap-skeleton rc-cap-skeleton--line" />
        </div>
        {message ? <p className="rc-inline-error" role="alert">{message.text}</p> : null}
      </div>
    );
  }

  const title = copy.previewTitleTemplate.replace('{serial}', String(design.serial));
  const total = lockPrice(catalog, design);
  const decor = findEntry(catalog.icons, design.icon) ?? findEntry(catalog.centre_patterns, design.centre);
  const bandEntry = findEntry(catalog.band_patterns, design.band);
  const lines = [
    { label: `${copy.schemeLabel}: ${scheme.name[lang]}`, amount: BigInt(scheme.price_grain) },
    ...(decor ? [{ label: `${copy.centreLabel}: ${decor.name[lang]}`, amount: priceOf(decor) }] : []),
    ...(bandEntry ? [{ label: `${copy.bandLabel}: ${bandEntry.name[lang]}`, amount: priceOf(bandEntry) }] : []),
  ];
  const stepIndex = STEPS.indexOf(step);
  const nextStep = STEPS[stepIndex + 1];

  // The colour of a chosen motif sits right under its rail, so nobody has
  // to discover it three screens later.
  const inlineColour = (zone: ZoneId, chosen: CatalogEntry | null) =>
    chosen ? (
      <div className="rc-cap-inline-colour">
        <ColourToggle
          label={`${zoneName(zone)}: ${chosen.name[lang]}`}
          name={`${henId}-motif-colour-${zone}`}
          choices={colourChoices}
          value={design.colours[zone]}
          blocked={pairedZone(catalog, zone) ? design.colours[pairedZone(catalog, zone) as ZoneId] : null}
          blockedReason={copy.hints.numberRule}
          onChange={(role) => setColour(zone, role)}
          disabled={!editable}
        />
        <p className="rc-cap-hint rc-cap-hint--quiet">{copy.hints.motifColour}</p>
      </div>
    ) : null;

  return (
    <div className="rc-cap-editor" data-editable={editable ? 'true' : 'false'}>
      <div className="rc-cap-editor__hero">
        <div className="rc-cap-editor__heading">
          <p className="rc-kicker">{copy.title}</p>
          <h2 className="rc-cap-editor__title">{title}</h2>
        </div>
        <CapStage
          design={design}
          catalog={catalog}
          layout={layout}
          title={title}
          status={design.status}
          statusText={copy.status[design.status]}
          celebrateKey={celebrateKey}
          proofUrl={design.proofUrl}
          proofAlt={copy.proofAlt}
        />
      </div>

      <div className="rc-cap-editor__flow">
        <Segmented
          label={copy.stepsLabel}
          idPrefix={`${henId}-step`}
          numbered
          items={STEPS.map((s) => ({ id: s, title: copy.steps[s] }))}
          value={step}
          onChange={setStep}
        />
        {!editable ? <p className="rc-cap-hint rc-cap-hint--frozen">{copy.hints.readOnly}</p> : null}

        <section
          className="rc-cap-panel"
          role="tabpanel"
          id={`${henId}-step-panel-palette`}
          aria-labelledby={`${henId}-step-tab-palette`}
          hidden={step !== 'palette'}
        >
          <p className="rc-cap-hint">{copy.hints.palette}</p>
          <SchemeCards
            label={copy.schemeLabel}
            name={`${henId}-scheme`}
            cards={schemeCards}
            value={design.scheme}
            onChange={(scheme) => void change({ scheme })}
            disabled={!editable}
          />
        </section>

        <section
          className="rc-cap-panel"
          role="tabpanel"
          id={`${henId}-step-panel-motif`}
          aria-labelledby={`${henId}-step-tab-motif`}
          hidden={step !== 'motif'}
        >
          <p className="rc-cap-hint">{copy.hints.motif}</p>
          <p className="rc-cap-hint rc-cap-hint--quiet">{copy.hints.packs}</p>
          <h3 className="rc-cap-panel__h">{copy.centreLabel}</h3>
          {inlineColour('centre', decor)}
          <PackRail
            label={copy.centreLabel}
            name={`${henId}-centre`}
            groups={centreGroups}
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
          <h3 className="rc-cap-panel__h">{copy.bandLabel}</h3>
          {inlineColour('band', bandEntry)}
          <PackRail
            label={copy.bandLabel}
            name={`${henId}-band`}
            groups={bandGroups}
            value={design.band}
            onChange={(band) => void change({ band })}
            disabled={!editable}
          />
        </section>

        <section
          className="rc-cap-panel"
          role="tabpanel"
          id={`${henId}-step-panel-colours`}
          aria-labelledby={`${henId}-step-tab-colours`}
          hidden={step !== 'colours'}
        >
          <ColoursPanel
            catalog={catalog}
            design={design}
            copy={copy}
            lang={lang}
            choices={colourChoices}
            editable={editable}
            onColour={setColour}
            henId={henId}
          />
        </section>

        <BottomBar walletCopy={walletCopy} locale={locale} balance={balance} total={total} totalLabel={copy.summaryLabel} free={copy.free} message={message}>
          {design.status === 'draft' ? (
            <>
              {nextStep ? (
                <button type="button" className="rc-cap-btn rc-cap-btn--ghost rc-cap-press" onClick={() => setStep(nextStep)}>
                  {copy.continueLabel}
                </button>
              ) : null}
              <button type="button" className="rc-cap-btn rc-cap-btn--primary rc-cap-press" onClick={() => setDialogOpen(true)} disabled={busy}>
                {copy.lock}
              </button>
            </>
          ) : null}
          {design.status === 'locked' ? (
            <button
              type="button"
              className="rc-cap-btn rc-cap-btn--ghost rc-cap-press"
              onClick={() => armed.handleTap(() => void act(() => client.unlockForEdit(henId), () => setStep('palette')))}
              onBlur={armed.disarm}
              disabled={busy}
            >
              {armed.armed ? copy.confirmAgain : copy.editAgainTemplate.replace('{amount}', formatGoldenGrain(BigInt(catalog.fees.reedit_grain), locale))}
            </button>
          ) : null}
          {design.status === 'installed' ? (
            <button
              type="button"
              className="rc-cap-btn rc-cap-btn--ghost rc-cap-press"
              onClick={() => armed.handleTap(() => void act(() => client.requestReplacement(henId), () => setStep('palette')))}
              onBlur={armed.disarm}
              disabled={busy}
            >
              {armed.armed ? copy.confirmAgain : copy.requestReplacementTemplate.replace('{amount}', formatGoldenGrain(BigInt(catalog.fees.replacement_grain), locale))}
            </button>
          ) : null}
        </BottomBar>
      </div>

      {dialogOpen ? (
        <LockDialog
          copy={copy}
          walletCopy={walletCopy}
          locale={locale}
          lines={lines}
          total={total}
          balance={balance ?? 0n}
          busy={busy}
          onCancel={() => setDialogOpen(false)}
          onConfirm={() =>
            void act(() => client.lock(henId), () => {
              setCelebrateKey((k) => k + 1);
              say({ text: copy.celebrate, tone: 'success' }, 6000);
            })}
        />
      ) : null}
    </div>
  );
}

function codeOf(e: unknown): ClientErrorCode {
  return isClientError(e) ? e.code : 'NOT_EDITABLE';
}
