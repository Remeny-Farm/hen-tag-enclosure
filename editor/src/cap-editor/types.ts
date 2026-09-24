import type catalogJson from './data/catalog.json';
import type layoutJson from './data/layout.json';

// The design state machine (spec §7.2). `replaced` is terminal.
export type CapStatus = 'draft' | 'locked' | 'batched' | 'printed' | 'installed' | 'replaced';

// A plate carries four filaments: the scheme's base (the shell), its two free
// colours a and b, and clear. The LED annulus is always clear; every other
// zone of the top plate may take any of the four.
export type ColourRole = 'base' | 'a' | 'b' | 'clear';
export type ZoneId = 'ring' | 'number' | 'disc' | 'centre' | 'band';
export const ZONES: readonly ZoneId[] = ['ring', 'number', 'disc', 'centre', 'band'];
export const COLOUR_ROLES: readonly ColourRole[] = ['base', 'a', 'b', 'clear'];
export type ZoneColours = Record<ZoneId, ColourRole>;

export type CapDesign = {
  henId: string;
  serial: number;
  scheme: string;
  icon: string | null;
  centre: string | null;
  band: string | null;
  colours: ZoneColours;
  status: CapStatus;
  designHash: string;
  proofUrl: string | null;
};

export type CapDraft = Pick<CapDesign, 'scheme' | 'icon' | 'centre' | 'band' | 'colours'>;

// Data assets generated in ../cad: catalog.json is the source of truth for
// what may be chosen, layout.json carries the generator's own sketches.
export type Catalog = typeof catalogJson;
export type Layout = typeof layoutJson;
export type CatalogEntry = { id: string; name: { hu: string; en: string }; pack?: string; price_grain: number; limited?: boolean };

export type WalletView = { balance: bigint };

export type ClientErrorCode = 'INSUFFICIENT_GRAIN' | 'DESIGN_BATCHED' | 'CATALOG_MISMATCH' | 'NOT_EDITABLE';
export type ClientError = { code: ClientErrorCode };

// The only seam between the editor and chirp: the prototype ships an
// in-memory implementation (mock-client.ts); chirp supplies an SDK adapter.
export interface CapDesignClient {
  load(henId: string): Promise<CapDesign>;
  save(henId: string, draft: CapDraft): Promise<CapDesign>;
  lock(henId: string): Promise<CapDesign>;
  unlockForEdit(henId: string): Promise<CapDesign>;
  requestReplacement(henId: string): Promise<CapDesign>;
  getWallet(): Promise<WalletView>;
}

export type CapEditorCopy = {
  title: string;
  schemeLabel: string;
  centreLabel: string;
  bandLabel: string;
  coloursLabel: string;
  noneOption: string;
  free: string;
  limited: string;
  totalTemplate: string; // "{amount}"
  lock: string;
  lockTitle: string;
  lockBody: string;
  lockConfirm: string;
  cancel: string;
  editAgainTemplate: string; // "{amount}"
  requestReplacementTemplate: string; // "{amount}"
  confirmAgain: string;
  previewTitleTemplate: string; // "{serial}"
  proofAlt: string;
  colourRoles: Record<ColourRole, string>;
  status: Record<CapStatus, string>;
  errors: Record<ClientErrorCode, string>;
  // --- UI-only copy for the guided flow (game feel, explanations) ---
  steps: { palette: string; motif: string; colours: string };
  stepsLabel: string;
  // Accessible names of the rail paging arrows.
  railPrev: string;
  railNext: string;
  hints: {
    palette: string;
    motif: string;
    packs: string;
    colours: string;
    window: string;
    numberRule: string;
    lock: string;
    readOnly: string;
    motifColour: string;
  };
  schemeBlurbs: Record<string, string>;
  packBlurbs: Record<string, string>;
  perItemTemplate: string; // "{amount}"
  autoFixTemplate: string; // "{zone}"
  celebrate: string;
  summaryLabel: string;
  loading: string;
  continueLabel: string;
};

export function isClientError(e: unknown): e is ClientError {
  return typeof e === 'object' && e !== null && typeof (e as ClientError).code === 'string';
}

export function defaultColours(catalog: Catalog): ZoneColours {
  const z = catalog.zones;
  return { ring: z.ring.default, number: z.number.default, disc: z.disc.default, centre: z.centre.default, band: z.band.default } as ZoneColours;
}

// The zone a zone's colour must differ from, or null (from the catalog).
export function pairedZone(catalog: Catalog, zone: ZoneId): ZoneId | null {
  const rule = (catalog.zones as Record<string, { must_differ_from?: string }>)[zone];
  return (rule.must_differ_from as ZoneId | undefined) ?? null;
}

export function findEntry(list: readonly CatalogEntry[], id: string | null): CatalogEntry | null {
  return id === null ? null : (list.find((e) => e.id === id) ?? null);
}

// Golden Grain charged at lock: scheme + icon + centre pattern + band.
export function lockPrice(catalog: Catalog, d: Pick<CapDesign, 'scheme' | 'icon' | 'centre' | 'band'>): bigint {
  const scheme = catalog.schemes.find((s) => s.id === d.scheme);
  let total = BigInt(scheme?.price_grain ?? 0);
  for (const e of [findEntry(catalog.icons, d.icon), findEntry(catalog.centre_patterns, d.centre), findEntry(catalog.band_patterns, d.band)]) {
    total += BigInt(e?.price_grain ?? 0);
  }
  return total;
}

// Every problem with a draft, as error codes (empty = valid). Mirrors
// cad/cap_design.py validate_design.
export function validateDraft(catalog: Catalog, d: CapDraft): string[] {
  const errs: string[] = [];
  if (!catalog.schemes.some((s) => s.id === d.scheme)) errs.push('scheme');
  if (d.icon !== null && !findEntry(catalog.icons, d.icon)) errs.push('icon');
  if (d.centre !== null && !findEntry(catalog.centre_patterns, d.centre)) errs.push('centre');
  if (d.band !== null && !findEntry(catalog.band_patterns, d.band)) errs.push('band');
  if (d.icon !== null && d.centre !== null) errs.push('icon+centre');
  for (const z of ZONES) {
    if (!COLOUR_ROLES.includes(d.colours[z])) errs.push(`colour:${z}`);
  }
  if (errs.length === 0) {
    for (const z of ZONES) {
      const other = pairedZone(catalog, z);
      if (other && d.colours[z] === d.colours[other]) errs.push(`same:${z}/${other}`);
    }
  }
  return errs;
}
