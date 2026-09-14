# Hen Cap Customisation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Patrons design their hen's cap (scheme, icon or centre pattern, band pattern) in a drop-in React editor; staff batch one scheme's locked caps onto a 6 × 6 P1S plate with one CLI command.

**Architecture:** Part A extends the deterministic Python generator (`cad/`): a catalog manifest, pattern sketches, a layout/proof SVG export, a pure-Python Bambu project writer and a batch CLI driven by a JSON contract. Part B is a Vite + React 19 prototype (`editor/`) that consumes chirp's own UI package and design tokens from the chirp checkout by path alias, ships an in-memory client with the full design state machine, and is written so its files move into `packages/real-chicken-ui/src/cap-editor/` unchanged.

**Tech Stack:** Python 3.12 + build123d via `uv run`; Bambu Studio CLI (optional, for checks); TypeScript strict, React 19, Vite, vitest + @testing-library; pnpm.

**Spec:** `docs/superpowers/specs/2026-09-14-hen-cap-customisation-design.md`

## Global Constraints

- English only in code, comments, commit messages, docs; HU strings only inside copy catalogs (`editor/src/copy/hu.ts`) and the catalog's `name.hu` fields.
- Python: `# /// script` PEP 723 header with `dependencies = ["build123d"]`; run every script as `uv run --python 3.12 <script>`; wrap builds/tests in `dev-budget run --kind heavy -- ...`.
- Determinism: identical inputs → byte-identical files (canonical meshes, fixed zip timestamps `(2026, 1, 1, 0, 0, 0)`, deterministic UUIDs).
- Physical: inlay depth 0.64 mm; pattern feature ≥ 0.8 mm and gap ≥ 0.8 mm; LED ring r 8.5–11.5 ≥ 60 % clear; centre patterns r ≤ 7.4; band patterns r 12.0–15.0 inside the fixed window −10°…190°; number centred at 270°, Verdana 6.0 pt, uniform digit advance 3.814 mm.
- Plate: 6 × 6, pitch 36 mm, centres `38 + 36·i` on both axes, ≤ 36 caps, one scheme per plate; AMS 1 = clear, 2 = text, 3 = accent; project settings `wall_loops=3`, `wall_generator=arachne`, `reduce_crossing_wall=1`.
- Design hash: first 16 hex chars of SHA-256 over `json.dumps({"band","centre","icon","scheme","serial","v":1}, sort_keys=True, separators=(",",":"))`. Test vector: serial 67, classic, heart, band stripes → `05dcdb796b921b25`; serial 8, meadow, centre rings → `0371884d05cc4f6b`; serial 12345, classic, star, band dots → `8fc7c9f4fcdb32c0`.
- Editor: no raw hex/px/rem/em in `.ts/.tsx/.css` (only `var(--rc-*)`); the only colour literals live in `cad/catalog.json` (data). React 19, `jsx: react-jsx`, tests with vitest + testing-library. chirp checkout is read only; never write under `CHIRP_DIR`.
- Import rule for chirp modules in the editor: deep paths only (`@chirpcoop/real-chicken-ui/components`, `/wallet-pill`, `/golden-grain`, `/theme-vars`, `/dialog-focus`, `/styles.css`, `@chirpcoop/design-tokens`), never `/client` or `/index` (they drag `@chirpcoop/client-sdk` and recharts in). In chirp these become relative imports.

---

## File structure

**Part A (`cad/`)**
- `catalog.json` — schemes, icons, centre/band patterns, fees, `generator_version` (new).
- `cap_design.py` — catalog loader, `design_hash`, `validate_design` (new, no build123d import).
- `cap_marking.py` — add `PATTERNS_CENTRE`, `PATTERNS_BAND`, three new icons, `--centre/--band`, pattern checks, `--layout-json`, `--proof`, `build(..., cap=None)` (modify).
- `cap_svg.py` — sketch → SVG path helpers, layout export, proof writer (new).
- `bambu_project.py` — pure-Python Bambu 3MF plate writer + `bambu/project_settings.json` template (new).
- `cap_batch.py` — batch JSON → cached bodies → plate → manifest → proofs → slice check (new).
- `fixtures/batch_sample.json` — 3-cap fixture (new).
- `test_cap_marking.py` — parity + pattern + layout tests (modify); `test_cap_batch.py` (new).
- `slice_check.py` — accept a plate 3MF argument (modify).

**Part B (`editor/`)**
- `package.json`, `vite.config.ts`, `tsconfig.json`, `test/setup-dom.ts`, `index.html`, `src/main.tsx` (scaffold).
- `src/cap-editor/types.ts` — `CapDesign`, `CapStatus`, `Catalog`, `Layout`, `CapDesignClient`, `CapEditorCopy`.
- `src/cap-editor/design-hash.ts` (+ test) — mirrors Python.
- `src/cap-editor/cap-preview.tsx` (+ test) — pure SVG.
- `src/cap-editor/mock-client.ts` (+ test) — state machine + wallet.
- `src/cap-editor/cap-editor.tsx`, `lock-dialog.tsx`, `pickers.tsx`, `cap-editor.css` (+ tests).
- `src/cap-editor/data/catalog.json`, `data/layout.json` — copied from `cad/` by `pnpm sync:data`.
- `src/copy/hu.ts`, `src/copy/en.ts`, `src/page.tsx` — demo page with mock hens and a locale toggle.

---

### Task 1: Catalog manifest, design hash, parity test

**Files:**
- Create: `cad/catalog.json`, `cad/cap_design.py`
- Modify: `cad/test_cap_marking.py` (append a section before the tidy-up loop)

**Interfaces:**
- Produces: `load_catalog(path=None) -> dict`; `design_hash(serial:int, scheme:str, icon:str|None, centre:str|None, band:str|None) -> str`; `validate_design(cat, d: dict) -> list[str]` (empty list = valid; `d` has keys serial, scheme, icon, centre, band); `CATALOG_PATH`.

- [ ] **Step 1: Write the catalog**

```json
{
  "schema": "hen-cap-catalog/1",
  "generator_version": "dev",
  "schemes": [
    {"id": "classic", "name": {"hu": "Klasszikus", "en": "Classic"},
     "text": {"filament": "Bambu PETG Basic Black", "hex": "#101010"},
     "accent": {"filament": "Bambu PETG Basic White", "hex": "#F4F4F0"},
     "price_grain": 0},
    {"id": "meadow", "name": {"hu": "Rét", "en": "Meadow"},
     "text": {"filament": "Bambu PETG Basic Blue", "hex": "#1F5FBF"},
     "accent": {"filament": "Bambu PETG Basic White", "hex": "#F4F4F0"},
     "price_grain": 150},
    {"id": "sunset", "name": {"hu": "Naplemente", "en": "Sunset"},
     "text": {"filament": "Bambu PETG Basic Red", "hex": "#C8102E"},
     "accent": {"filament": "Bambu PETG Basic Yellow", "hex": "#F3C43E"},
     "price_grain": 300}
  ],
  "icons": [
    {"id": "heart", "name": {"hu": "Szív", "en": "Heart"}},
    {"id": "star", "name": {"hu": "Csillag", "en": "Star"}},
    {"id": "flower", "name": {"hu": "Virág", "en": "Flower"}},
    {"id": "egg", "name": {"hu": "Tojás", "en": "Egg"}},
    {"id": "sun", "name": {"hu": "Nap", "en": "Sun"}},
    {"id": "moon", "name": {"hu": "Hold", "en": "Moon"}}
  ],
  "centre_patterns": [
    {"id": "rings", "name": {"hu": "Körök", "en": "Rings"}},
    {"id": "solid", "name": {"hu": "Tele", "en": "Solid"}},
    {"id": "dots", "name": {"hu": "Pöttyök", "en": "Dots"}}
  ],
  "band_patterns": [
    {"id": "stripes", "name": {"hu": "Csíkok", "en": "Stripes"}},
    {"id": "dots", "name": {"hu": "Pöttyök", "en": "Dots"}},
    {"id": "arc", "name": {"hu": "Ív", "en": "Arc"}}
  ],
  "fees": {"reedit_grain": 50, "replacement_grain": 500}
}
```

`generator_version` stays `"dev"` in git; the batch CLI compares it to the batch file. Prices and fees are placeholders (spec §12).

- [ ] **Step 2: Write `cad/cap_design.py`**

```python
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""Catalog and design identity shared by the generator, the batch CLI and the
tests. Deliberately free of build123d so it imports in milliseconds."""

import hashlib
import json
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "catalog.json"
HASH_VERSION = 1


def load_catalog(path: Path | None = None) -> dict:
    cat = json.loads((path or CATALOG_PATH).read_text())
    if cat.get("schema") != "hen-cap-catalog/1":
        raise SystemExit(f"unsupported catalog schema {cat.get('schema')!r}")
    return cat


def ids(cat: dict, key: str) -> list[str]:
    return [e["id"] for e in cat[key]]


def design_hash(serial: int, scheme: str, icon: str | None,
                centre: str | None, band: str | None) -> str:
    canon = json.dumps({"band": band, "centre": centre, "icon": icon,
                        "scheme": scheme, "serial": serial, "v": HASH_VERSION},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()[:16]


def validate_design(cat: dict, d: dict) -> list[str]:
    """Every problem with one design, as human-readable strings."""
    errs = []
    serial = d.get("serial")
    if not isinstance(serial, int) or isinstance(serial, bool) or not 1 <= serial <= 99999:
        errs.append("serial must be an integer 1..99999")
    if d.get("scheme") not in ids(cat, "schemes"):
        errs.append(f"unknown scheme {d.get('scheme')!r}")
    icon, centre, band = d.get("icon"), d.get("centre"), d.get("band")
    if icon is not None and icon not in ids(cat, "icons"):
        errs.append(f"unknown icon {icon!r}")
    if centre is not None and centre not in ids(cat, "centre_patterns"):
        errs.append(f"unknown centre pattern {centre!r}")
    if band is not None and band not in ids(cat, "band_patterns"):
        errs.append(f"unknown band pattern {band!r}")
    if icon is not None and centre is not None:
        errs.append("icon and centre pattern are mutually exclusive")
    if not errs and "design_hash" in d:
        want = design_hash(serial, d["scheme"], icon, centre, band)
        if d["design_hash"] != want:
            errs.append(f"design_hash {d['design_hash']} does not match fields ({want})")
    return errs
```

- [ ] **Step 3: Append the parity/hash test section to `test_cap_marking.py`** (before the `# Tidy the per-test artifacts` block)

```python
print("=== catalog parity and design hash ===")
sys.path.insert(0, str(HERE))
from cap_design import design_hash, load_catalog, validate_design  # noqa: E402
import cap_marking as cm  # noqa: E402
cat = load_catalog()
check(sorted(e["id"] for e in cat["icons"]) == sorted(k for k in cm.ICONS if k != "none"),
      "catalog icons == generator ICONS")
check(sorted(e["id"] for e in cat["centre_patterns"]) == sorted(cm.PATTERNS_CENTRE),
      "catalog centre patterns == PATTERNS_CENTRE")
check(sorted(e["id"] for e in cat["band_patterns"]) == sorted(cm.PATTERNS_BAND),
      "catalog band patterns == PATTERNS_BAND")
check(design_hash(67, "classic", "heart", None, "stripes") == "05dcdb796b921b25",
      "design_hash test vector 1")
check(design_hash(8, "meadow", None, "rings", None) == "0371884d05cc4f6b",
      "design_hash test vector 2")
check(validate_design(cat, {"serial": 67, "scheme": "classic", "icon": "heart",
                            "centre": "rings", "band": None})
      == ["icon and centre pattern are mutually exclusive"], "icon+centre rejected")
check(validate_design(cat, {"serial": 0, "scheme": "nope", "icon": None, "centre": None,
                            "band": None})[:2]
      == ["serial must be an integer 1..99999", "unknown scheme 'nope'"], "serial/scheme rejected")
```

