// Layout gate for the cap editor. Vitest/jsdom cannot see geometry, so this
// runs a real Chromium against a running dev server and fails when:
//   - the document scrolls sideways on any step at 360 / 390 / 1200 px
//     (the rail must scroll, never the page),
//   - a rail does not scroll with a horizontal wheel/swipe when it overflows,
//   - a chip or tile is smaller than the 44 px touch target.
//
// Usage (see README "Layout gate"):
//   pnpm dev                       # in another terminal
//   NODE_PATH=<dir with playwright/node_modules> pnpm check:layout
// Playwright is not a devDependency here on purpose (browser download); point
// NODE_PATH at any install that has `playwright`, or run `pnpm exec playwright`
// from such a directory. Override the target with EDITOR_URL.
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const URL = process.env.EDITOR_URL ?? 'http://localhost:5173/';
const VIEWPORTS = [
  [360, 780],
  [390, 844],
  [1200, 900],
];
const STEPS = ['palette', 'motif', 'colours'];
const MIN_TAP = 44;

const failures = [];
const browser = await chromium.launch();

for (const [width, height] of VIEWPORTS) {
  const page = await browser.newPage({ viewport: { width, height } });
  page.on('pageerror', (e) => failures.push(`${width}px: page error ${e.message}`));
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForSelector('.rc-cap-editor[data-editable]');
  const tabs = page.getByRole('tab');

  for (let i = 0; i < STEPS.length; i += 1) {
    await tabs.nth(i).click();
    await page.waitForTimeout(120);

    const overflow = await page.evaluate(() => {
      const doc = document.documentElement;
      return { scrollWidth: doc.scrollWidth, clientWidth: doc.clientWidth };
    });
    if (overflow.scrollWidth > overflow.clientWidth) {
      failures.push(`${width}px / ${STEPS[i]}: document scrolls sideways (${overflow.scrollWidth} > ${overflow.clientWidth})`);
    }

    const small = await page.evaluate((min) => {
      const out = [];
      for (const el of document.querySelectorAll('.rc-cap-chip, .rc-cap-tile, .rc-cap-seg__item, .rc-cap-card')) {
        const r = el.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) continue; // hidden panel
        if (r.width < min || r.height < min) {
          out.push(`${el.className.split(' ')[0]} ${Math.round(r.width)}x${Math.round(r.height)}`);
        }
      }
      return out;
    }, MIN_TAP);
    for (const s of small) failures.push(`${width}px / ${STEPS[i]}: touch target under ${MIN_TAP}px: ${s}`);

    if (STEPS[i] === 'motif') {
      // The rail must be the element that scrolls: wheel over the first
      // overflowing rail and expect its scrollLeft to move while the page stays.
      const rail = page.locator('.rc-cap-rail').filter({ has: page.locator('.rc-cap-tile:nth-child(6)') }).first();
      if ((await rail.count()) > 0) {
        await rail.scrollIntoViewIfNeeded();
        await page.waitForTimeout(100);
        const box = await rail.boundingBox();
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await page.mouse.wheel(120, 0);
        await page.waitForTimeout(200);
        const moved = await rail.evaluate((el) => ({ rail: el.scrollLeft, page: window.scrollX }));
        if (moved.rail <= 0) failures.push(`${width}px / motif: rail did not scroll on a horizontal wheel`);
        if (moved.page !== 0) failures.push(`${width}px / motif: the page scrolled sideways (${moved.page}px)`);
      }

      // Keyboard: ArrowRight on the checked icon moves focus to the next tile
      // inside the rail without moving the page.
      const checked = page.locator('.rc-cap-tile[data-checked] input').first();
      await checked.scrollIntoViewIfNeeded();
      await checked.focus();
      await page.keyboard.press('ArrowRight');
      await page.waitForTimeout(150);
      const kb = await page.evaluate(() => {
        const tile = document.activeElement?.closest('.rc-cap-tile');
        const rail = tile?.closest('.rc-cap-rail');
        if (!tile || !rail) return { ok: false };
        const t = tile.getBoundingClientRect();
        const r = rail.getBoundingClientRect();
        return { ok: t.left >= r.left - 1 && t.right <= r.right + 1, page: window.scrollX };
      });
      if (!kb.ok) failures.push(`${width}px / motif: arrow-focused tile is not fully visible inside its rail`);
      if (kb.page) failures.push(`${width}px / motif: arrow navigation scrolled the page sideways`);
    }
  }
  await page.close();
}

await browser.close();

if (failures.length) {
  console.error(`layout gate: ${failures.length} failure(s)`);
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}
console.log(`layout gate: ok (${VIEWPORTS.map(([w]) => `${w}px`).join(', ')} × ${STEPS.join('/')})`);
