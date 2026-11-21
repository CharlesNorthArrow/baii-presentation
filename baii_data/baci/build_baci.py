"""Build the Book Access Context Index (BACI), v0.2: hex, tract, district
tiers plus state / planning-region / area-type benchmarks.

Four equally weighted ingredients. Each one is oriented so that a higher
value means more need:

    noHS      % of adults 25+ without a high school diploma   (ACS B15002, tract)
    LEA       % of adults 18+ who speak English less than      (ACS B16004, tract,
              "very well"                                       Esri Living Atlas layer)
    hardship  % of people below 150% of the federal poverty    (ACS C17002, tract)
              level ("Economic Hardship")
    ELA       Grade 3 ELA Performance Index (EdSight, district).
              Higher PI = better outcomes, so it is FLIPPED.

Two variants are built so the formula choice can be tested on the map:

    A  percentile   P = share of CT children living in units with a lower
                    value (ties at midpoint). ELA enters as 100 - P(PI).
                    BACI_A = mean of the available P's (0-100).
    B  log-z        Townsend-style. ACS rates are ln(1 + %), then
                    child-weighted z-scores. ELA enters as -z(PI).
                    BACI_B = mean of the available z's.

Reference distributions (frozen in _meta so later years can be scored
against the 2026 baseline):
    ACS ingredients  ranked / standardised across tracts, weighted by children
    ELA              ranked / standardised across districts, weighted by children
Children = pop_pre + pop_elementary + pop_middle + pop_high (same as child_pop).

Tiers
  hex       tract ACS rates + the hex's own district ELA.
  tract     tract ACS rates + child-weighted mean ELA PI of the tract's hexes
            (a tract can straddle districts). `district_idx` = the district
            holding most of the tract's children.
  district  tract counts apportioned to hexes by population share, summed per
            district into district rates, scored through the SAME tract lookup,
            so every tier sits on one scale.
  benchmarks  state, 9 planning regions, 4 area types: built exactly like a
            district (summed apportioned counts, child-weighted mean ELA PI).

Area type (typ): 0 Rural, 1 Suburban, 2 Urban Periphery, 3 Urban Core, from
baii_snapshot.json. Hex = its own; district = the snapshot's modal type;
tract = the type holding most of the tract's children.

Rules
  - EdSight 0 values are missing, not scores -> NaN.
  - A unit needs all three ACS ingredients. Missing ELA -> mean of three,
    flagged partial_ela.
  - Tracts with any ACS denominator < 100 are flagged small_n.
  - Populated hex = car_bin >= 1 in baii_h3.json (BAII definition).
  - rank_a / rank_b: 1 = highest need. Flagged units (partial_ela, small_n)
    are not ranked (null); n_ranked is in _meta.

Inputs (parent folder baii_data/): baii-2026-06-25.gpkg, baii_h3.json,
baii_districts.json, baii_snapshot.json. Here: ct_tracts_B16004_limited_english.csv.
Needs only pandas + numpy.

    python baii_data/baci/build_baci.py
"""
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
GPKG = SRC / "baii-2026-06-25.gpkg"
H3_JSON = SRC / "baii_h3.json"
DISTRICTS_JSON = SRC / "baii_districts.json"
SNAPSHOT_JSON = SRC / "baii_snapshot.json"
LEA_CSV = HERE / "ct_tracts_B16004_limited_english.csv"
OUT_H3 = HERE / "baci_h3.json"
OUT_TRACTS = HERE / "baci_tracts.json"
OUT_DISTRICTS = HERE / "baci_districts.json"
OUT_BENCH = HERE / "baci_benchmarks.json"

VERSION = "0.2"
KID_FIELDS = ["pop_pre", "pop_elementary", "pop_middle", "pop_high"]
C17 = [f"C17002_00{i}E" for i in range(2, 9)]
ACS = ["noHS", "LEA", "hardship"]
ING = ACS + ["ELA"]
SMALL_N = 100
CLASS_LABELS = ["Lowest need", "Low", "Moderate", "High", "Highest need"]
TYP_LABELS = ["Rural", "Suburban", "Urban Periphery", "Urban Core"]


def wpct_lookup(ref_vals, ref_w):
    """Return f(x) = child-weighted midpoint percentile of x in the reference."""
    order = np.argsort(ref_vals)
    v, w = ref_vals[order], ref_w[order]
    cw = np.concatenate([[0.0], np.cumsum(w)])
    tot = cw[-1]

    def f(x):
        x = np.asarray(x, dtype=float)
        lo = np.searchsorted(v, x, side="left")
        hi = np.searchsorted(v, x, side="right")
        p = 100 * (cw[lo] + 0.5 * (cw[hi] - cw[lo])) / tot
        return np.where(np.isnan(x), np.nan, p)

    return f


