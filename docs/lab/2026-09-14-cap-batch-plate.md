# Lab Note: 36-Cap Batch Plate Sliced

- **Date**: 2026-09-14
- **Author**: Hen-Tag Engineering
- **Status**: Completed (slicer) / UNVERIFIED in print (no plate printed)

---

## Purpose & Objective

Prove that one batch of locked cap designs — one colour scheme, as many
caps as fit — comes out of `cad/cap_batch.py` as a single Bambu Studio
project that slices whole, and record what the slicer estimates for a full
plate.

---

## Verified Evidence (slicer only)

Generated from a synthetic 36-cap batch (every icon, every band pattern,
five centre patterns, serials 100…4895) with `cap_batch.py` and sliced by
Bambu Studio 02.08.02.60 through the CLI:

| | |
|---|---|
| Caps on the plate | **36** (6 × 6, pitch 36 mm, centres 38…218 mm) |
| Objects in the G-code | **36** |
| Layers | 37 at 0.16 mm (cap height 7.40 mm) |
| Estimated print time | **4 h 13 m** |
| Slicer warnings / errors | 0 |
| `max_cantilever_dist` | 66 968 (the O-ring groove ceiling, as on every cap since revision A) |
| Build time on the Mac | ~4 min for 36 caps (one shared shell, bodies cached per design hash) |
| Plate file | 6.6 MB |

A second run of the same batch is byte-identical (`test_cap_batch.py`), and
the 3-cap fixture plate slices to 3 objects.

## Reported / Measured

Two Bambu Studio behaviours found while making the writer, both bisected on
a two-cube plate:

1. **Application metadata decides everything.** A package whose
   `3D/3dmodel.model` does not name `BambuStudio-…` as its Application is
   loaded as a "3mf from other vendor": project settings are ignored, the
   plate defaults to 200 × 200 mm and caps beyond it are dropped without a
   message (26 of 36 sliced). The writer now names the Bambu version its
   settings template was exported from.
2. **Per-filament arrays must stay as Bambu exported them.** The template
   carries three `filament_settings_id` entries but one `filament_colour`
   and one `filament_type`. Widening `filament_colour` to three makes the
   CLI's G-code export fail silently; widening `filament_type` floods the
   log with `group_nozzle_info` errors. Every other edit (walls, Arachne,
   avoid crossing walls, plate area) passes.

## Technical Interpretation

- The CLI slice contains **no tool changes** for any three-body project —
  including Bambu Studio's own export of the single cap, `cap_67_P1S.3mf`.
  The CLI cannot prove the three-colour assignment; the GUI does the AMS
  mapping when the project is opened, which is the operator's existing
  workflow for the single-cap projects. Per-part extruders 1/2/3 are in the
  plate's `model_settings.config` exactly as in the CLI-exported reference.
- Colour changes happen only in the first four layers (the 0.64 mm inlays
  print first, the cap is top-plate-down), so a full plate costs the same
  number of filament changes as one cap; the 4 h 13 m estimate is the
  single-filament CLI figure and excludes the changes.

## Key Decisions

1. `slice_check.py` accepts a plate and reports objects, warnings and the
   slicer's estimate; `cap_batch.py` runs it after every batch.
2. The filament colours of a scheme are recorded in `catalog.json`, the
   manifest and the README, not in the project file.

## Addendum, same day: four bodies per cap

The colour model changed to a base-coloured shell with a clear LED window
and two free colours assigned per zone (spec §2/§3). Each cap is now four
bodies (shell, window, a, b) on AMS 1–4; the settings template was
re-exported from Bambu Studio with four filaments loaded. The 3-cap fixture
plate slices to 3 objects in **21 m 10 s** (≈ 7 min per cap, consistent with
the 36-cap estimate above); no warnings. Every motif in `cad/cap_motifs.py`
(26 icons, 16 patterns) passes `check_motifs.py`. Still UNVERIFIED in print.

## Open Questions & Verification Items

1. **Print one plate.** Confirm in Bambu Studio that the three parts of one
   cap map to AMS 1/2/3, that the plate preview shows 36 caps at 38…218 mm,
   and that a printed cap from the plate matches its proof SVG.
2. Measure the real plate time and filament use; the CLI estimate carries no
   colour-change time.
3. Check whether a newer Bambu Studio accepts three `filament_colour`
   entries so the plate can carry the scheme colours itself.
