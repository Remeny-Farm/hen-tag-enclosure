import type { Layout } from './types.js';

// The barcode band is unique per hen and generated on both sides from the
// serial with the same linear congruential generator (cad/cap_motifs.py
// lcg/barcode_bars); layout.json carries a sample so the test proves parity.
// All arithmetic stays below 2^53 by splitting the multiplication.
const MOD = 2147483648;

function mulmod(a: number, b: number): number {
  const hi = Math.floor(b / 65536);
  const lo = b % 65536;
  return ((a * hi) % MOD * 65536 + a * lo) % MOD;
}

export function* lcg(seed: number): Generator<number> {
  let x = (mulmod(seed % MOD, 2654435761 % MOD) + 12345) % MOD;
  while (true) {
    x = (mulmod(x, 1103515245) + 12345) % MOD;
    yield Math.floor(x / 65536) & 0x7fff;
  }
}

export function barcodeBars(serial: number, window: [number, number]): [number, number][] {
  const perMm = 180 / (Math.PI * 13.5);
  const g = lcg(serial);
  const bars: [number, number][] = [];
  let a = window[0] + 2;
  const end = window[1] - 2;
  while (true) {
    const w = (g.next().value % 3 === 0 ? 1.8 : 0.9) * perMm;
    const gap = (g.next().value % 4 === 0 ? 1.8 : 0.9) * perMm;
    if (a + w > end) break;
    bars.push([Math.round(a * 1000) / 1000, Math.round(w * 1000) / 1000]);
    a += w + gap;
  }
  return bars;
}

// SVG path (mm, y up) of the bars as annular sectors r 12.1-14.9.
export function barcodePath(serial: number, layout: Layout): string {
  const [rIn, rOut] = [12.1, 14.9];
  const pt = (r: number, deg: number) => `${(r * Math.cos((deg * Math.PI) / 180)).toFixed(3)} ${(r * Math.sin((deg * Math.PI) / 180)).toFixed(3)}`;
  return barcodeBars(serial, layout.band_window as [number, number])
    .map(([a, w]) => `M ${pt(rOut, a)} A ${rOut} ${rOut} 0 0 1 ${pt(rOut, a + w)} L ${pt(rIn, a + w)} A ${rIn} ${rIn} 0 0 0 ${pt(rIn, a)} Z`)
    .join(' ');
}
