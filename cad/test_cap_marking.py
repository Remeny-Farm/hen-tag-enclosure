# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Test suite for the deterministic tag generator.

    uv run --python 3.12 test_cap_marking.py            # fast: no Bambu export
    uv run --python 3.12 test_cap_marking.py --bambu    # + one full project export

Covers the customer-facing input envelope (number, message, icon, font),
the rejection paths, and byte-level determinism. Exits non-zero on failure.
"""

import hashlib
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
PASS, FAIL = 0, []


def run_cli(*args: str, bambu: bool = False) -> subprocess.CompletedProcess:
    cmd = ["uv", "run", "--python", "3.12", str(HERE / "cap_marking.py"), *args]
    if not bambu:
        cmd.append("--skip-bambu")
    return subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)


def check(cond: bool, label: str, detail: str = "") -> None:
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append(label)
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def all_checks_passed(r: subprocess.CompletedProcess) -> bool:
    return r.returncode == 0 and "[FAIL]" not in r.stdout


print("=== acceptance: the customer envelope ===")
t0 = time.time()

# Worst-case number (5 wide digits) + real Hungarian messages (accented
# capitals, descender letters -- both get uppercased) + each icon.
matrix = [
    ("88888", ["--top", "Bözsi!", "--icon", "heart"]),
    ("1",     ["--top", "Őzikém", "--icon", "star"]),
    ("40404", ["--icon", "flower", "--font", "tahoma"]),
    ("67",    ["--centre", "rings", "--band", "stripes"]),
    ("99999", ["--icon", "sun", "--band", "dots"]),
    ("3",     ["--centre", "solid", "--band", "arc"]),
    ("4242",  ["--centre", "dots", "--icon", "none"]),
    ("5",     ["--icon", "egg"]),
    ("6",     ["--icon", "moon"]),
]
for number, extra in matrix:
    r = run_cli(number, *extra)
    check(all_checks_passed(r), f"generate {number} {' '.join(extra)}",
          "" if all_checks_passed(r) else r.stdout.splitlines()[-1] if r.stdout else r.stderr[-200:])
    for suffix in ("", "_marking", "_core"):
        f = OUT / (f"cap_{number}.3mf" if not suffix else f"{suffix[1:]}_{number}.stl")
        check(f.exists() and f.stat().st_size > 1000, f"  output {f.name}")

print("=== the guaranteed-safe message length is honoured ===")
r = run_cli("7", "--top", "Szeretlek Bözsi!")
check(r.returncode != 0 and "shorten" in (r.stdout + r.stderr),
      "16-char message rejected for arc length (big-lettering layout)")
r = run_cli("7", "--top", "W" * 40)
check(r.returncode != 0 and "guaranteed-safe length" in (r.stdout + r.stderr),
      "40x'W' rejected with the safe-length hint")
import re
m = re.search(r"guaranteed-safe length: (\d+)", r.stdout + r.stderr)
check(m is not None, "safe length reported", m.group(1) if m else "missing")
if m:
    n_safe = int(m.group(1))
    r = run_cli("7", "--top", "W" * n_safe, "--icon", "none")
    check(all_checks_passed(r), f"{n_safe}x'W' (the guaranteed worst case) accepted",
          "" if all_checks_passed(r) else (r.stdout + r.stderr)[-200:])

print("=== rejection paths ===")
for label, args, needle in [
    ("6-digit number", ["123456"], "1-5 digits"),
    ("empty number", [""], "1-5 digits"),
    ("non-numeric id", ["12a"], "1-5 digits"),
    ("emoji in message", ["7", "--top", "hi ❤"], "unsupported characters"),
    ("comma in message (descends below baseline)", ["7", "--top", "szia, tyúk"],
     "unsupported characters"),
    ("unknown icon", ["7", "--icon", "unicorn"], "invalid choice"),
    ("unknown font", ["7", "--font", "comic-sans"], "invalid choice"),
    ("icon and centre together", ["7", "--icon", "star", "--centre", "rings"], "mutually exclusive"),
    ("unknown band", ["7", "--band", "zigzag"], "invalid choice"),
]:
    r = run_cli(*args)
    blob = r.stdout + r.stderr
    check(r.returncode != 0 and needle in blob, f"reject {label}",
          "" if needle in blob else blob[-120:])

print("=== determinism: same input, byte-identical output ===")
r1 = run_cli("31415", "--top", "Det 314!", "--icon", "flower")
h1 = {f.name: sha(f) for f in [OUT / "cap_31415.3mf", OUT / "cap_31415.stl",
                               OUT / "marking_31415.stl", OUT / "core_31415.stl"]}
r2 = run_cli("31415", "--top", "Det 314!", "--icon", "flower")
h2 = {f.name: sha(f) for f in [OUT / "cap_31415.3mf", OUT / "cap_31415.stl",
                               OUT / "marking_31415.stl", OUT / "core_31415.stl"]}
check(all_checks_passed(r1) and all_checks_passed(r2), "both runs clean")
for name in h1:
    check(h1[name] == h2[name], f"  {name} byte-identical", h1[name][:12])

if "--bambu" in sys.argv:
    print("=== Bambu project export (one full case) ===")
    r = run_cli("88888", "--top", "Bözsi!", bambu=True)
    f = OUT / "cap_88888_P1S.3mf"
    check(all_checks_passed(r) and "P1S.3mf" in r.stdout and f.exists(),
          "cap_88888_P1S.3mf produced with registration verify")

print("=== layout export and proof ===")
r = run_cli("67", "--icon", "heart", "--band", "stripes",
            "--layout-json", str(OUT / "layout.json"), "--proof", str(OUT / "proof_67.svg"))
check(all_checks_passed(r), "generate with layout + proof", "" if all_checks_passed(r) else (r.stdout + r.stderr)[-200:])
import json as _json
lay = _json.loads((OUT / "layout.json").read_text())
check(lay["schema"] == "hen-cap-layout/1" and len(lay["number"]["digits"]) == 10, "layout has 10 digits")
check(abs(lay["number"]["advance"] - 3.814) < 0.01, "digit advance 3.814", str(lay["number"]["advance"]))
check(all(v["d"].startswith("M ") for v in lay["number"]["digits"].values()), "digit paths well-formed")
check(set(lay["icons"]) == {"heart", "star", "flower", "egg", "sun", "moon"}, "layout icons complete")
check(set(lay["centre_patterns"]) == {"rings", "solid", "dots"} and set(lay["band_patterns"]) == {"stripes", "dots", "arc"},
      "layout patterns complete")
svg = (OUT / "proof_67.svg").read_text()
check(svg.count("<path") == 2 and "#101010" in svg and "#F4F4F0" in svg, "proof has both colours")

print("=== catalog parity and design hash ===")
sys.path.insert(0, str(HERE))
from cap_design import design_hash, load_catalog, validate_design  # noqa: E402
import cap_marking as cm  # noqa: E402
cat = load_catalog()
check(sorted(e["id"] for e in cat["icons"]) == sorted(k for k in cm.ICONS if k != "none"),
      "catalog icons == generator ICONS")
check(sorted(e["id"] for e in cat["centre_patterns"]) == sorted(cm.PATTERNS_CENTRE),
      "catalog centre patterns == PATTERNS_CENTRE")
check(sorted(e["id"] for e in cat["band_patterns"]) == sorted(cm.PATTERNS_BAND),
      "catalog band patterns == PATTERNS_BAND")
check(design_hash(67, "classic", "heart", None, "stripes") == "05dcdb796b921b25",
      "design_hash test vector 1")
check(design_hash(8, "meadow", None, "rings", None) == "0371884d05cc4f6b",
      "design_hash test vector 2")
check(validate_design(cat, {"serial": 67, "scheme": "classic", "icon": "heart",
                            "centre": "rings", "band": None})
      == ["icon and centre pattern are mutually exclusive"], "icon+centre rejected")
check(validate_design(cat, {"serial": 0, "scheme": "nope", "icon": None, "centre": None,
                            "band": None})[:2]
      == ["serial must be an integer 1..99999", "unknown scheme 'nope'"], "serial/scheme rejected")

# Tidy the per-test artifacts (gitignored anyway, but keep out/ readable).
for pat in ("*_88888*", "*_31415*", "*_40404*", "*_1.*", "*_1_*", "*_7*", "marking_1.stl",
            "*_99999*", "*_3.*", "*_3_*", "*_4242*", "*_5.*", "*_5_*", "*_6.*", "*_6_*"):
    for f in OUT.glob(pat):
        f.unlink()

print("=" * 60)
print(f"{PASS} passed, {len(FAIL)} failed in {time.time() - t0:.0f}s"
      + (f": {', '.join(FAIL)}" if FAIL else ""))
sys.exit(1 if FAIL else 0)
