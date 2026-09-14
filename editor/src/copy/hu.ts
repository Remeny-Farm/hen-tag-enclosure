import type { GoldenGrainPillCopy } from '@chirpcoop/real-chicken-ui/wallet-pill';

import type { CapEditorCopy } from '../cap-editor/types.js';
import type { ShellCopy } from './types.js';

// Hungarian copy; the display strings are the only non-English text in the
// editor, mirroring the apps/web/i18n *-hu.ts catalogs.
export const hu = {
  shell: { appTitle: 'Tyutyu', appSubtitle: 'A tyúkod, a kupakod' } satisfies ShellCopy,
  wallet: { label: 'Aranymag', ariaTemplate: '{amount} aranymag' } satisfies GoldenGrainPillCopy,
  capEditor: {
    title: 'Kupakterv',
    schemeLabel: 'Színséma',
    centreLabel: 'Közép',
    bandLabel: 'Felső sáv',
    coloursLabel: 'Színek',
    limited: 'limitált',
    totalTemplate: 'Összesen {amount}',
    colourRoles: { base: 'Alapszín', a: 'A szín', b: 'B szín', clear: 'Átlátszó' },
    noneOption: 'Nincs',
    free: 'Ingyenes',
    lock: 'Rögzítés',
    lockTitle: 'Rögzíted ezt a tervet?',
    lockBody: 'A kupak pontosan az előnézet szerint készül, a választott színkiosztással. A későbbi újraszerkesztés aranymagba kerül, és ha már nyomtatási kötegben van, csak cserével módosítható.',
    lockConfirm: 'Rögzítés és fizetés',
    cancel: 'Mégse',
    editAgainTemplate: 'Újraszerkesztés ({amount})',
    requestReplacementTemplate: 'Csere kérése ({amount})',
    confirmAgain: 'Koppints újra a megerősítéshez',
    previewTitleTemplate: '{serial}. kupak',
    proofAlt: 'A kupak nyomtatási proofja',
    status: {
      draft: 'Piszkozat',
      locked: 'Rögzítve, nyomtatásra vár',
      batched: 'Nyomtatási kötegben',
      printed: 'Kinyomtatva',
      installed: 'A tyúkon',
      replaced: 'Lecserélve',
    },
    errors: {
      INSUFFICIENT_GRAIN: 'Nincs elég aranymag.',
      DESIGN_BATCHED: 'Ez a kupak már nyomtatási kötegben van.',
      CATALOG_MISMATCH: 'Ez a kombináció nem elérhető.',
      NOT_EDITABLE: 'Ez a kupak most nem módosítható.',
    },
  } satisfies CapEditorCopy,
};
