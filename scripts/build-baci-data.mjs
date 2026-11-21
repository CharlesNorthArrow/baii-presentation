// Builds the static files behind baci.html. Run: node scripts/build-baci-data.mjs
//
// The BACI scores themselves are built by baii_data/baci/build_baci.py and are
// never touched here. This script adds what the page needs around them:
//   tracts.geojson       census tract boundaries, fetched once from ArcGIS,
//                        one property `idx` (from baci_tracts.json, -1 = unscored)
//   hex_children.json    children per scored hexagon, in baci_h3.json order,
//                        read from the BAII gpkg when it is present
//   build_meta.json      sources, vintages and counts for the "Data as of" line
// Decisions behind the choices here live in docs/baci/RECON.md.

import { readFile, writeFile, access } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "baii_data", "baci");
const GPKG = path.join(ROOT, "baii_data", "baii-2026-06-25.gpkg");
const MAX_TRACTS_BYTES = 1.5 * 1024 * 1024;
const EDSIGHT_YEAR = "2024-2025"; // Gate 0 decision D6

const ACS_SERVICE = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/ACS_English_Ability_and_Linguistic_Isolation_View_Boundaries/FeatureServer";
const PRIMARY = {
  key: "acs_english_ability",
  url: ACS_SERVICE + "/2",
  where: "GEOID LIKE '09%'",
  idField: "GEOID",
  joinKey: id => id,                    // same 2022 planning-region GEOIDs as baci_tracts.json
};
// Old county codes (09001 to 09015): join on the last 6 digits, unique statewide.
const FALLBACK = {
  key: "usa_census_tracts",
  url: "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Census_Tracts/FeatureServer/0",
  where: "STATE_FIPS='09'",
  idField: "FIPS",
  joinKey: id => id.slice(5),
};
const EXPECTED_CT_TRACTS = 879;

const log = (...a) => process.stdout.write(a.join(" ") + "\n");
const readJson = async f => JSON.parse(await readFile(path.join(ROOT, f), "utf8"));
const exists = f => access(f).then(() => true, () => false);

async function fetchJson(url, init, label) {
  let lastErr;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const r = await fetch(url, init);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      if (j.error) throw new Error(`ArcGIS error ${j.error.code}: ${j.error.message}`);
      return j;
    } catch (err) {
      lastErr = err;
      if (attempt < 3) await new Promise(res => setTimeout(res, 1000 * attempt));
    }
  }
  throw new Error(`${label}: failed after 3 attempts (${lastErr.message})\n  ${url}`);
}

async function fetchTracts(layer) {
  const body = new URLSearchParams({
    where: layer.where,
    outFields: layer.idField,
    outSR: "4326",
    geometryPrecision: "5",
    maxAllowableOffset: "0.0002",
    resultRecordCount: "2000",
    f: "geojson",
  });
  const fc = await fetchJson(layer.url + "/query", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  }, layer.key);
  if (fc.exceededTransferLimit || (fc.properties && fc.properties.exceededTransferLimit)) {
    throw new Error(`${layer.key}: exceededTransferLimit is set, the tract query was truncated`);
  }
  if (!Array.isArray(fc.features) || fc.features.length !== EXPECTED_CT_TRACTS) {
    throw new Error(`${layer.key}: expected ${EXPECTED_CT_TRACTS} Connecticut tracts, got ${fc.features ? fc.features.length : "none"}`);
  }
  return fc;
}

// "Current Vintage : 2020-2024" in the Living Atlas item description.
async function acsVintage() {
  try {
    const svc = await fetchJson(ACS_SERVICE + "?f=json", undefined, "acs service");
    const item = await fetchJson(`https://www.arcgis.com/sharing/rest/content/items/${svc.serviceItemId}?f=json`, undefined, "acs item");
    const text = (item.description || "").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ");
    const m = text.match(/Current Vintage\s*:\s*(\d{4}\s*-\s*\d{4})/i);
    return { vintage: m ? m[1].replace(/\s/g, "") : null, item_title: item.title, item_modified: new Date(item.modified).toISOString().slice(0, 10) };
  } catch (err) {
    log(`WARN could not read the ACS layer vintage: ${err.message.split("\n")[0]}`);
    return { vintage: null };
  }
}

// node:sqlite is built in (Node 22.5+) but still prints an experimental warning.
async function openSqlite(file) {
  const emit = process.emitWarning;
  process.emitWarning = (w, ...rest) => { if (!String(w).includes("SQLite")) emit.call(process, w, ...rest); };
  try {
    const { DatabaseSync } = await import("node:sqlite");
    return new DatabaseSync(file, { readOnly: true });
  } finally {
    process.emitWarning = emit;
  }
}

