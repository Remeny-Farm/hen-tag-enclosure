import type catalogJson from './data/catalog.json';
import type layoutJson from './data/layout.json';

// The design state machine (spec §7.2). `replaced` is terminal.
export type CapStatus = 'draft' | 'locked' | 'batched' | 'printed' | 'installed' | 'replaced';

export type CapDesign = {
  henId: string;
  serial: number;
  scheme: string;
  icon: string | null;
  centre: string | null;
  band: string | null;
  status: CapStatus;
  designHash: string;
  proofUrl: string | null;
};

export type CapDraft = Pick<CapDesign, 'scheme' | 'icon' | 'centre' | 'band'>;

// Data assets generated in ../cad: catalog.json is the source of truth for
// what may be chosen, layout.json carries the generator's own sketches.
export type Catalog = typeof catalogJson;
export type Layout = typeof layoutJson;
export type SchemeId = Catalog['schemes'][number]['id'];

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
  noneOption: string;
  free: string;
  lock: string;
  lockTitle: string;
  lockBody: string;
  lockConfirm: string;
  cancel: string;
  // "{amount}" is replaced with the formatted Golden Grain fee.
  editAgainTemplate: string;
  requestReplacementTemplate: string;
  confirmAgain: string;
  // "{serial}" is replaced with the hen's serial number.
  previewTitleTemplate: string;
  proofAlt: string;
  status: Record<CapStatus, string>;
  errors: Record<ClientErrorCode, string>;
};

export function isClientError(e: unknown): e is ClientError {
  return typeof e === 'object' && e !== null && typeof (e as ClientError).code === 'string';
}
