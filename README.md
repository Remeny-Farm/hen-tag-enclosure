# Hen Tag Enclosure

Parametric, 3D-printed enclosure for the Remeny Farm hen tag: a small
BLE activity tag worn by free-range laying hens under the farm's hen-patron
program. This repository holds the mechanical design only — the parametric
[build123d](https://build123d.readthedocs.io/) CAD source, the verification
and per-tag cap generators, and the physical evidence gathered from printing
and fitting it — as real solid-body CAD (STEP as well as STL), not a dead
triangle mesh.

## Hardware context

The tag is built around a **Holyiot 25008** module (Nordic **nRF54L15** SoC,
ST **LIS2DH12** accelerometer) powered by a **CR2032** coin cell. It is worn
by the hen on a figure-eight elastic harness through the enclosure's in-plane
side tabs, assembled and installed by farm staff following the documented
procedure. The electronics and firmware live in a separate, private
repository; this repository covers the mechanical enclosure only.

The design is welfare-first: the current (Revision B) model lands at
**10.92 g assembled**, conductive/carbon-fibre filament is strictly
prohibited (it detunes the 2.4 GHz antenna and creates an ESD/short hazard
against the exposed coin-cell terminals), and every geometry decision is
checked against interference, wall thickness and printability before it is
considered done. See [`docs/requirements.md`](docs/requirements.md) for the
full material and welfare-adjacent requirements this design has to satisfy.

## Goals

- **Durable, hen-safe enclosure** — a sealed transparent PETG housing (radial
  O-ring, target IP54-level dust/splash protection — not yet tested), no
  conductive filament, and a mass budget held close to a 10 g target.
- **Per-hen customizable cap** — [`cad/cap_marking.py`](cad/cap_marking.py)
  generates a deterministic, per-hen cap (id number, an optional short
  message, an icon) and exports it straight to a ready-to-slice, multi-colour
  Bambu Studio project.
- **Accessory platform** — [`platform/`](platform/) proposes a keeper collar
  and bayonet mount so decorative and functional accessories can be added
  without ever modifying or replacing the shipping cap. Proposal stage, open
  for contribution.
- **Community contributions** — parametric, machine-verified, test-covered
  source with dated physical lab notes and explicit verified-vs-unverified
  labeling, so outside contributors have a real basis to trust and extend the
  design. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Repository structure

| Path | Contents |
|---|---|
| [`DESIGN.md`](DESIGN.md) | Full mechanical design spec: decisions, verification results, print settings, open questions. |
| [`docs/requirements.md`](docs/requirements.md) | Source-of-truth requirements: materials, sealing/ingress target, conformal-coating protocol, form factor. |
| [`docs/lab/`](docs/lab/) | Dated lab notes: physical measurements, print trials, photo-based findings. |
| [`cad/`](cad/) | Parametric build123d source, the per-tag cap generator, the verification script, and the test suite. |
| [`cad/out/`](cad/out/) | Exported STL/STEP. Stable printables (body, cap, fit coupons) are committed; per-tag and debugging outputs are gitignored — see `cad/out/.gitignore`. |
| [`platform/`](platform/) | Accessory-platform **proposal**: keeper collar, bayonet interface spec, saddle integration. Not yet built. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to contribute: environment, verification requirements, lab-note style, accessory safety envelope. |
| [`LICENSE`](LICENSE) | MIT license. |

## Quickstart

Both CAD scripts carry [PEP 723](https://peps.python.org/pep-0723/) inline
dependencies, so `uv` resolves everything (build123d, bd_warehouse) on first
run. No virtualenv, nothing installed into the repository.

```sh
cd cad

# Build the enclosure and export STEP + STL to out/
uv run --python 3.12 hen_tag_enclosure.py

# 38 machine checks (interference, fit, bayonet, wall thickness, seal, harness) + half sections
uv run --python 3.12 verify.py

# Generate one hen's cap: id, optional message, icon
uv run --python 3.12 cap_marking.py 67 --top "Bözsi!" --icon heart

# Generator test suite (add --bambu for the full Bambu Studio export path)
uv run --python 3.12 test_cap_marking.py

# Real-slicer check: warnings + travels over open air (needs Bambu Studio)
uv run --python 3.12 slice_check.py

# Bambu Studio project with all four parts and the print settings baked in
uv run --python 3.12 slice_check.py --project   # -> out/hen_tag_revC_P1S.3mf
```

First run downloads the OCCT wheel (~60 MB) and a CPython 3.12 toolchain;
after that it is cached. `verify.py` exits non-zero on any failed check, so
it works as a pre-commit or CI gate. See [`cad/README.md`](cad/README.md)
for the full command reference, including re-checking a part against the
real slicer.

## Print settings

| Setting | Value | Why |
|---|---|---|
| Material | Transparent PETG | Impact resistance, UV stability, low moisture absorption; keeps the LED and lettering readable. |
| Nozzle | 0.40 mm | Thinnest wall in the design is 0.80 mm = 2 perimeters. |
| Layer height | 0.16 mm | The bayonet ramps and the O-ring groove need the resolution. |
| Perimeters | 3 | The bayonet lips make the skirt 5 lines thick in places. |
| Wall generator | **Arachne** | Variable-width walls absorb the lips as walls, not infill islands. |
| Avoid crossing walls | **On** | Routes travels over the print, not across the open bore; without it PETG strings the bore (58 → 3 crossing travels on the cap coupon). |
| Infill | 30 %+ | Parts are nearly all perimeter anyway. |
| Supports | None | Verified by slicing — all four parts return `Success.` with zero warnings. |
| Orientation | Already baked into the exported STLs | Drop them on the plate as-is; re-orienting the cap turns its top plate into a ~28 mm bridge. |

Or skip the settings altogether: [`cad/out/hen_tag_revC_P1S.3mf`](cad/out/hen_tag_revC_P1S.3mf)
is a Bambu Studio project with the four printables on one P1S plate and every
setting above already applied — open, slice, print.

Full rationale, tolerances and the slicer verification log are in
[`DESIGN.md`](DESIGN.md#print-settings).

## Design highlights

- **Radial seal, not an axial face seal** — the O-ring seals on a bore
  diameter instead of a compressed flange, which also removes ~1.7 g of pure
  overhead. [`DESIGN.md`](DESIGN.md#1-radial-seal-not-the-axial-face-seal)
- **Bayonet closure below the seal** — three lugs and self-locking helical
  ramps replace a thread whose ridges were thinner than one extrusion; every
  face on both parts prints without support, and the O-ring never crosses the
  lugs. [`DESIGN.md`](DESIGN.md#9-bayonet-not-a-thread)
- **Three-colour coin cap** — a deterministic per-hen cap with coin-style
  bent lettering, an accent-ring icon, and a clear shell so the LED needs no
  aligned window. [`DESIGN.md`](DESIGN.md#8-customer-cap-clear-shell-big-coin-lettering-accent-core)
- **Flat underside** — verified at 0.000 mm³ of material below the floor
  plane, so nothing presses on the hen but the harness itself.
  [`DESIGN.md`](DESIGN.md#7-in-plane-side-tabs-for-the-harness)
- **In-plane side tabs** — the harness elastic wraps a bar on two flat tabs
  in the plane of the base, which is what makes the flat underside possible.
  [`DESIGN.md`](DESIGN.md#7-in-plane-side-tabs-for-the-harness)

## Status

**v1 is Revision C geometry.** It is machine-verified — 38 checks in
`cad/verify.py`, all passing — but that is a claim about the model, not about
a worn device:

- **Revision A** was printed and fitted on a Bambu Lab P1S: dimensions good,
  and its thread mated on that one pair. Later caps tore along the thread,
  whose ridges compute to less than one extrusion wide, so revision C
  replaced it with a bayonet.
- **Revision B's body** has also been printed and accepted the board in its
  intended orientation, and revision B sliced clean in Bambu Studio.
- **Revision C's bayonet** slices clean and its coupon pair has been printed
  once: dimensions good, lock-up angle not yet reported. The full cap, the
  complete sealed assembly and the harness tabs under load remain untested —
  no O-ring has been compressed, no water has touched it, and no elastic has
  loaded a tab.
- **No hen has worn this device.**

See [`DESIGN.md`](DESIGN.md#verified-evidence-vs-working-hypotheses) for the
full verified-vs-unverified breakdown and the open questions blocking the
next print.

## Animal welfare

The tag is worn continuously by a live animal, so mass and fit are treated as
hard constraints, not just engineering targets. At ~10.9 g assembled the
device is a small fraction of a laying hen's typical body mass — well inside
commonly cited bio-logging guidance of keeping an attached device under
roughly 3 % of body mass — though `DESIGN.md` is explicit that whether the
project's own 10 g figure is a hard welfare limit or a design aspiration is
still an open decision, not yet resolved. The design avoids magnets, sharp
edges and anything a beak could catch or detach; production tags are
assembled and fitted by farm staff, with daily visual checks as part of
normal husbandry. This is not a consumer product for end users to assemble
or fit themselves.

## Accessory platform

[`platform/`](platform/) is a **design proposal**, not a shipping feature:
nothing in it has been printed or tested, and the current shipping design
(`DESIGN.md`, `cad/hen_tag_enclosure.py`) is untouched by it. It describes a
keeper collar and quarter-turn bayonet mount for a family of accessories —
decorative rings, villa-only builds, a mesh saddle — without ever modifying
the personalised cap. It is open for contribution; see
[`platform/README.md`](platform/README.md) for the architecture and
[`platform/accessories.md`](platform/accessories.md) for the hard safety
envelope every accessory design must satisfy.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development environment,
what has to pass before a PR (generators, `verify.py`, the test suite), how
physical evidence is recorded, and the accessory safety envelope.

## License

MIT. See [`LICENSE`](LICENSE).
