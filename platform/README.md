# Accessory Platform — Design Proposal (separate from the shipping design)

## Purpose & Status

Design for making the existing Rev B tag the mounting platform for a family of
accessories (decorative add-ons, villa builds, saddle integration) **without
changing anything the current tag already does**: LED ring window, coin
lettering, radial seal, screw cap, flat underside, harness tabs, mass budget.

- **Status: PROPOSAL. Nothing here has been printed or tested.**
- These files are deliberately separate. `../DESIGN.md` and
  `../cad/hen_tag_enclosure.py` are untouched; the current design remains the
  shipping design and works with or without the platform parts.
- Direction and welfare constraints follow a three-tier model: T1 always-worn
  accessories in the flock, T2 "villa wardrobe" builds only in the wellness
  villa, T3 functional mesh saddle. Active feather pecking exists in the
  flock; summer peaks hit 42 °C.

## Files

| File | Contents |
|---|---|
| [`collar.md`](collar.md) | The keeper collar: the one new load-bearing part. Clamshell ring that locks the cap and carries the bayonet mount. |
| [`accessories.md`](accessories.md) | Bayonet interface spec v0.1, hard safety envelope, T1 catalog (halo ring, flush medallion, low dome), T2 villa rules. |
| [`saddle-integration.md`](saddle-integration.md) | Mesh saddle with grommet window and the fabric-lock ring that registers it to the tag. |

## Architecture in one paragraph

A two-piece **keeper collar** clips around the cap skirt. It is keyed by the two
harness tabs (so it cannot rotate), rests on the tab shoulders, and hooks over
the cap rim with a lip that stops **outside** the lettering band — every printed
feature of the cap face stays visible. Clamping the skirt (plus ribs matching
the existing grip scallops) locks the cap against unscrewing. The collar's crown
carries a **quarter-turn bayonet** ring: accessories twist on and off with a
motion a beak cannot reproduce, and any torque they receive is routed
collar → tabs → body, never into the cap thread. With no accessory mounted the
tag looks almost exactly as it does today, plus a slim ring around the skirt.

## What must change on the current tag

**The cap: nothing, ever.** The personalised transparent cap (lettering, LED
window) is never modified and never replaced — this is a hard user
requirement. A first iteration put the collar's retention groove on the cap
OD; **rejected 2026-08-30** because it would have meant reprinting
personalised caps.

**The body gets one cut** — the `body_platform` variant
(`../cad/hen_tag_platform.py`, built and machine-checked, not yet printed):
a lateral retention groove on the base-flange OD (z −0.55…0.00, 0.5 deep,
root r 15.47). The collar's bottom bead enters it sideways as the clamshell
closes: positive up/down lock with zero flexing, and every accessory load
routes collar → body → harness, **bypassing the cap thread entirely** — which
also dissolves the original cap-unscrewing concern. The body is the generic
part: existing tags swap to a grooved body at a normal battery service and
the personal cap carries over unchanged; until then the collar fits existing
bodies in friction-only mode (bench work yes, deployment no).

Machine-verified on 2026-08-30: the variant removes 30.1 mm³, adds 0.0 mm³ —
thread, seal band, cavity, tabs, flat underside untouched; the collar coupon
shows 0.000 mm³ interference against both the grooved body and the cap, and
its lowest point stays 0.40 mm above the floor plane (it never touches the
hen). Optional Rev C nicety: 0.3 mm pad-seat recesses on the tab shoulder
ledges.

## Frozen interface (contract for every future revision)

Any revision that keeps these values stays collar-compatible. Values from
`hen_tag_enclosure.py` (Rev B):

| Parameter | Value | Why frozen |
|---|---|---|
| Cap skirt OD (`2*r_cap_out`) | 31.94 mm | collar bore, lip radius |
| Cap face height (assembled) | 8.70 mm | collar crown deck height |
| Rim edge zone | r 15.4–15.97 | lip lands here, outside lettering |
| Lettering band | r 12.5–15.4 | must stay uncovered |
| Clear LED ring | r 8.5–11.5 | optical keep-out for accessories |
| Grip scallops | 8 × 45°, R1.4 cutter, 0.25 deep | anti-rotation ribs mate these |
| Tab width (`tab_w`) | 13.00 mm | rotation key windows |
| Tab shoulder height | z = +2.20 (tab_top) | collar support pads land here |
| Slot span (`r_slot_in`–`r_slot_out`) | r 16.77–18.57 | elastic must stay clear |
| Tab span (`2*r_tab_out`) | 40.14 mm | saddle grommet sizing |
| Flat underside | 0 mm³ below floor plane | collar must also respect it |

## Safety inheritance

The welfare framework below gates everything here. Hard rules
repeated where they bite: no magnets; no part a peck can detach (bayonet +
detent, tool-release clamshell); no dangling elements; ≤5–10 g per accessory,
worn total target 25–30 g; muted matte colours in the flock (active pecking);
bright/tall builds only in the villa; bleach-only disinfection of PETG
(alcohol degrades FDM parts); collar and accessories are cheap consumables —
replace rather than scrub when soiled.

## Verification plan (before any hen wears any of this)

1. Print the collar fit coupon (defined in `collar.md`), then a full collar.
2. **Torque test**: measure the cap's break-loose torque; with collar fitted,
   apply 3× that torque to a mounted dummy accessory — cap must not move.
3. **Pull-off**: mounted accessory must survive ≥30 N axial pull
   (≈2× a hen's grab-peck force, 15 N literature value).
4. **Cycling**: 50 mount/dismount cycles, re-check detent and clamp.
5. **Elastic check**: thread the 8 mm elastic with collar fitted — zero
   interference through the slot windows.
6. Mass on the scale: collar ≤2.5 g target.
7. **RF A/B**: RSSI with and without collar (antenna location is unknown).
8. **Chemistry**: 24 h in 3 % bleach solution, re-test snap and detent.
9. Only then: on-hen habituation trial per the welfare protocol
   (2–7 days close watch), daily checks unchanged.

## Open questions

- Actual cap break-loose torque (bench, needed for the 3× margin).
- Whether friction-only cap lock suffices on unmodified Rev B caps, or the
  Rev C finer scallops are required for the positive lock.
- Antenna keep-out: no data; the RF A/B test answers whether the collar wall
  (PETG, ≥2 mm off the body wall) matters at all.
- Vet sign-off items and certifier notification per the welfare framework.
