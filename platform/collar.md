# Keeper Collar — Design (PROPOSAL, not printed)

The one new load-bearing part. A two-piece PETG ring that clips around the
assembled tag, locks the cap against turning open, and carries the quarter-turn
bayonet every accessory mounts on. Fits the unmodified Rev B tag.

## Cross-section (at a tab azimuth → window; elsewhere the wall is closed)

```
                bayonet ring, 3 J-slots          crown deck z 8.85…10.05
              ┌────┐                ┌────┐
              │    │   accessory    │    │       ← lugs twist in here
      ════════╪════╪════════════════╪════╪══════
   lip r15.55 ▄▄                          ▄▄     lip hooks over cap rim bevel
              │ ░░░░░░ cap face ░░░░░░░░ │       lettering ≤ r15.4: VISIBLE
              │                          │
      wall    │  cap skirt Ø31.94        │  wall r 16.22 … 17.77 (OD 35.54)
      ribs →  ▌  8 scallops, 0.25 deep   ▐  ← 8 inner ribs + clamp preload
              │                          │
              │      ┌────────────┐      │
   pad ▄▄▄▄▄▄▄│▄     │  WINDOW    │    ▄▄│▄▄▄▄▄  pads land on tab shoulders
   z=2.20     │      │ tab passes │      │       (ledges beside the slot ends)
   ┌──────────┴──────┤  through,  ├──────┴─────┐
   │   tab ░░░░░░░░░ │ slot+elastic░░░░░░░░░░░ │  slot r16.77–18.57: OPEN
   └─────────────────┴────────────┴────────────┘
        FLAT UNDERSIDE — collar never goes below it, never touches the hen
```

## How it holds — four constraints, none touching the closure

| Constraint | Feature | Load path |
|---|---|---|
| Rotation (its own) | two windows keyed on the 13.0 mm tabs (13.40 opening) | collar → tab flanks → body |
| Rotation (the cap's) | bonus only: spring finger clicking into a stock 0.25 grip scallop | cap → finger → collar → body |
| Down | support pads on the tab shoulder ledges at z = 2.20; deck lip 0.15 over the cap face | collar → tabs |
| Up | **bottom bead in a 0.5-deep lateral groove on the body's flange OD** (`body_platform` variant) | collar → groove → **body** → harness |

**Design corrections (2026-08-30).** (1) The Rev B tag has no upward-facing
undercut anywhere — deliberately snag-free — so friction alone cannot retain
the collar for deployment. (2) A first fix grooved the **cap** OD; rejected,
because the personalised transparent cap must never be modified or replaced.
The groove therefore lives on the **body flange** (z −0.55…0.00, root
r 15.47), and the collar wall now reaches down to z −0.60 — still 0.40 mm
above the floor plane, so the collar never touches the hen. The bead enters
the groove **laterally** as the clamshell closes: no snap-over, no flexing,
zero-fatigue positive lock, and all accessory loads bypass the cap closure
entirely — the original cap-opening concern dissolves. Machine-verified in
`../cad/hen_tag_platform.py`: body variant removes 30.1 mm³ / adds 0.0 mm³;
collar interference 0.000 mm³ vs. grooved body and vs. cap; lowest collar
point +0.40 mm above the floor plane. Existing (ungrooved) bodies take the
collar in friction-only mode for bench work; deployment wants the grooved
body, swapped at a battery service with the personal cap carried over.

The deck lip stops at r 15.55 — 0.15 mm outside the lettering band (≤ r 15.4),
so id, message and heart remain fully visible. The clear LED ring (r 8.5–11.5)
is nowhere near the collar.

Service order is forced and is a safety feature: **accessory off → collar
open → cap off**. The clamshell latch sits on the crown deck under the
bayonet ring, so a mounted accessory physically covers it; and the collar must
come off before the cap can be serviced, so the cap can never be opened by
anything that got past the accessory.

## Dimensions

| Feature | Value | Basis |
|---|---|---|
| Bore over skirt | r 16.22 (fit 0.25) | same class as `fit_lug_r` |
| Wall | 1.55 mm (r 16.22–17.77) | ≥3 perimeters at 0.4 nozzle |
| Collar OD | **35.54 mm** | still inside the 40.14 tab span |
| Height | z −0.60 → 11.65 (12.25 mm part) | bead zone to bayonet top; lowest point 0.40 above the floor plane |
| Crown deck | z 8.85–10.05 (t 1.20) | 0.15 clearance over cap face |
| Bayonet ring | r 16.2–17.8, 1.6 tall, on deck | see `accessories.md` |
| Rim lip | inner r 15.55, 0.55 engagement, 0.60 t | over the rim bevel |
| Windows | 2 ×, 13.40 wide, full height below deck | tab + elastic clearance |
| Support pads | 4 ×, ~1.8 × 2.0, land z 2.20 | on the ledges beside slot ends (slot is 8.8 long in a 13.0 tab → 2.1 mm ledge each side) |
| Retention bead | z −0.45…−0.10, 0.35 radial engagement, 0.10 axial play each way | mates the body flange groove |
| Spring finger | R1.2 bump, 0.30 proud, clicks a stock 0.25 scallop | bonus cap lock only |
| Mass | ~2.2 g (estimate, verify on scale) | PETG 1.27 g/cm³ |

## Two-piece clamshell

Two 180° halves, parting plane on the tab axis (through the windows). Each
half ends in a bridge over a window at deck level; the halves join there:
dovetail rail + a snap latch released by twisting a flat blade in a slot on
the deck top. Closing the halves preloads the bore onto the skirt (target
0.10–0.15 mm diametral interference → the friction component of the cap lock).

Why clamshell instead of one flexible ring: no ovalizing strain on layer
lines (PETG snap-fit L/t limits), each half prints in a strong orientation,
and mounting never drags anything across the O-ring, cap face or elastic.

Print: halves standing, parting face down candidates — decide at slicing; the
latch hook must load in compression, not layer peel. Layer 0.16, 3 perimeters,
same profile as the enclosure.

## Failure modes considered

- **Peck on the collar edge**: all outer edges ≥1 mm radius; the lip and deck
  overhang ≤0.6 mm — nothing a beak can get under.
- **Latch failure**: halves are individually captive on the tabs (windows) and
  under the lip; a failed latch loosens the clamp but the collar cannot leave
  the tag as one piece, and halves cannot slide off past the tabs. Degraded,
  not detached. Daily check catches it.
- **Torque overload** (snag on mesh, another hen): routed to tab flanks — the
  tab root carries harness load in tension across 13 mm already; torque adds
  shear at the same section. Bench item; if marginal, Rev C pad seats spread it.
- **Dirt trap** between wall and skirt: 0.25 gap, open at the windows; collar
  is removed at every battery service and is a cheap reprint — replace when
  soiled rather than scrub (FDM biofilm rule).

## Fit coupon

`coupon_collar`: a 120° wall segment (bore, bottom bead, spring finger,
deck + lip, bayonet blank), ~15 min print, mating `coupon_flangering` — a base
slice of the grooved body. Both are generated and exported by
`../cad/hen_tag_platform.py`. Settles bore fit and bead click before
committing to full halves — same philosophy as the closure coupons in
`../DESIGN.md`.

## UNVERIFIED

Everything. Specifically: skirt OD as-printed (design 31.94; Rev A printed
thread was confirmed, skirt OD was not measured), scallop depth as-printed,
cap break-loose torque, tab shear under torque, PETG clamp relaxation over
weeks outdoors, RF effect (antenna unknown).
