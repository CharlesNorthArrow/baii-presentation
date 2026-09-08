"""Add the share of children living in low-access neighborhoods to
baii_districts.json.

For each district, over its populated neighborhoods (car_bin >= 1):

    cov_car = children in hexes with car_bin <= 2 / all children
    cov_pt  = children in hexes with pt_bin  <= 2 / all children

"Low access" is any bin below Moderate (No data / No transit, Very low,
Low), the same cut the gap tree uses. Children = pre-K through high
school (pop_pre + pop_elementary + pop_middle + pop_high), which
reproduces the shipped child_pop exactly. The statewide shares go to
_meta.coverage.state.

Inputs (all in this folder):
  baii-2026-06-25.gpkg   per-hex child counts (untracked, 19 MB; keep it
                         next to this script)
  baii_h3.json           per-hex bins and district index
  baii_districts.json    updated in place

Re-run after regenerating baii_h3.json or baii_districts.json: the
upstream export does not produce these fields.

    python baii_data/coverage_by_district.py
"""
import json
from collections import defaultdict
from pathlib import Path

import geopandas as gpd

HERE = Path(__file__).resolve().parent
GPKG = HERE / "baii-2026-06-25.gpkg"
H3_JSON = HERE / "baii_h3.json"
DISTRICTS_JSON = HERE / "baii_districts.json"

POP_FIELDS = ["pop_pre", "pop_elementary", "pop_middle", "pop_high"]
LOW_ACCESS_MAX_BIN = 2
BREAKS = [0.1, 0.25, 0.5, 0.75]
LABELS = ["Under 10%", "10–25%", "25–50%", "50–75%", "Over 75%"]


def main():
    if not GPKG.exists():
        raise SystemExit(f"missing {GPKG.name}; the geopackage must sit next to this script")
    hexes = gpd.read_file(GPKG, columns=["h3_index", *POP_FIELDS], ignore_geometry=True)
    hexes["kids"] = hexes[POP_FIELDS].fillna(0).sum(axis=1)
    kids_by_hex = dict(zip(hexes["h3_index"], hexes["kids"]))

    cells = json.loads(H3_JSON.read_text(encoding="utf-8"))["cells"]
    # [all children, children in low car access, children in low transit access]
    tallies = defaultdict(lambda: [0.0, 0.0, 0.0])
    state = [0.0, 0.0, 0.0]
    for h3key, car_bin, pt_bin, didx, *_ in cells:
        if car_bin < 1 or didx < 0:
            continue
        k = kids_by_hex.get(h3key, 0.0)
        for acc in (tallies[didx], state):
            acc[0] += k
            if car_bin <= LOW_ACCESS_MAX_BIN:
                acc[1] += k
            if pt_bin <= LOW_ACCESS_MAX_BIN:
                acc[2] += k

    share = lambda part, whole: round(part / whole, 3) if whole > 0 else None

    data = json.loads(DISTRICTS_JSON.read_text(encoding="utf-8"))
    for d in data["districts"]:
        t = tallies.get(d["idx"], [0.0, 0.0, 0.0])
        d["cov_car"] = share(t[1], t[0])
        d["cov_pt"] = share(t[2], t[0])
    data["_meta"]["coverage"] = {
        "def": "cov_car / cov_pt = share of the district's children (pre-K..12) living in "
               "neighborhoods whose car / transit bin is below Moderate (bins 0-2). "
               "Computed by coverage_by_district.py from the geopackage child counts.",
        "low_access_bins": [0, 1, 2],
        "child_pop_def": "pop_pre + pop_elementary + pop_middle + pop_high",
        "breaks": BREAKS,
        "labels": LABELS,
        "state": {"car": share(state[1], state[0]), "pt": share(state[2], state[0])},
    }
    DISTRICTS_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    n = sum(1 for d in data["districts"] if d["cov_pt"] is not None)
    print(f"{n} districts with coverage; statewide low-access share car "
          f"{data['_meta']['coverage']['state']['car']}, transit {data['_meta']['coverage']['state']['pt']}")


if __name__ == "__main__":
    main()