Importing `cap_marking` at test time loads build123d (~2 s); acceptable.

- [ ] **Step 4: Run the suite; expect the two pattern-parity checks to FAIL** (`PATTERNS_CENTRE` does not exist yet) and the icon parity to FAIL (egg/sun/moon missing)

Run: `cd cad && dev-budget run --kind heavy -- uv run --python 3.12 test_cap_marking.py`
Expected: `AttributeError: module 'cap_marking' has no attribute 'PATTERNS_CENTRE'` (a crash, not a check) — that is the red state for Task 2.

- [ ] **Step 5: Commit**

```bash
git add cad/catalog.json cad/cap_design.py cad/test_cap_marking.py
git commit -m "feat(cad): catalog manifest, design hash, parity test"
```

---

### Task 2: Patterns, new icons and their checks in the generator

**Files:**
- Modify: `cad/cap_marking.py` (icons block ~line 270–301, `build_lettering`, `build`, `main` argparse + checks)
- Modify: `cad/test_cap_marking.py` (matrix + rejections)

**Interfaces:**
- Produces: `PATTERNS_CENTRE: dict[str, Callable[[], bd.Sketch]]`, `PATTERNS_BAND: dict[str, Callable[[], bd.Sketch]]`, `ICONS` gains `egg`, `sun`, `moon`; `BAND_WINDOW = (-10.0, 190.0)`; `build_lettering(number, top, icon, centre=None, band=None) -> (mk, ic, spans, stroke_raw, band_sk)`; `build(number, top, icon, depth, centre=None, band=None, cap=None) -> (cap, shell, inlay, core_body, mk, core, spans, stroke_raw, band_sk)`; CLI flags `--centre {rings,solid,dots}`, `--band {stripes,dots,arc}`.

- [ ] **Step 1: Add the icon and pattern sketches** (after `flower_sketch`)

```python
def egg_sketch(h: float = 12.0) -> bd.Sketch:
    """Egg: a circle stretched 1.3x along Y, tip up."""
    return bd.Sketch() + bd.Ellipse(h / 2 / 1.3, h / 2)


def sun_sketch(r: float = 6.9) -> bd.Sketch:
    """Disc plus eight 1.1 mm rays; rays overlap the disc so it is one face."""
    out = bd.Circle(r * 0.5)
    for k in range(8):
        a = 45 * k
        out = out + bd.Rot(0, 0, a) * bd.Pos(r * 0.62, 0) * bd.Rectangle(r * 0.76, 1.1)
    return out


def moon_sketch(r: float = 6.6) -> bd.Sketch:
    """Crescent: a disc minus an offset disc, horns to the left."""
    return bd.Circle(r) - bd.Pos(r * 0.45, 0) * bd.Circle(r * 0.82)


ICONS = {"heart": heart_sketch, "star": star_sketch, "flower": flower_sketch,
         "egg": egg_sketch, "sun": sun_sketch, "moon": moon_sketch, "none": None}

# --- patterns ---------------------------------------------------------------
# Centre patterns replace the icon inside the accent disc (text colour);
# band patterns sit in the lettering band above the number (accent colour).
# Every element >= 0.8 mm, every gap >= 0.8 mm: printable with a 0.4 nozzle.
CORE_PATTERN_R_MAX = 7.4     # keeps >= 1.2 mm of accent ring outside
BAND_PATTERN_R = (12.2, 14.8)
BAND_WINDOW = (-10.0, 190.0)  # deg; clear of a 5-digit number by 22 deg each side
PATTERN_FEATURE_MIN = 0.8
PATTERN_GAP_MIN = 0.8


def rings_sketch() -> bd.Sketch:
    out = bd.Sketch()
    for r_in in (1.6, 4.0, 6.4):
        out = out + (bd.Circle(r_in + 0.9) - bd.Circle(r_in))
    return out


def solid_sketch() -> bd.Sketch:
    return bd.Sketch() + bd.Circle(7.3)


def centre_dots_sketch() -> bd.Sketch:
    out = bd.Circle(1.0)
    for k in range(8):
        a = math.radians(45 * k)
        out = out + bd.Pos(5.2 * math.cos(a), 5.2 * math.sin(a)) * bd.Circle(0.9)
    return out


def _annular_sector(r_in: float, r_out: float, a0: float, a1: float) -> bd.Sketch:
    n = max(2, int((a1 - a0) / 5) + 1)
    pts = [(0.0, 0.0)] + [
        ((r_out + 2) * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
         (r_out + 2) * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
        for i in range(n + 1)]
    return (bd.Circle(r_out) - bd.Circle(r_in)) & bd.Polygon(*pts, align=None)


def stripes_sketch() -> bd.Sketch:
    r_in, r_out = BAND_PATTERN_R
    out = bd.Sketch()
    for a in range(-6, 187, 12):
        out = out + bd.Rot(0, 0, a) * bd.Pos((r_in + r_out) / 2, 0) * bd.Rectangle(r_out - r_in, 0.9)
    return out


def band_dots_sketch() -> bd.Sketch:
    out = bd.Sketch()
    for a in range(-5, 186, 10):
        out = out + bd.Pos(13.5 * math.cos(math.radians(a)), 13.5 * math.sin(math.radians(a))) * bd.Circle(0.6)
    return out


def arc_sketch() -> bd.Sketch:
    return _annular_sector(13.05, 13.95, BAND_WINDOW[0], BAND_WINDOW[1])


PATTERNS_CENTRE = {"rings": rings_sketch, "solid": solid_sketch, "dots": centre_dots_sketch}
PATTERNS_BAND = {"stripes": stripes_sketch, "dots": band_dots_sketch, "arc": arc_sketch}


def pattern_gap_ok(sk: bd.Sketch) -> bool:
    """Islands closer than PATTERN_GAP_MIN merge when each is dilated by half
    of it, so a changed face count means a gap too narrow to print."""
    return len(fatten(sk, PATTERN_GAP_MIN / 2).faces()) == len(sk.faces())


def led_ring_clear_fraction(*inlays: bd.Sketch) -> float:
    ring = bd.Circle(11.5) - bd.Circle(8.5)
    covered = 0.0
    for sk in inlays:
        hit = ring & sk
        covered += hit.area if hit is not None else 0.0
    return 1.0 - covered / ring.area
```

- [ ] **Step 2: Extend `build_lettering` and `build`**

Replace the icon block at the end of `build_lettering` and its signature:

```python
def build_lettering(number: str, top: str, icon: str, centre: str | None = None,
                    band: str | None = None):
    ...  # unchanged number/top code above
    ic = None
    if centre is not None:
        ic = PATTERNS_CENTRE[centre]()
    elif ICONS[icon] is not None:
        ic = ICONS[icon]()
    if ic is not None:
        if radial_range(ic)[1] > CORE_R_OUT - 1.2:
            raise SystemExit(f"centre element too large for the accent disc")
        mk = mk + ic
    band_sk = PATTERNS_BAND[band]() if band is not None else None
    if band_sk is not None:
        # keep the accent-colour band pattern away from the text-colour number
        lo_w, hi_w = BAND_WINDOW
        gap = min((b_lo - hi_w) % 360, (lo_w - b_hi) % 360)
        if gap < GAP_ARC / 2:
            raise SystemExit(f"band pattern within {gap:.0f} deg of the number")
    return mk, ic, spans, stroke_raw, band_sk
```

and in `build`:

```python
def build(number: str, top: str, icon: str, depth: float, centre: str | None = None,
          band: str | None = None, cap: bd.Solid | None = None):
    p = P
    z_top = p.z_ceiling + p.cap_top_t
    mk, ic, spans, stroke_raw, band_sk = build_lettering(number, top, icon, centre, band)
    core = bd.Circle(CORE_R_OUT) - ic if ic is not None else bd.Circle(CORE_R_OUT)
    if band_sk is not None:
        core = core + band_sk          # same filament (accent), one body
    if cap is None:
        cap = build_cap(p, foam=FOAM_INNER)
    inlay = bd.Pos(0, 0, z_top - depth) * bd.extrude(mk, amount=depth)
    shell = cap - inlay
    core_body = bd.Pos(0, 0, z_top - depth) * bd.extrude(core, amount=depth)
    shell = shell - core_body
    return cap, shell, inlay, core_body, mk, core, spans, stroke_raw, band_sk
```

- [ ] **Step 3: CLI flags and checks in `main`**

Add after `--icon`:

```python
    ap.add_argument("--centre", default=None, choices=sorted(PATTERNS_CENTRE),
                    help="centre pattern instead of an icon")
    ap.add_argument("--band", default=None, choices=sorted(PATTERNS_BAND),
                    help="pattern in the band above the number (accent colour)")
```

After parsing: `if a.centre is not None and a.icon != "none" and "--icon" in sys.argv: raise SystemExit("--centre and --icon are mutually exclusive")`; pass `a.centre, a.band` into `build(...)` and unpack the extra `band_sk`. Add checks after "icon fills its cut in the disc":

```python
    for label, sk in (("centre pattern", ic if a.centre else None), ("band pattern", band_sk)):
        if sk is None:
            continue
        check(min_feature(sk) >= PATTERN_FEATURE_MIN, f"{label} feature printable",
              f"{min_feature(sk):.2f} mm >= {PATTERN_FEATURE_MIN}")
        check(pattern_gap_ok(sk), f"{label} gaps printable",
              f">= {PATTERN_GAP_MIN} mm between islands")
    clear = led_ring_clear_fraction(mk, core)
    check(clear >= 0.60, "LED ring stays clear", f"{clear * 100:.0f}% of r 8.5-11.5 open")
```

- [ ] **Step 4: Tests** — extend the acceptance matrix in `test_cap_marking.py`:

```python
    ("67",    ["--centre", "rings", "--band", "stripes"]),
    ("99999", ["--icon", "sun", "--band", "dots"]),
    ("3",     ["--centre", "solid", "--band", "arc"]),
    ("4242",  ["--centre", "dots", "--icon", "none"]),
```

and rejections: `("icon and centre together", ["7", "--icon", "star", "--centre", "rings"], "mutually exclusive")`, `("unknown band", ["7", "--band", "zigzag"], "invalid choice")`.

- [ ] **Step 5: Run the suite**

Run: `cd cad && dev-budget run --kind heavy -- uv run --python 3.12 test_cap_marking.py`
Expected: all PASS including the Task 1 parity checks (icons now 6; the "LED ring stays clear" check ≥ 60 % for every matrix row; fix radii if one fails — the numbers above were chosen with margin).

- [ ] **Step 6: Commit**

```bash
git add cad/cap_marking.py cad/test_cap_marking.py
git commit -m "feat(cad): centre and band patterns, egg/sun/moon icons, printability checks"
```

---

### Task 3: Layout export and proof SVG

**Files:**
- Create: `cad/cap_svg.py`
- Modify: `cad/cap_marking.py` (`main`: `--layout-json`, `--proof`)
- Modify: `cad/test_cap_marking.py`

**Interfaces:**
- Produces: `sketch_to_path(sk: bd.Sketch, samples: int = 16) -> str` (SVG `d`, mm, y-up, evenodd subpaths); `digit_outlines() -> dict[str, dict]` (`{"0": {"d": ..., "advance": 3.814}}`, glyph bbox centred at origin); `write_layout(path: Path) -> dict`; `write_proof(path: Path, mk, core, scheme: dict) -> None`.
- Layout JSON schema `hen-cap-layout/1`:

