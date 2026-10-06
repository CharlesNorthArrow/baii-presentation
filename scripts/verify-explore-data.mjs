// Prints the Prompt 1 verification gate for baii_data/explore/.
// Run after the build: node scripts/verify-explore-data.mjs

import { readFile, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "baii_data", "explore");
const read = async f => JSON.parse(await readFile(path.join(ROOT, f), "utf8"));
const log = (...a) => process.stdout.write(a.join(" ") + "\n");

const meta = await read("baii_data/explore/build_meta.json");
const pts = (await read("baii_data/explore/access_points.geojson")).features;
const details = meta.details_split ? await read("baii_data/explore/access_point_details.json") : null;
const regions = await read("baii_data/explore/regions.geojson");
const districts = await read("baii_data/explore/districts.geojson");
const { areas } = await read("baii_data/explore/areas.json");
const roster = (await read("baii_data/ingredients_assets.json")).assets;
const rosterCount = t => roster.filter(a => t(a.type)).reduce((s, a) => s + a.count, 0);

log("== Areas ==");
log(`planning regions: ${regions.features.length} (expected 9)`);
log(`school districts: ${districts.features.length} (the BAII district set; TIGER has 167 incl. overlapping elementary/secondary)`);
log(`points in no region: ${meta.points_outside_regions}; in no district: ${meta.points_outside_districts}`);
const noRegion = pts.filter(f => f.properties.region == null);
log("  no-region points:", noRegion.map(f => `${f.properties.id}@${f.geometry.coordinates.join(",")}`).join(" "));

log("\n== Per sub-type: ArcGIS fetched / duplicates / final vs BAII storymap roster ==");
const BAII = {
  "School With Library Staff": rosterCount(t => /^School Score [1-5]$/.test(t)),
  "School Without Library Staff": rosterCount(t => t === "School Score 0"),
  "Public Library": rosterCount(t => t === "Public Library"),
  "Bookstore": rosterCount(t => t === "Bookstore"),
  "Museum": rosterCount(t => t === "Museum"),
  "Child Care Center": rosterCount(t => t === "Child Care Center"),
  "Group Child Care Home": rosterCount(t => t === "Group Child Care Home"),
  "Child Care Center Exempt": rosterCount(t => t === "Child Care Center Exempt"),
  "Youth Camp Exempt": rosterCount(t => t === "Youth Camp Exempt"),
  "Little Free Library": rosterCount(t => t === "Little Free Library"),
  "Read to Grow BFK Organization": rosterCount(t => t === "Read to Grow BFK Organization"),
  "Read to Grow BFB Organization": rosterCount(t => t === "Read to Grow BFB Birthing Center"),
  "Read to Grow Bookmobile Stop": null,
};
log("sub_type | fetched | dupes | final | BAII | final-BAII | %");
for (const st of meta.sub_types) {
  const c = meta.sub_type_counts[st.key];
  const actual = pts.filter(f => f.properties.sub_type === st.key).length;
  if (actual !== c.final) throw new Error(`${st.key}: file has ${actual}, meta says ${c.final}`);
  const b = BAII[st.key];
  const diff = b == null ? "n/a" : c.final - b;
  const pct = b ? `${((c.final - b) / b * 100).toFixed(1)}%` : "n/a";
  log(`${st.key} | ${c.fetched} | ${c.duplicates} | ${c.final} | ${b ?? "none"} | ${diff} | ${pct}`);
}
log(`total points: ${pts.length}`);

log("\n== 5 random samples per sub-type ==");
let seed = 42;
const rand = () => ((seed = (seed * 1103515245 + 12345) % 2 ** 31) / 2 ** 31);
for (const st of meta.sub_types) {
  const pool = pts.filter(f => f.properties.sub_type === st.key);
  const picks = [];
  while (picks.length < Math.min(5, pool.length)) {
    const f = pool[Math.floor(rand() * pool.length)];
    if (!picks.includes(f)) picks.push(f);
  }
  log(`-- ${st.label}`);
  for (const f of picks) {
    const p = f.properties;
    const d = (details ? details[p.id] : p.details) || [];
    log(`   ${p.name ?? "(no name)"} | ${[p.address, p.town].filter(Boolean).join(", ") || "(no address)"} | ${d.map(x => `${x.label}: ${x.value}`).join(" · ") || "(no details)"}`);
  }
}