async function buildHexChildren(cells, stateChildren) {
  const outFile = path.join(OUT, "hex_children.json");
  if (!(await exists(GPKG))) {
    if (!(await exists(outFile))) throw new Error("hex_children.json is missing and the BAII gpkg is not here to rebuild it");
    log("hex_children.json: BAII gpkg not present, keeping the committed file");
    return null;
  }
  const db = await openSqlite(GPKG);
  const table = db.prepare("select table_name from gpkg_contents where data_type = 'features'").get().table_name;
  const rows = db.prepare(`select h3_index, pop_pre, pop_elementary, pop_middle, pop_high from "${table}"`).all();
  db.close();
  const kids = new Map(rows.map(r => [r.h3_index, r.pop_pre + r.pop_elementary + r.pop_middle + r.pop_high]));
  const children = cells.map(c => {
    const k = kids.get(c[0]);
    if (k == null || !Number.isFinite(k)) throw new Error(`no child count in the gpkg for hexagon ${c[0]}`);
    return Math.round(k * 100) / 100;
  });
  const sum = children.reduce((s, k) => s + k, 0);
  if (Math.abs(sum - stateChildren) > 5) throw new Error(`hexagon children add up to ${sum.toFixed(1)}, statewide child_pop is ${stateChildren}`);
  await writeFile(outFile, JSON.stringify({
    _meta: {
      source: "BAII gpkg baii-2026-06-25, pop_pre + pop_elementary + pop_middle + pop_high per hexagon",
      order: "same order as baci_h3.json cells",
      rounding: "0.01 child",
      total: Math.round(sum),
    },
    children,
  }));
  log(`hex_children.json: ${children.length} hexagons, ${Math.round(sum).toLocaleString("en-US")} children`);
  return Math.round(sum);
}

async function main() {
  const tracts = (await readJson("baii_data/baci/baci_tracts.json")).tracts;
  const { cells, _meta } = await readJson("baii_data/baci/baci_h3.json");
  const bench = await readJson("baii_data/baci/baci_benchmarks.json");

  // ── Tract boundaries ──
  let layer = PRIMARY, fc;
  try {
    fc = await fetchTracts(PRIMARY);
  } catch (err) {
    log(`WARN primary tract layer failed, trying the fallback: ${err.message.split("\n")[0]}`);
    layer = FALLBACK;
    fc = await fetchTracts(FALLBACK);
  }
  const byKey = new Map(tracts.map(t => [layer.joinKey(t.geoid), t.idx]));
  const seen = new Set();
  const features = fc.features.map(f => {
    const id = String(f.properties[layer.idField]);
    const key = layer.joinKey(id);
    if (seen.has(key)) throw new Error(`duplicate tract ${id} in ${layer.key}`);
    seen.add(key);
    if (!f.geometry) throw new Error(`tract ${id} has no geometry`);
    return { type: "Feature", properties: { idx: byKey.has(key) ? byKey.get(key) : -1 }, geometry: f.geometry };
  });
  const unmatched = tracts.filter(t => !seen.has(layer.joinKey(t.geoid)));
  if (unmatched.length) throw new Error(`${unmatched.length} scored tracts have no boundary: ${unmatched.slice(0, 10).map(t => t.geoid).join(", ")}`);
  const tractsJson = JSON.stringify({ type: "FeatureCollection", features });
  if (tractsJson.length > MAX_TRACTS_BYTES) throw new Error(`tracts.geojson is ${(tractsJson.length / 1048576).toFixed(2)} MB, over the 1.5 MB budget`);
  await writeFile(path.join(OUT, "tracts.geojson"), tractsJson);
  const unscored = features.filter(f => f.properties.idx === -1).length;
  log(`tracts.geojson: ${features.length} tracts from ${layer.key}, ${features.length - unscored} scored, ${unscored} unscored, ${(tractsJson.length / 1024).toFixed(0)} KB`);

  // ── Children per hexagon ──
  const hexTotal = await buildHexChildren(cells, bench.state.child_pop);

  // ── Build metadata ──
  const acs = await acsVintage();
  const metaFile = path.join(OUT, "build_meta.json");
  const prev = (await exists(metaFile)) ? JSON.parse(await readFile(metaFile, "utf8")) : {};
  await writeFile(metaFile, JSON.stringify({
    built_at: new Date().toISOString(),
    index_version: _meta.version,
    tract_source: { layer: layer.key, url: layer.url },
    acs_vintage: acs.vintage,
    acs_vintage_source: acs.vintage ? `${acs.item_title}, item updated ${acs.item_modified}` : null,
    edsight_year: EDSIGHT_YEAR,
    counts: { tracts_drawn: features.length, tracts_unscored: unscored, hexagons: cells.length },
    hex_children_total: hexTotal ?? prev.hex_children_total ?? null,
  }, null, 2) + "\n");
  log(`build_meta.json: ACS ${acs.vintage || "vintage unknown"}, EdSight ${EDSIGHT_YEAR}, index ${_meta.version}`);
}

main().catch(err => { process.stderr.write(`build-baci-data failed: ${err.stack || err}\n`); process.exit(1); });
