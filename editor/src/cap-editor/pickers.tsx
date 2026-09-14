import type { ReactNode } from 'react';

export type PickerOption<T extends string | null> = {
  id: T;
  title: string;
  badge?: ReactNode;
  // Two filament hexes from the catalog (text, accent) rendered as a swatch.
  swatch?: [string, string];
  // An SVG path from layout.json (mm, y up) drawn as a small glyph; `reach`
  // is the radius the glyph fits in (7.4 for centre elements, 15.4 for the
  // band, whose window sits at the top of the cap).
  glyph?: { d: string; reach: number };
};

function Glyph({ d, reach }: { d: string; reach: number }) {
  const r = reach + 0.5;
  return (
    <svg className="rc-cap-option__glyph" viewBox={`${-r} ${-r} ${2 * r} ${2 * r}`} aria-hidden="true" focusable="false">
      <g transform="scale(1,-1)">
        <path d={d} fillRule="evenodd" />
      </g>
    </svg>
  );
}

type Props<T extends string | null> = {
  label: string;
  name: string;
  options: PickerOption<T>[];
  value: T;
  onChange: (value: T) => void;
  disabled?: boolean;
};

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
              {o.swatch ? (
                <span
                  className="rc-cap-option__swatch"
                  aria-hidden="true"
                  // design-tokens-allow: the two values are catalog filament colours (data), not design literals
                  style={{ background: `linear-gradient(135deg, ${o.swatch[0]} 50%, ${o.swatch[1]} 50%)` }}
                />
              ) : null}
              {o.glyph ? <Glyph d={o.glyph.d} reach={o.glyph.reach} /> : null}
              <span className="rc-cap-option__title">{o.title}</span>
              {o.badge ? <span className="rc-cap-option__badge">{o.badge}</span> : null}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
