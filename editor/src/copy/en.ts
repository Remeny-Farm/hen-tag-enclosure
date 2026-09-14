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
    steps: { palette: 'Palette', motif: 'Motif', colours: 'Colours' },
    stepsLabel: 'Design steps',
    hints: {
      palette: 'Pick the three filaments your cap is printed from. Everything else is yours to arrange.',
      motif: 'One symbol or pattern in the middle, one pattern on the top arc. The number is always on the cap.',
      packs: 'Basic is free. Vibe and Drop cost Golden Grain per item; Drop motifs are limited editions.',
      colours: 'Four colours on the cap: the base, colours A and B, and clear. Each zone can take any of them.',
      window: 'The ring around the middle stays clear so the tag\u2019s light shines through it.',
      numberRule: 'The number always keeps a different colour from the ring, so it stays readable. If you change one, the other steps aside.',
      lock: 'Locking sends your cap to the next print batch. You can edit again for a small fee until it is printed.',
      motifColour: 'Its colour is right here: tap a chip. The crossed one is the disc\u2019s own colour, which would hide it.',
      readOnly: 'This cap is on its way to the printer, so the design is frozen.',
    },
    schemeBlurbs: {
      pasture: 'Pistachio green with black and white. Calm, clear, at home in the grass.',
      bluedye: 'Deep ocean blue with white and chalk blue. Folk blue-dye, made for a hen.',
      gold: 'Galaxy black with gold and white. The one everyone notices at feeding time.',
    },
    packBlurbs: { basic: 'Free', vibe: 'Vibe pack', drop: 'Drop pack, limited' },
    perItemTemplate: '{amount} each',
    autoFixTemplate: 'The {zone} moved to another colour so it stays visible.',
    celebrate: 'Locked! Your cap is in the queue for the next print.',
    summaryLabel: 'Your cap',
    loading: 'Fetching your cap\u2026',
    continueLabel: 'Next',
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
