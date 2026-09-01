# Bayonet Interface v0.1 + Accessory Rules (PROPOSAL)

The single mounting standard every accessory uses. Lives on the keeper
collar's crown (`collar.md`); the tag itself is never touched by accessories.

## Quarter-turn bayonet — female side (on the collar crown)

| Feature | Value |
|---|---|
| Ring | r 16.2–17.8, 1.6 mm tall, on the crown deck |
| Slots | 3 × J-slots at 120°, entry gap 20° wide |
| Travel | 60° to seat |
| Ramp | 0.8 mm axial rise (pulls the accessory down as it turns) |
| Detent | 0.25 mm bump before the seat; tactile click, holds against wind-back |
| Land | 1.2 mm bearing surface per slot |

Male side (on every accessory): 3 lugs, 2.4 × 1.6 × 1.2 mm, chamfered lead.
Fits: entry clearance 0.25, seated interference at the detent 0.05–0.10.
The mounting motion is *press + twist 60°* — a beak produces pull, pry and
torque-on-snag, none of which reproduces press-then-rotate past a detent.

Publish this section + a printable test coupon as the open spec
(Framework-style): envelope, tolerances, the safety envelope below as hard
pass/fail, CC-licensed reference accessory. Patron-submitted designs are
printed by the farm only after passing the checklist.

## Hard safety envelope — every accessory, no exceptions

1. One rigid piece (or permanently bonded); nothing a peck can separate.
2. No magnets. No zinc-plated or galvanized metal. Preferably no metal at all.
3. No dangling, swinging or flexible protruding elements.
4. All edges ≥1 mm radius; no points.
5. Mass ≤5 g (T1) — weighed, not estimated.
6. Height above the crown deck ≤6 mm (T1).
7. Optical keep-out: the cylinder over the clear LED ring (r 8.5–11.5) stays
   open or is bridged only by clear PETG.
8. Flock wear: matte, muted colours only — active feather pecking in this
   flock; saturated red and gloss/mirror finishes are refused.
9. Survives 3 % bleach soak; no paint, no coatings that flake.
10. Passes the pull-off (≥30 N) and torque (3× cap break-loose) bench tests.

## T1 catalog — always-worn, in the flock

| Accessory | What it is | Est. mass | Height over deck |
|---|---|---|---|
| **Halo ring** | Coloured ring, OD ~40, frames the cap face; the patron's colour reads at 3–5 m | ~3 g | 2 mm |
| **Flush medallion** | Full-face disc with relief motif, clear window over the LED ring, seasonal/patron themes | ~2.5 g | 1.5 mm |
| **Low dome** | Rounded "hat" silhouette, recognizable at distance | ~4 g | 6 mm |

All three print in the existing three-filament pipeline; per-patron variants
can reuse the deterministic `cap_marking.py` approach (same font/arc rules) on
the accessory face, so the cap id and the accessory never disagree.

## T2 — villa wardrobe (only in the wellness villa)

The villa (hen alone, no flockmates, livestream running) lifts the two flock
vetoes that ban builds: nothing can be pecked off *by another hen* and
swallowed, and bright colours attract no one. Rules that remain:

- Base is the **stage plate**: bayonet male base carrying stud-array top
  ("building-block compatible" wording only; no brand names/logos on parts).
  Studs are for build-time creativity; the plate itself locks with the same
  bayonet + detent.
- Relaxed limits: height ≤25 mm, mass ≤10 g, colours free.
- Self-risk remains (the hen can reach her own back when preening): builds
  use large-format bricks (DUPLO scale), click-checked by staff.
- SOP: staff mounts entering the villa, dismounts on exit, **piece count in =
  piece count out**, logged; bleach-wipe between guests.
- Never worn back into the flock, even briefly.

## Bench tests (per accessory design, before catalog entry)

Pull-off ≥30 N; torque per `README.md`; 50 mount cycles; drop from 1 m onto
concrete (no fragmentation — PETG, not PLA, partly for this); weigh; bleach
soak 24 h; photo legibility at 3 m and 5 m through the run fence.
