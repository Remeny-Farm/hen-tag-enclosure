# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""The batch CLI on the 3-cap fixture: outputs, determinism, cache, refusals.

    uv run --python 3.12 test_cap_batch.py
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures" / "batch_sample.json"
OUT = HERE / "out" / "plates_test"
PASS, FAIL = 0, []


def check(cond, label, detail=""):
    global PASS
    PASS += bool(cond)
    FAIL.extend([] if cond else [label])
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}  {detail}")


def run(batch: Path, *extra):
    return subprocess.run(["uv", "run", "--python", "3.12", str(HERE / "cap_batch.py"), str(batch),
                           "--out", str(OUT), "--no-slice", *extra],
                          capture_output=True, text=True, cwd=HERE)


def variant(name, mutate):
    b = json.loads(FIX.read_text())
    mutate(b)
    p = OUT / f"{name}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(b))
    return p


shutil.rmtree(OUT, ignore_errors=True)
print("=== happy path ===")
r = run(FIX)
plate = OUT / "plate_2026-09-14-classic-01_P1S.3mf"
manifest = OUT / "plate_2026-09-14-classic-01_manifest.csv"
check(r.returncode == 0, "batch runs", "" if r.returncode == 0 else (r.stdout + r.stderr)[-400:])
check(plate.exists() and manifest.exists(), "plate and manifest written")
rows = manifest.read_text().splitlines() if manifest.exists() else []
check(rows[:1] == ["position,serial,hen_name,design_hash"] and len(rows) == 4
      and rows[1].startswith("1A,67,") and rows[3].startswith("3A,3,"), "manifest rows", str(rows[:2]))
check((OUT / "proof" / "05dcdb796b921b25.svg").exists() and (OUT / "proof" / "fc52296fdb64d29e.svg").exists(),
      "proofs named by design hash")
h1 = hashlib.sha256(plate.read_bytes()).hexdigest() if plate.exists() else ""
r2 = run(FIX)
check(r2.returncode == 0 and hashlib.sha256(plate.read_bytes()).hexdigest() == h1, "byte-identical rerun", h1[:12])
check(r2.stdout.count("cache") >= 3, "second run served all three from cache")

print("=== refusals ===")
cases = [
    ("bad hash", lambda b: b["caps"][0].update(design_hash="0000000000000000"), "does not match"),
    ("unknown icon", lambda b: b["caps"][1].update(icon="unicorn"), "unknown icon"),
    ("duplicate serial", lambda b: b["caps"][1].update(serial=67), "duplicate serial"),
    ("version mismatch", lambda b: b.update(generator_version="v9"), "generator_version"),
    ("icon and centre", lambda b: b["caps"][0].update(centre="rings"), "mutually exclusive"),
    ("unknown scheme", lambda b: b.update(scheme="nope"), "unknown scheme"),
    ("too many caps", lambda b: b["caps"].extend(
        [dict(b["caps"][2], serial=100 + i, design_hash="x") for i in range(40)]), "1..36"),
]
for label, mutate, needle in cases:
    r = run(variant(label.replace(" ", "_"), mutate))
    blob = r.stdout + r.stderr
    check(r.returncode != 0 and needle in blob, f"refuse {label}", "" if needle in blob else blob[-160:])
print(f"{PASS} passed, {len(FAIL)} failed" + (f": {FAIL}" if FAIL else ""))
sys.exit(1 if FAIL else 0)
