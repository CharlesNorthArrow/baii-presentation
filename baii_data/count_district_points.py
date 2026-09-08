"""Add per-district access-point counts to baii_districts.json.

Counts the index's own access points (baii_access_points.json, one
[lat, lng, labelIdx] triple per point) that fall inside each district
polygon in baii_districts.geojson, and writes the count as `n_pts` on
every record in baii_districts.json `districts[]`. Points that fall
outside every polygon (coastline slivers, out-of-state) are reported
in `_meta.n_pts_def` and not counted anywhere.

Re-run this after regenerating baii_districts.json or
baii_access_points.json: the upstream gpkg -> json export does not
produce n_pts, so it is lost on every regeneration.

    python baii_data/count_district_points.py
"""
import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

HERE = Path(__file__).resolve().parent
DISTRICTS_JSON = HERE / "baii_districts.json"
DISTRICTS_GEO = HERE / "baii_districts.geojson"
ACCESS_POINTS = HERE / "baii_access_points.json"


def main():
    ap = json.loads(ACCESS_POINTS.read_text(encoding="utf-8"))
    polys = gpd.read_file(DISTRICTS_GEO)[["idx", "geometry"]]
    pts = gpd.GeoDataFrame(
        {"lab": [p[2] for p in ap["points"]]},
        geometry=[Point(p[1], p[0]) for p in ap["points"]],
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(pts, polys, how="left", predicate="within")
    if joined.index.duplicated().any():
        raise SystemExit("a point matched more than one district; polygons overlap")
    unassigned = int(joined["idx"].isna().sum())
    counts = joined.dropna(subset=["idx"]).groupby("idx").size()
    counts = {int(k): int(v) for k, v in counts.items()}

    data = json.loads(DISTRICTS_JSON.read_text(encoding="utf-8"))
    for d in data["districts"]:
        d["n_pts"] = counts.get(d["idx"], 0)
    data["_meta"]["n_pts_def"] = (
        "n_pts = count of index access points (baii_access_points.json, all "
        f"categories) whose location falls within the district polygon; "
        f"{unassigned} of {len(pts)} points fall outside every district and are "
        "not counted. Computed by count_district_points.py."
    )
    DISTRICTS_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"{len(counts)} districts counted, {sum(counts.values())} points assigned, {unassigned} unassigned")


if __name__ == "__main__":
    main()
