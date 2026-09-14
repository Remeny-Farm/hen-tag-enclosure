# Hen Cap Customisation — Design

- **Date**: 2026-09-14
- **Status**: in progress — the generator side (§6) and the editor prototype (§7) are built on branch `feat/cap-customisation`; the chirp side (§8) is not
- **Scope of this repository**: the generator changes, the batch CLI, the
  catalog manifest, the preview layout export, and a browser-testable
  prototype of the patron editor built with chirp's own UI library. The chirp
  side (tables, endpoints, admin pages) is specified here as requirements and
  is implemented in the chirp repository only on explicit instruction.

---

## 1. Purpose

Patrons of a real hen edit their hen's 3D-printed tag cap in the app: they
choose one of three preset colour schemes (some cost Golden Grain), an icon or
a centre pattern, and a top-band pattern. The hen's serial number is always on
the cap. They preview it live, then **lock** it. Staff batch the locked caps
of one colour scheme onto one printer plate — as many as fit — generate the
print file on the farm Mac with one command, print, and install. A patron can
re-edit a locked cap for a fee before it is batched, and later request a
physical replacement for a larger fee.

## 2. Decisions taken

| Question | Decision |
|---|---|
| Free text on the cap | **No.** Serial number plus icon/pattern only. The generator keeps `--top` for staff use; the patron editor never exposes it. |
| Where the CAD generator runs | **On the farm Mac, by CLI.** No server-side CAD, no CI job. |
| How a batch reaches the Mac | **Admin downloads a batch JSON; the CLI consumes it.** The CLI never talks to the API. |
| Preview | **Live SVG in the app**, drawn from a layout export of the generator. The authoritative CAD render (proof) is produced with the batch and uploaded by staff. |
| After lock | Patron may re-edit for Golden Grain while the design is not yet batched. After installation a replacement can be requested for a larger fee (someone has to catch the hen in the evening and swap the cap). |
| Pattern zones | Two independent choices: **centre** (icon *or* pattern inside the accent ring) and **top band** (none / stripes / dots / thin arc). |
| Editor | Built **here** as a drop-in component using `@chirpcoop/real-chicken-ui` and `@chirpcoop/design-tokens`, testable in a browser from this repo; merged into chirp only on instruction. Web patron surface first (`apps/web/(patron)`); the mobile runtime reuses the same component library, so it can adopt it later. |

## 3. Physical and printability constraints (facts the design is built on)

- The cap shell is always **clear PETG** so the LED reads through it. A colour
  scheme is therefore a pair: **text colour** (AMS slot 2, the number, icon,
  centre pattern) and **accent colour** (AMS slot 3, the core ring and the band
  pattern). Slot 1 is clear. A 4-slot AMS holds **one scheme per plate**.
- Plate: Bambu Lab P1S, 256 × 256 mm, front-left exclusion 18 × 28 mm.
  Grid **6 × 6 = 36 caps** at 36 mm pitch, origin (20, 8) mm — clear of the
  exclusion zone. Hex packing would reach ~42; not done in v1.
- Colour changes happen only in the first 4 layers (the 0.64 mm inlays), so
  a full plate costs the same number of filament changes as one cap.
  Estimated ~10 min per cap, a full plate is an overnight print.
  **Estimate; the plate is sliced by `slice_check.py` before the first print.**
- Serial numbers: 1–5 digits (`real_chickens.serial`), Verdana 6.0 pt on the
  bottom arc. Font is fixed; the patron does not choose it.
- Inlays: 0.64 mm deep, flush with the outer face, minimum printable feature
  0.58 mm (0.8 mm for patterns, with ≥ 0.8 mm gaps). Every inlay island is
  one connected solid.
- LED ring r 8.5–11.5 mm: the number already covers part of it; patterns must
  leave **≥ 60 %** of the ring's area clear (generator check). Centre patterns
  live inside r ≤ 8.6, band patterns in r 11.5–15.4 unless sparse.
- Icons and patterns are **parametric code**, not fonts or uploads. Adding
  one is a sketch function plus tests in this repository. A set of ~12 is the
  realistic v1 size.
