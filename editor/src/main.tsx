import { createRoot } from 'react-dom/client';
import '@chirpcoop/real-chicken-ui/styles.css';
import { RealChickenShell } from '@chirpcoop/real-chicken-ui/components';

import { asShellCopy } from './copy/types.js';
import { en } from './copy/en.js';

createRoot(document.getElementById('root')!).render(
  <RealChickenShell copy={asShellCopy(en.shell)}>
    <p className="rc-help-text">Cap editor scaffold</p>
  </RealChickenShell>,
);
