# Hen cap editor — prototype

Browser-testable prototype of the patron-facing cap editor from
`../docs/superpowers/specs/2026-09-14-hen-cap-customisation-design.md` §7.
It is written to be dropped into the chirp repository unchanged, so it renders
with chirp's own `@chirpcoop/real-chicken-ui` components and
`@chirpcoop/design-tokens`, aliased **from the chirp checkout's source** — the
chirp repository is read, never written.

```sh
pnpm install
pnpm sync:data     # copies ../cad/catalog.json and ../cad/out/layout.json into src/cap-editor/data/
pnpm dev           # http://localhost:5173 with the in-memory mock client
pnpm test          # vitest + testing-library
pnpm typecheck
pnpm build
```

`CHIRP_DIR` overrides the chirp checkout location (default `../../chirp`);
`tsconfig.json`'s `paths` must be edited to match, tsc cannot read env.

## What it looks like

A three-step game — Palette → Motif → Colours — with the cap on stage and a
summary bar stuck to the bottom. Design decisions, the mobile integration
path and a reviewer checklist: [`DESIGN-NOTES.md`](DESIGN-NOTES.md).

## Rules the code already obeys

- Only `var(--rc-*)` and `@chirpcoop/design-tokens` values in TS/CSS; the
  only colour literals are the filament hexes in `data/catalog.json` (data).
- Deep imports only: `@chirpcoop/real-chicken-ui/components`, `/wallet-pill`,
  `/golden-grain`, `/theme-vars`, `/dialog-focus`, `/armed-confirm`,
  `/styles.css`. Never `/client` or `/index`: they pull `@chirpcoop/client-sdk`
  and recharts in. In chirp these become relative imports inside the package.
- React 19, TypeScript strict, vitest + testing-library, English-only source;
  Hungarian only inside `src/copy/hu.ts`.

## Integration map (executed only on instruction, in chirp)

| Prototype file | Lands in chirp as |
|---|---|
| `src/cap-editor/*.tsx`, `*.css`, `*.test.tsx` | `packages/real-chicken-ui/src/cap-editor/` |
| `src/copy/{hu,en}.ts` | keys in `apps/web/i18n/` catalogs |
| `src/cap-editor/types.ts` (`CapDesignClient`) + `mock-client.ts` | interface stays; SDK adapter in `apps/web/lib/`; mock stays for tests |
| `src/page.tsx` | `apps/web/app/(patron)/my-hen/cap/page.tsx` + client wrapper |
| `src/cap-editor/data/*.json` | data assets under `packages/real-chicken-ui/src/cap-editor/data/` |
