// Checks the data behind baci.html. Run after the build: node scripts/verify-baci-data.mjs
// Exits with code 1 if any check fails.

import { readFile, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = async f => JSON.parse(await readFile(path.join(ROOT, f), "utf8"));
const log = (...a) => process.stdout.write(a.join(" ") + "\n");

let failures = 0;
function check(label, ok, detail = "") {
  if (!ok) failures++;
  log(`${ok ? "ok  " : "FAIL"} ${label}${detail ? `  (${detail})` : ""}`);
}
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

const h3File = await read("baii_data/baci/baci_h3.json");
const { cells, _meta: meta } = h3File;
const tracts = (await read("baii_data/baci/baci_tracts.json")).tracts;
const districts = (await read("baii_data/baci/baci_districts.json")).districts;
const bench = await read("baii_data/baci/baci_benchmarks.json");
const tractGeo = await read("baii_data/baci/tracts.geojson");
const hexKids = await read("baii_data/baci/hex_children.json");
const buildMeta = await read("baii_data/baci/build_meta.json");
const districtGeo = await read("baii_data/explore/districts.geojson");
const regionGeo = await read("baii_data/explore/regions.geojson");

const F = Object.fromEntries(meta.cell_fields.map((f, i) => [f.split("(")[0], i]));
const tractByIdx = new Map(tracts.map(t => [t.idx, t]));

log("== Counts ==");
check("16,189 hexagons", cells.length === 16189, cells.length);
check("843 tracts", tracts.length === 843, tracts.length);
check("tract idx values are unique", tractByIdx.size === tracts.length);
check("158 districts", districts.length === 158, districts.length);
check("district idx equals position", districts.every((d, i) => d.idx === i));
check("9 regions", bench.regions.length === 9, bench.regions.length);
check("4 area types", bench.area_types.length === 4 && meta.typ_labels.length === 4, bench.area_types.length);
check("5 class labels", meta.class_labels.length === 5);

log("\n== Classes and ranking ==");
check("class_breaks.A", same(meta.class_breaks.A, [26.104, 38.608, 56.514, 77.582]), meta.class_breaks.A.join(", "));
check("class_breaks.B", same(meta.class_breaks.B, [-0.786, -0.369, 0.171, 0.892]), meta.class_breaks.B.join(", "));
check("n_ranked tract 813", meta.n_ranked.tract === 813, meta.n_ranked.tract);
check("n_ranked district 141", meta.n_ranked.district === 141, meta.n_ranked.district);
check("813 tracts have a rank", tracts.filter(t => t.rank_a != null && t.rank_b != null).length === 813);
check("141 districts have a rank", districts.filter(d => d.rank_a != null && d.rank_b != null).length === 141);
check("flagged units are never ranked",
  tracts.every(t => !(t.partial_ela || t.small_n) || (t.rank_a == null && t.rank_b == null))
  && districts.every(d => !d.partial_ela || (d.rank_a == null && d.rank_b == null)));
check("every scored unit has a class 1 to 5",
  [...tracts, ...districts].every(u => u.cls_a >= 1 && u.cls_a <= 5 && u.cls_b >= 1 && u.cls_b <= 5)
  && cells.every(c => c[F.cls_a] >= 1 && c[F.cls_a] <= 5 && c[F.cls_b] >= 1 && c[F.cls_b] <= 5));

log("\n== Statewide ==");
check("statewide baci_a 58.0", bench.state.baci_a === 58, bench.state.baci_a);
check("statewide child_mean_a 50.0", bench.state.child_mean_a === 50, bench.state.child_mean_a);

log("\n== Highest and lowest need districts ==");
// Same ordering the page uses: score, then name.
const short = n => n.replace(/ School District$/, "");
function ends(key) {
  const ranked = districts.filter(d => d[key === "baci_a" ? "rank_a" : "rank_b"] != null);
  const hi = [...ranked].sort((a, b) => b[key] - a[key] || a.name.localeCompare(b.name)).slice(0, 5);
  const lo = [...ranked].sort((a, b) => a[key] - b[key] || a.name.localeCompare(b.name)).slice(0, 5);
  const fmt = l => l.map(d => `${short(d.name)} ${d[key]}`);
  return { hi: fmt(hi), lo: fmt(lo) };
}
const A = ends("baci_a"), B = ends("baci_b");
const expect = {
  hiA: ["Hartford 90.8", "Bridgeport 87.2", "New Britain 84.7", "New Haven 82.9", "New London 82.5"],
  loA: ["New Hartford 9.9", "Madison 10.6", "Weston 11.5", "Regional School District 18 12.7", "Andover 13.8"],
  hiB: ["Hartford 1.38", "Bridgeport 1.31", "New Britain 1.25", "New Haven 1.1", "Waterbury 1.09"],
  loB: ["New Hartford -1.38", "Madison -1.34", "Andover -1.28", "Weston -1.27", "Bethany -1.24"],
};
check("formula A highest need", same(A.hi, expect.hiA), A.hi.join("; "));
check("formula A lowest need", same(A.lo, expect.loA), A.lo.join("; "));
check("formula B highest need", same(B.hi, expect.hiB), B.hi.join("; "));
check("formula B lowest need", same(B.lo, expect.loB), B.lo.join("; "));

log("\n== Joins ==");
const badTract = cells.filter(c => !tractByIdx.has(c[F.tract_idx]));
check("every hexagon tract_idx exists in the tract file (joined on idx)", badTract.length === 0, `${badTract.length} missing`);
const badDistrict = cells.filter(c => c[F.district_idx] !== -1 && !districts[c[F.district_idx]]);
check("every hexagon district_idx is a district or -1", badDistrict.length === 0, `${badDistrict.length} bad`);
const noDistrict = cells.filter(c => c[F.district_idx] === -1);
check("hexagons with no district are flagged partial ELA", noDistrict.every(c => c[F.flags] & 1), `${noDistrict.length} hexagons`);
check("every tract district_idx is a district", tracts.every(t => districts[t.district_idx]));
const regionNames = new Set(bench.regions.map(r => r.name));
check("every tract and district region is a benchmark region",
  tracts.every(t => regionNames.has(t.region)) && districts.every(d => regionNames.has(d.region)));

// The page reads formula B components for a hexagon from its tract (census
// measures) and its district (Grade 3 reading). That is only right while the
// formula A side of the same lookup is exact.
const acsKeys = ["noHS", "LEA", "hardship"];
const acsMismatch = cells.filter(c => {
  const t = tractByIdx.get(c[F.tract_idx]);
  return !t || acsKeys.some(k => t[k] !== c[F[k]] || t["p_" + k] !== c[F["p_" + k]]);
});
check("hexagon census measures equal their tract's", acsMismatch.length === 0, `${acsMismatch.length} differ`);
const elaMismatch = cells.filter(c => {
  if (c[F.district_idx] === -1) return c[F.ELA_PI] != null;
  const d = districts[c[F.district_idx]];
  return d.ELA_PI !== c[F.ELA_PI] || d.p_ELA !== c[F.p_ELA];
});
check("hexagon Grade 3 reading equals its district's", elaMismatch.length === 0, `${elaMismatch.length} differ`);
check("z_* present wherever p_* is (tracts, districts, benchmarks)",
  [...tracts, ...districts, bench.state, ...bench.regions, ...bench.area_types]
    .every(u => [...acsKeys, "ELA"].every(k => (u["p_" + k] == null) === (u["z_" + k] == null))));

log("\n== Geometry ==");
const geoNames = districtGeo.features.map(f => f.properties.name);
check("158 district geometries", districtGeo.features.length === 158, districtGeo.features.length);
check("all 158 district names match districts.geojson, in idx order", districts.every((d, i) => geoNames[i] === d.name),
  districts.filter((d, i) => geoNames[i] !== d.name).map(d => d.name).join(", "));
check("all 9 region names match regions.geojson", bench.regions.every(r => regionGeo.features.some(f => f.properties.name === r.name)));
const tIdx = tractGeo.features.map(f => f.properties.idx);
const scoredIdx = tIdx.filter(i => i !== -1);
check("879 tract geometries", tractGeo.features.length === 879, tractGeo.features.length);
check("36 unscored tract geometries (idx -1)", tIdx.filter(i => i === -1).length === 36, tIdx.filter(i => i === -1).length);
check("every scored tract joins to exactly one geometry",
  scoredIdx.length === 843 && new Set(scoredIdx).size === 843 && tracts.every(t => scoredIdx.includes(t.idx)));
check("every tract geometry is a polygon",
  tractGeo.features.every(f => f.geometry && (f.geometry.type === "Polygon" || f.geometry.type === "MultiPolygon")));
const tractBytes = (await stat(path.join(ROOT, "baii_data/baci/tracts.geojson"))).size;
check("tracts.geojson under 1.5 MB", tractBytes < 1.5 * 1024 * 1024, `${(tractBytes / 1024).toFixed(0)} KB`);

log("\n== Children per hexagon ==");
const kids = hexKids.children;
check("one child count per hexagon", Array.isArray(kids) && kids.length === cells.length, kids && kids.length);
check("child counts are non-negative numbers", kids.every(k => Number.isFinite(k) && k >= 0));
const kidSum = kids.reduce((s, k) => s + k, 0);
check("hexagon children add up to the statewide child_pop", Math.abs(kidSum - bench.state.child_pop) < 5,
  `${kidSum.toFixed(1)} vs ${bench.state.child_pop}`);
const byType = [0, 1, 2, 3].map(t => cells.reduce((s, c, i) => s + (c[F.typ] === t ? kids[i] : 0), 0));
check("hexagon children by area type match the area-type benchmarks",
  bench.area_types.every(a => Math.abs(byType[a.typ] - a.child_pop) < 5),
  byType.map(Math.round).join(", "));

log("\n== Build metadata ==");
check("index version matches the data", buildMeta.index_version === meta.version, buildMeta.index_version);
check("ACS vintage recorded", /^\d{4}-\d{4}$/.test(buildMeta.acs_vintage || ""), buildMeta.acs_vintage);
check("EdSight year recorded", buildMeta.edsight_year === "2024-2025", buildMeta.edsight_year);

log(failures ? `\n${failures} check(s) failed.` : "\nAll checks passed.");
process.exit(failures ? 1 : 0);
