# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Slice the printables with the real slicer and count what the model cannot see.

`verify.py` proves the geometry; this proves the toolpath. Bambu Studio's CLI
slices each exported STL with the P1S 0.4 mm machine, the 0.16 mm process and
the PETG Basic filament, plus the three process settings DESIGN.md asks for
(3 walls, Arachne, avoid crossing walls), and the G-code is then read back for:

  1. slicer warnings, and its `max_cantilever_dist` metric: 0 for the body
     since revision A; ~65 000 for the cap, which is the O-ring groove
     ceiling and has been identical from revision B to C
  2. travel moves that fly across OPEN air, where PETG leaves a string:
       cap / coupon_cap  across the bore, above the top plate
       body / coupon_body  across the cavity above the cell fill, and across
                           the cell pocket

The bayonet lips are three islands per layer, so a few travels are inherent;
the limits below are calibrated to the 2026-09-10 numbers (see the lab note)
and exist to catch a regression, not to demand zero. Pass --stock to see what
the untouched Bambu profile does instead, and --keep to leave the G-code in
out/slice/ for inspection.

--project writes out/hen_tag_revC_P1S.3mf instead: a Bambu Studio project
with all four printables on one plate and the three settings already applied,
so a maker can open it and print without touching a single setting.

Skips cleanly (exit 0, one line) when Bambu Studio is not installed.
"""

import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).parent / "out"
APP = Path("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
PROFILES = Path("/Applications/BambuStudio.app/Contents/Resources/profiles/BBL")
MACHINE = PROFILES / "machine/Bambu Lab P1S 0.4 nozzle.json"
PROCESS = "0.16mm Optimal @BBL X1C"
FILAMENT = PROFILES / "filament/Bambu PETG Basic @BBL X1C.json"

# The three settings that make the bayonet print clean. Everything else is the
# stock Bambu profile.
RECOMMENDED = {
    "wall_loops": "3",              # the lip region is 5 lines wide; 3 walls + gap fill
    "wall_generator": "arachne",    # variable-width walls absorb the lips as walls
    "reduce_crossing_wall": "1",    # route travels over the print, not across the bore
}

# Where open air is, per part, in PRINT coordinates (z from the bed).
#   (label, centre offset x, y, radius, z_lo, z_hi)  -- travels within `radius`
#   of that centre between those heights are counted.
from hen_tag_enclosure import P  # noqa: E402

_p = P
OPEN_AIR = {
    "cap": [("bore above the top plate", 0.0, 0.0, 12.0, _p.cap_top_t + 0.05, 99.0)],
    "coupon_cap": [("bore", 0.0, 0.0, 12.0, 0.0, 99.0)],
    "body": [("cavity above the cell fill", 0.0, 0.0, 12.0,
              _p.floor_t + _p.z_fill_top + 0.05, 99.0),
             ("cell pocket", _p.holder_offset, 0.0, _p.r_pocket - 1.0,
              _p.floor_t, _p.floor_t + _p.z_fill_top + 0.05)],
    "coupon_body": [("bore", 0.0, 0.0, 12.0, _p.floor_t + 0.05, 99.0)],
}
# Travels across open air with the recommended settings, 2026-09-10, plus margin.
LIMIT = {"cap": 40, "coupon_cap": 12, "body": 100, "coupon_body": 20}
# max_cantilever_dist: the groove ceiling on the cap parts, nothing on the body.
CANTILEVER_LIMIT = {"cap": 70000, "coupon_cap": 70000, "body": 0, "coupon_body": 0}


def flatten(name: str) -> dict:
    d = json.load(open(PROFILES / "process" / f"{name}.json"))
    base = flatten(d["inherits"]) if "inherits" in d else {}
    base.update({k: v for k, v in d.items() if k != "inherits"})
    return base


def slice_part(stl: Path, overrides: dict, workdir: Path) -> tuple[Path | None, str]:
    prof = flatten(PROCESS)
    prof.update(overrides)
    prof["name"], prof["from"] = "hen_tag_check", "User"
    pj = workdir / "process.json"
    json.dump(prof, open(pj, "w"))
    r = subprocess.run(
        [str(APP), "--debug", "4", "--load-settings", f"{MACHINE};{pj}",
         "--load-filaments", str(FILAMENT), "--slice", "0",
         "--outputdir", str(workdir), str(stl)],
        capture_output=True, text=True)
    g = workdir / "plate_1.gcode"
    return (g if g.exists() else None), r.stdout + r.stderr


def moves(gcode: Path):
    """(z, x0, y0, x1, y1, extruding) for every XY move, arcs included."""
    out = []
    x = y = z = None
    for ln in open(gcode, errors="replace"):
        m = re.match(r"; Z_HEIGHT: ([\d.]+)", ln)
        if m:
            z = float(m.group(1))
            continue
        if not re.match(r"G[0123] ", ln):
            continue
        nx = re.search(r"X(-?[\d.]+)", ln)
        ny = re.search(r"Y(-?[\d.]+)", ln)
        e = re.search(r"E(-?[\d.]+)", ln)
        if not (nx and ny):
            continue
        x1, y1 = float(nx.group(1)), float(ny.group(1))
        if x is not None and z is not None:
            out.append((z, x, y, x1, y1, bool(e and float(e.group(1)) > 0)))
        x, y = x1, y1
    return out


def seg_dist(x0, y0, x1, y1, cx, cy) -> float:
    dx, dy = x1 - x0, y1 - y0
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(x0 - cx, y0 - cy)
    t = max(0.0, min(1.0, ((cx - x0) * dx + (cy - y0) * dy) / l2))
    return math.hypot(x0 + t * dx - cx, y0 + t * dy - cy)


def open_air_travels(mv, zones):
    ext = [m for m in mv if m[5]]
    cx = (min(m[3] for m in ext) + max(m[3] for m in ext)) / 2
    cy = (min(m[4] for m in ext) + max(m[4] for m in ext)) / 2
    per_zone = defaultdict(lambda: [0, 0.0])
    for z, x0, y0, x1, y1, e in mv:
        if e:
            continue
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 3.0:
            continue
        for label, ox, oy, r, zlo, zhi in zones:
            if zlo < z <= zhi and seg_dist(x0, y0, x1, y1, cx + ox, cy + oy) < r:
                per_zone[label][0] += 1
                per_zone[label][1] += length
    return per_zone


PROJECT = OUT / "hen_tag_revC_P1S.3mf"


def write_project(parts: list[str]) -> bool:
    """Bambu project: the printables arranged on one P1S plate, settings baked in."""
    work = Path(tempfile.mkdtemp())
    prof = flatten(PROCESS)
    prof.update(RECOMMENDED)
    prof["name"], prof["from"] = "hen_tag_revC", "User"
    pj = work / "process.json"
    json.dump(prof, open(pj, "w"))
    r = subprocess.run(
        [str(APP), "--debug", "2", "--load-settings", f"{MACHINE};{pj}",
         "--load-filaments", str(FILAMENT), "--export-3mf", str(PROJECT)]
        + [str(OUT / f"{n}.stl") for n in parts],
        capture_output=True, text=True)
    shutil.rmtree(work, ignore_errors=True)
    ok = r.returncode == 0 and PROJECT.exists()
    print(f"  {'wrote' if ok else 'FAILED to write'} {PROJECT.name}: "
          f"{', '.join(parts)} on one plate, "
          + ", ".join(f"{k}={v}" for k, v in RECOMMENDED.items()))
    return ok


def main() -> int:
    if not (APP.exists() and MACHINE.exists() and FILAMENT.exists()):
        print("Bambu Studio not installed; slicer check skipped.")
        return 0
    stock = "--stock" in sys.argv
    keep = "--keep" in sys.argv
    plates = [Path(a).resolve() for a in sys.argv[1:] if a.endswith(".3mf")]
    parts = [a for a in sys.argv[1:] if not a.startswith("--") and not a.endswith(".3mf")]
    if not parts and not plates:
        parts = list(OPEN_AIR)
    if "--project" in sys.argv:
        return 0 if write_project(parts or list(OPEN_AIR)) else 1
    fails = []
    # A finished plate (cap_batch.py output) carries its own settings: slice
    # it as-is and report objects, warnings and the slicer's estimate.
    for plate in plates:
        work = Path(tempfile.mkdtemp())
        r = subprocess.run([str(APP), "--debug", "4", "--slice", "0", "--outputdir", str(work), str(plate)],
                           capture_output=True, text=True)
        log = r.stdout + r.stderr
        g = work / "plate_1.gcode"
        text = g.read_text(errors="replace") if g.exists() else ""
        n_obj = len(set(re.findall(r"; OBJECT_ID: (\d+)", text)))
        warn = [ln.strip()[:100] for ln in log.splitlines()
                if re.search(r"floating cantilever|CRITICAL|\[error\]", ln, re.I)
                and "[WARNING]" not in ln and "no filament colors" not in ln]
        est = re.search(r"; total estimated time: (.+)", text)
        m = re.search(r"max_cantilever_dist=([\d.]+)", log)
        ok = g.exists() and not warn
        print(f"  [{'PASS' if ok else 'FAIL'}] {plate.name:36} {n_obj} objects sliced"
              + (f", {est.group(1).strip()}" if est else "")
              + (f", max_cantilever_dist {float(m.group(1)):.0f}" if m else ""))
        for w in warn:
            print(f"         slicer: {w}")
        if not ok:
            fails.append(plate.name)
        shutil.rmtree(work, ignore_errors=True)
    overrides = {} if stock else RECOMMENDED
    if parts:
        print("slicer check --", "STOCK Bambu profile" if stock else
              "recommended settings: " + ", ".join(f"{k}={v}" for k, v in overrides.items()))
    for name in parts:
        stl = OUT / f"{name}.stl"
        if not stl.exists():
            print(f"  [FAIL] {name}: {stl} missing, run hen_tag_enclosure.py")
            fails.append(name)
            continue
        work = (OUT / "slice" / name) if keep else Path(tempfile.mkdtemp())
        if keep:
            shutil.rmtree(work, ignore_errors=True)
            work.mkdir(parents=True)
        gcode, log = slice_part(stl, overrides, work)
        warn = [ln.strip()[:100] for ln in log.splitlines()
                if re.search(r"floating cantilever|CRITICAL|\[error\]", ln, re.I)
                and "[WARNING]" not in ln and "no filament colors" not in ln]
        m = re.search(r"max_cantilever_dist=([\d.]+)", log)
        cant = float(m.group(1)) if m else 0.0
        if gcode is None:
            print(f"  [FAIL] {name}: slicing failed")
            for w in warn[:3]:
                print(f"         {w}")
            fails.append(name)
            continue
        zones = open_air_travels(moves(gcode), OPEN_AIR[name])
        total = sum(n for n, _ in zones.values())
        ok = total <= LIMIT[name] and cant <= CANTILEVER_LIMIT[name] and not warn
        tag = "PASS" if ok else "FAIL"
        if not ok:
            fails.append(name)
        detail = "; ".join(f"{n} across the {lbl} ({L:.0f} mm)" for lbl, (n, L) in zones.items()) \
            or "none"
        print(f"  [{tag}] {name:12} open-air travels: {detail}  (limit {LIMIT[name]}); "
              f"max_cantilever_dist {cant:.0f} (limit {CANTILEVER_LIMIT[name]})")
        for w in warn:
            print(f"         slicer: {w}")
        if not keep:
            shutil.rmtree(work, ignore_errors=True)
    print("FAILED: " + ", ".join(fails) if fails else "Slicer check passed.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
