import type { CapDraft } from './types.js';

// First 16 hex chars of SHA-256 over the canonical design JSON -- the same
// bytes cad/cap_design.py hashes: keys in sorted order, no whitespace, v 1.
// JSON.stringify keeps the literal's key order, so the keys are written
// sorted here on purpose.
export async function designHash(d: CapDraft & { serial: number }): Promise<string> {
  const canon = JSON.stringify({
    band: d.band,
    centre: d.centre,
    icon: d.icon,
    scheme: d.scheme,
    serial: d.serial,
    v: 1,
  });
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canon));
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
    .slice(0, 16);
}
