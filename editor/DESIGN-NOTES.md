# Cap editor — design notes

The patron's cap editor is a short game, not a form. This note records the
decisions behind `src/cap-editor/`, how it behaves on a phone, and how it
lands in the Tyutyu mobile app and the web patron route.

## The one idea

**The cap is on stage the whole time.** Every tap gets a physical answer from
the hero: the cap settles with a small spring, a lock sweeps a shine across
it and throws gold sparks. The patron never has to imagine what a choice
does — the cap shows it before the server has answered (optimistic save,
stale answers dropped by sequence).

## Interaction model

Three numbered steps in a segmented control (a real `tablist`): the order is
real, not decoration — the palette decides which four filaments exist, so it
comes first.

1. **Palette** — three big cards (swatch, name, blurb, price). One decision,
   plenty of room, the price stated up front.
2. **Motif** — two rails, *Centre* and *Top band*, each split into the packs
   Basic (free) / Vibe (30) / Drop (80, limited). Rails scroll sideways with
   snap points, so 26 icons stay a thumb-flick away instead of a wall. The
   chosen motif's **colour chips sit directly above its rail**, with the
   blocked chip crossed out and a one-line reason — the colour is found
   where the motif is chosen, not three screens later.
3. **Colours** — one chip row per zone of the top plate (outer ring, number,
   inner disc, plus centre and band when present), four chips each: base,
   A, B, clear. Explanations under the rows: what the four colours are, why
   the ring around the middle stays clear (the tag's light), and the
   readability rule.

A **summary bar** is stuck to the bottom above the home indicator: what the
cap costs right now (live region), the wallet, *Next* on steps 1–2 and the
primary *Lock*. Locked / installed caps swap the primary action for the
two-tap *Edit again* / *Request a replacement* (armed confirm from the
package, no `window.confirm`).

**Rules stay invisible until they matter.** The catalog's colour rules
(number ≠ ring, centre ≠ disc, band ≠ ring) show up as one crossed chip per
row with the reason in its accessible name; when the patron changes the
ring, the number quietly steps to another colour and the bar says so.

**Locking is a sheet** on phones (slides up, grip handle, safe-area padding)
and a card on wide screens: itemised price, total, balance, and the plain
consequence ("you can edit again for a small fee until it is printed").

## Explanations

Short hints live in the copy (`hints.*`, `schemeBlurbs`, `packBlurbs`,
`autoFixTemplate`, `celebrate`) in both languages, Tyutyu tone: warm, no
jargon, one or two sentences. They sit exactly where the question arises.

## Native feel

- 44 px targets everywhere (`--rc-tap`); chips, tiles, cards and buttons
  scale to 0.97 on press; no hover-only affordances.
- Segmented control instead of a radio list; rails instead of grids;
  sheet instead of a centred modal on phones.
- Skeleton stage while the design loads; inline toasts in the bar for
  errors, auto-fix notes and the lock celebration (`role=status/alert`).
- Motion is transform/opacity only and stops under
  `prefers-reduced-motion`; durations come from the timing tokens.
- No `position: fixed` except the dialog overlay (there is no text input,
  so no iOS keyboard interaction). The stage and the bar use `sticky`.

## Accessibility

Tabs with arrow-key navigation and a single tab stop; radiogroups with
names for every picker and every colour row; focus rings on every control;
prices and limited tags are text, never colour alone; live regions for the
total, status and notes. Tested with accessible queries only.

## Mobile integration (packages/mobile-app)

- The editor becomes a patron screen, e.g.
  `packages/mobile-app/src/hen-profile/CapEditorScreen.tsx`, rendered inside
  the companion shell that already seeds the `--rc-*` vars. The screen wraps
  `CapEditor` and supplies the SDK-backed `CapDesignClient`, the hen from the
  route, `copy` from the app catalog and the locale.
- The bottom bar's `env(safe-area-inset-bottom)` works in the Capacitor
  WKWebView with `viewport-fit=cover` (already set by the app shell); the
  bar is `sticky`, so it lives inside the scrolling content and never fights
  the tab bar — mount the screen without the companion's own bottom tabs, or
  add their height to the bar's padding through a CSS variable.
- Rails use native horizontal scrolling with snap; no gesture library.
- Haptics: the app can wire `Haptics.impact({ style: 'light' })` on the
  `onChange` of the pickers (Capacitor Haptics); the prototype only does the
  visual press.

## Horizontal overflow: what bit us

Two separate causes made the document scroll sideways on the Motif step:

1. Grid tracks default to `auto`, so `.rc-cap-rails` and the rail group grew
   to their content. Every link of the chain now has `min-inline-size: 0`
   (`grid-template-columns: minmax(0, 1fr)` on the grid, `contain: inline-size`
   on the group) and only `.rc-cap-rail` has `overflow-x: auto`.
2. The visually hidden radio inputs are `position: absolute`; without a
   positioned ancestor their containing block is the page, so the off-screen
   inputs stretched the document even though the rail clipped its tiles.
   `.rc-cap-tile` and `.rc-cap-card` are `position: relative`.

`pnpm check:layout` (README, "Layout gate") guards both. Keyboard focus in a
rail aligns the tile to its snap start (`inline: 'start'`): with `nearest`
the proximity snap pulled the rail back and left the tile cut off.

## One shell change

`RealChickenShell` sets `overflow-x: hidden`, which makes the shell a scroll
container and silently defeats `position: sticky` inside it (the stage and
the summary bar would scroll away). The prototype overrides it on the page
(`src/demo.css`: `.rc-shell { overflow-x: clip }`); in chirp make the same
one-line change on `.rc-shell` or on the cap page's wrapper. `clip` keeps the
clipping without creating a scroll container and is supported by the
WKWebView the app runs in.

## Web route (apps/web/(patron))

`apps/web/app/(patron)/my-hen/cap/page.tsx` renders the same component
inside `RealChickenShell` with `showHero={false}` (the cap is the hero). On
≥ 48em the layout goes two-column with the stage sticky on the left; the
sheet becomes a centred card.

## What a reviewer should test

1. Phone (390 px): the stage stays visible while scrolling the rails; the
   bar never covers the last rail; the sheet respects the home indicator.
2. Change the ring colour to the number's colour: the number moves, the bar
   explains, the cap settles.
3. Pick an icon, then its clear chip: the icon turns to glass tinted by the
   base colour; the disc chip is crossed and its name carries the reason.
4. Lock with a Drop icon and a Vibe band: the sheet itemises scheme + icon
   + band, the wallet drops by the total, the cap shines and sparks, the bar
   says it is queued.
5. Keyboard only: Tab to the steps, arrows switch them, Space picks tiles,
   Escape closes the sheet.
6. `prefers-reduced-motion`: no settle, no sparks, sheet appears without a
   slide.