- Determinism: identical inputs give byte-identical files. A locked design is
  fully described by its inputs plus the generator version.

## 4. Catalog

One catalog, two copies kept identical by a test:

- **chirp**: code constants (like the hen traits), shipped to the client and
  validated server-side at lock.
- **this repository**: `cad/catalog.json`, the source of truth for the
  generator; `test_cap_marking.py` fails when its keys differ from the
  generator's `ICONS` / `PATTERNS` tables.

```json
{
  "schema": "hen-cap-catalog/1",
  "generator_version": "<git sha>",
  "schemes": [
    {"id": "classic", "name": {"hu": "Klasszikus", "en": "Classic"},
     "text": {"filament": "Bambu PETG Basic Black", "hex": "#1a1a1a"},
     "accent": {"filament": "Bambu PETG Basic White", "hex": "#f2f2f2"},
     "price_grain": 0}
  ],
  "icons": [{"id": "heart", "name": {"hu": "Szív", "en": "Heart"}}],
  "centre_patterns": [{"id": "rings", "name": {"hu": "Körök", "en": "Rings"}}],
  "band_patterns": [{"id": "stripes", "name": {"hu": "Csíkok", "en": "Stripes"}}],
  "fees": {"reedit_grain": 50, "replacement_grain": 500}
}
```

The three schemes, their filaments and prices are **open** (§12); the shape
above is fixed. Hex values are physical filament colours used by the preview
and the proof; in chirp they live in a data asset, not in TS/CSS, so the
raw-design-value hook does not apply.

## 5. The batch contract (the only interface between the two sides)

`hen-cap-batch/1`, produced by the admin UI, consumed by `cap_batch.py`:

```json
{
  "schema": "hen-cap-batch/1",
  "batch_id": "2026-09-14-classic-01",
  "scheme": "classic",
  "generator_version": "71abeb5",
  "created_at": "2026-09-14T18:00:00Z",
  "caps": [
    {"serial": 67, "icon": "heart", "centre": null, "band": "stripes",
     "design_hash": "3f9c2a7b1e5d4c08", "hen_name": "Bözsi"}
  ]
}
```

- `icon` and `centre` are mutually exclusive; both `null` means a plain
  accent disc. `band` may be `null`.
- `design_hash` = first 16 hex chars of SHA-256 over the canonical JSON
  `{"band":"stripes","centre":null,"icon":"heart","scheme":"classic","serial":67,"v":1}`
  (sorted keys, no whitespace). It covers the design only, not the
  generator version, so a generator release does not invalidate locked
  designs. Both sides compute it; the CLI refuses a cap whose hash does not
  match its fields.
- `generator_version` is the value the app took from the published
  `cad/catalog.json`; the CLI refuses a batch whose value differs from the
  catalog on the Mac, so a catalog change is always deployed to both sides
  before a batch crosses.
- Outputs, all named by the batch id and design hash so they can be matched
  back without a database:
  `plate_<batch_id>_P1S.3mf`, `plate_<batch_id>_manifest.csv`
  (position `1A`…`6F` = column number + row letter, serial, hen name, design
  hash), `proof/<design_hash>.svg`.
- The plate file does not carry the scheme's filament colours: Bambu Studio
  02.08 rejects a three-entry `filament_colour` on export (lab note
  2026-09-14). The AMS mapping 1 clear / 2 text / 3 accent is set on the
  printer from the catalog's filament names.

## 6. Generator side (this repository)

### 6.1 `cap_marking.py`
- `--centre <pattern>` (rings, solid, dots; exclusive with `--icon`) and
  `--band <pattern>` (stripes, dots, arc). Patterns are sketch functions in a
  `PATTERNS` table beside `ICONS`; band patterns go into the **core body**
  (accent colour), centre patterns into the **marking body** (text colour).
- New machine checks: pattern feature ≥ 0.8 mm and gap ≥ 0.8 mm, LED-ring
  clearance ≥ 60 %, no inlay touches another inlay of a different colour.
