import { designHash } from './design-hash.js';
import {
  lockPrice,
  validateDraft,
  type CapDesign,
  type CapDesignClient,
  type CapDraft,
  type Catalog,
  type ClientError,
  type ClientErrorCode,
  type WalletView,
} from './types.js';

const err = (code: ClientErrorCode): ClientError => ({ code });

export type MockClient = CapDesignClient & {
  // Test and demo access to the store; never part of the CapDesignClient seam.
  state(): { hens: CapDesign[]; balance: bigint };
};

// In-memory CapDesignClient with the full state machine and a Golden Grain
// wallet, so the editor can be exercised in a browser and in tests without
// the chirp backend. Every rule here is a requirement for the real endpoints
// (spec §8): server-priced (scheme + icon + centre + band), validated
// against the catalog including the zone colour rules, fees from it.
export function createMockClient(seed: { hens: CapDesign[]; balance: bigint; catalog: Catalog }): MockClient {
  const hens = seed.hens.map((h) => ({ ...h, colours: { ...h.colours } }));
  let balance = seed.balance;
  const cat = seed.catalog;

  const find = (henId: string): CapDesign => {
    const h = hens.find((x) => x.henId === henId);
    if (!h) throw err('NOT_EDITABLE');
    return h;
  };
  const charge = (amount: bigint): void => {
    if (balance < amount) throw err('INSUFFICIENT_GRAIN');
    balance -= amount;
  };
  const toDraft = (h: CapDesign): CapDraft => ({ scheme: h.scheme, icon: h.icon, centre: h.centre, band: h.band, colours: h.colours });

  return {
    async load(henId) {
      const h = find(henId);
      return { ...h, colours: { ...h.colours } };
    },
    async save(henId, draft) {
      const h = find(henId);
      if (h.status !== 'draft') throw err('NOT_EDITABLE');
      if (validateDraft(cat, draft).length > 0) throw err('CATALOG_MISMATCH');
      Object.assign(h, draft, { colours: { ...draft.colours }, designHash: await designHash({ ...draft, serial: h.serial }) });
      return { ...h, colours: { ...h.colours } };
    },
    async lock(henId) {
      const h = find(henId);
      if (h.status !== 'draft') throw err('NOT_EDITABLE');
      if (validateDraft(cat, toDraft(h)).length > 0) throw err('CATALOG_MISMATCH');
      charge(lockPrice(cat, h));
      Object.assign(h, { status: 'locked', designHash: await designHash(h) });
      return { ...h, colours: { ...h.colours } };
    },
    async unlockForEdit(henId) {
      const h = find(henId);
      if (h.status !== 'locked') throw err(h.status === 'draft' ? 'NOT_EDITABLE' : 'DESIGN_BATCHED');
      charge(BigInt(cat.fees.reedit_grain));
      h.status = 'draft';
      return { ...h, colours: { ...h.colours } };
    },
    async requestReplacement(henId) {
      const h = find(henId);
      if (h.status !== 'installed') throw err('NOT_EDITABLE');
      charge(BigInt(cat.fees.replacement_grain));
      h.status = 'draft';
      h.proofUrl = null;
      return { ...h, colours: { ...h.colours } };
    },
    async getWallet(): Promise<WalletView> {
      return { balance };
    },
    state() {
      return { hens, balance };
    },
  };
}
