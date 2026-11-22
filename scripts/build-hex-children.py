"""Children per neighborhood for the storymap's 3D view.

Writes baii_data/baii_hex_children.json: one number per cell, in the same
order as baii_data/baii_h3.json. Children = pop_pre + pop_elementary +
pop_middle + pop_high from the BAII GeoPackage, the same definition as
baii_data/baci/hex_children.json, which this script checks itself against.

Reads the local GeoPackage (never committed) with the standard library only.

    python scripts/build-hex-children.py
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GPKG = ROOT / "baii_data" / "baii-2026-06-25.gpkg"
CELLS = ROOT / "baii_data" / "baii_h3.json"
BACI_CELLS = ROOT / "baii_data" / "baci" / "baci_h3.json"
BACI_CHILDREN = ROOT / "baii_data" / "baci" / "hex_children.json"
OUT = ROOT / "baii_data" / "baii_hex_children.json"

if not GPKG.exists():
    sys.exit(f"Missing {GPKG.name}: copy the BAII GeoPackage into baii_data/ first.")

con = sqlite3.connect(GPKG)
(table,) = con.execute("select table_name from gpkg_contents").fetchone()
kids = {
    h: (pre or 0) + (ele or 0) + (mid or 0) + (high or 0)
    for h, pre, ele, mid, high in con.execute(
        f'select h3_index, pop_pre, pop_elementary, pop_middle, pop_high from "{table}"'
    )
}

cells = json.loads(CELLS.read_text(encoding="utf-8"))["cells"]
missing = [c[0] for c in cells if c[0] not in kids]
if missing:
    sys.exit(f"{len(missing)} storymap cells are not in the GeoPackage, e.g. {missing[:3]}")
children = [round(kids[c[0]], 2) for c in cells]

# Cross-check against the Constraints Index child counts.
baci_cells = json.loads(BACI_CELLS.read_text(encoding="utf-8"))["cells"]
baci_kids = json.loads(BACI_CHILDREN.read_text(encoding="utf-8"))["children"]
bad = [(c[0], k, round(kids[c[0]], 2)) for c, k in zip(baci_cells, baci_kids) if abs(round(kids[c[0]], 2) - k) > 0.011]
if bad:
    sys.exit(f"{len(bad)} neighborhoods disagree with hex_children.json, e.g. {bad[:3]}")

populated = [k for c, k in zip(cells, children) if c[1] >= 1]
out = {
    "_meta": {
        "source": "BAII GeoPackage baii-2026-06-25, pop_pre + pop_elementary + pop_middle + pop_high per hexagon",
        "order": "same order as baii_h3.json cells",
        "rounding": "0.01 child",
        "total": round(sum(children)),
        "max": max(children),
        "checked_against": "baii_data/baci/hex_children.json (all shared neighborhoods match)",
    },
    "children": children,
}
OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print(f"{len(children)} cells, {len(populated)} populated, {round(sum(children)):,} children, "
      f"max {max(children)}, checked {len(baci_kids)} against hex_children.json -> {OUT.name}")
