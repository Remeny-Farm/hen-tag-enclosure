import { useMemo, useState } from 'react';
import { RealChickenShell } from '@chirpcoop/real-chicken-ui/components';

import { CapEditor } from './cap-editor/cap-editor.js';
import catalog from './cap-editor/data/catalog.json';
import layout from './cap-editor/data/layout.json';
import { createMockClient } from './cap-editor/mock-client.js';
import type { CapDesign } from './cap-editor/types.js';
import { en } from './copy/en.js';
import { hu } from './copy/hu.js';
import { asShellCopy } from './copy/types.js';

// Demo harness only: three hens in different states, one shared wallet, a
// locale toggle. In chirp the (patron) page supplies the SDK client, the
// hen from the route and the copy from useLocale().
const HENS: CapDesign[] = [
  { henId: 'h67', serial: 67, scheme: 'classic', icon: 'heart', centre: null, band: null, status: 'draft', designHash: '', proofUrl: null },
  { henId: 'h8', serial: 8, scheme: 'meadow', icon: null, centre: 'rings', band: 'dots', status: 'locked', designHash: '0371884d05cc4f6b', proofUrl: null },
  { henId: 'h12345', serial: 12345, scheme: 'sunset', icon: 'star', centre: null, band: 'stripes', status: 'installed', designHash: '', proofUrl: '/proof-sample.svg' },
];

export function Page() {
  const [lang, setLang] = useState<'hu' | 'en'>('hu');
  const [henId, setHenId] = useState(HENS[0].henId);
  const client = useMemo(() => createMockClient({ hens: HENS, balance: 1000n, catalog }), []);
  const copy = lang === 'hu' ? hu : en;
  const locale = lang === 'hu' ? 'hu-HU' : 'en-US';
  return (
    <RealChickenShell copy={asShellCopy(copy.shell)}>
      <div className="rc-cap-demo-bar">
        <div className="rc-cap-demo-bar__group" role="group" aria-label="hen">
          {HENS.map((h) => (
            <button
              key={h.henId}
              type="button"
              className="rc-cap-btn rc-cap-btn--ghost"
              aria-pressed={h.henId === henId}
              onClick={() => setHenId(h.henId)}
            >
              #{h.serial}
            </button>
          ))}
        </div>
        <div className="rc-cap-demo-bar__group" role="group" aria-label="language">
          {(['hu', 'en'] as const).map((l) => (
            <button key={l} type="button" className="rc-cap-btn rc-cap-btn--ghost" aria-pressed={l === lang} onClick={() => setLang(l)}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
      <CapEditor henId={henId} client={client} catalog={catalog} layout={layout} copy={copy.capEditor} walletCopy={copy.wallet} locale={locale} />
    </RealChickenShell>
  );
}
