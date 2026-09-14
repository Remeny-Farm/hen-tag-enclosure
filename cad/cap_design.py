# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""Catalog and design identity shared by the generator, the batch CLI and the
tests. Deliberately free of build123d so it imports in milliseconds.

The catalog (catalog.json) is the source of truth for what a patron may
choose: colour schemes (text + accent filament), icons, centre patterns, band
patterns and the Golden Grain fees. The app ships an identical copy; the
parity test in test_cap_marking.py keeps this file and the generator's
sketch tables in step.
"""

import hashlib
import json
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "catalog.json"
HASH_VERSION = 1
SERIAL_MAX = 99999


def load_catalog(path: Path | None = None) -> dict:
    cat = json.loads((path or CATALOG_PATH).read_text())
    if cat.get("schema") != "hen-cap-catalog/1":
        raise SystemExit(f"unsupported catalog schema {cat.get('schema')!r}")
    return cat


def ids(cat: dict, key: str) -> list[str]:
    return [e["id"] for e in cat[key]]


def design_hash(serial: int, scheme: str, icon: str | None,
                centre: str | None, band: str | None) -> str:
    """First 16 hex chars of SHA-256 over the canonical design JSON.

    Covers the design only, not the generator version, so a generator
    release does not invalidate locked designs. The app computes the same
    value (editor/src/cap-editor/design-hash.ts)."""
    canon = json.dumps({"band": band, "centre": centre, "icon": icon,
                        "scheme": scheme, "serial": serial, "v": HASH_VERSION},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()[:16]


def validate_design(cat: dict, d: dict) -> list[str]:
    """Every problem with one design, as human-readable strings."""
    errs = []
    serial = d.get("serial")
    if not isinstance(serial, int) or isinstance(serial, bool) or not 1 <= serial <= SERIAL_MAX:
        errs.append(f"serial must be an integer 1..{SERIAL_MAX}")
    if d.get("scheme") not in ids(cat, "schemes"):
        errs.append(f"unknown scheme {d.get('scheme')!r}")
    icon, centre, band = d.get("icon"), d.get("centre"), d.get("band")
    if icon is not None and icon not in ids(cat, "icons"):
        errs.append(f"unknown icon {icon!r}")
    if centre is not None and centre not in ids(cat, "centre_patterns"):
        errs.append(f"unknown centre pattern {centre!r}")
    if band is not None and band not in ids(cat, "band_patterns"):
        errs.append(f"unknown band pattern {band!r}")
    if icon is not None and centre is not None:
        errs.append("icon and centre pattern are mutually exclusive")
    if not errs and "design_hash" in d:
        want = design_hash(serial, d["scheme"], icon, centre, band)
        if d["design_hash"] != want:
            errs.append(f"design_hash {d['design_hash']} does not match fields ({want})")
    return errs
