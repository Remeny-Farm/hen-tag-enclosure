import type { ReactNode } from 'react';

import type { ColourRole } from './types.js';

// ---------------------------------------------------------------- schemes
export type SchemeCard = {
  id: string;
  title: string;
  blurb?: string;
  price: ReactNode;
  // Three filament hexes from the catalog (base, a, b): base ring around a
  // disc split into the two free colours. Data, not design literals.
  swatch: [string, string, string];
};

type SchemeProps = {
  label: string;
  name: string;
  cards: SchemeCard[];
  value: string;
  onChange: (id: string) => void;
  disabled?: boolean;
};

function Swatch({ base, a, b }: { base: string; a: string; b: string }) {
  return (
    <svg className="rc-cap-swatch" viewBox="-10 -10 20 20" aria-hidden="true" focusable="false">
      <circle r="10" fill={base} />
      <path d="M 0 -6 A 6 6 0 0 1 0 6 Z" fill={b} />
      <path d="M 0 -6 A 6 6 0 0 0 0 6 Z" fill={a} />
    </svg>
  );
}

// Three big cards: the palette is the first decision and the one that
// changes the most, so it gets room, a blurb and the price up front.
export function SchemeCards({ label, name, cards, value, onChange, disabled }: SchemeProps) {
  return (
    <fieldset className="rc-cap-fieldset" disabled={disabled}>
      <legend className="rc-cap-sr-only">{label}</legend>
      <div className="rc-cap-cards" role="radiogroup" aria-label={label}>
        {cards.map((c) => {
          const checked = c.id === value;
          return (
            <label key={c.id} className="rc-cap-card rc-cap-press" data-checked={checked ? 'true' : undefined}>
              <input type="radio" name={name} className="rc-cap-sr-only" checked={checked} onChange={() => onChange(c.id)} aria-label={c.title} />
              <Swatch base={c.swatch[0]} a={c.swatch[1]} b={c.swatch[2]} />
              <span className="rc-cap-card__text">
                <span className="rc-cap-card__title">{c.title}</span>
                {c.blurb ? <span className="rc-cap-card__blurb">{c.blurb}</span> : null}
              </span>
              <span className="rc-cap-card__price">{c.price}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

// ---------------------------------------------------------------- rails
export type RailTile<T extends string | null> = {
  id: T;
  title: string;
  badge?: ReactNode;
  // An SVG path from layout.json (mm, y up) drawn as a small glyph; `reach`
  // is the radius it fits in (7.4 for centre elements, 15.4 for the band).
  glyph?: { d: string; reach: number };
};

export type RailGroup<T extends string | null> = {
  id: string;
  title: string;
  note?: string;
  limited?: string;
  tiles: RailTile<T>[];
};

type RailProps<T extends string | null> = {
  label: string;
  name: string;
  groups: RailGroup<T>[];
  value: T;
  onChange: (id: T) => void;
  disabled?: boolean;
};

function Glyph({ d, reach }: { d: string; reach: number }) {
  const r = reach + 0.5;
  // Band patterns live in the top window of the cap, so their tile shows
  // the upper half at twice the scale instead of a mostly empty disc.
  const band = reach > 10;
  const viewBox = band ? `${-r} ${-r} ${2 * r} ${r * 0.55}` : `${-r} ${-r} ${2 * r} ${2 * r}`;
  return (
    <svg className="rc-cap-tile__glyph" viewBox={viewBox} preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
      <g transform="scale(1,-1)">
        <path d={d} fillRule="evenodd" />
      </g>
    </svg>
  );
}

// One radio group across several horizontally snapping rails, one rail per
// pack: the 26 icons stay browsable with a thumb and never become a wall.
export function PackRail<T extends string | null>({ label, name, groups, value, onChange, disabled }: RailProps<T>) {
  return (
    <fieldset className="rc-cap-fieldset" disabled={disabled}>
      <legend className="rc-cap-sr-only">{label}</legend>
      <div role="radiogroup" aria-label={label} className="rc-cap-rails">
        {groups.map((g) => (
          <section key={g.id} className="rc-cap-rail-group" aria-label={g.title}>
            <header className="rc-cap-rail-group__head">
              <span className="rc-cap-rail-group__title">{g.title}</span>
              {g.note ? <span className="rc-cap-rail-group__note">{g.note}</span> : null}
              {g.limited ? <span className="rc-cap-rail-group__limited">{g.limited}</span> : null}
            </header>
            <div className="rc-cap-rail">
              {g.tiles.map((t) => {
                const checked = t.id === value;
                return (
                  <label key={String(t.id)} className="rc-cap-tile rc-cap-press" data-checked={checked ? 'true' : undefined}>
                    <input type="radio" name={name} className="rc-cap-sr-only" checked={checked} onChange={() => onChange(t.id)} aria-label={t.title} />
                    {t.glyph ? <Glyph d={t.glyph.d} reach={t.glyph.reach} /> : <span className="rc-cap-tile__none" aria-hidden="true" />}
                    <span className="rc-cap-tile__title">{t.title}</span>
                    {t.badge ? <span className="rc-cap-tile__badge">{t.badge}</span> : null}
                  </label>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </fieldset>
  );
}

// ---------------------------------------------------------------- colours
export type ColourChoice = { role: ColourRole; hex: string; title: string };

type ColourProps = {
  label: string;
  name: string;
  choices: ColourChoice[];
  value: ColourRole;
  // A role the paired zone already uses; it cannot be picked here.
  blocked: ColourRole | null;
  blockedReason?: string;
  onChange: (role: ColourRole) => void;
  disabled?: boolean;
};

// Four filament chips for one zone of the cap. The blocked chip is the
// colour of the zone this one sits on (number on ring, pattern on ring,
// icon on disc): the catalog rule that keeps every element visible.
export function ColourToggle({ label, name, choices, value, blocked, blockedReason, onChange, disabled }: ColourProps) {
  return (
    <div className="rc-cap-colour" role="radiogroup" aria-label={label}>
      <span className="rc-cap-colour__label">{label}</span>
      <span className="rc-cap-colour__chips">
        {choices.map((c) => {
          const isBlocked = c.role === blocked;
          return (
            <label
              key={c.role}
              className="rc-cap-chip rc-cap-press"
              data-checked={c.role === value ? 'true' : undefined}
              data-blocked={isBlocked ? 'true' : undefined}
              title={isBlocked && blockedReason ? blockedReason : undefined}
            >
              <input
                type="radio"
                name={name}
                className="rc-cap-sr-only"
                checked={c.role === value}
                disabled={disabled || isBlocked}
                onChange={() => onChange(c.role)}
                aria-label={isBlocked && blockedReason ? `${c.title} (${blockedReason})` : c.title}
              />
              {c.role === 'clear' ? (
                <span className="rc-cap-chip__fill rc-cap-chip__fill--clear" aria-hidden="true" />
              ) : (
                /* design-tokens-allow: catalog filament colour (data) */
                <span className="rc-cap-chip__fill" style={{ background: c.hex }} aria-hidden="true" />
              )}
            </label>
          );
        })}
      </span>
    </div>
  );
}
