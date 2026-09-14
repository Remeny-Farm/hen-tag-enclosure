import type { ReactNode } from 'react';

import type { ColourRole } from './types.js';

export type PickerOption<T extends string | null> = {
  id: T;
  title: string;
  badge?: ReactNode;
  // Pack tag under the title (e.g. "Vibe", "Drop · limited").
  tag?: string;
  // Three filament hexes from the catalog (base, a, b) rendered as a swatch:
  // base ring around a disc split into the two free colours.
  swatch?: [string, string, string];
  // An SVG path from layout.json (mm, y up) drawn as a small glyph; `reach`
  // is the radius the glyph fits in (7.4 for centre elements, 15.4 for the
  // band, whose window sits at the top of the cap).
  glyph?: { d: string; reach: number };
};

type Props<T extends string | null> = {
  label: string;
  name: string;
  options: PickerOption<T>[];
  value: T;
  onChange: (value: T) => void;
  disabled?: boolean;
};

// Fill values are catalog filament colours (data), never design literals.
function Swatch({ base, text, accent }: { base: string; text: string; accent: string }) {
  return (
    <svg className="rc-cap-option__swatch" viewBox="-10 -10 20 20" aria-hidden="true" focusable="false">
      <circle r="10" fill={base} />
      <path d="M 0 -6 A 6 6 0 0 1 0 6 Z" fill={accent} />
      <path d="M 0 -6 A 6 6 0 0 0 0 6 Z" fill={text} />
    </svg>
  );
}

function Glyph({ d, reach }: { d: string; reach: number }) {
  const r = reach + 0.5;
  // Band patterns live in the top window of the cap, so their tile shows
  // the upper half at twice the scale instead of a mostly empty disc.
  const band = reach > 10;
  const viewBox = band ? `${-r} ${-r} ${2 * r} ${r * 0.55}` : `${-r} ${-r} ${2 * r} ${2 * r}`;
  return (
    <svg className="rc-cap-option__glyph" viewBox={viewBox} preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
      <g transform="scale(1,-1)">
        <path d={d} fillRule="evenodd" />
      </g>
    </svg>
  );
}

// One radio group per choice (scheme, centre, band): native radios for
// keyboard and screen-reader behaviour, styled tiles with a 44 px tap floor.
export function OptionGroup<T extends string | null>({ label, name, options, value, onChange, disabled }: Props<T>) {
  return (
    <fieldset className="rc-cap-options" disabled={disabled}>
      <legend className="rc-kicker">{label}</legend>
      <div className="rc-cap-options__grid" role="radiogroup" aria-label={label}>
        {options.map((o) => {
          const checked = o.id === value;
          return (
            <label key={String(o.id)} className="rc-cap-option" data-checked={checked ? 'true' : undefined}>
              <input
                type="radio"
                name={name}
                className="rc-cap-sr-only"
                checked={checked}
                onChange={() => onChange(o.id)}
                aria-label={o.title}
              />
              {o.swatch ? <Swatch base={o.swatch[0]} text={o.swatch[1]} accent={o.swatch[2]} /> : null}
              {o.glyph ? <Glyph d={o.glyph.d} reach={o.glyph.reach} /> : null}
              <span className="rc-cap-option__title">{o.title}</span>
              {o.badge ? <span className="rc-cap-option__badge">{o.badge}</span> : null}
              {o.tag ? <span className="rc-cap-option__tag">{o.tag}</span> : null}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

export type ColourChoice = { role: ColourRole; hex: string; title: string };

type ColourProps = {
  label: string;
  name: string;
  choices: ColourChoice[];
  value: ColourRole;
  // A role the paired zone already uses; it cannot be picked here.
  blocked: ColourRole | null;
  onChange: (role: ColourRole) => void;
  disabled?: boolean;
};

// Three filament swatches for one zone of the cap. The blocked swatch is the
// colour of the zone this one sits on (number on ring, pattern on ring,
// icon on disc): the catalog rule that keeps every element visible.
export function ColourToggle({ label, name, choices, value, blocked, onChange, disabled }: ColourProps) {
  return (
    <div className="rc-cap-colour" role="radiogroup" aria-label={label}>
      <span className="rc-cap-colour__label">{label}</span>
      <span className="rc-cap-colour__swatches">
        {choices.map((c) => {
          const off = disabled || c.role === blocked;
          return (
            <label
              key={c.role}
              className="rc-cap-colour__swatch"
              data-checked={c.role === value ? 'true' : undefined}
              data-blocked={c.role === blocked ? 'true' : undefined}
            >
              <input
                type="radio"
                name={name}
                className="rc-cap-sr-only"
                checked={c.role === value}
                disabled={off}
                onChange={() => onChange(c.role)}
                aria-label={c.title}
              />
              {c.role === 'clear' ? (
                <span className="rc-cap-colour__chip rc-cap-colour__chip--clear" aria-hidden="true" />
              ) : (
                /* design-tokens-allow: catalog filament colour (data) */
                <span className="rc-cap-colour__chip" style={{ background: c.hex }} aria-hidden="true" />
              )}
            </label>
          );
        })}
      </span>
    </div>
  );
}