- `--layout-json out/layout.json`: band and core radii, font sizes, arc
  centres, `GAP_ARC`, the dilated outlines of digits 0–9 at 6.0 pt as SVG
  path strings with advances (mm), and every icon/pattern as an SVG path.
  This is what the app's live preview draws from, so the preview and the
  print come from the same numbers and no system font is needed on any
  device.
- `--proof out/proof/<hash>.svg`: top view of the cap in the scheme's colours
  from the exact 2D sketches (clear disc outline, accent ring, marking,
  patterns).
- `--top` stays for staff; it is not in the batch contract.

### 6.2 `cap_batch.py` (new)
1. Read and validate the batch JSON (schema, `generator_version` equal to
   the local catalog's, catalog keys, unique serials, hashes).
   Any failure refuses the whole batch and lists every offending cap.
2. Build each cap's three bodies, cached under `out/cache/<design_hash>/`
   so a re-run or a re-print costs nothing.
3. Place caps on the 6 × 6 grid in list order (row-major, deterministic).
4. Write the Bambu project with a **pure-Python writer** modelled on the
   CLI-exported projects in `out/` (`3D/3dmodel.model`, per-object meshes,
   `Metadata/model_settings.config` with part extruders 1/2/3 and plate
   positions, `Metadata/project_settings.config` with the P1S machine,
   0.16 mm process, PETG Basic and the three settings from `DESIGN.md`:
   3 walls, Arachne, avoid crossing walls). No dependency on the Bambu
   Studio CLI, so the writer also runs where the app is not installed.
5. Write the manifest and the proofs.
6. Run `slice_check.py` on the plate when Bambu Studio is present (open-air
   travel limit scaled by cap count, cantilever 0 on the shared plate check,
   slicer warnings) and print the slicer's time and filament estimates.

### 6.3 `slice_check.py`
Accepts a plate 3MF as input in addition to the four printables.

## 7. Patron editor (prototype built here, drop-in for chirp)

### 7.1 Component architecture (`editor/src/`)
- `CapEditor` — the page body: scheme picker, decor pickers, preview, price
  line, primary action. Props: `{ design, catalog, layout, wallet, copy,
  client }`. No data fetching inside; the page wrapper supplies a client.
- `CapPreview` — pure SVG from `layout.json` + design: clear disc, accent
  ring in the scheme's accent colour, digits placed along the bottom arc from
  the exported glyph paths and advances (same algorithm as the generator:
  centred on 270°, per-glyph advance), icon/centre pattern in text colour,
  band pattern in accent colour. Deterministic (INV-7 spirit).
- `SchemePicker`, `DecorPicker` — segmented option groups with 44 px tap
  targets, price badges via `GoldenGrainGlyph`, locked/paid affordances.
- `LockDialog` — confirmation with the price, the wallet balance
  (`GoldenGrainPill`), and the consequence text ("editing later costs X").
- `CapDesignClient` interface: `load(serial)`, `save(draft)`, `lock()`,
  `unlockForEdit()`, `requestReplacement()`, `getWallet()`. The prototype
  ships an in-memory mock with the full state machine and a fake wallet;
  chirp later supplies the SDK adapter.
- Copy: a `CapEditorCopy` object passed in (HU and EN provided), following
  the `RealChickenCopy` pattern; no string literals in the component.

### 7.2 Design states shown by the editor
`draft → locked → batched → printed → installed → replaced`
- draft: editable; primary action **Lock** (shows the scheme price if paid).
- locked: read-only preview; **Edit again** for the re-edit fee.
- batched / printed: read-only, "waiting for print / being printed"; the
  proof image appears once staff upload it.
- installed: proof, **Request replacement** for the replacement fee, which
  opens a new draft; the old design becomes `replaced` when the new one is
  installed.

### 7.3 Style and tooling rules the prototype already obeys
- Only `@chirpcoop/real-chicken-ui` components and `var(--rc-*)` /
  `@chirpcoop/design-tokens` values; no raw hex, px, rem in TS or CSS
  (the cap's filament colours come from the catalog data asset).
- Plain CSS file beside the component, `.rc-cap-*` class prefix, React 19,
  TypeScript strict, vitest + testing-library tests, English-only source.
- Harness: `editor/` is a Vite app whose `vite.config.ts` aliases
  `@chirpcoop/real-chicken-ui` and `@chirpcoop/design-tokens` to the chirp
  checkout's `src` (path from `CHIRP_DIR`, default `../chirp`), and imports
  `dist/tokens.css` and the package CSS. chirp is read, never written.
  `pnpm dev` serves the editor with the mock client; `pnpm test` runs the
  component tests. A single-file build can be published as an artifact for
  review on another device.

### 7.4 Integration map (executed only on instruction, in chirp)
| Prototype file | Lands in chirp as |
|---|---|
| `editor/src/cap-editor/*.tsx`, `*.css`, `*.test.tsx` | `packages/real-chicken-ui/src/cap-editor/` |
| `editor/src/copy/{hu,en}.ts` | keys in `apps/web/i18n/` catalogs |
| `editor/src/client.ts` (interface) + mock | interface stays; SDK adapter in `apps/web/lib/` |
| `editor/src/page.tsx` | `apps/web/app/(patron)/my-hen/cap/page.tsx` + client wrapper |
| `cad/catalog.json`, `cad/out/layout.json` | data assets under `packages/real-chicken-ui/src/cap-editor/data/` |

## 8. Requirements for the chirp side (for a chirp ADR)

- **Tables**: `hen_cap_designs` (chicken_id, serial snapshot, scheme, icon,
  centre, band, design_hash, status, locked_at, batch_id, proof_url,
  grain ledger refs, patronage interval ref); `hen_cap_batches` (scheme,
  generator_version, cap list, json_downloaded_at, printed_at,
  installed_at). At most one design per hen that is not `installed` or
  `replaced`. Patronage change → the open design is abandoned, a new draft
  starts; installed designs stay as history.
- **Endpoints** (server-authoritative, Zod in `shared-types`): get/save
  draft, lock (quote → atomic spend for a paid scheme, idempotent), unlock
  for edit (fee, only while `locked`), request replacement (fee, only while
  `installed`), get catalog; admin: list locked by scheme, create batch
  (≤ 36, FIFO by `locked_at`, sets `batched`), download batch JSON, upload
  proofs (file name = design hash), mark printed / installed.
- **Validation at lock**: scheme/icon/centre/band exist in the catalog,
  icon and centre exclusive, serial equals the hen's, design_hash recomputed
  server-side.
- **Admin UI**: scheme tabs, cap counts, "Create batch", "Download JSON",
  proof upload (folder), printed/installed buttons, replacement queue.
- **Invariants**: currency as `bigint`; no raw design values; English-only
  source; every state transition audited in the wallet ledger where it
  charges.

## 9. Error handling

- CLI: refuses a batch on schema/version/catalog/hash/duplicate errors with
  a complete list; partial plates (< 36) are normal; a cap whose CAD checks
  fail (should not happen for catalog inputs) stops the batch and names the
  cap.
- Editor: server errors map to copy keys by `code` (insufficient grain,
  design already batched, catalog mismatch); the preview never blocks on the
  network; lock is disabled until the draft is saved.
- Staff: a proof file whose name matches no design in the batch is rejected
  on upload.

## 10. Testing

- This repository: pattern printability and LED-clearance checks; catalog
  parity; `cap_batch.py` on a 3-cap fixture (byte-identical plate on two
  runs, manifest and proofs present, refusal cases); `slice_check.py` on a
  full 36-cap plate; editor component tests (state transitions, price and
  balance display, lock confirmation, preview determinism for a fixed
  design), plus a manual browser pass.
- chirp (later): endpoint tests for the state machine and idempotent grain
  spend; admin batch creation limits.

## 11. Out of scope for v1

Free text, custom uploads, per-icon pricing, hex packing, mobile runtime
screens, automatic proof upload from the CLI, server-side CAD.

## 12. Open questions

1. The three schemes: filament pairs and Golden Grain prices.
2. Re-edit fee and replacement fee.
3. Whether the band pattern should be offered in the text colour as well as
   the accent colour (v1: accent only).
4. Whether staff upload proofs from the admin UI or the CLI gets an optional
   upload later.
