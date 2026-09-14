import type { GoldenGrainPillCopy } from '@chirpcoop/real-chicken-ui/wallet-pill';

import type { ShellCopy } from './types.js';

// Hungarian copy; the display strings are the only non-English text in the
// editor, mirroring the apps/web/i18n *-hu.ts catalogs.
export const hu = {
  shell: { appTitle: 'Tyutyu', appSubtitle: 'A tyúkod, a kupakod' } satisfies ShellCopy,
  wallet: { label: 'Aranymag', ariaTemplate: '{amount} aranymag' } satisfies GoldenGrainPillCopy,
};
