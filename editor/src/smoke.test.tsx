import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RealChickenShell } from '@chirpcoop/real-chicken-ui/components';
import { GoldenGrainPill } from '@chirpcoop/real-chicken-ui/wallet-pill';

import { asShellCopy } from './copy/types.js';
import { en } from './copy/en.js';

test('chirp shell and wallet pill render through the alias', () => {
  render(
    <RealChickenShell copy={asShellCopy(en.shell)} showHero={false}>
      <GoldenGrainPill balance={1234n} copy={en.wallet} locale="en-US" />
    </RealChickenShell>,
  );
  expect(screen.getByLabelText('1,234 Golden Grain')).toBeInTheDocument();
});