log("\n== Exclusions ==");
const raw = JSON.stringify(pts) + JSON.stringify(details ?? {});
log(`"Family" anywhere in output: ${(raw.match(/Family/g) || []).length} occurrences`);
log(`CustomerType field in output: ${raw.includes("CustomerType")}`);
log(`Family Day Care features: ${pts.filter(f => /Family Day Care/i.test(f.properties.sub_type)).length}`);
log(`RTG points: ${pts.filter(f => f.properties.id.startsWith("rtg-")).length} (layer query was CustomerType = 'Organization'; 443 orgs minus duplicates)`);
const codeLeaks = raw.match(/\b(FSCS|C_OUT_TY|LOCALE|DISCIPL|STATSTRU|"CE"|"BR"|"BS"|"HST"|"ART"|"CMU")\b/g);
log(`raw code leaks: ${codeLeaks ? codeLeaks.join(",") : "none"}`);

log("\n== Statewide schools ==");
const sw = areas.find(a => a.id === "statewide").kpis;
log(`with staff / without staff: ${sw.schools_with_staff} / ${sw.schools_without_staff} (dashboard 794 / 700)`);
log(`mean students per library staff: ${sw.students_per_library_staff_mean} over n=${sw.students_per_library_staff_n} (dashboard 434.1 over 794)`);

// Legacy Middlesex County, decoded from the bundled us-atlas TopoJSON, for
// comparison with the old dashboard only. Not part of the output.
const topo = await read("counties.json");
const { scale: [kx, ky], translate: [tx, ty] } = topo.transform;
const arcs = topo.arcs.map(arc => { let x = 0, y = 0; return arc.map(([dx, dy]) => [(x += dx) * kx + tx, (y += dy) * ky + ty]); });
const ringFrom = idxs => idxs.flatMap((i, n) => { const a = i < 0 ? [...arcs[~i]].reverse() : arcs[i]; return n ? a.slice(1) : a; });
const mx = topo.objects.counties.geometries.find(g => g.id === "09007");
const polys = mx.type === "Polygon" ? [mx.arcs] : mx.arcs;
const rings = polys.map(p => p.map(ringFrom));
const inRing = (r, x, y) => { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const [xi, yi] = r[i], [xj, yj] = r[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; };
const inMx = ([x, y]) => rings.some(([o, ...h]) => inRing(o, x, y) && !h.some(r => inRing(r, x, y)));
const mxPts = pts.filter(f => inMx(f.geometry.coordinates));
const n = k => mxPts.filter(f => f.properties.sub_type === k).length;
const ratios = mxPts.filter(f => f.properties.sub_type === "School With Library Staff")
  .map(f => ((details ? details[f.properties.id] : f.properties.details) || []).find(d => d.label === "Students per library staff"))
  .filter(Boolean).map(d => Number(String(d.value).replace(/,/g, "")));
log("\n== Middlesex County (legacy county, verification only) ==");
log(`schools with staff ${n("School With Library Staff")} (ref 49), without ${n("School Without Library Staff")} (ref 29)`);
log(`mean students per library staff ${(ratios.reduce((s, v) => s + v, 0) / ratios.length).toFixed(1)} over n=${ratios.length} (ref 347.4)`);
log(`public libraries ${n("Public Library")} (ref 18)`);
log(`childcare licensed ${n("Child Care Center") + n("Group Child Care Home")} (ref 69), exempt ${n("Child Care Center Exempt") + n("Youth Camp Exempt")} (ref 9)`);

const lcrv = areas.find(a => a.name === "Lower Connecticut River Valley Planning Region").kpis;
log("\n== Lower Connecticut River Valley Planning Region (the region that replaces Middlesex) ==");
log(JSON.stringify({ with: lcrv.schools_with_staff, without: lcrv.schools_without_staff, mean: lcrv.students_per_library_staff_mean, n: lcrv.students_per_library_staff_n, libraries: lcrv.by_sub_type["Public Library"], licensed: lcrv.childcare_licensed, exempt: lcrv.childcare_exempt, total: lcrv.total }));

log("\n== Files ==");
for (const f of ["access_points.geojson", "access_point_details.json", "regions.geojson", "districts.geojson", "areas.json", "build_meta.json"]) {
  try { log(`${f}: ${(await stat(path.join(OUT, f))).size.toLocaleString("en-US")} bytes`); } catch { log(`${f}: not written`); }
}
log("\n== Layers ==");
for (const [k, m] of Object.entries(meta.layers)) log(`${k}: ${m.source_count} at source, last edit ${m.last_edit_date}, where ${m.where}`);
