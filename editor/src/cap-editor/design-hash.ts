import { ZONES, type CapDraft } from './types.js';

// First 16 hex chars of SHA-256 over the canonical design JSON -- the same
// bytes cad/cap_design.py hashes: keys in sorted order, no whitespace, v 2
// (v 2 added the five zone colours). JSON.stringify keeps the literal's key
// order, so the keys are written sorted here on purpose.
export async function designHash(d: CapDraft & { serial: number }): Promise<string> {
  const colours: Record<string, string> = {};
  for (const z of ZONES) colours[z] = d.colours[z];
  const canon = JSON.stringify({
    band: d.band,
    centre: d.centre,
    colours: { band: colours.band, centre: colours.centre, disc: colours.disc, number: colours.number, ring: colours.ring },
    icon: d.icon,
    scheme: d.scheme,
    serial: d.serial,
    v: 2,
  });
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canon));
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
    .slice(0, 16);
}