```json
{"schema":"hen-cap-layout/1","generator_version":"dev",
 "cap_r":15.97,"scallops":{"n":8,"r":1.4,"orbit":17.12},
 "core_r":8.6,"band":{"r_min":9.6,"r_max":15.4},"band_window":[-10,190],
 "number":{"font_pt":6.0,"centre_deg":270,"base_r":12.5,"stroke":0.36,
           "advance":3.814,"digits":{"0":"M ... Z", "...":"..."}},
 "icons":{"heart":"M ... Z"},"centre_patterns":{"rings":"..."},"band_patterns":{"stripes":"..."}}
```

- [ ] **Step 1: Write `cad/cap_svg.py`**

```python
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""2D sketch -> SVG helpers: the app's live preview and the proof image are
drawn from the same sketches the printer gets."""

import json
import sys
from pathlib import Path

import build123d as bd

sys.path.insert(0, str(Path(__file__).parent))
import cap_marking as cm  # noqa: E402
from cap_design import load_catalog  # noqa: E402
from hen_tag_enclosure import P  # noqa: E402


def _wire_path(wire: bd.Wire, samples: int) -> str:
    pts = []
    for e in wire.edges():
        n = 1 if e.geom_type == bd.GeomType.LINE else samples
        for i in range(n):
            v = e.position_at(i / n)
            pts.append(f"{v.X:.3f} {v.Y:.3f}")
    return "M " + " L ".join(pts) + " Z"


def sketch_to_path(sk: bd.Sketch, samples: int = 16) -> str:
    parts = []
    for f in sk.faces():
        parts.append(_wire_path(f.outer_wire(), samples))
        for w in f.inner_wires():
            parts.append(_wire_path(w, samples))
    return " ".join(parts)


def digit_outlines() -> dict[str, dict]:
    out = {}
    for d in "0123456789":
        one = bd.Text(d, font_size=cm.NUM_FONT, font_path=cm._font(),
                      align=(bd.Align.CENTER, bd.Align.CENTER))
        left = bd.Text(d, font_size=cm.NUM_FONT, font_path=cm._font(),
                       align=(bd.Align.MIN, bd.Align.MIN))
        two = bd.Text(d + d, font_size=cm.NUM_FONT, font_path=cm._font(),
                      align=(bd.Align.MIN, bd.Align.MIN))
        adv = two.bounding_box().size.X - left.bounding_box().size.X
        out[d] = {"d": sketch_to_path(one), "advance": round(adv, 3)}
    return out


def write_layout(path: Path) -> dict:
    cat = load_catalog()
    layout = {
        "schema": "hen-cap-layout/1",
        "generator_version": cat["generator_version"],
        "cap_r": round(P.r_cap_out, 3),
        "scallops": {"n": 8, "r": 1.4, "orbit": round(P.r_cap_out + 1.15, 3)},
        "core_r": cm.CORE_R_OUT,
        "band": {"r_min": cm.BAND_R_MIN, "r_max": cm.BAND_R_MAX},
        "band_window": list(cm.BAND_WINDOW),
        "number": {"font_pt": cm.NUM_FONT, "centre_deg": 270.0,
                   "base_r": round((cm.BAND_R_MIN + cm.BAND_R_MAX) / 2, 3),
                   "stroke": round(2 * cm.GLYPH_FATTEN, 3),
                   "digits": digit_outlines()},
        "icons": {k: sketch_to_path(f()) for k, f in cm.ICONS.items() if f is not None},
        "centre_patterns": {k: sketch_to_path(f()) for k, f in cm.PATTERNS_CENTRE.items()},
        "band_patterns": {k: sketch_to_path(f()) for k, f in cm.PATTERNS_BAND.items()},
    }
    adv = {v["advance"] for v in layout["number"]["digits"].values()}
    layout["number"]["advance"] = max(adv)
    path.write_text(json.dumps(layout, indent=1, sort_keys=True) + "\n")
    return layout


def write_proof(path: Path, mk: bd.Sketch, core: bd.Sketch, scheme: dict) -> None:
    r = P.r_cap_out + 0.5
    text_hex, accent_hex = scheme["text"]["hex"], scheme["accent"]["hex"]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-r} {-r} {2 * r} {2 * r}" '
           f'width="256" height="256"><g transform="scale(1,-1)">'
           f'<circle r="{P.r_cap_out:.2f}" fill="#e9eef2" stroke="#b7c0c8" stroke-width="0.2"/>'
           f'<path d="{sketch_to_path(core)}" fill="{accent_hex}" fill-rule="evenodd"/>'
           f'<path d="{sketch_to_path(mk)}" fill="{text_hex}" fill-rule="evenodd"/>'
           f'</g></svg>\n')
    path.write_text(svg)


if __name__ == "__main__":
    out = write_layout(cm.OUT / "layout.json")
    print(f"wrote layout.json: {len(out['number']['digits'])} digits, "
          f"{len(out['icons'])} icons, advance {out['number']['advance']}")
```

- [ ] **Step 2: Wire the flags into `cap_marking.main`**

```python
    ap.add_argument("--layout-json", default=None, help="also write the preview layout JSON here")
    ap.add_argument("--proof", default=None, help="write a top-view proof SVG here")
    ap.add_argument("--scheme", default="classic", help="catalog scheme id for the proof colours")
```

After the checks pass (before export): 

```python
    if a.layout_json:
        from cap_svg import write_layout
        write_layout(Path(a.layout_json))
    if a.proof:
        from cap_svg import write_proof
        from cap_design import load_catalog
        scheme = next(s for s in load_catalog()["schemes"] if s["id"] == a.scheme)
        write_proof(Path(a.proof), mk, core, scheme)
```

- [ ] **Step 3: Tests** (append to the acceptance section):

```python
print("=== layout export and proof ===")
r = run_cli("67", "--icon", "heart", "--band", "stripes",
            "--layout-json", str(OUT / "layout.json"), "--proof", str(OUT / "proof_67.svg"))
check(all_checks_passed(r), "generate with layout + proof")
import json as _json
lay = _json.loads((OUT / "layout.json").read_text())
check(lay["schema"] == "hen-cap-layout/1" and len(lay["number"]["digits"]) == 10, "layout has 10 digits")
check(abs(lay["number"]["advance"] - 3.814) < 0.01, "digit advance 3.814", str(lay["number"]["advance"]))
check(all(v["d"].startswith("M ") for v in lay["number"]["digits"].values()), "digit paths well-formed")
check(set(lay["icons"]) == {"heart", "star", "flower", "egg", "sun", "moon"}, "layout icons complete")
svg = (OUT / "proof_67.svg").read_text()
check(svg.count("<path") == 2 and "#101010" in svg and "#F4F4F0" in svg, "proof has both colours")
```

- [ ] **Step 4: Run the suite** — Expected: all PASS.

- [ ] **Step 5: Generate and commit `cad/out/layout.json`** (stable data asset) and allow it in `cad/out/.gitignore` (add `!layout.json` under the sample exception).

```bash
cd cad && dev-budget run --kind heavy -- uv run --python 3.12 cap_svg.py
git add cad/cap_svg.py cad/cap_marking.py cad/test_cap_marking.py cad/out/layout.json cad/out/.gitignore
git commit -m "feat(cad): layout JSON for the app preview and proof SVG export"
```

---

### Task 4: Pure-Python Bambu plate writer

**Files:**
- Create: `cad/bambu_project.py`, `cad/bambu/project_settings.json`
- Create: `cad/test_bambu_project.py`

**Interfaces:**
- Produces: `write_plate(path: Path, caps: list[PlateCap], scheme: dict, batch_id: str) -> None` where `PlateCap = dict(name: str, position: tuple[float, float], bodies: dict[str, tuple[verts, tris]])` with body keys `shell`, `marking`, `core` (canonical meshes from `cap_marking.canonical_mesh`, world coords: cap bottom at z 0, centred on xy origin, already in print orientation); `grid_positions(n: int) -> list[tuple[float, float]]` (row-major, `38 + 36*i`); `PLATE_MAX = 36`; `P1S_PRINTABLE_AREA`, `P1S_EXCLUDE`.

- [ ] **Step 1: Extract the settings template once**

```bash
cd cad && python3 - <<'EOF'
import json, zipfile
cfg = json.loads(zipfile.ZipFile("out/cap_67_P1S.3mf").read("Metadata/project_settings.config"))
cfg.update({"wall_loops": "3", "wall_generator": "arachne", "reduce_crossing_wall": "1",
            "printable_area": ["0x0", "256x0", "256x256", "0x256"],
            "bed_exclude_area": ["0x0", "18x0", "18x28", "0x28"],
            "filament_type": ["PETG", "PETG", "PETG"],
            "filament_colour": ["#F4F4F0", "#101010", "#F4F4F0"]})
import os; os.makedirs("bambu", exist_ok=True)
json.dump(cfg, open("bambu/project_settings.json", "w"), indent=1, sort_keys=True)
print(len(cfg), "keys")
EOF
```

- [ ] **Step 2: Failing test `cad/test_bambu_project.py`**

```python
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""The plate writer: structure, determinism, and (when Bambu Studio is
installed) a real slice of a two-cube plate."""
import hashlib, json, re, subprocess, sys, zipfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from bambu_project import APP, grid_positions, write_plate  # noqa: E402

PASS, FAIL = 0, []
def check(cond, label, detail=""):
    global PASS
    PASS += cond; FAIL.extend([] if cond else [label])
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}  {detail}")

def cube(s: float, z0: float = 0.0):
    v = [(x, y, z) for z in (z0, z0 + s) for y in (-s/2, s/2) for x in (-s/2, s/2)]
    t = [(0,2,1),(1,2,3),(4,5,6),(5,7,6),(0,1,4),(1,5,4),(2,6,3),(3,6,7),(0,4,2),(2,4,6),(1,3,5),(3,7,5)]
    return v, t

scheme = {"id": "classic", "text": {"hex": "#101010"}, "accent": {"hex": "#F4F4F0"}}
caps = [{"name": f"cap_{n}", "position": pos,
         "bodies": {"shell": cube(10.0), "marking": cube(4.0, 10.0), "core": cube(2.0, 14.0)}}
        for n, pos in zip((1, 2), grid_positions(2))]
out = HERE / "out" / "test_plate.3mf"
write_plate(out, caps, scheme, "test-batch")
z = zipfile.ZipFile(out)
names = z.namelist()
check("3D/3dmodel.model" in names and "Metadata/model_settings.config" in names
      and "Metadata/project_settings.config" in names and "3D/Objects/object_2.model" in names,
      "package structure")
model = z.read("3D/3dmodel.model").decode()
check(model.count("<item ") == 2 and 'transform="1 0 0 0 1 0 0 0 1 38 38 0"' in model
      and 'transform="1 0 0 0 1 0 0 0 1 74 38 0"' in model, "two items on the grid")
ms = z.read("Metadata/model_settings.config").decode()
check(ms.count('<metadata key="extruder" value="1"/>') == 2
      and ms.count('<metadata key="extruder" value="2"/>') == 2
      and ms.count('<metadata key="extruder" value="3"/>') == 2, "extruders 1/2/3 per cap")
cfg = json.loads(z.read("Metadata/project_settings.config"))
check(cfg["wall_loops"] == "3" and cfg["reduce_crossing_wall"] == "1"
      and cfg["filament_colour"] == ["#F4F4F0", "#101010", "#F4F4F0"], "settings and colours")
h1 = hashlib.sha256(out.read_bytes()).hexdigest()
write_plate(out, caps, scheme, "test-batch")
check(hashlib.sha256(out.read_bytes()).hexdigest() == h1, "byte-identical on rerun", h1[:12])
check(grid_positions(36)[-1] == (218.0, 218.0) and len(grid_positions(36)) == 36, "36-cap grid")
if APP.exists():
    r = subprocess.run([str(APP), "--debug", "2", "--slice", "0", "--outputdir", str(HERE / "out" / "slice_test"), str(out)],
                       capture_output=True, text=True)
    g = HERE / "out" / "slice_test" / "plate_1.gcode"
    ok = g.exists() and "[error]" not in r.stdout + r.stderr
    ids = set(re.findall(r"; OBJECT_ID: (\d+)", g.read_text(errors="replace"))) if g.exists() else set()
    check(ok and len(ids) == 2, "Bambu Studio slices the plate with 2 objects", f"{len(ids)} object ids")
print(f"{PASS} passed, {len(FAIL)} failed" + (f": {FAIL}" if FAIL else ""))
sys.exit(1 if FAIL else 0)
```

