import type { GoldenGrainPillCopy } from '@chirpcoop/real-chicken-ui/wallet-pill';

import type { ShellCopy } from './types.js';

// English copy. In chirp these keys join the apps/web/i18n catalogs and the
// page passes the full RealChickenCopy from useLocale(); the prototype only
// needs the two shell fields the shell actually renders.
export const en = {
  shell: { appTitle: 'Tyutyu', appSubtitle: 'Your hen, your cap' } satisfies ShellCopy,
  wallet: { label: 'Golden Grain', ariaTemplate: '{amount} Golden Grain' } satisfies GoldenGrainPillCopy,
};