def wstats(vals, w):
    m = np.average(vals, weights=w)
    sd = np.sqrt(np.average((vals - m) ** 2, weights=w))
    return float(m), float(sd)


def wquantiles(vals, w, qs):
    o = np.argsort(vals)
    v, cw = vals[o], np.cumsum(w[o]) / w.sum()
    return [float(v[np.searchsorted(cw, q)]) for q in qs]


def wmode(frame, key, val, w):
    """Value of `val` holding the most weight `w` within each `key`."""
    g = frame.dropna(subset=[key, val]).groupby([key, val])[w].sum().reset_index()
    g = g.sort_values([key, w, val], ascending=[True, False, True]).drop_duplicates(key)
    return g.set_index(key)[val]


def read_hexes():
    cols = ["h3_index", "GEOID", "NAME_ct", "NAME_sd", "County", "pop_total", *KID_FIELDS,
            "B15002_001E", "B15002_calc_numLTHSE", *C17, "Grade_3___Grade_3___ELA"]
    con = sqlite3.connect(GPKG)
    table = con.execute("select table_name from gpkg_contents where data_type='features'").fetchone()[0]
    hx = pd.read_sql(f'select {", ".join(chr(34) + c + chr(34) for c in cols)} from "{table}"', con)
    con.close()
    return hx


