import type { CapDesign, Catalog, Layout } from './types.js';

type Props = {
  design: Pick<CapDesign, 'serial' | 'scheme' | 'icon' | 'centre' | 'band'>;
  catalog: Catalog;
  layout: Layout;
  size?: number;
  title: string;
};

// Pure SVG in millimetres, y-up (one scale(1,-1) group), so every path from
// layout.json -- the generator's own sketches -- is used verbatim. The digits
// are laid along the bottom arc exactly like the printer's: centred on
// 270 deg, uniform advance, tops toward the centre. No hooks, no state:
// the same design renders the same markup every time.
export function CapPreview({ design, catalog, layout, size, title }: Props) {
  const scheme = catalog.schemes.find((s) => s.id === design.scheme) ?? catalog.schemes[0];
  const r = layout.cap_r;
  const vb = r + 1;
  const n = layout.number;
  const digits = String(design.serial).split('');
  const glyphs = digits.map((d, i) => {
    const s = (i + 0.5) * n.advance - (digits.length * n.advance) / 2;
    const theta = n.centre_deg + (s / n.base_r) * (180 / Math.PI);
    return { d, theta, path: n.digits[d as keyof typeof n.digits].d };
  });
  const circle = (cx: number, cy: number, rr: number): string =>
    `M ${cx + rr} ${cy} A ${rr} ${rr} 0 1 0 ${cx - rr} ${cy} A ${rr} ${rr} 0 1 0 ${cx + rr} ${cy} Z`;
  const scallops = Array.from({ length: layout.scallops.n }, (_, i) => {
    const a = (2 * Math.PI * i) / layout.scallops.n;
    return circle(layout.scallops.orbit * Math.cos(a), layout.scallops.orbit * Math.sin(a), layout.scallops.r);
  });
  // The grip scallops are eight nicks in the rim: evenodd cuts the lens each
  // small circle shares with the disc, the clip drops the rest of it.
  const discPath = [circle(0, 0, r), ...scallops].join(' ');
  const centrePath = design.centre ? layout.centre_patterns[design.centre as keyof typeof layout.centre_patterns] : null;
  const iconPath = !design.centre && design.icon ? layout.icons[design.icon as keyof typeof layout.icons] : null;
  const bandPath = design.band ? layout.band_patterns[design.band as keyof typeof layout.band_patterns] : null;
  const dim = size ? { width: size, height: size } : {};
  const textFill = scheme.text.hex;
  const accentFill = scheme.accent.hex;
  const baseFill = scheme.base.hex;
  // The clear LED window is an annulus through the base-coloured top plate;
  // the board shows through it and the number overlaps it by design.
  const windowPath = `${circle(0, 0, layout.window.r_max)} ${circle(0, 0, layout.window.r_min)}`;
  return (
    <svg className="rc-cap-preview" viewBox={`${-vb} ${-vb} ${2 * vb} ${2 * vb}`} role="img" aria-label={title} {...dim}>
      <defs>
        <clipPath id="rc-cap-disc">
          <circle r={r} />
        </clipPath>
      </defs>
      <g transform="scale(1,-1)">
        <path data-part="base" d={discPath} fill={baseFill} className="rc-cap-preview__shell" fillRule="evenodd" clipPath="url(#rc-cap-disc)" />
        <path data-part="window" d={windowPath} className="rc-cap-preview__window" fillRule="evenodd" />
        <path data-part="core" d={circle(0, 0, layout.core_r)} fill={accentFill} />
        {bandPath ? <path data-part="band" d={bandPath} fill={accentFill} fillRule="evenodd" /> : null}
        {centrePath ? <path data-part="centre" d={centrePath} fill={textFill} fillRule="evenodd" /> : null}
        {iconPath ? <path data-part="icon" d={iconPath} fill={textFill} fillRule="evenodd" /> : null}
        {glyphs.map((g, i) => (
          <g key={i} data-glyph={g.d} transform={`rotate(${g.theta + 90}) translate(0 ${-n.base_r})`}>
            <path
              d={g.path}
              fill={textFill}
              stroke={textFill}
              strokeWidth={n.stroke}
              strokeLinejoin="round"
              fillRule="evenodd"
            />
          </g>
        ))}
      </g>
    </svg>
  );
}
