# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""The plate writer: structure, determinism, and (when Bambu Studio is
installed) a real slice of a two-cube plate.

    uv run --python 3.12 test_bambu_project.py
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent   # the Bambu CLI needs an absolute --outputdir
sys.path.insert(0, str(HERE))
from bambu_project import APP, grid_label, grid_positions, write_plate  # noqa: E402

PASS, FAIL = 0, []


def check(cond, label, detail=""):
    global PASS
    PASS += bool(cond)
    FAIL.extend([] if cond else [label])
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}  {detail}")


def cube(s: float, z0: float = 0.0):
    v = [(x, y, z) for z in (z0, z0 + s) for y in (-s / 2, s / 2) for x in (-s / 2, s / 2)]
    t = [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4),
         (2, 6, 3), (3, 6, 7), (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)]
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
check(cfg["wall_loops"] == "3" and cfg["reduce_crossing_wall"] == "1" and cfg["wall_generator"] == "arachne"
      and len(cfg["filament_type"]) == 1 and len(cfg["filament_colour"]) == 1
      and cfg["printable_area"][2] == "256x256", "settings and plate area; filament arrays untouched")
h1 = hashlib.sha256(out.read_bytes()).hexdigest()
write_plate(out, caps, scheme, "test-batch")
check(hashlib.sha256(out.read_bytes()).hexdigest() == h1, "byte-identical on rerun", h1[:12])
check(grid_positions(36)[-1] == (218.0, 218.0) and len(grid_positions(36)) == 36, "36-cap grid")
check(grid_label((38.0, 38.0)) == "1A" and grid_label((218.0, 218.0)) == "6F", "grid labels 1A..6F")
try:
    grid_positions(37)
    check(False, "37 caps refused")
except SystemExit:
    check(True, "37 caps refused")
if APP.exists():
    work = HERE / "out" / "slice_test"
    shutil.rmtree(work, ignore_errors=True)
    r = subprocess.run([str(APP), "--debug", "2", "--slice", "0", "--outputdir", str(work), str(out)],
                       capture_output=True, text=True)
    g = work / "plate_1.gcode"
    log = r.stdout + r.stderr
    ids = set(re.findall(r"; OBJECT_ID: (\d+)", g.read_text(errors="replace"))) if g.exists() else set()
    # "[error] [WARNING]: the parent path ... is not there, create it!" is
    # the CLI creating the output directory; every other [error] is real.
    errors = [ln for ln in log.splitlines() if "[error]" in ln and "[WARNING]" not in ln]
    check(g.exists() and not errors and len(ids) == 2,
          "Bambu Studio slices the plate with 2 objects",
          f"{len(ids)} object ids" if g.exists() and not errors else (errors[-1:] or [log[-300:]])[0][-200:])
    shutil.rmtree(work, ignore_errors=True)
else:
    print("  (Bambu Studio not installed; slice step skipped)")
out.unlink(missing_ok=True)
print(f"{PASS} passed, {len(FAIL)} failed" + (f": {FAIL}" if FAIL else ""))
sys.exit(1 if FAIL else 0)
