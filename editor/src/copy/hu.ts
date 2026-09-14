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
    steps: { palette: 'Paletta', motif: 'Motívum', colours: 'Színek' },
    stepsLabel: 'Tervezési lépések',
    hints: {
      palette: 'Válaszd ki a három filamentet, amiből a kupak készül. A többit te rendezed el.',
      motif: 'Egy szimbólum vagy minta középre, egy minta a felső ívre. A sorszám mindig rajta van.',
      packs: 'Az Alap ingyenes. A Vibe és a Drop tételenként aranymagba kerül; a Drop motívumok limitáltak.',
      colours: 'Négy szín van a kupakon: az alap, az A és a B szín, meg az átlátszó. Mindegyik zóna bármelyiket kaphatja.',
      window: 'A közép körüli gyűrű átlátszó marad, hogy a tag fénye átvilágítson rajta.',
      numberRule: 'A sorszám mindig más színű, mint a gyűrű, hogy olvasható maradjon. Ha az egyiket átállítod, a másik odébb lép.',
      lock: 'A rögzítéssel a kupak a következő nyomtatási kötegbe kerül. Amíg ki nem nyomtatják, kis díjért újra szerkesztheted.',
      motifColour: 'A színét itt állítod: koppints egy chipre. Az áthúzott a korong saját színe, abban eltűnne.',
      readOnly: 'Ez a kupak már úton van a nyomtató felé, a terv nem módosítható.',
    },
    schemeBlurbs: {
      pasture: 'Pisztáciazöld feketével és fehérrel. Nyugodt, tiszta, otthonos a fűben.',
      bluedye: 'Mély óceánkék fehérrel és krétakékkel. Kékfestő, tyúkra szabva.',
      gold: 'Galaxisfekete arannyal és fehérrel. Ezt mindenki észreveszi etetéskor.',
    },
    packBlurbs: { basic: 'Ingyenes', vibe: 'Vibe csomag', drop: 'Drop csomag, limitált' },
    perItemTemplate: '{amount} / darab',
    autoFixTemplate: 'A(z) {zone} másik színre lépett, hogy látható maradjon.',
    celebrate: 'Rögzítve! A kupakod sorban áll a következő nyomtatásra.',
    summaryLabel: 'A kupakod',
    loading: 'Hozzuk a kupakodat\u2026',
    continueLabel: 'Tovább',
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
