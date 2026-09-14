# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Batch JSON (hen-cap-batch/1) -> one Bambu plate, a manifest and proofs.

    uv run --python 3.12 cap_batch.py batch.json [--out out/plates] [--no-slice]

The batch file is what the app's admin page downloads: one colour scheme,
up to 36 caps, each fully described by serial, icon / centre pattern, band
pattern and its design hash. Outputs, all named so they match back without a
database:

    plate_<batch_id>_P1S.3mf        Bambu Studio project, 6 x 6 grid, AMS 1 clear
                                    / 2 text / 3 accent, print settings baked in
    plate_<batch_id>_manifest.csv   position, serial, hen name, design hash
    proof/<design_hash>.svg         top view in the scheme colours, one per cap

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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bambu_project import PLATE_MAX, grid_label, grid_positions, write_plate  # noqa: E402
from cap_design import ids, load_catalog, validate_design  # noqa: E402

BATCH_SCHEMA = "hen-cap-batch/1"


def validate_batch(batch: dict, cat: dict) -> list[str]:
    errs = []
    if batch.get("schema") != BATCH_SCHEMA:
        errs.append(f"unsupported batch schema {batch.get('schema')!r}")
    if batch.get("generator_version") != cat["generator_version"]:
        errs.append(f"generator_version {batch.get('generator_version')!r} != catalog "
                    f"{cat['generator_version']!r}: deploy the same catalog on both sides")
    if batch.get("scheme") not in ids(cat, "schemes"):
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


def build_bodies(c: dict, cap_solid, cache: Path) -> tuple[dict, dict, bool]:
    """(canonical meshes by body, 2D sketches, from_cache)."""
    key = cache / c["design_hash"]
    if (key / "bodies.pkl").exists() and (key / "sketches.pkl").exists():
        return (pickle.loads((key / "bodies.pkl").read_bytes()),
                pickle.loads((key / "sketches.pkl").read_bytes()), True)
    import build123d as bd
    from cap_marking import DEPTH_DEFAULT, build, canonical_mesh
    icon = c["icon"] or "none"
    _, shell, inlay, core_body, mk, core, _, _, _ = build(
        str(c["serial"]), "", icon, DEPTH_DEFAULT, centre=c["centre"], band=c["band"], cap=cap_solid)
    dz = -(bd.Rot(180, 0, 0) * shell).bounding_box().min.Z
    bodies = {}
    for name, solid in (("shell", shell), ("marking", inlay), ("core", core_body)):
        oriented = bd.Pos(0, 0, dz) * (bd.Rot(180, 0, 0) * solid)
        bodies[name] = canonical_mesh(oriented, f"{c['serial']}:{name}")
    sketches = {"mk": mk, "core": core}
    key.mkdir(parents=True, exist_ok=True)
    (key / "bodies.pkl").write_bytes(pickle.dumps(bodies))
    (key / "sketches.pkl").write_bytes(pickle.dumps(sketches))
    return bodies, sketches, False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch", help="hen-cap-batch/1 JSON from the admin page")
    ap.add_argument("--out", default=str(HERE / "out" / "plates"))
    ap.add_argument("--no-slice", action="store_true",
                    help="skip the Bambu Studio slice check of the finished plate")
    a = ap.parse_args()
    cat = load_catalog()
    batch = json.loads(Path(a.batch).read_text())
    errs = validate_batch(batch, cat)
    if errs:
        print("batch refused:")
        for e in errs:
            print(f"  - {e}")
        return 1

    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cache = HERE / "out" / "cache"
    proof_dir = out / "proof"
    proof_dir.mkdir(exist_ok=True)
    scheme = next(s for s in cat["schemes"] if s["id"] == batch["scheme"])
    print(f"batch {batch['batch_id']}: {len(batch['caps'])} caps, scheme {scheme['id']} "
          f"(text {scheme['text']['filament']}, accent {scheme['accent']['filament']})")

    from cap_marking import FOAM_INNER
    from cap_svg import write_proof
    from hen_tag_enclosure import P, build_cap
    cap_solid = None
    plate_caps, rows, hits = [], [], 0
    for pos, c in zip(grid_positions(len(batch["caps"])), batch["caps"]):
        cached = (cache / c["design_hash"] / "bodies.pkl").exists()
        if not cached and cap_solid is None:
            cap_solid = build_cap(P, foam=FOAM_INNER)    # one shell for the whole batch
        bodies, sketches, hit = build_bodies(c, cap_solid, cache)
        hits += hit
        write_proof(proof_dir / f"{c['design_hash']}.svg", sketches["mk"], sketches["core"], scheme)
        plate_caps.append({"name": f"cap_{c['serial']}", "position": pos, "bodies": bodies})
        rows.append((grid_label(pos), c["serial"], c.get("hen_name", ""), c["design_hash"]))
        print(f"  cap {c['serial']:>5} at {rows[-1][0]}  {'cache' if hit else 'built'}")

    plate = out / f"plate_{batch['batch_id']}_P1S.3mf"
    write_plate(plate, plate_caps, scheme, batch["batch_id"])
    with open(out / f"plate_{batch['batch_id']}_manifest.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["position", "serial", "hen_name", "design_hash"])
        w.writerows(rows)
    print(f"wrote {plate.name}, manifest, {len(rows)} proofs ({hits} from cache)")
    if a.no_slice:
        return 0
    r = subprocess.run(["uv", "run", "--python", "3.12", str(HERE / "slice_check.py"), str(plate)],
                       cwd=HERE)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