Run: `cd cad && uv run --python 3.12 test_bambu_project.py` → Expected: `ModuleNotFoundError: bambu_project`.

- [ ] **Step 3: Write `cad/bambu_project.py`**

```python
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""Bambu Studio project (3MF) writer with no dependency on the Bambu CLI.

Mirrors the package the CLI writes (see out/cap_67_P1S.3mf): one assembly
object per cap in 3D/3dmodel.model, its three mesh bodies in
3D/Objects/object_<k>.model, per-part extruders in Metadata/model_settings.config,
and a full project_settings.config copied from bambu/project_settings.json
with the scheme's filament colours patched in. Deterministic: fixed
timestamps, uuid5 ids, sorted keys."""

import json
import struct
import uuid
import zipfile
import zlib
from pathlib import Path

HERE = Path(__file__).parent
APP = Path("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
TEMPLATE = HERE / "bambu" / "project_settings.json"
P1S_PRINTABLE_AREA = ["0x0", "256x0", "256x256", "0x256"]
P1S_EXCLUDE = ["0x0", "18x0", "18x28", "0x28"]
PLATE_MAX = 36
GRID_ORIGIN = 38.0
GRID_PITCH = 36.0
STAMP = (2026, 1, 1, 0, 0, 0)
NS = uuid.UUID("6f1c2b7e-9c1e-4b2a-8f0e-2d5f7a1c3e44")
XML_HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n'
MODEL_NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
            'requiredextensions="p"')
BODY_EXTRUDER = {"shell": 1, "marking": 2, "core": 3}


def grid_positions(n: int) -> list[tuple[float, float]]:
    if not 1 <= n <= PLATE_MAX:
        raise SystemExit(f"a plate holds 1..{PLATE_MAX} caps, got {n}")
    return [(GRID_ORIGIN + GRID_PITCH * (i % 6), GRID_ORIGIN + GRID_PITCH * (i // 6))
            for i in range(n)]


def _uid(*parts: str) -> str:
    return str(uuid.uuid5(NS, ":".join(parts)))


def _png_1x1() -> bytes:
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\xe9\xee\xf2")) + chunk(b"IEND", b""))


def _mesh_xml(oid: int, name: str, verts, tris) -> str:
    vx = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in verts)
    tx = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
    return (f'<object id="{oid}" p:UUID="{_uid("mesh", name)}" type="model">'
            f'<mesh><vertices>{vx}</vertices><triangles>{tx}</triangles></mesh></object>')


def write_plate(path: Path, caps: list[dict], scheme: dict, batch_id: str) -> None:
    if len(caps) > PLATE_MAX:
        raise SystemExit(f"{len(caps)} caps exceed the plate ({PLATE_MAX})")
    entries: list[tuple[str, bytes]] = []
    assemblies, items, settings_objects, instances = [], [], [], []
    for k, cap in enumerate(caps):
        base = 4 * k
        meshes, comps, parts = [], [], []
        for bi, body in enumerate(("shell", "marking", "core")):
            oid = base + 1 + bi
            verts, tris = cap["bodies"][body]
            meshes.append(_mesh_xml(oid, f'{cap["name"]}:{body}', verts, tris))
            comps.append(f'<component p:path="/3D/Objects/object_{k + 1}.model" objectid="{oid}" '
                         f'p:UUID="{_uid("comp", cap["name"], body)}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>')
            parts.append(f'<part id="{oid}" subtype="normal_part" uuid="{_uid("part", cap["name"], body)}">'
                         f'<metadata key="name" value="{cap["name"]}_{body}"/>'
                         f'<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>'
                         f'<metadata key="extruder" value="{BODY_EXTRUDER[body]}"/></part>')
        entries.append((f"3D/Objects/object_{k + 1}.model",
                        (XML_HEAD + f'<model unit="millimeter" xml:lang="en-US" {MODEL_NS}>'
                         '<metadata name="BambuStudio:3mfVersion">1</metadata>'
                         f'<resources>{"".join(meshes)}</resources><build/></model>').encode()))
        aid = base + 4
        x, y = cap["position"]
        assemblies.append(f'<object id="{aid}" p:UUID="{_uid("asm", cap["name"])}" type="model">'
                          f'<components>{"".join(comps)}</components></object>')
        items.append(f'<item objectid="{aid}" p:UUID="{_uid("item", cap["name"])}" '
                     f'transform="1 0 0 0 1 0 0 0 1 {x:g} {y:g} 0" printable="1"/>')
        settings_objects.append(f'<object id="{aid}"><metadata key="name" value="{cap["name"]}"/>'
                                f'{"".join(parts)}</object>')
        instances.append(f'<model_instance><metadata key="object_id" value="{aid}"/>'
                         f'<metadata key="instance_id" value="0"/>'
                         f'<metadata key="identify_id" value="{100 + k}"/></model_instance>')
    model = (XML_HEAD + f'<model unit="millimeter" xml:lang="en-US" {MODEL_NS}>'
             '<metadata name="Application">hen-tag cap_batch</metadata>'
             '<metadata name="BambuStudio:3mfVersion">1</metadata>'
             f'<metadata name="Title">{batch_id}</metadata>'
             f'<resources>{"".join(assemblies)}</resources>'
             f'<build p:UUID="{_uid("build", batch_id)}">{"".join(items)}</build></model>')
    model_settings = (XML_HEAD + '<config>' + "".join(settings_objects)
                      + '<plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value=""/>'
                      '<metadata key="locked" value="false"/><metadata key="filament_map_mode" value="Auto For Flush"/>'
                      '<metadata key="gcode_file" value=""/><metadata key="thumbnail_file" value="Metadata/plate_1.png"/>'
                      '<metadata key="thumbnail_no_light_file" value="Metadata/plate_no_light_1.png"/>'
                      '<metadata key="top_file" value="Metadata/top_1.png"/><metadata key="pick_file" value="Metadata/pick_1.png"/>'
                      + "".join(instances) + '</plate><assemble></assemble></config>')
    cfg = json.loads(TEMPLATE.read_text())
    cfg["printable_area"], cfg["bed_exclude_area"] = P1S_PRINTABLE_AREA, P1S_EXCLUDE
    cfg["filament_colour"] = [scheme["accent"]["hex"], scheme["text"]["hex"], scheme["accent"]["hex"]]
    cfg["filament_colour"][0] = "#F4F4F0"   # slot 1 is always clear PETG; shown as white
    cfg.update({"wall_loops": "3", "wall_generator": "arachne", "reduce_crossing_wall": "1"})
    ctypes = (XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
              '<Default Extension="png" ContentType="image/png"/></Types>')
    rels = (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '<Relationship Target="/Metadata/plate_1.png" Id="rel-2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>'
            '</Relationships>')
    model_rels = (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                  + "".join(f'<Relationship Target="/3D/Objects/object_{k + 1}.model" Id="rel-{k + 1}" '
                            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>' for k in range(len(caps)))
                  + '</Relationships>')
    slice_info = XML_HEAD + '<config><header><header_item key="X-BBL-Client-Type" value="slicer"/></header></config>'
    png = _png_1x1()
    head = [("[Content_Types].xml", ctypes.encode()), ("_rels/.rels", rels.encode()),
            ("3D/3dmodel.model", model.encode()), ("3D/_rels/3dmodel.model.rels", model_rels.encode())]
    tail = [("Metadata/project_settings.config", json.dumps(cfg, indent=4, sort_keys=True).encode()),
            ("Metadata/model_settings.config", model_settings.encode()),
            ("Metadata/slice_info.config", slice_info.encode()),
            ("Metadata/plate_1.png", png), ("Metadata/plate_no_light_1.png", png),
            ("Metadata/top_1.png", png), ("Metadata/pick_1.png", png)]
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in head + entries + tail:
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, payload)
```

- [ ] **Step 4: Run the test** — Expected: all PASS; with Bambu Studio installed the slice check reports 2 object ids. If Bambu refuses the package, compare `unzip -l` and the XML against `out/cap_67_P1S.3mf` and fix the writer, not the test.

- [ ] **Step 5: Ignore test outputs and commit**

Append to `cad/out/.gitignore`: `test_plate.3mf`, `slice_test/`, `plates/`, `cache/`, `proof/`.

```bash
git add cad/bambu_project.py cad/bambu/project_settings.json cad/test_bambu_project.py cad/out/.gitignore
git commit -m "feat(cad): pure-Python Bambu plate writer"
```

---

### Task 5: Batch CLI

**Files:**
- Create: `cad/cap_batch.py`, `cad/fixtures/batch_sample.json`, `cad/test_cap_batch.py`
- Modify: `cad/slice_check.py` (accept a `.3mf` path)

**Interfaces:**
- Consumes: `build`, `canonical_mesh`, `FOAM_INNER`, `DEPTH_DEFAULT` from `cap_marking`; `build_cap`, `P` from `hen_tag_enclosure`; `write_plate`, `grid_positions` from `bambu_project`; `load_catalog`, `validate_design`, `design_hash` from `cap_design`; `write_proof` from `cap_svg`.
- Produces: CLI `uv run --python 3.12 cap_batch.py <batch.json> [--out out/plates] [--no-slice]` writing `plate_<batch_id>_P1S.3mf`, `plate_<batch_id>_manifest.csv` (`position,serial,hen_name,design_hash`), `proof/<design_hash>.svg`; exit 1 with every problem listed on an invalid batch.

- [ ] **Step 1: Fixture `cad/fixtures/batch_sample.json`**

```json
{
  "schema": "hen-cap-batch/1",
  "batch_id": "2026-09-14-classic-01",
  "scheme": "classic",
  "generator_version": "dev",
  "created_at": "2026-09-14T18:00:00Z",
  "caps": [
    {"serial": 67, "icon": "heart", "centre": null, "band": "stripes",
     "design_hash": "05dcdb796b921b25", "hen_name": "Bözsi"},
    {"serial": 12345, "icon": "star", "centre": null, "band": "dots",
     "design_hash": "8fc7c9f4fcdb32c0", "hen_name": "Piroska"},
    {"serial": 3, "icon": null, "centre": "solid", "band": "arc",
     "design_hash": "", "hen_name": "Kata"}
  ]
}
```

Fill the third hash by running `python3 -c "import sys; sys.path.insert(0,'cad'); from cap_design import design_hash; print(design_hash(3,'classic',None,'solid','arc'))"` and pasting the value.

- [ ] **Step 2: Failing test `cad/test_cap_batch.py`**

