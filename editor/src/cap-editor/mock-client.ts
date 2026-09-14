import { designHash } from './design-hash.js';
import type { CapDesign, CapDesignClient, CapDraft, Catalog, ClientError, ClientErrorCode, WalletView } from './types.js';

const err = (code: ClientErrorCode): ClientError => ({ code });

export type MockClient = CapDesignClient & {
  // Test and demo access to the store; never part of the CapDesignClient seam.
  state(): { hens: CapDesign[]; balance: bigint };
};

// In-memory CapDesignClient with the full state machine and a Golden Grain
// wallet, so the editor can be exercised in a browser and in tests without
// the chirp backend. Every rule here is a requirement for the real endpoints
// (spec §8): server-priced, validated against the catalog, fees from it.
export function createMockClient(seed: { hens: CapDesign[]; balance: bigint; catalog: Catalog }): MockClient {
  const hens = seed.hens.map((h) => ({ ...h }));
  let balance = seed.balance;
  const cat = seed.catalog;

  const find = (henId: string): CapDesign => {
    const h = hens.find((x) => x.henId === henId);
    if (!h) throw err('NOT_EDITABLE');
    return h;
  };
  const price = (scheme: string): bigint => BigInt(cat.schemes.find((s) => s.id === scheme)?.price_grain ?? 0);
  const charge = (amount: bigint): void => {
    if (balance < amount) throw err('INSUFFICIENT_GRAIN');
    balance -= amount;
  };
  const valid = (d: CapDraft): boolean =>
    cat.schemes.some((s) => s.id === d.scheme)
    && (d.icon === null || cat.icons.some((i) => i.id === d.icon))
    && (d.centre === null || cat.centre_patterns.some((p) => p.id === d.centre))
    && (d.band === null || cat.band_patterns.some((p) => p.id === d.band))
    && !(d.icon !== null && d.centre !== null);

  return {
    async load(henId) {
      return { ...find(henId) };
    },
    async save(henId, draft) {
      const h = find(henId);
      if (h.status !== 'draft') throw err('NOT_EDITABLE');
      if (!valid(draft)) throw err('CATALOG_MISMATCH');
      Object.assign(h, draft, { designHash: await designHash({ ...draft, serial: h.serial }) });
      return { ...h };
    },
    async lock(henId) {
      const h = find(henId);
      if (h.status !== 'draft') throw err('NOT_EDITABLE');
      if (!valid(h)) throw err('CATALOG_MISMATCH');
      charge(price(h.scheme));
      Object.assign(h, { status: 'locked', designHash: await designHash(h) });
      return { ...h };
    },
    async unlockForEdit(henId) {
      const h = find(henId);
      if (h.status !== 'locked') throw err(h.status === 'draft' ? 'NOT_EDITABLE' : 'DESIGN_BATCHED');
      charge(BigInt(cat.fees.reedit_grain));
      h.status = 'draft';
      return { ...h };
    },
    async requestReplacement(henId) {
      const h = find(henId);
      if (h.status !== 'installed') throw err('NOT_EDITABLE');
      charge(BigInt(cat.fees.replacement_grain));
      h.status = 'draft';
      h.proofUrl = null;
      return { ...h };
    },
    async getWallet(): Promise<WalletView> {
      return { balance };
    },
    state() {
      return { hens, balance };
    },
  };
}
