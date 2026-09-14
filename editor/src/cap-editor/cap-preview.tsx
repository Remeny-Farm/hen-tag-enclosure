import { barcodePath } from './barcode.js';
import type { CapDesign, Catalog, ColourRole, Layout } from './types.js';

type Props = {
  design: Pick<CapDesign, 'serial' | 'scheme' | 'icon' | 'centre' | 'band' | 'colours'>;
  catalog: Catalog;
  layout: Layout;
  size?: number;
  title: string;
};

// Pure SVG in millimetres, y-up (one scale(1,-1) group), so every path from
// layout.json -- the generator's own sketches -- is used verbatim. The
// digits are laid along the bottom arc exactly like the printer's: centred on
// 270 deg, uniform advance, tops toward the centre. Fill colours come from
// the scheme's filaments through the design's zone assignment, like the
// four bodies the generator builds. No hooks, no state.
export function CapPreview({ design, catalog, layout, size, title }: Props) {
  const scheme = catalog.schemes.find((s) => s.id === design.scheme) ?? catalog.schemes[0];
  const hexOf: Record<ColourRole, string> = { base: scheme.base.hex, a: scheme.a.hex, b: scheme.b.hex, clear: catalog.window.hex };
  const fill = (zone: keyof typeof design.colours) => hexOf[design.colours[zone]];
  const isClear = (zone: keyof typeof design.colours) => design.colours[zone] === 'clear';
  // Clear PETG over the base-coloured body reads as frosted glass with the
  // base tint: a light layer, then the base colour at low opacity.
  const Glass = ({ d, part }: { d: string; part: string }) => (
    <g data-part={part} data-clear="true">
      <path d={d} className="rc-cap-preview__glass" fillRule="evenodd" />
      <path d={d} fill={scheme.base.hex} fillOpacity={0.35} fillRule="evenodd" />
    </g>
  );
  const Zone = ({ zone, d, part }: { zone: keyof typeof design.colours; d: string; part: string }) =>
    isClear(zone) ? <Glass d={d} part={part} /> : <path data-part={part} d={d} fill={fill(zone)} fillRule="evenodd" />;
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
  const windowPath = `${circle(0, 0, layout.window.r_max)} ${circle(0, 0, layout.window.r_min)}`;
  const centrePath = design.centre ? layout.centre_patterns[design.centre as keyof typeof layout.centre_patterns] : null;
  const iconPath = !design.centre && design.icon ? layout.icons[design.icon as keyof typeof layout.icons] : null;
  const bandPath = design.band === 'barcode'
    ? barcodePath(design.serial, layout)
    : design.band
      ? layout.band_patterns[design.band as keyof typeof layout.band_patterns]
      : null;
  const dim = size ? { width: size, height: size } : {};
  return (
    <svg className="rc-cap-preview" viewBox={`${-vb} ${-vb} ${2 * vb} ${2 * vb}`} role="img" aria-label={title} {...dim}>
      <defs>
        <clipPath id="rc-cap-disc">
          <circle r={r} />
        </clipPath>
      </defs>
      <g transform="scale(1,-1)">
        <path d={discPath} fill={scheme.base.hex} className="rc-cap-preview__shell" fillRule="evenodd" clipPath="url(#rc-cap-disc)" />
        <g clipPath="url(#rc-cap-disc)"><Zone zone="ring" d={discPath} part="ring" /></g>
        <Glass d={windowPath} part="window" />
        <Zone zone="disc" d={circle(0, 0, layout.core_r)} part="disc" />
        {bandPath ? <Zone zone="band" d={bandPath} part="band" /> : null}
        {centrePath ? <Zone zone="centre" d={centrePath} part="centre" /> : null}
        {iconPath ? <Zone zone="centre" d={iconPath} part="icon" /> : null}
        {glyphs.map((g, i) => (
          <g key={i} data-glyph={g.d} data-clear={isClear('number') ? 'true' : undefined} transform={`rotate(${g.theta + 90}) translate(0 ${-n.base_r})`}>
            {isClear('number') ? (
              <>
                <path d={g.path} className="rc-cap-preview__glass" stroke="var(--rc-paper-bright)" strokeWidth={n.stroke} strokeLinejoin="round" fillRule="evenodd" />
                <path d={g.path} fill={scheme.base.hex} fillOpacity={0.35} stroke={scheme.base.hex} strokeOpacity={0.35} strokeWidth={n.stroke} strokeLinejoin="round" fillRule="evenodd" />
              </>
            ) : (
              <path d={g.path} fill={fill('number')} stroke={fill('number')} strokeWidth={n.stroke} strokeLinejoin="round" fillRule="evenodd" />
            )}
          </g>
        ))}
      </g>
    </svg>
  );
}