```python
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
FIX = HERE / "fixtures" / "batch_sample.json"
OUT = HERE / "out" / "plates_test"
PASS, FAIL = 0, []
def check(cond, label, detail=""):
    global PASS
    PASS += cond; FAIL.extend([] if cond else [label])
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}  {detail}")
def run(batch: Path, *extra):
    return subprocess.run(["uv", "run", "--python", "3.12", str(HERE / "cap_batch.py"), str(batch),
                           "--out", str(OUT), "--no-slice", *extra], capture_output=True, text=True, cwd=HERE)
def variant(name, mutate):
    b = json.loads(FIX.read_text()); mutate(b)
    p = OUT / f"{name}.json"; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(b)); return p

print("=== happy path ===")
r = run(FIX)
plate = OUT / "plate_2026-09-14-classic-01_P1S.3mf"
manifest = OUT / "plate_2026-09-14-classic-01_manifest.csv"
check(r.returncode == 0, "batch runs", r.stdout[-300:] + r.stderr[-300:])
check(plate.exists() and manifest.exists(), "plate and manifest written")
rows = manifest.read_text().splitlines()
check(rows[0] == "position,serial,hen_name,design_hash" and len(rows) == 4, "manifest rows", str(rows[:2]))
check((OUT / "proof" / "05dcdb796b921b25.svg").exists(), "proof named by design hash")
h1 = hashlib.sha256(plate.read_bytes()).hexdigest()
r2 = run(FIX)
check(r2.returncode == 0 and hashlib.sha256(plate.read_bytes()).hexdigest() == h1, "byte-identical rerun", h1[:12])
check("cache" in r2.stdout, "second run reports cache hits")

print("=== refusals ===")
cases = [
    ("bad hash", lambda b: b["caps"][0].update(design_hash="0000000000000000"), "does not match"),
    ("unknown icon", lambda b: b["caps"][1].update(icon="unicorn"), "unknown icon"),
    ("duplicate serial", lambda b: b["caps"][1].update(serial=67), "duplicate serial"),
    ("version mismatch", lambda b: b.update(generator_version="v9"), "generator_version"),
    ("icon and centre", lambda b: b["caps"][0].update(centre="rings"), "mutually exclusive"),
    ("wrong scheme in cap", lambda b: b.update(scheme="nope"), "unknown scheme"),
    ("too many caps", lambda b: b["caps"].extend([dict(b["caps"][2], serial=100 + i, design_hash="x") for i in range(40)]), "36"),
]
for label, mutate, needle in cases:
    r = run(variant(label.replace(" ", "_"), mutate))
    check(r.returncode != 0 and needle in r.stdout + r.stderr, f"refuse {label}", (r.stdout + r.stderr)[-160:] if needle not in r.stdout + r.stderr else "")
print(f"{PASS} passed, {len(FAIL)} failed" + (f": {FAIL}" if FAIL else ""))
sys.exit(1 if FAIL else 0)
```

- [ ] **Step 3: Write `cad/cap_batch.py`**

```python
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Batch JSON (hen-cap-batch/1) -> one Bambu plate, a manifest and proofs.

    uv run --python 3.12 cap_batch.py batch.json [--out out/plates] [--no-slice]

Refuses the whole batch on any problem and lists every offending cap. Bodies
are cached under out/cache/<design_hash>/ so re-runs and re-prints are free.
"""
import argparse
import csv
import json
import pickle
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bambu_project import PLATE_MAX, grid_positions, write_plate  # noqa: E402
from cap_design import load_catalog, validate_design  # noqa: E402

HERE = Path(__file__).parent


def validate_batch(batch: dict, cat: dict) -> list[str]:
    errs = []
    if batch.get("schema") != "hen-cap-batch/1":
        errs.append(f"unsupported batch schema {batch.get('schema')!r}")
    if batch.get("generator_version") != cat["generator_version"]:
        errs.append(f"generator_version {batch.get('generator_version')!r} != catalog {cat['generator_version']!r}")
    if batch.get("scheme") not in [s["id"] for s in cat["schemes"]]:
        errs.append(f"unknown scheme {batch.get('scheme')!r}")
    caps = batch.get("caps") or []
    if not 1 <= len(caps) <= PLATE_MAX:
        errs.append(f"a plate holds 1..{PLATE_MAX} caps, batch has {len(caps)}")
    seen = set()
    for i, c in enumerate(caps):
        d = {"serial": c.get("serial"), "scheme": batch.get("scheme"), "icon": c.get("icon"),
             "centre": c.get("centre"), "band": c.get("band"), "design_hash": c.get("design_hash")}
        for e in validate_design(cat, d):
            errs.append(f"cap {i} (serial {c.get('serial')}): {e}")
        if c.get("serial") in seen:
            errs.append(f"cap {i}: duplicate serial {c.get('serial')}")
        seen.add(c.get("serial"))
    return errs


def build_bodies(c: dict, cap_solid, cache: Path) -> tuple[dict, bool]:
    from cap_marking import DEPTH_DEFAULT, build, canonical_mesh
    import build123d as bd
    key = cache / c["design_hash"] / "bodies.pkl"
    if key.exists():
        return pickle.loads(key.read_bytes()), True
    icon = c["icon"] or "none"
    _, shell, inlay, core_body, mk, core, _, _, _ = build(
        str(c["serial"]), "", icon, DEPTH_DEFAULT, centre=c["centre"], band=c["band"], cap=cap_solid)
    dz = -(bd.Rot(180, 0, 0) * shell).bounding_box().min.Z
    bodies = {}
    for name, solid in (("shell", shell), ("marking", inlay), ("core", core_body)):
        oriented = bd.Pos(0, 0, dz) * (bd.Rot(180, 0, 0) * solid)
        bodies[name] = canonical_mesh(oriented, f"{c['serial']}:{name}")
    key.parent.mkdir(parents=True, exist_ok=True)
    key.write_bytes(pickle.dumps(bodies))
    (key.parent / "sketches.pkl").write_bytes(pickle.dumps({"mk": mk, "core": core}))
    return bodies, False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("batch")
    ap.add_argument("--out", default=str(HERE / "out" / "plates"))
    ap.add_argument("--no-slice", action="store_true")
    a = ap.parse_args()
    cat = load_catalog()
    batch = json.loads(Path(a.batch).read_text())
    errs = validate_batch(batch, cat)
    if errs:
        print("batch refused:")
        for e in errs:
            print(f"  - {e}")
        return 1
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    cache = HERE / "out" / "cache"
    scheme = next(s for s in cat["schemes"] if s["id"] == batch["scheme"])
    from cap_marking import FOAM_INNER
    from cap_svg import write_proof
    from hen_tag_enclosure import P, build_cap
    import pickle as _pickle
    print(f"batch {batch['batch_id']}: {len(batch['caps'])} caps, scheme {scheme['id']}")
    cap_solid = build_cap(P, foam=FOAM_INNER)
    plate_caps, rows, hits = [], [], 0
    proof_dir = out / "proof"; proof_dir.mkdir(exist_ok=True)
    for pos, c in zip(grid_positions(len(batch["caps"])), batch["caps"]):
        bodies, hit = build_bodies(c, cap_solid, cache)
        hits += hit
        sk = _pickle.loads((cache / c["design_hash"] / "sketches.pkl").read_bytes())
        write_proof(proof_dir / f"{c['design_hash']}.svg", sk["mk"], sk["core"], scheme)
        plate_caps.append({"name": f"cap_{c['serial']}", "position": pos, "bodies": bodies})
        rows.append((f"{int((pos[0] - 38) / 36) + 1}{chr(65 + int((pos[1] - 38) / 36))}",
                     c["serial"], c.get("hen_name", ""), c["design_hash"]))
        print(f"  cap {c['serial']:>5} at {rows[-1][0]}  {'cache' if hit else 'built'}")
    plate = out / f"plate_{batch['batch_id']}_P1S.3mf"
    write_plate(plate, plate_caps, scheme, batch["batch_id"])
    with open(out / f"plate_{batch['batch_id']}_manifest.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["position", "serial", "hen_name", "design_hash"]); w.writerows(rows)
    print(f"wrote {plate.name}, manifest, {len(rows)} proofs ({hits} from cache)")
    if not a.no_slice:
        r = subprocess.run(["uv", "run", "--python", "3.12", str(HERE / "slice_check.py"), str(plate)], cwd=HERE)
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Positions in the manifest read `1A`…`6F` (column number, row letter).

- [ ] **Step 4: `slice_check.py` accepts a plate path** — in `main()`, before the parts loop:

```python
    plates = [Path(a) for a in sys.argv[1:] if a.endswith(".3mf")]
    for plate in plates:
        work = Path(tempfile.mkdtemp())
        r = subprocess.run([str(APP), "--debug", "4", "--slice", "0", "--outputdir", str(work), str(plate)],
                           capture_output=True, text=True)
        log = r.stdout + r.stderr
        g = work / "plate_1.gcode"
        n_obj = len(set(re.findall(r"; OBJECT_ID: (\d+)", g.read_text(errors="replace")))) if g.exists() else 0
        warn = [ln.strip()[:100] for ln in log.splitlines() if re.search(r"floating cantilever|CRITICAL|\[error\]", ln, re.I)]
        est = re.search(r"; total estimated time: (.+)", g.read_text(errors="replace")) if g.exists() else None
        ok = g.exists() and not warn
        print(f"  [{'PASS' if ok else 'FAIL'}] {plate.name:36} {n_obj} objects sliced"
              + (f", {est.group(1)}" if est else ""))
        for w_ in warn:
            print(f"         slicer: {w_}")
        if not ok:
            fails.append(plate.name)
        shutil.rmtree(work, ignore_errors=True)
    parts = [a for a in sys.argv[1:] if not a.startswith("--") and not a.endswith(".3mf")] or (list(OPEN_AIR) if not plates else [])
```

(`fails` must be defined before this block — move `fails = []` up.)

- [ ] **Step 5: Run the batch test** — `cd cad && dev-budget run --kind heavy -- uv run --python 3.12 test_cap_batch.py` → Expected: all PASS (first happy-path run builds 3 caps, ~1 min).

- [ ] **Step 6: Full-plate proof once** — generate a 36-cap batch from the fixture programmatically and slice it:

```bash
cd cad && python3 - <<'EOF'
import json, sys; sys.path.insert(0, '.')
from cap_design import design_hash
b = json.load(open('fixtures/batch_sample.json')); b['batch_id'] = 'full-plate-test'; caps = []
icons = ['heart', 'star', 'flower', 'egg', 'sun', 'moon']; bands = [None, 'stripes', 'dots', 'arc']
for i in range(36):
    s = 100 + i * 137 % 99999; ic = icons[i % 6]; bd_ = bands[i % 4]
    caps.append({'serial': s, 'icon': ic, 'centre': None, 'band': bd_, 'design_hash': design_hash(s, 'classic', ic, None, bd_), 'hen_name': f'Hen {i}'})