def main():
    hx = read_hexes()
    hx["kids"] = hx[KID_FIELDS].fillna(0).sum(axis=1)
    lea = pd.read_csv(LEA_CSV, dtype={"GEOID": str})
    hx = hx.merge(lea, on="GEOID", how="left")

    # tract counts (constant within tract in the gpkg)
    hx["n_noHS"], hx["d_noHS"] = hx.B15002_calc_numLTHSE, hx.B15002_001E
    hx["n_LEA"], hx["d_LEA"] = hx.B16004_calc_numGE18LEAE, hx.B16004_calc_numGE18E
    hx["n_hardship"], hx["d_hardship"] = hx[C17[:4]].sum(axis=1, min_count=4), hx[C17].sum(axis=1, min_count=7)
    hx["ELA_PI"] = hx["Grade_3___Grade_3___ELA"].replace(0, np.nan)

    # storymap joins: bins + district index, area type
    h3cells = pd.DataFrame(json.loads(H3_JSON.read_text())["cells"],
                           columns=["h3_index", "car_bin", "pt_bin", "district_idx", "gap_class"])
    snap = json.loads(SNAPSHOT_JSON.read_text())
    typ_i = snap["_meta"]["hex_fields"].index("typ")
    htyp = pd.Series({h: v[typ_i] for h, v in snap["hex"].items() if v[typ_i] >= 0}, name="typ")  # -1 = no type
    hx = h3cells.merge(hx, on="h3_index", how="left").join(htyp, on="h3_index")
    dtyp = {d["idx"]: d["typ"] for d in snap["districts"]}

    # ---- tract table ------------------------------------------------------
    tg = hx.dropna(subset=["GEOID"])
    tr = tg.groupby("GEOID").agg(
        name=("NAME_ct", "first"), region=("County", "first"),
        kids=("kids", "sum"), pop=("pop_total", "sum"),
        **{f"{p}_{k}": (f"{p}_{k}", "first") for k in ACS for p in ("n", "d")})
    for k in ACS:
        tr[k] = np.where(tr[f"d_{k}"] > 0, 100 * tr[f"n_{k}"] / tr[f"d_{k}"], np.nan)
    tr["small_n"] = (tr[[f"d_{k}" for k in ACS]] < SMALL_N).any(axis=1)
    e = tg[tg.ELA_PI.notna() & (tg.kids > 0)]
    tr["ELA_PI"] = ((e.ELA_PI * e.kids).groupby(e.GEOID).sum() / e.kids.groupby(e.GEOID).sum()).round(6)  # round: keeps exact ties with district values
    tr["district_idx"] = wmode(tg[tg.district_idx >= 0], "GEOID", "district_idx", "kids")
    tr["typ"] = wmode(tg, "GEOID", "typ", "kids")
    tr = tr.sort_index()
    tr["idx"] = np.arange(len(tr))

    # ---- apportioned counts (district + benchmark tiers) ------------------
    hx["tpop"] = hx.groupby("GEOID").pop_total.transform("sum")
    share = np.where(hx.tpop > 0, hx.pop_total / hx.tpop, 0.0)
    for k in ACS:
        hx[f"an_{k}"] = hx[f"n_{k}"] * share
        hx[f"ad_{k}"] = hx[f"d_{k}"] * share
    hx["ela_w"] = np.where(hx.ELA_PI.notna(), hx.kids, 0.0)
    hx["ela_wx"] = hx.ELA_PI.fillna(0) * hx.ela_w

    def aggregate(frame, key):
        g = frame.groupby(key).agg(
            kids=("kids", "sum"), ela_w=("ela_w", "sum"), ela_wx=("ela_wx", "sum"),
            **{f"{p}_{k}": (f"{p}_{k}", "sum") for k in ACS for p in ("an", "ad")})
        for k in ACS:
            g[k] = np.where(g[f"ad_{k}"] > 0, 100 * g[f"an_{k}"] / g[f"ad_{k}"], np.nan)
        g["ELA_PI"] = np.round(np.where(g.ela_w > 0, g.ela_wx / g.ela_w, np.nan), 6)  # exact ties
        return g

    dd = aggregate(hx.dropna(subset=["NAME_sd"]), "NAME_sd")

    # ---- frozen lookups -----------------------------------------------------
    ref, pct_f, z_par = {}, {}, {}
    for k in ACS:
        ok = tr[k].notna() & (tr.kids > 0)
        v, w = tr.loc[ok, k].to_numpy(), tr.loc[ok, "kids"].to_numpy()
        pct_f[k] = wpct_lookup(v, w)
        z_par[k] = wstats(np.log1p(v), w)
        ref[k] = {"unit": "tract", "n": int(ok.sum()),
                  "deciles": [round(q, 2) for q in wquantiles(v, w, np.arange(0.1, 1.0, 0.1))],
                  "ln1p_mean": round(z_par[k][0], 5), "ln1p_sd": round(z_par[k][1], 5)}
    ok = dd.ELA_PI.notna() & (dd.kids > 0)
    v, w = dd.loc[ok, "ELA_PI"].to_numpy(), dd.loc[ok, "kids"].to_numpy()
    pct_f["ELA"] = wpct_lookup(v, w)
    z_par["ELA"] = wstats(v, w)
    ref["ELA"] = {"unit": "district", "n": int(ok.sum()),
                  "deciles": [round(q, 2) for q in wquantiles(v, w, np.arange(0.1, 1.0, 0.1))],
                  "mean": round(z_par["ELA"][0], 4), "sd": round(z_par["ELA"][1], 4)}

    def score(frame):
        out = pd.DataFrame(index=frame.index)
        for k in ACS:
            out[f"P_{k}"] = pct_f[k](frame[k].to_numpy(dtype=float))
            m, s = z_par[k]
            out[f"Z_{k}"] = (np.log1p(frame[k].to_numpy(dtype=float)) - m) / s
        ela = frame["ELA_PI"].to_numpy(dtype=float)
        out["P_ELA"] = 100 - pct_f["ELA"](ela)        # flipped: high PI = low need
        m, s = z_par["ELA"]
        out["Z_ELA"] = -(ela - m) / s                 # flipped
        has_acs = out[[f"P_{k}" for k in ACS]].notna().all(axis=1)
        out["BACI_A"] = out[[f"P_{k}" for k in ING]].mean(axis=1).where(has_acs)
        out["BACI_B"] = out[[f"Z_{k}" for k in ING]].mean(axis=1).where(has_acs)
        out["partial_ela"] = has_acs & out["P_ELA"].isna()
        return out

    # ---- hex tier -----------------------------------------------------------
    hx = hx.join(tr[ACS + ["small_n", "idx"]].rename(columns={"idx": "tract_idx"}), on="GEOID")
    hx = pd.concat([hx, score(hx)], axis=1)
    pop = (hx.car_bin >= 1) & hx.BACI_A.notna()
    breaks = {}
    for var in ("A", "B"):
        breaks[var] = wquantiles(hx.loc[pop, f"BACI_{var}"].to_numpy(),
                                 hx.loc[pop, "kids"].to_numpy(), [0.2, 0.4, 0.6, 0.8])
        hx[f"cls_{var}"] = np.where(pop, np.digitize(hx[f"BACI_{var}"].fillna(-1e9), breaks[var]) + 1, 0)

    def classify(frame):
        for var in ("A", "B"):
            frame[f"cls_{var}"] = np.where(frame[f"BACI_{var}"].notna(),
                                           np.digitize(frame[f"BACI_{var}"].fillna(0), breaks[var]) + 1, 0)
        return frame

    def rank(frame, flagged):
        for var in ("A", "B"):
            frame[f"rank_{var}"] = frame[f"BACI_{var}"].where(~flagged).rank(ascending=False, method="min")
        return frame

    # ---- tract tier -----------------------------------------------------------
    tr = classify(pd.concat([tr, score(tr)], axis=1))
    tr = tr[tr.BACI_A.notna() & (tr.kids > 0)].copy()
    tr = rank(tr, tr.small_n | tr.partial_ela)

    # ---- district tier --------------------------------------------------------
    dmeta = pd.DataFrame(json.loads(DISTRICTS_JSON.read_text())["districts"])[["idx", "name", "county", "child_pop"]]
    dd = pd.concat([dd, score(dd)], axis=1).reset_index().rename(columns={"NAME_sd": "name"})
    dd = classify(dmeta.merge(dd, on="name", how="left"))
    dd["typ"] = dd.idx.map(dtyp)
    dd = rank(dd, dd.partial_ela)

    # ---- benchmarks -------------------------------------------------------------
    scored = hx[pop]

    def bench(frame, key):
        b = aggregate(frame, key)
        b = classify(pd.concat([b, score(b)], axis=1))
        cm = frame.assign(wa=frame.BACI_A * frame.kids, wb=frame.BACI_B * frame.kids).groupby(key)[["wa", "wb", "kids"]].sum()
        b["child_mean_A"], b["child_mean_B"] = cm.wa / cm.kids, cm.wb / cm.kids
        return b

    b_state = bench(scored.assign(_k="Connecticut"), "_k")
    b_region = bench(scored.dropna(subset=["County"]), "County")
    b_typ = bench(scored.dropna(subset=["typ"]), "typ")

    # ---- write --------------------------------------------------------------------
    r1 = lambda x: None if pd.isna(x) else round(float(x), 1)
    r2 = lambda x: None if pd.isna(x) else round(float(x), 2)
    ri = lambda x: None if pd.isna(x) else int(x)

    def fields(r):
        return {"noHS": r1(r.noHS), "LEA": r1(r.LEA), "hardship": r1(r.hardship), "ELA_PI": r1(r.ELA_PI),
                "p_noHS": r1(r.P_noHS), "p_LEA": r1(r.P_LEA), "p_hardship": r1(r.P_hardship), "p_ELA": r1(r.P_ELA),
                "z_noHS": r2(r.Z_noHS), "z_LEA": r2(r.Z_LEA), "z_hardship": r2(r.Z_hardship), "z_ELA": r2(r.Z_ELA),
                "baci_a": r1(r.BACI_A), "baci_b": r2(r.BACI_B), "cls_a": int(r.cls_A), "cls_b": int(r.cls_B)}

    meta = {
        "version": VERSION,
        "index": "Book Access Context Index (BACI). Higher = more need.",
        "ingredients": {
            "noHS": "% adults 25+ without HS diploma (B15002_calc_numLTHSE / B15002_001E), tract",
            "LEA": "% adults 18+ speaking English less than 'very well' (B16004_calc_numGE18LEAE / B16004_calc_numGE18E), tract",
            "hardship": "% below 150% FPL ((C17002_002..005) / sum C17002_002..008), tract",
            "ELA": "Grade 3 ELA Performance Index, district. Flipped: high PI = low need. EdSight 0 treated as missing."},
        "field_guide": {
            "noHS / LEA / hardship": "raw rate, percent",
            "ELA_PI": "raw Performance Index (higher = better). Tract and benchmark values are child-weighted means of district PIs",
            "p_*": "variant A component, 0-100, higher = more need (p_ELA already flipped)",
            "z_*": "variant B component, z-score, higher = more need (z_ELA already flipped)",
            "baci_a": "mean of p_*", "baci_b": "mean of z_*",
            "cls_a / cls_b": "1-5 need class on the shared breaks; 0 = not scored",
            "typ": "area type code, see typ_labels",
            "rank_a / rank_b": "1 = highest need among unflagged units of that tier; null if flagged"},
        "variant_A": "child-weighted midpoint percentile per ingredient (ELA = 100 - P), averaged",
        "variant_B": "child-weighted z of ln(1+%) per ACS ingredient, -z(PI) for ELA, averaged",
        "reference": ref,
        "class_breaks": {k: [round(b, 3) for b in v] for k, v in breaks.items()},
        "class_def": "child-weighted quintiles of populated-hex BACI; every tier is classed with the same breaks",
        "class_labels": CLASS_LABELS,
        "typ_labels": TYP_LABELS,
        "populated_def": "car_bin >= 1 and all three ACS ingredients present",
        "flags": {"partial_ela": "no Grade 3 ELA PI; BACI is the mean of 3 ingredients",
                  "small_n": f"tract has an ACS denominator < {SMALL_N}"},
        "n_ranked": {"tract": int(tr.rank_A.notna().sum()), "district": int(dd.rank_A.notna().sum())},
        "cell_fields": ["h3_index", "baci_a", "baci_b", "cls_a", "cls_b",
                        "noHS", "LEA", "hardship", "ELA_PI", "p_noHS", "p_LEA", "p_hardship", "p_ELA",
                        "district_idx", "flags(1=partial_ela,2=small_n)", "tract_idx", "typ"],
    }

    tract_ok = set(tr.idx)
    cells = []
    for r in hx[hx.cls_A > 0].itertuples(index=False):
        flags = (1 if r.partial_ela else 0) | (2 if r.small_n is True else 0)
        cells.append([r.h3_index, r1(r.BACI_A), r2(r.BACI_B), int(r.cls_A), int(r.cls_B),
                      r1(r.noHS), r1(r.LEA), r1(r.hardship), r1(r.ELA_PI),
                      r1(r.P_noHS), r1(r.P_LEA), r1(r.P_hardship), r1(r.P_ELA),
                      int(r.district_idx), flags,
                      int(r.tract_idx) if r.tract_idx in tract_ok else -1, ri(r.typ)])
    OUT_H3.write_text(json.dumps({"_meta": meta, "cells": cells}, separators=(",", ":")), encoding="utf-8")

    trecs = []
    for geoid, r in zip(tr.index, tr.itertuples(index=False)):
        trecs.append({"idx": int(r.idx), "geoid": geoid, "name": r.name, "region": r.region,
                      "district_idx": ri(r.district_idx), "typ": ri(r.typ), "child_pop": int(round(r.kids)),
                      **fields(r), "rank_a": ri(r.rank_A), "rank_b": ri(r.rank_B),
                      "partial_ela": bool(r.partial_ela), "small_n": bool(r.small_n)})
    OUT_TRACTS.write_text(json.dumps({"_meta": meta, "tracts": trecs}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    drecs = []
    for r in dd.itertuples(index=False):
        drecs.append({"idx": int(r.idx), "name": r.name, "region": r.county, "typ": ri(r.typ),
                      "child_pop": int(r.child_pop), **fields(r),
                      "rank_a": ri(r.rank_A), "rank_b": ri(r.rank_B), "partial_ela": bool(r.partial_ela)})
    OUT_DISTRICTS.write_text(json.dumps({"_meta": meta, "districts": drecs}, ensure_ascii=False), encoding="utf-8")

    def brecs(b, namer):
        return [{"name": namer(k), "child_pop": int(round(r.kids)), **fields(r),
                 "child_mean_a": r1(r.child_mean_A), "child_mean_b": r2(r.child_mean_B)}
                for k, r in zip(b.index, b.itertuples(index=False))]

    bench_meta = dict(meta, benchmark_def=(
        "Each benchmark is built like a district: apportioned tract counts summed into one rate per ingredient, "
        "child-weighted mean ELA PI, then scored through the same lookups. child_mean_a / child_mean_b = "
        "child-weighted mean of hex BACI (the need level of the average child's neighborhood). "
        "Populated, scored hexes only."))
    OUT_BENCH.write_text(json.dumps({
        "_meta": bench_meta,
        "state": brecs(b_state, str)[0],
        "regions": brecs(b_region, str),
        "area_types": [dict(typ=int(k), **rec) for k, rec in zip(b_typ.index, brecs(b_typ, lambda k: TYP_LABELS[int(k)]))],
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"v{VERSION}: {len(cells)} hexes, {len(trecs)} tracts "
          f"({int(tr.small_n.sum())} small_n, {int(tr.partial_ela.sum())} partial ELA), "
          f"{int(dd.BACI_A.notna().sum())} districts ({int(dd.partial_ela.sum())} partial ELA)")
    print("class breaks A", [round(b, 1) for b in breaks["A"]], "| B", [round(b, 2) for b in breaks["B"]])


if __name__ == "__main__":
    main()
