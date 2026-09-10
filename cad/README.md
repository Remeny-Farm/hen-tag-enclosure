# Enclosure CAD

Parametric source for the hen tag enclosure. Solid B-rep modelling via
[build123d](https://build123d.readthedocs.io/) on the OCCT kernel, so the output
is real CAD geometry with true fillets and helical sweeps, exported as **STEP as well
as STL** — the model stays editable in FreeCAD or any other CAD tool rather than
being a dead triangle mesh.

## Running

Both scripts carry PEP 723 inline dependencies, so `uv` resolves everything on
first run. No virtualenv, and nothing is installed into the repository.

```sh
uv run --python 3.12 hen_tag_enclosure.py   # build + export to out/
uv run --python 3.12 verify.py              # 38 machine checks + half sections
uv run --python 3.12 slice_check.py         # real-slicer check, needs Bambu Studio
```

First run downloads the OCCT wheel (~60 MB) and a CPython 3.12 toolchain; after
that it is cached. `verify.py` exits non-zero when a check fails, so it works as
a pre-commit or CI gate.

**STLs are exported already lying in their print orientation** — the cap and the
female coupon are flipped top-plate-down on export. Drop them on the plate as
they are; re-orienting the cap makes its top plate a ~28 mm bridge. The STEP
files keep the design coordinate system so the model stays readable in CAD.

`slice_check.py` re-checks printability against the real slicer: it runs the
Bambu Studio CLI on the four printables with the P1S 0.4 mm machine, the
0.16 mm process, PETG Basic, and the three settings `../DESIGN.md` asks for
(3 walls, Arachne, avoid crossing walls), then reads the G-code back and
counts travel moves that fly across open air — the bore of the cap, the cavity
and cell pocket of the body — where PETG leaves a string. It fails on a slicer
warning or when a count exceeds a limit set just above the 2026-09-10 numbers.
`--stock` slices with the untouched Bambu profile for comparison, `--keep`
leaves the G-code in `out/slice/`. Skips with exit 0 when Bambu Studio is not
installed.

## Per-tag cap markings — the deterministic tag generator

```sh
uv run --python 3.12 cap_marking.py 67 --top "Bözsi!" --icon heart
uv run --python 3.12 cap_marking.py 12345 --icon star
uv run --python 3.12 cap_marking.py 133 --icon flower --font tahoma
uv run --python 3.12 test_cap_marking.py            # test suite; --bambu for the full path
```

This is the back end for the customer design UI. The inputs are exactly the
customer-facing choices, everything else is fixed:

| Input | Envelope |
|---|---|
| number | **required**, 1–5 digits, bottom arc, 6.0 pt |
| `--top` message | ALL CAPS coin lettering at 5.2 pt; letters incl. Hungarian (ő/ű), digits, space, `.:!?'"+-`; **guaranteed-safe length: 8 characters** (all-'W' worst case), typical texts fit ~11–13 — over-length is rejected with the measured span |
| `--icon` | `heart` / `star` / `flower` / `none` — parametric shapes in the centre |
| `--font` | curated list: verdana (default), tahoma, arial, futura, din, rounded |

**Layout (second print-driven revision): the whole shell is CLEAR PETG.** The
first trial printed the lettering at a 2.9 mm band and it was unreadable, and
the product look wanted a transparent body anyway. With the shell clear, the
dedicated LED window disappears — the LED shines through wherever it lands, so
there is nothing to align — and the lettering band grows to ~6 mm: double the
letter height, at the price of a shorter message. The centre is a full
**accent disc** (Ø17.2) in the third colour with the icon cut out of it and
inlaid in the text colour — the two colours meet edge to edge, no clear gap.

| Slot | Body | Filament |
|---|---|---|
| 1 | `cap_<n>` | the whole shell — **clear PETG** |
| 2 | `marking_<n>` | lettering + icon, text colour (0.64 mm flush inlay) |
| 3 | `core_<n>` | accent disc, the icon cut from it (0.64 mm flush inlay) |

Deterministic by design: **font sizes are fixed**, misfits are rejected with
measured numbers, and identical input produces **byte-identical** output
(canonically ordered welded meshes, deterministic STL writer, fixed zip
timestamps) — a regenerated tag can be diffed against a shipped one.

Envelope rules the test suite forced: the message is uppercased (a lowercase
descender plus an accented capital outgrows any printable band height, while
accented capitals alone fit), and comma/semicolon/parentheses are excluded
from the charset for the same below-the-baseline reason.

The deliverable for the P1S is **`out/cap_<n>_P1S.3mf`** — a Bambu Studio
project with the three bodies as parts of ONE object (`--assemble` via the
Bambu CLI, so nothing can be arranged apart or dragged out of register) and
the filament slots pre-assigned. Open it, load the project settings, put clear
PETG in AMS slot 1, the text colour in 2, the accent colour in 3, slice. Each
part's `extruder` is patched into `Metadata/model_settings.config`, the
assembler's per-part recentring is undone with measured translations, and the
result is verified numerically against the source solids plus round-tripped
through the CLI. Needs `/Applications/BambuStudio.app`; without it only the
vendor-neutral `cap_<n>.3mf` + per-part STLs are written (assign filaments by
hand in other slicers).

Because the cap prints top-plate-down, all three bodies meet in the first
layers against the plate; the outer face comes out as one smooth plane. There
is no clear layer over or under the inlays — the first layer is already the
final colour. A washed-out colour means the coloured PETG itself is
translucent at 0.64 mm: deepen with `--depth` (up to 0.80) at the cost of
thinner cover above.

The 3MF is written by the script itself: one mesh object per body (libraries
explode the glyphs into a dozen objects), tessellation **welded** (OCCT
duplicates vertices per face; 3MF importers trust the index buffer and the
cracks sliced into "floating region" warnings) and refused if any non-manifold
edge remains. Lettering defaults to **Verdana** with the full Hungarian glyph
set; hairline strokes are lifted by dilation and any printable feature under
0.58 mm is refused. Icons are parametric geometry, no emoji fonts. The cap's
closure, seal and envelope are untouched — `build_cap()` is imported, not
copied.

## Files

| File | Role |
|---|---|
| `hen_tag_enclosure.py` | All geometry. `Params` at the top holds every dimension. |
| `verify.py` | Interference, fit, bayonet, wall thickness, seal and harness checks. |
| `slice_check.py` | Real-slicer check: warnings and open-air travel counts per part; `--project` writes the ready-to-print Bambu project. Needs Bambu Studio. |
| `out/hen_tag_revC_P1S.3mf` | Bambu Studio project: body, cap and both coupons on one P1S plate, print settings baked in. |
| `cap_marking.py` | Deterministic per-tag cap generator (number, message, icon, font). |
| `test_cap_marking.py` | Generator test suite: envelope, rejections, determinism. |
| `out/body.stl` / `.step` | Main housing. |
| `out/cap.stl` / `.step` | Bayonet cap. |
| `out/coupon_*.stl` | Bayonet + groove fit coupons. Print these first: the bayonet has not been printed anywhere yet. |
| `out/section_*.stl` | Half sections, for looking at the internals only. |

## Changing dimensions

Every dimension lives in the `Params` dataclass. Derived values — groove depth,
lug and lip stations, cap diameter, Z stations — are computed properties, so changing
one input propagates correctly instead of leaving stale constants behind.

The values most likely to need correcting, all currently UNVERIFIED:

```python
pcb_env_h  = 2.0    # full board envelope; see the height ambiguity in the lab note
holder_h   = 4.0    # holder + seated cell, off the PCB face
oring_cs   = 1.50   # measure the ring you actually have
strap_w    = 8.80   # slot length; measure the elastic you actually have
strap_t    = 1.80   # slot width, along the spine
foam_id    = 16.0   # LED window through the foam ring
```

Board orientation is **holder down, PCB up** — the LED has to look out through
the cap, not at the bird. `cell_fill()` builds the crescent that retains the
holder; `strap_tabs()` builds the in-plane side tabs; `body_lugs()` and
`cap_channels()` build the two halves of the bayonet, both from one helical
sweep helper so their bearing faces share a pitch.

After any change, re-run `verify.py` before printing. It is what caught the
assembly-path defect described in `../DESIGN.md`.

## Bayonet fit

Print the coupons and note where the cap stops turning freely. Nominal is 30°
clockwise from the entry slots; anywhere from about 5° to 55° still locks. Then
adjust and regenerate — do not file the parts:

```python
cam_lock   = 30.0   # deg of rotation to nominal contact: raise if it locks early, lower if late
fit_lug_r  = 0.15   # radial clearance, lug crest to channel root: raise if the lugs bind
fit_lug_z  = 0.30   # axial clearance, lug top to channel ceiling
cam_rate   = 0.012  # ramp rise per degree; lower for a longer, softer tightening
```

Note for anyone extending this: the cap is modelled in its **locked** pose, so
the cap solid is already the assembled one. `verify.py` turns it back toward
the entry angle (`pose(phi)`) to prove the drop-on, the free run and the wedge.
Lugs and lips are swept along helices of the same pitch; change `cam_rate` and
both follow.