b['caps'] = caps; json.dump(b, open('out/full_plate.json', 'w'))
EOF
dev-budget run --kind heavy -- uv run --python 3.12 cap_batch.py out/full_plate.json --out out/plates_test
```

Expected: the plate slices with 36 objects and no warnings; record the slicer's time estimate in the lab note (Task 10).

- [ ] **Step 7: Commit**

```bash
git add cad/cap_batch.py cad/fixtures/batch_sample.json cad/test_cap_batch.py cad/slice_check.py
git commit -m "feat(cad): batch CLI: batch JSON to plate, manifest and proofs"
```

---

### Task 6: Editor scaffold on chirp's UI package

**Files:**
- Create: `editor/package.json`, `editor/vite.config.ts`, `editor/tsconfig.json`, `editor/index.html`, `editor/test/setup-dom.ts`, `editor/src/main.tsx`, `editor/src/smoke.test.tsx`, `editor/.gitignore`, `editor/README.md`

**Interfaces:**
- Produces: `pnpm dev`, `pnpm test`, `pnpm typecheck`, `pnpm build`, `pnpm sync:data`; alias `@chirpcoop/real-chicken-ui/*` → `${CHIRP_DIR}/packages/real-chicken-ui/src/*`, `@chirpcoop/design-tokens` → `${CHIRP_DIR}/packages/design-tokens/src/index.ts`.

- [ ] **Step 1: `editor/package.json`**

```json
{
  "name": "hen-cap-editor-prototype",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "typecheck": "tsc --noEmit",
    "sync:data": "cp ../cad/catalog.json src/cap-editor/data/catalog.json && cp ../cad/out/layout.json src/cap-editor/data/layout.json"
  },
  "dependencies": {
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^7.0.1",
    "@testing-library/react": "^16.3.3",
    "@testing-library/user-event": "^14.6.7",
    "@types/react": "^19.2.18",
    "@types/react-dom": "^19.2.7",
    "@vitejs/plugin-react": "^5.0.0",
    "jsdom": "^30.0.1",
    "typescript": "^6.0.3",
    "vite": "^7.0.0",
    "vitest": "^4.1.11"
  }
}
```

- [ ] **Step 2: `editor/vite.config.ts`**

```ts
/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
// The chirp checkout is read, never written: its UI package and design tokens
// are aliased from source so the editor renders with the real components.
export const CHIRP = process.env.CHIRP_DIR ?? path.resolve(here, '../../chirp');

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: /^@chirpcoop\/real-chicken-ui\/(.+)$/, replacement: path.join(CHIRP, 'packages/real-chicken-ui/src/$1') },
      { find: /^@chirpcoop\/design-tokens$/, replacement: path.join(CHIRP, 'packages/design-tokens/src/index.ts') },
    ],
    dedupe: ['react', 'react-dom'],
  },
  server: { fs: { allow: [here, CHIRP] } },
  test: {
    environment: 'jsdom',
    setupFiles: ['./test/setup-dom.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    css: false,
  },
});
```

- [ ] **Step 3: `editor/tsconfig.json`** (real-chicken-ui's options + paths)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable", "ES2023.Intl"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": false,
    "exactOptionalPropertyTypes": false,
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "isolatedModules": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "noEmit": true,
    "types": ["vite/client"],
    "baseUrl": ".",
    "paths": {
      "@chirpcoop/real-chicken-ui/*": ["../../chirp/packages/real-chicken-ui/src/*"],
      "@chirpcoop/design-tokens": ["../../chirp/packages/design-tokens/src/index.ts"],
      "@chirpcoop/shared-types": ["../../chirp/packages/shared-types/src/index.ts"],
      "@chirpcoop/shared-types/*": ["../../chirp/packages/shared-types/src/*"],
      "@chirpcoop/client-sdk": ["../../chirp/packages/client-sdk/src/index.ts"]
    }
  },
  "include": ["src", "test", "vite.config.ts"]
}
```

If `CHIRP_DIR` is not `../../chirp`, edit the paths (tsconfig cannot read env).

- [ ] **Step 4: `editor/test/setup-dom.ts`, `editor/index.html`, `editor/src/main.tsx`, `editor/.gitignore`**

```ts
// test/setup-dom.ts
import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
afterEach(() => { cleanup(); });
```

```html
<!doctype html>
<html lang="hu">
  <head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>Hen cap editor</title></head>
  <body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body>
</html>
```

```tsx
// src/main.tsx  (Task 9 replaces the placeholder with the demo page)
import { createRoot } from 'react-dom/client';
import '@chirpcoop/real-chicken-ui/styles.css';
import { RealChickenShell } from '@chirpcoop/real-chicken-ui/components';
import { en } from './copy/en.js';

createRoot(document.getElementById('root')!).render(
  <RealChickenShell copy={en.shell}><p className="rc-help-text">Cap editor scaffold</p></RealChickenShell>,
);
```

`RealChickenCopy` has many required fields; `src/copy/en.ts` provides a minimal `shell` object typed as `RealChickenCopy` — fill every required key with a short English string (copy the field list from `${CHIRP}/packages/real-chicken-ui/src/types.ts`; only `appTitle`/`appSubtitle` are rendered by the shell). `src/copy/hu.ts` mirrors it in Hungarian.

`.gitignore`: `node_modules/`, `dist/`.

- [ ] **Step 5: Smoke test `src/smoke.test.tsx`**

```tsx
import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RealChickenShell } from '@chirpcoop/real-chicken-ui/components';
import { GoldenGrainPill } from '@chirpcoop/real-chicken-ui/wallet-pill';
import { en } from './copy/en.js';

test('chirp shell and wallet pill render through the alias', () => {
  render(
    <RealChickenShell copy={en.shell} showHero={false}>
      <GoldenGrainPill balance={1234n} copy={{ label: 'Golden Grain', ariaTemplate: '{amount} Golden Grain' }} locale="en-US" />
    </RealChickenShell>,
  );
  expect(screen.getByLabelText('1,234 Golden Grain')).toBeInTheDocument();
});
```

- [ ] **Step 6: Install and run**

```bash
cd editor && dev-budget run --kind heavy -- pnpm install
dev-budget run --kind heavy -- pnpm test
dev-budget run --kind heavy -- pnpm typecheck
dev-budget run --kind heavy -- pnpm build
```

Expected: test PASS, typecheck clean (if duplicate React type errors appear from chirp files, add `"react": ["./node_modules/react"], "react-dom": ["./node_modules/react-dom"]` to `paths`), build writes `dist/`.

- [ ] **Step 7: `editor/README.md`** — how to run (`CHIRP_DIR`), the import rule, the integration map (spec §7.4). Commit:

```bash
git add editor
git commit -m "feat(editor): Vite scaffold rendering chirp's real-chicken-ui from source"
```

---

### Task 7: Domain types, design hash, mock client

**Files:**
- Create: `editor/src/cap-editor/types.ts`, `design-hash.ts`, `design-hash.test.ts`, `mock-client.ts`, `mock-client.test.ts`, `data/` (via `pnpm sync:data`)

**Interfaces:**
- Produces:

```ts
export type CapStatus = 'draft' | 'locked' | 'batched' | 'printed' | 'installed' | 'replaced';
export type CapDesign = { henId: string; serial: number; scheme: string; icon: string | null; centre: string | null; band: string | null; status: CapStatus; designHash: string; proofUrl: string | null };
export type Catalog = typeof import('./data/catalog.json');
export type Layout = typeof import('./data/layout.json');
export type WalletView = { balance: bigint };
export type ClientError = { code: 'INSUFFICIENT_GRAIN' | 'DESIGN_BATCHED' | 'CATALOG_MISMATCH' | 'NOT_EDITABLE' };
export interface CapDesignClient {
  load(henId: string): Promise<CapDesign>;
  save(henId: string, draft: Pick<CapDesign, 'scheme' | 'icon' | 'centre' | 'band'>): Promise<CapDesign>;
  lock(henId: string): Promise<CapDesign>;
  unlockForEdit(henId: string): Promise<CapDesign>;
  requestReplacement(henId: string): Promise<CapDesign>;
  getWallet(): Promise<WalletView>;
}
export function designHash(d: {serial: number; scheme: string; icon: string|null; centre: string|null; band: string|null}): Promise<string>;
export function createMockClient(seed: { hens: CapDesign[]; balance: bigint; catalog: Catalog }): CapDesignClient & { state(): { hens: CapDesign[]; balance: bigint } };
```

- [ ] **Step 1: `pnpm sync:data`** then commit the two JSON files (they are the generator's outputs; `sync:data` is re-run whenever `cad/` changes them).

- [ ] **Step 2: Failing tests**

```ts
// design-hash.test.ts
import { expect, test } from 'vitest';
import { designHash } from './design-hash.js';
test('matches the Python vectors', async () => {
  expect(await designHash({ serial: 67, scheme: 'classic', icon: 'heart', centre: null, band: 'stripes' })).toBe('05dcdb796b921b25');
  expect(await designHash({ serial: 8, scheme: 'meadow', icon: null, centre: 'rings', band: null })).toBe('0371884d05cc4f6b');
});
```

```ts
// mock-client.test.ts
import { expect, test } from 'vitest';
import catalog from './data/catalog.json';
import { createMockClient } from './mock-client.js';
const hen = { henId: 'h1', serial: 67, scheme: 'classic', icon: 'heart', centre: null, band: null, status: 'draft' as const, designHash: '', proofUrl: null };
function client(balance = 1000n) { return createMockClient({ hens: [hen], balance, catalog }); }
test('lock on a free scheme charges nothing and recomputes the hash', async () => {
  const c = client();
  const d = await c.lock('h1');
  expect(d.status).toBe('locked'); expect(d.designHash).toHaveLength(16);
  expect((await c.getWallet()).balance).toBe(1000n);
});
test('lock on a paid scheme charges its price', async () => {
  const c = client(200n);
  await c.save('h1', { scheme: 'meadow', icon: 'star', centre: null, band: 'dots' });
  await c.lock('h1');
  expect((await c.getWallet()).balance).toBe(50n);
});
test('lock refuses when grain is short', async () => {
  const c = client(10n);
  await c.save('h1', { scheme: 'sunset', icon: null, centre: 'rings', band: null });
  await expect(c.lock('h1')).rejects.toMatchObject({ code: 'INSUFFICIENT_GRAIN' });
});
test('re-edit costs the fee and returns to draft; batched designs cannot be unlocked', async () => {
  const c = client(100n);
  await c.lock('h1');
  expect((await c.unlockForEdit('h1')).status).toBe('draft');
  expect((await c.getWallet()).balance).toBe(50n);
  await c.lock('h1'); c.state().hens[0].status = 'batched';
  await expect(c.unlockForEdit('h1')).rejects.toMatchObject({ code: 'DESIGN_BATCHED' });
});
test('replacement from installed opens a new draft and charges the fee', async () => {
  const c = client(600n); c.state().hens[0].status = 'installed';
  const d = await c.requestReplacement('h1');
  expect(d.status).toBe('draft'); expect((await c.getWallet()).balance).toBe(100n);
});
test('save rejects icon together with centre pattern', async () => {
  await expect(client().save('h1', { scheme: 'classic', icon: 'heart', centre: 'rings', band: null })).rejects.toMatchObject({ code: 'CATALOG_MISMATCH' });
});
```

Run `pnpm test` → Expected: FAIL (modules missing).

- [ ] **Step 3: Implement**

```ts
// design-hash.ts — same canonical JSON as cad/cap_design.py
export async function designHash(d: { serial: number; scheme: string; icon: string | null; centre: string | null; band: string | null }): Promise<string> {
  const canon = JSON.stringify({ band: d.band, centre: d.centre, icon: d.icon, scheme: d.scheme, serial: d.serial, v: 1 });
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canon));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
}
```

(`JSON.stringify` with keys written in sorted order and no spaces equals Python's `sort_keys=True, separators=(",",":")`.)

```ts
// mock-client.ts
import type { CapDesign, CapDesignClient, Catalog, ClientError, WalletView } from './types.js';
import { designHash } from './design-hash.js';

const err = (code: ClientError['code']): ClientError => ({ code });

export function createMockClient(seed: { hens: CapDesign[]; balance: bigint; catalog: Catalog }) {
  const hens = seed.hens.map((h) => ({ ...h }));
  let balance = seed.balance;
  const cat = seed.catalog;
  const find = (henId: string) => { const h = hens.find((x) => x.henId === henId); if (!h) throw err('NOT_EDITABLE'); return h; };
  const price = (scheme: string) => BigInt(cat.schemes.find((s) => s.id === scheme)?.price_grain ?? 0);
  const charge = (amount: bigint) => { if (balance < amount) throw err('INSUFFICIENT_GRAIN'); balance -= amount; };
  const valid = (d: Pick<CapDesign, 'scheme' | 'icon' | 'centre' | 'band'>) =>
    cat.schemes.some((s) => s.id === d.scheme)
    && (d.icon === null || cat.icons.some((i) => i.id === d.icon))
    && (d.centre === null || cat.centre_patterns.some((p) => p.id === d.centre))
    && (d.band === null || cat.band_patterns.some((p) => p.id === d.band))
    && !(d.icon !== null && d.centre !== null);
  const client: CapDesignClient & { state(): { hens: CapDesign[]; balance: bigint } } = {
    async load(henId) { return { ...find(henId) }; },
    async save(henId, draft) {
      const h = find(henId);
      if (h.status !== 'draft') throw err('NOT_EDITABLE');
      if (!valid(draft)) throw err('CATALOG_MISMATCH');
      Object.assign(h, draft, { designHash: await designHash({ ...draft, serial: h.serial }) });
      return { ...h };
    },
    async lock(henId) {
      const h = find(henId);
      if (h.status !== 'draft') throw err('NOT_EDITABLE');
      charge(price(h.scheme));
      Object.assign(h, { status: 'locked', designHash: await designHash(h) });
      return { ...h };
    },
    async unlockForEdit(henId) {
      const h = find(henId);
      if (h.status !== 'locked') throw err(h.status === 'draft' ? 'NOT_EDITABLE' : 'DESIGN_BATCHED');
      charge(BigInt(cat.fees.reedit_grain));
      h.status = 'draft';
      return { ...h };
    },
    async requestReplacement(henId) {
      const h = find(henId);
      if (h.status !== 'installed') throw err('NOT_EDITABLE');
      charge(BigInt(cat.fees.replacement_grain));
      h.status = 'draft'; h.proofUrl = null;
      return { ...h };
    },
    async getWallet(): Promise<WalletView> { return { balance }; },
    state() { return { hens, balance }; },
  };
  return client;
}
```

- [ ] **Step 4: Run `pnpm test`** → Expected: all PASS. **Step 5: Commit** `feat(editor): domain types, design hash, mock client with the design state machine`.

---

### Task 8: Cap preview (pure SVG)

**Files:**
- Create: `editor/src/cap-editor/cap-preview.tsx`, `cap-preview.test.tsx`, `cap-preview.css`

**Interfaces:**
- Produces: `CapPreview({ design, catalog, layout, size?: number, title: string })` — renders `<svg role="img" aria-label={title}>`; deterministic; no hooks.

- [ ] **Step 1: Failing test**

```tsx
import { expect, test } from 'vitest';
import { render } from '@testing-library/react';
import catalog from './data/catalog.json';
import layout from './data/layout.json';
import { CapPreview } from './cap-preview.js';
const base = { henId: 'h', serial: 67, scheme: 'sunset', icon: 'heart', centre: null, band: 'stripes', status: 'draft' as const, designHash: '', proofUrl: null };
test('draws the digits, the icon and the band pattern in the scheme colours', () => {
  const { container } = render(<CapPreview design={base} catalog={catalog} layout={layout} title="cap 67" />);
  expect(container.querySelectorAll('[data-glyph]')).toHaveLength(2);
  expect(container.querySelector('[data-part="icon"]')?.getAttribute('fill')).toBe('#C8102E');
  expect(container.querySelector('[data-part="band"]')?.getAttribute('fill')).toBe('#F3C43E');
  expect(container.querySelector('[data-part="core"]')).not.toBeNull();
});
test('centre pattern replaces the icon and a 5-digit serial has five glyphs', () => {
  const { container } = render(<CapPreview design={{ ...base, serial: 12345, icon: null, centre: 'rings' }} catalog={catalog} layout={layout} title="cap" />);
  expect(container.querySelectorAll('[data-glyph]')).toHaveLength(5);
  expect(container.querySelector('[data-part="icon"]')).toBeNull();
  expect(container.querySelector('[data-part="centre"]')).not.toBeNull();
});
test('is deterministic', () => {
  const a = render(<CapPreview design={base} catalog={catalog} layout={layout} title="t" />).container.innerHTML;
  const b = render(<CapPreview design={base} catalog={catalog} layout={layout} title="t" />).container.innerHTML;
  expect(a).toBe(b);
});
```

- [ ] **Step 2: Implement**

```tsx
import type { CapDesign, Catalog, Layout } from './types.js';

type Props = { design: Pick<CapDesign, 'serial' | 'scheme' | 'icon' | 'centre' | 'band'>; catalog: Catalog; layout: Layout; size?: number; title: string };

// Pure SVG in millimetres, y-up (one scale(1,-1) group), so every path from
// layout.json — the generator's own sketches — is used verbatim. The digits
// are laid along the bottom arc exactly like the printer's: centred on
// 270 deg, uniform advance, tops toward the centre.
export function CapPreview({ design, catalog, layout, size, title }: Props) {
  const scheme = catalog.schemes.find((s) => s.id === design.scheme) ?? catalog.schemes[0];
  const r = layout.cap_r;
  const vb = r + 1;
  const n = layout.number;
  const digits = String(design.serial).split('');
  const glyphs = digits.map((d, i) => {
    const s = (i + 0.5) * n.advance - (digits.length * n.advance) / 2;
    const theta = n.centre_deg + (s / n.base_r) * (180 / Math.PI);
    return { d, theta, path: n.digits[d as keyof typeof n.digits] };
  });
  const scallops = Array.from({ length: layout.scallops.n }, (_, i) => {
    const a = (2 * Math.PI * i) / layout.scallops.n;
    return { cx: layout.scallops.orbit * Math.cos(a), cy: layout.scallops.orbit * Math.sin(a) };
  });
  const circle = (cx: number, cy: number, rr: number) =>
    `M ${cx + rr} ${cy} A ${rr} ${rr} 0 1 0 ${cx - rr} ${cy} A ${rr} ${rr} 0 1 0 ${cx + rr} ${cy} Z`;
  const discPath = circle(0, 0, r) + ' ' + scallops.map((s) => circle(s.cx, s.cy, layout.scallops.r)).join(' ');
  const centrePath = design.centre ? layout.centre_patterns[design.centre as keyof typeof layout.centre_patterns] : null;
  const iconPath = !design.centre && design.icon ? layout.icons[design.icon as keyof typeof layout.icons] : null;
  const bandPath = design.band ? layout.band_patterns[design.band as keyof typeof layout.band_patterns] : null;
  const dim = size ? { width: size, height: size } : {};
  return (
    <svg className="rc-cap-preview" viewBox={`${-vb} ${-vb} ${2 * vb} ${2 * vb}`} role="img" aria-label={title} {...dim}>
      <defs><clipPath id="rc-cap-disc"><circle r={r} /></clipPath></defs>
      <g transform="scale(1,-1)">
        <path d={discPath} className="rc-cap-preview__shell" fillRule="evenodd" clipPath="url(#rc-cap-disc)" />
        <path data-part="core" d={circle(0, 0, layout.core_r)} fill={scheme.accent.hex} />
        {bandPath ? <path data-part="band" d={bandPath} fill={scheme.accent.hex} fillRule="evenodd" /> : null}
        {centrePath ? <path data-part="centre" d={centrePath} fill={scheme.text.hex} fillRule="evenodd" /> : null}
        {iconPath ? <path data-part="icon" d={iconPath} fill={scheme.text.hex} fillRule="evenodd" /> : null}
        {glyphs.map((g, i) => (
          <g key={i} data-glyph={g.d} transform={`rotate(${g.theta + 90}) translate(0 ${-n.base_r})`}>
            <path d={g.path} fill={scheme.text.hex} stroke={scheme.text.hex} strokeWidth={n.stroke} strokeLinejoin="round" fillRule="evenodd" />
          </g>
        ))}
      </g>
    </svg>
  );
}
```

Placement check: `rotate(θ+90) translate(0, −base_r)` puts the glyph origin at radius `base_r` on angle θ (rotate(φ) maps (0, −b) to (b·sin φ, −b·cos φ) = (b·cos θ, b·sin θ) for φ = θ + 90°) with the glyph's +y pointing to −radial (tops toward the centre). At θ = 270° the glyph sits at (0, −b) unrotated: upright, reading left to right along the bottom. The stroke reproduces the 0.18 mm dilation the printer applies.

`cap-preview.css`:

```css
.rc-cap-preview { inline-size: 100%; block-size: auto; max-inline-size: var(--rc-content-max); }
.rc-cap-preview__shell { fill: color-mix(in srgb, var(--rc-sky) 22%, var(--rc-paper-bright)); stroke: color-mix(in srgb, var(--rc-stone) 60%, transparent); stroke-width: 0.2; }
```

(The scheme hexes are data from the catalog; `fill` attributes carry them, not CSS.)

- [ ] **Step 3: `pnpm test`** → PASS. **Step 4: Commit** `feat(editor): deterministic SVG cap preview from the generator layout`.

---

### Task 9: Editor, pickers, lock dialog, copy, demo page

**Files:**
- Create: `editor/src/cap-editor/cap-editor.tsx`, `pickers.tsx`, `lock-dialog.tsx`, `cap-editor.css`, `cap-editor.test.tsx`, `editor/src/copy/{hu,en}.ts` (extend), `editor/src/page.tsx`; modify `editor/src/main.tsx`

**Interfaces:**
- Produces:

```ts
export type CapEditorCopy = { title: string; schemeLabel: string; centreLabel: string; bandLabel: string; noneOption: string; iconGroup: string; patternGroup: string; free: string; priceTemplate: string /* "{amount}" */; lock: string; lockTitle: string; lockBody: string; lockConfirm: string; cancel: string; editAgainTemplate: string; requestReplacementTemplate: string; status: Record<CapStatus, string>; errors: Record<ClientError['code'], string>; walletLabel: string; walletAria: string; previewTitleTemplate: string /* "{serial}" */ };
export function CapEditor(props: { henId: string; client: CapDesignClient; catalog: Catalog; layout: Layout; copy: CapEditorCopy; locale: string }): JSX.Element;
```

- [ ] **Step 1: Failing tests `cap-editor.test.tsx`** (user-event; assert visible behaviour only)

```tsx
import { expect, test } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import catalog from './data/catalog.json';
import layout from './data/layout.json';
import { CapEditor } from './cap-editor.js';
import { createMockClient } from './mock-client.js';
import { en } from '../copy/en.js';
const hen = { henId: 'h1', serial: 67, scheme: 'classic', icon: 'heart', centre: null, band: null, status: 'draft' as const, designHash: '', proofUrl: null };
function setup(balance = 1000n, status: typeof hen.status = 'draft') {
  const client = createMockClient({ hens: [{ ...hen, status }], balance, catalog });
  render(<CapEditor henId="h1" client={client} catalog={catalog} layout={layout} copy={en.capEditor} locale="en-US" />);
  return client;
}
test('shows the wallet, the preview and the scheme options', async () => {
  setup();
  expect(await screen.findByRole('img', { name: 'Cap 67' })).toBeInTheDocument();
  expect(screen.getByLabelText('1,000 Golden Grain')).toBeInTheDocument();
  expect(screen.getByRole('radio', { name: /Meadow/ })).toBeInTheDocument();
});
test('locking a paid scheme asks for confirmation, charges, and locks', async () => {
  const client = setup(500n);
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: /Sunset/ }));
  await user.click(screen.getByRole('button', { name: en.capEditor.lock }));
  await user.click(screen.getByRole('button', { name: en.capEditor.lockConfirm }));
  await waitFor(() => expect(screen.getByText(en.capEditor.status.locked)).toBeInTheDocument());
  expect((await client.getWallet()).balance).toBe(200n);
  expect(screen.getByRole('button', { name: /Edit again/ })).toBeInTheDocument();
});
test('insufficient grain shows the mapped error and stays a draft', async () => {
  setup(10n);
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: /Meadow/ }));
  await user.click(screen.getByRole('button', { name: en.capEditor.lock }));
  await user.click(screen.getByRole('button', { name: en.capEditor.lockConfirm }));
  expect(await screen.findByRole('alert')).toHaveTextContent(en.capEditor.errors.INSUFFICIENT_GRAIN);
});
test('choosing a centre pattern clears the icon', async () => {
  setup();
  const user = userEvent.setup();
  await user.click(await screen.findByRole('radio', { name: /Rings/ }));
  expect(screen.getByRole('radio', { name: /Heart/ })).not.toBeChecked();
  expect(screen.getByRole('img', { name: 'Cap 67' }).querySelector('[data-part="centre"]')).not.toBeNull();
});
test('installed caps offer a replacement for the fee', async () => {
  setup(1000n, 'installed');
  expect(await screen.findByRole('button', { name: /Request a replacement/ })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: en.capEditor.lock })).toBeNull();
});
```

- [ ] **Step 2: Copy** — `src/copy/en.ts` exports `en = { shell: RealChickenCopy, capEditor: CapEditorCopy, wallet: GoldenGrainPillCopy }`; `hu.ts` the Hungarian twin. English values: `lock: 'Lock design'`, `lockConfirm: 'Lock and pay'`, `editAgainTemplate: 'Edit again ({amount})'`, `requestReplacementTemplate: 'Request a replacement ({amount})'`, `priceTemplate: '{amount}'`, `free: 'Free'`, `previewTitleTemplate: 'Cap {serial}'`, `status: { draft: 'Draft', locked: 'Locked — waiting for the print batch', batched: 'In the print batch', printed: 'Printed', installed: 'On the hen', replaced: 'Replaced' }`, `errors: { INSUFFICIENT_GRAIN: 'Not enough Golden Grain.', DESIGN_BATCHED: 'This cap is already in a print batch.', CATALOG_MISMATCH: 'That combination is not available.', NOT_EDITABLE: 'This cap cannot be changed right now.' }`. Hungarian: `'Rögzítés'`, `'Rögzítés és fizetés'`, `'Újraszerkesztés ({amount})'`, `'Csere kérése ({amount})'`, `'Ingyenes'`, `'{serial}. kupak'`, statuses `Piszkozat / Rögzítve — nyomtatásra vár / Nyomtatási kötegben / Kinyomtatva / A tyúkon / Lecserélve`, errors `Nincs elég aranymag. / Ez a kupak már nyomtatási kötegben van. / Ez a kombináció nem elérhető. / Ez a kupak most nem módosítható.`

- [ ] **Step 3: `pickers.tsx`** — one component:

```tsx
export function OptionGroup<T extends string | null>({ label, name, options, value, onChange, disabled }: {
  label: string; name: string; options: { id: T; title: string; badge?: ReactNode; swatch?: [string, string] }[]; value: T; onChange: (v: T) => void; disabled?: boolean;
}) {
  return (
    <fieldset className="rc-cap-options" disabled={disabled}>
      <legend className="rc-kicker">{label}</legend>
      <div className="rc-cap-options__grid" role="radiogroup" aria-label={label}>
        {options.map((o) => (
          <label key={String(o.id)} className="rc-cap-option" data-checked={o.id === value ? 'true' : undefined}>
            <input type="radio" name={name} className="rf-sr-only" checked={o.id === value} onChange={() => onChange(o.id)} aria-label={o.title} />
            {o.swatch ? <span className="rc-cap-option__swatch" aria-hidden="true" style={{ background: `linear-gradient(135deg, ${o.swatch[0]} 50%, ${o.swatch[1]} 50%)` }} /> : null}
            <span className="rc-cap-option__title">{o.title}</span>
            {o.badge ? <span className="rc-cap-option__badge">{o.badge}</span> : null}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
```

(`o.swatch` hexes come from catalog data; the inline style is data-driven, not a literal — add `// design-tokens-allow: catalog filament colours` on that line for the chirp hook.) `.rf-sr-only` does not exist in the package; define `.rc-cap-sr-only` in `cap-editor.css` and use it instead.

- [ ] **Step 4: `lock-dialog.tsx`** — `role="dialog" aria-modal`, `wrapDialogTabFocus` from `@chirpcoop/real-chicken-ui/dialog-focus` in `onKeyDown`, Escape → `onCancel`, shows `copy.lockBody`, the price (`GoldenGrainGlyph` + `formatGoldenGrain(price, locale)` or `copy.free`), the balance (`GoldenGrainPill`), buttons `copy.cancel` / `copy.lockConfirm` (disabled while `busy`). Classes `rc-cap-dialog__overlay`, `rc-cap-dialog`, `rc-cap-dialog__actions`, `rc-cap-btn`, `rc-cap-btn--primary`, `rc-cap-btn--ghost`, styled like `44-rename-modal.css` but with `--rc-*` vars only.

- [ ] **Step 5: `cap-editor.tsx`**

State: `design | null`, `wallet | null`, `busy`, `error: ClientError['code'] | null`, `dialogOpen`. On mount: `Promise.all([client.load(henId), client.getWallet()])`. Every option change: optimistic local update + `client.save` (debounce not needed: the mock is instant; keep a `saveSeq` ref to drop stale responses). Derived: `price = BigInt(scheme.price_grain)`; `editable = design.status === 'draft'`. Layout (all `.rc-panel` sections inside a `.rc-cap-editor` grid): preview panel (CapPreview + status line + proof `<img>` when `proofUrl`), options panel (scheme `OptionGroup` with swatches and price badges; centre group = `[none, ...icons, ...centre_patterns]` where choosing an icon sets `centre: null` and choosing a pattern sets `icon: null`; band group `[none, ...band_patterns]`), action bar (wallet pill; per status: draft → `lock` button opening `LockDialog`; locked → `editAgainTemplate` button with `useArmedConfirm` from `@chirpcoop/real-chicken-ui/armed-confirm` (first tap arms, second calls `unlockForEdit`); installed → replacement button with the same armed confirm; batched/printed/replaced → status only). Errors render in `<p role="alert" className="rc-inline-error">{copy.errors[code]}</p>`.

- [ ] **Step 6: `cap-editor.css`** — grid `.rc-cap-editor { display: grid; gap: var(--rc-card-gap); grid-template-columns: minmax(0, 1fr); } @media (min-width: 48em) /* design-tokens-allow: layout breakpoint */ { .rc-cap-editor { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); } }`; options grid `repeat(auto-fill, minmax(calc(var(--rc-tap) * 2.5), 1fr))`; `.rc-cap-option { min-block-size: var(--rc-tap); border: var(--rc-border-thin) solid color-mix(in srgb, var(--rc-wood) 40%, transparent); border-radius: var(--rc-radius-button); padding: var(--rc-space-sm); display: grid; gap: var(--rc-space-xs); justify-items: center; cursor: pointer; background: var(--rc-paper); } .rc-cap-option[data-checked='true'] { outline: var(--rc-focus-size) solid var(--rc-yolk); background: color-mix(in srgb, var(--rc-yolk) 14%, var(--rc-paper)); } .rc-cap-option:focus-within { outline: var(--rc-focus-size) solid var(--rc-pasture-strong); }`; swatch `inline-size: var(--rc-space-lg); block-size: var(--rc-space-lg); border-radius: var(--rc-radius-pill)`; buttons and dialog as in Step 4; `.rc-cap-sr-only` = the standard visually-hidden rule with `--rc-border-thin` sized box.

- [ ] **Step 7: Demo page `src/page.tsx` + `main.tsx`** — `RealChickenShell` with a top bar: locale toggle (HU/EN buttons), hen selector (three mock hens: 67 draft/heart, 8 locked/meadow/rings, 12345 installed/sunset/star with `proofUrl` = the committed `cad/out/proof_67.svg` copied to `editor/public/proof-sample.svg`), balance 1 000 grain. `main.tsx` imports `@chirpcoop/real-chicken-ui/styles.css`, `./cap-editor/cap-preview.css`, `./cap-editor/cap-editor.css`. Copy the sample proof: `cp ../cad/out/proof_67.svg public/proof-sample.svg` (the file is a test output; generate with `uv run --python 3.12 cap_marking.py 67 --icon heart --band stripes --proof out/proof_67.svg --skip-bambu` first).

- [ ] **Step 8: Run** `pnpm test`, `pnpm typecheck`, `pnpm build`; then `pnpm dev` and check in the browser: option changes redraw the preview instantly, lock flow charges, HU/EN toggle relabels everything, keyboard: Tab through options, Space selects, dialog traps focus. Fix what the browser shows. Then commit:

```bash
git add editor
git commit -m "feat(editor): cap editor with pickers, lock dialog, HU/EN copy and a demo page"
```

---

### Task 10: Documentation and closing checks

**Files:**
- Modify: `README.md`, `cad/README.md`, `DESIGN.md` (one paragraph + pointer), `docs/superpowers/specs/2026-09-14-hen-cap-customisation-design.md` (status line, add `fees` to §4 and the manifest position format to §5), `docs/lab/2026-09-10-thread-print-failure.md` is untouched; new `docs/lab/2026-09-14-cap-batch-plate.md` with the 36-cap slice numbers from Task 5 step 6.

- [ ] **Step 1: README** — new section "Per-hen cap customisation" (three sentences + the commands: `cap_marking.py 67 --icon sun --band dots`, `cap_batch.py fixtures/batch_sample.json`, `cd editor && pnpm dev`) and the editor's integration note. `cad/README.md`: files table rows for `catalog.json`, `cap_design.py`, `cap_svg.py`, `bambu_project.py`, `cap_batch.py`, `test_cap_batch.py`, `test_bambu_project.py`; a "Batch workflow" subsection (admin JSON → CLI → plate + manifest + proofs → print → proofs uploaded); pattern printability rules.
- [ ] **Step 2: Lab note** — per the CONTRIBUTING structure: what was sliced (36 caps, settings), the slicer's time and filament estimate, object count, warnings (expect none), UNVERIFIED: nothing printed yet.
- [ ] **Step 3: Full gate**

```bash
cd cad && dev-budget run --kind heavy -- uv run --python 3.12 hen_tag_enclosure.py && \
dev-budget run --kind heavy -- uv run --python 3.12 verify.py && \
dev-budget run --kind heavy -- uv run --python 3.12 test_cap_marking.py && \
dev-budget run --kind heavy -- uv run --python 3.12 test_bambu_project.py && \
dev-budget run --kind heavy -- uv run --python 3.12 test_cap_batch.py && \
dev-budget run --kind heavy -- uv run --python 3.12 slice_check.py
cd ../editor && dev-budget run --kind heavy -- pnpm test && pnpm typecheck && dev-budget run --kind heavy -- pnpm build
```

Expected: every suite exits 0. `git status` clean of stray outputs (only tracked artifacts changed).

- [ ] **Step 4: Commit and push**

```bash
git add -A README.md cad/README.md DESIGN.md docs
git commit -m "docs: cap customisation workflow, batch lab note"
git push origin main
```

---

## Self-review

- **Spec coverage**: §3 constraints → Tasks 2, 4, 5; §4 catalog → Task 1 (+ `fees`, added to the spec in Task 10); §5 contract → Tasks 1, 5; §6.1 → Tasks 2, 3; §6.2 → Tasks 4, 5; §6.3 → Task 5 step 4; §7.1–7.3 → Tasks 6–9; §7.4 map → `editor/README.md` (Task 6) ; §8 chirp side → out of scope by design; §9 errors → Tasks 5, 7, 9; §10 tests → every task; §11 out of scope honoured.
- **Placeholders**: none; every step carries code or an exact command.
- **Type consistency**: `build()` returns 9 values everywhere (Tasks 2, 5); `PlateCap.bodies` keys `shell/marking/core` match `BODY_EXTRUDER`; `CapDesign` fields identical across Tasks 7–9; `ClientError` codes identical in the mock and the copy; layout JSON keys identical in `cap_svg.py` and `cap-preview.tsx`; hash vectors identical in Python and TS tests.
