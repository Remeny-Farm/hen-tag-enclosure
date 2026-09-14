import type { GoldenGrainPillCopy } from '@chirpcoop/real-chicken-ui/wallet-pill';

import type { CapEditorCopy } from '../cap-editor/types.js';
import type { ShellCopy } from './types.js';

// English copy. In chirp these keys join the apps/web/i18n catalogs and the
// page passes the full RealChickenCopy from useLocale(); the prototype only
// needs the two shell fields the shell actually renders.
export const en = {
  shell: { appTitle: 'Tyutyu', appSubtitle: 'Your hen, your cap' } satisfies ShellCopy,
  wallet: { label: 'Golden Grain', ariaTemplate: '{amount} Golden Grain' } satisfies GoldenGrainPillCopy,
  capEditor: {
    title: 'Cap design',
    schemeLabel: 'Colour scheme',
    centreLabel: 'Centre',
    bandLabel: 'Top band',
    coloursLabel: 'Colours',
    limited: 'limited',
    totalTemplate: 'Total {amount}',
    colourRoles: { base: 'Base colour', a: 'Colour A', b: 'Colour B', clear: 'Clear' },
    noneOption: 'None',
    free: 'Free',
    lock: 'Lock design',
    lockTitle: 'Lock this design?',
    lockBody: 'The cap is printed exactly like the preview, with the colours you assigned. Editing again later costs Golden Grain, and once it is in a print batch only a replacement can change it.',
    lockConfirm: 'Lock and pay',
    cancel: 'Cancel',
    editAgainTemplate: 'Edit again ({amount})',
    requestReplacementTemplate: 'Request a replacement ({amount})',
    confirmAgain: 'Tap again to confirm',
    previewTitleTemplate: 'Cap {serial}',
    proofAlt: 'Print proof of the cap',
    status: {
      draft: 'Draft',
      locked: 'Locked, waiting for the print batch',
      batched: 'In the print batch',
      printed: 'Printed',
      installed: 'On the hen',
      replaced: 'Replaced',
    },
    errors: {
      INSUFFICIENT_GRAIN: 'Not enough Golden Grain.',
      DESIGN_BATCHED: 'This cap is already in a print batch.',
      CATALOG_MISMATCH: 'That combination is not available.',
      NOT_EDITABLE: 'This cap cannot be changed right now.',
    },
  } satisfies CapEditorCopy,
};
