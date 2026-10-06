// Builds the static data behind explore.html. Run: node scripts/build-explore-data.mjs
//
// Pulls the access point feature layers from ArcGIS Online once, normalizes
// them to one schema with a curated, labeled set of display fields, and
// assigns every point to a planning region and a school district.
// Decisions behind the choices here live in docs/explore/RECON.md
// ("Gate 0 decisions"): layers are shown as published, no weights, no
// BAII index data, planning regions instead of counties.

import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "baii_data", "explore");
const AGOL = "https://services5.arcgis.com/IJjAyk93TGaMwoTf/arcgis/rest/services";
const REGIONS_URL = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1";
const MAX_POINTS_BYTES = 1.5 * 1024 * 1024;

// ── Sub-types: storymap keys where the storymap has one ─────
const CATEGORIES = [
  { key: "In-School", label: "In school" },
  { key: "Out-of-School", label: "Out of school" },
  { key: "Childcare", label: "Childcare" },
  { key: "Nonprofit", label: "Nonprofit and community" },
];
const SUB_TYPES = [
  { key: "School With Library Staff", category: "In-School", label: "School libraries with library staff", type_label: "School library" },
  { key: "School Without Library Staff", category: "In-School", label: "School libraries without library staff", type_label: "School library, no library staff" },
  { key: "Public Library", category: "Out-of-School", label: "Public libraries", type_label: "Public library" },
  { key: "Bookstore", category: "Out-of-School", label: "Bookstores", type_label: "Bookstore" },
  { key: "Museum", category: "Out-of-School", label: "Museums", type_label: "Museum" },
  { key: "Child Care Center", category: "Childcare", label: "Childcare centers", type_label: "Childcare center", licensing: "licensed" },
  { key: "Group Child Care Home", category: "Childcare", label: "Group childcare homes", type_label: "Group childcare home", licensing: "licensed" },
  { key: "Child Care Center Exempt", category: "Childcare", label: "License-exempt childcare centers", type_label: "License-exempt childcare center", licensing: "exempt" },
  { key: "Youth Camp Exempt", category: "Childcare", label: "License-exempt youth camps", type_label: "License-exempt youth camp", licensing: "exempt" },
  { key: "Little Free Library", category: "Nonprofit", label: "Little Free Libraries", type_label: "Little Free Library" },
  { key: "Read to Grow BFK Organization", category: "Nonprofit", label: "Read to Grow Books for Kids partners", type_label: "Read to Grow Books for Kids partner" },
  { key: "Read to Grow BFB Organization", category: "Nonprofit", label: "Read to Grow Books for Babies partners", type_label: "Read to Grow Books for Babies partner" },
  { key: "Read to Grow Bookmobile Stop", category: "Nonprofit", label: "Read to Grow Bookmobile stops", type_label: "Read to Grow Bookmobile stop" },
];
const SUB_TYPE_BY_KEY = Object.fromEntries(SUB_TYPES.map(s => [s.key, s]));

// ── Value cleaning ──────────────────────────────────────────
const PLACEHOLDERS = new Set(["", "n/a", "na", "null", "none", "*", "-"]);
function clean(v) {
  if (v == null) return null;
  if (typeof v === "string") {
    const t = v.trim();
    return PLACEHOLDERS.has(t.toLowerCase()) ? null : t;
  }
  return v;
}
const positive = v => (typeof v === "number" && v > 0 ? v : null);
const fmtInt = n => n.toLocaleString("en-US");
const fmtNum = n => (Number.isInteger(n) ? fmtInt(n) : String(Math.round(n * 100) / 100));

// Source names and addresses are often ALL CAPS. Only recase those.
const KEEP_UPPER = new Set(["YMCA", "YWCA", "CT", "USA", "LLC", "II", "III", "IV", "PO", "UCONN", "ABC", "CREC", "SAILS", "STEM", "STEAM", "PK", "K-8", "NE", "NW", "SE", "SW"]);
function recase(s) {
  if (s == null) return null;
  if (/[a-z]/.test(s)) return s;
  return s.toLowerCase().replace(/[a-z0-9'’.&-]+/g, w => {
    const up = w.toUpperCase();
    if (KEEP_UPPER.has(up.replace(/\.$/, ""))) return up;
    if (/^\d+(st|nd|rd|th)$/.test(w)) return w;
    return w.charAt(0).toUpperCase() + w.slice(1);
  });
}
function humanize(code) {
  const s = code.replace(/_/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}
function fmtPhone(v) {
  const d = String(v ?? "").replace(/\D/g, "");
  return d.length === 10 ? `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}` : null;
}
function details(pairs) {
  const out = [];
  for (const [label, raw] of pairs) {
    const value = clean(raw);
    if (value == null) continue;
    out.push({ label, value: typeof value === "number" ? fmtNum(value) : value });
  }
  return out;
}
const agesServed = v => clean(v)?.replace(/\s*-\s*/g, " to ").replace(/\b(Years?|Months?|Weeks?)\b/g, w => w.toLowerCase()) ?? null;

// ── Layers ──────────────────────────────────────────────────
const LIBRARY_TYPE = { CE: "Main library", BR: "Branch library", BS: "Bookmobile" };
const MUSEUM_TYPE = { ART: "Art museum", HST: "History museum", SCI: "Science center", CMU: "Children's museum", NAT: "Natural history museum" };
const STORE_TYPE = { bookstore: "Bookstore", comic_books_store: "Comic book store", academic_bookstore: "College bookstore" };
const RTG_PROGRAM_SUBTYPE = {
  "Books for Kids": "Read to Grow BFK Organization",
  "Books for Babies": "Read to Grow BFB Organization",
  "Bookmobile": "Read to Grow Bookmobile Stop",
};

const LAYERS = [
  {
    key: "schools",
    idPrefix: "sch",
    service: "Book_Access_Schools_with_Library_Staff",
    where: "1=1",
    fields: ["F2024_25_School", "Street", "City", "Total_Library_staff", "Num_students_per_library_staff", "Library___Media___Specialists__Certified_", "TotalStudents123"],
    map(a) {
      const staff = a.Total_Library_staff ?? 0;
      const hasStaff = staff > 0;
      return {
        sub_type: hasStaff ? "School With Library Staff" : "School Without Library Staff",
        name: recase(clean(a.F2024_25_School)),
        address: recase(clean(a.Street)),
        town: recase(clean(a.City)),
        details: details(hasStaff ? [
          ["Library staff", staff],
          ["Students per library staff", positive(a.Num_students_per_library_staff)],
          ["Certified library media specialists", a.Library___Media___Specialists__Certified_],
          ["Students enrolled", positive(a.TotalStudents123)],
        ] : [
          ["Library staff", "No library staff reported"],
          ["Students enrolled", positive(a.TotalStudents123)],
        ]),
        // Kept for the KPI mean; 0 means no staff or no enrollment reported.
        _ratio: hasStaff ? positive(a.Num_students_per_library_staff) : null,
      };
    },
  },
  {
    key: "libraries",
    idPrefix: "lib",
    service: "CT_Libraries_2026_(240_Libraries)",
    where: "1=1",
    fields: ["LIBNAME", "ADDRESS", "CITY", "C_OUT_TY", "STATUS", "PHONE"],
    map(a) {
      return {
        sub_type: "Public Library",
        name: recase(clean(a.LIBNAME)),
        address: recase(clean(a.ADDRESS)),
        town: recase(clean(a.CITY)),
        details: details([
          ["Library type", LIBRARY_TYPE[clean(a.C_OUT_TY)] ?? null],
          ["Status", clean(a.STATUS) === "Temporarily Closed" ? "Temporarily closed" : null],
          ["Phone", fmtPhone(a.PHONE)],
        ]),
      };
    },
  },
  {
    key: "childcare_licensed",
    idPrefix: "ccl",
    service: "Book_Access_Child_Care_Centers",
    where: "1=1",
    fields: ["Type", "Name", "Address", "City", "Ages_Served", "Total_Capacity", "Capacity_Under_3"],
    map(a) {
      const type = clean(a.Type);
      const sub = type === "Group Child Care Home" ? "Group Child Care Home" : "Child Care Center";
      return {
        sub_type: sub,
        name: recase(clean(a.Name)),
        address: recase(clean(a.Address)),
        town: recase(clean(a.City)),
        details: details([
          ["Program type", sub === "Group Child Care Home" ? "Group childcare home" : "Childcare center"],
          ["License", "Licensed"],
          ["Ages served", agesServed(a.Ages_Served)],
          ["Capacity", positive(a.Total_Capacity)],
          // 0 is a real answer here: no spots for infants and toddlers.
          ["Spots for children under 3", positive(a.Total_Capacity) ? a.Capacity_Under_3 : null],
        ]),
      };
    },
  },
  {
    key: "childcare_exempt",
    idPrefix: "cce",
    service: "Book_Access___Child_Care_Center_Exempt",
    where: "1=1",
    fields: ["Type", "Name", "Address", "City", "Exemption_Type", "Ages_Served"],
    map(a) {
      const camp = clean(a.Type) === "Youth Camp Exempt";
      const runBy = clean(a.Exemption_Type);
      return {
        sub_type: camp ? "Youth Camp Exempt" : "Child Care Center Exempt",
        name: recase(clean(a.Name)),
        address: recase(clean(a.Address)),
        town: recase(clean(a.City)),
        details: details([
          ["Program type", camp ? "Youth camp" : "Childcare center"],
          ["License", "License-exempt"],
          ["Run by", runBy ? runBy.charAt(0) + runBy.slice(1).toLowerCase() : null],
          ["Ages served", agesServed(a.Ages_Served)],
        ]),
      };
    },
  },
  {
    key: "bookstores",
    idPrefix: "bks",
    service: "Book_Access_OVERTURE_Bookstores_",
    where: "1=1",
    // Lat/Lon attributes in this layer are swapped; geometry is correct and is what we use.
    fields: ["name", "primary_category"],
    map(a) {
      const cat = clean(a.primary_category);
      return {
        sub_type: "Bookstore",
        name: clean(a.name),
        address: null,
        town: null,
        details: details([["Store type", cat ? (STORE_TYPE[cat] ?? humanize(cat)) : null]]),
      };
    },
  },
  {
    key: "museums",
    idPrefix: "mus",
    service: "MuseumFile2018_File1_Nulls",
    where: "ADSTATE = 'CT' AND DISCIPL IN ('ART','HST','SCI','CMU','NAT')",
    fields: ["COMMONNAME", "ADSTREET", "ADCITY", "DISCIPL", "WEBURL"],
    map(a) {
      return {
        sub_type: "Museum",
        name: recase(clean(a.COMMONNAME)),
        address: recase(clean(a.ADSTREET)),
        town: recase(clean(a.ADCITY)),
        details: details([
          ["Museum type", MUSEUM_TYPE[clean(a.DISCIPL)] ?? null],
          ["Website", clean(a.WEBURL)?.toLowerCase() ?? null],
        ]),
      };
    },
  },
  {
    key: "little_free_libraries",
    idPrefix: "lfl",
    service: "Mapped_Little_Free_Libraries___Connecticut",
    where: "1=1",
    fields: [],
    map() {
      return { sub_type: "Little Free Library", name: null, address: null, town: null, details: [] };
    },
  },
  {
    key: "rtg_partners",
    idPrefix: "rtg",
    service: "Active_Partners_Org_N_Families_Oct_24_to_25",
    // Positive match only. Household records must never be requested.
    where: "CustomerType = 'Organization'",
    fields: ["CustomerType", "Organization_Name", "OrganizationType", "ProgramType", "Address", "City"],
    map(a) {
      if (a.CustomerType !== "Organization") {
        throw new Error(`rtg_partners returned a non-organization record (CustomerType=${a.CustomerType})`);
      }
      const program = clean(a.ProgramType);
      const sub = RTG_PROGRAM_SUBTYPE[program];
      if (!sub) throw new Error(`rtg_partners: unknown ProgramType "${program}"`);
      return {
        sub_type: sub,
        name: clean(a.Organization_Name),
        address: clean(a.Address),
        town: clean(a.City),
        details: details([
          ["Partner type", clean(a.OrganizationType)],
          ["Read to Grow program", program],
        ]),
      };
    },
  },
];

// ── Fetch helpers ───────────────────────────────────────────
async function getJson(url, label) {
  let lastErr;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      if (j.error) throw new Error(`ArcGIS error ${j.error.code}: ${j.error.message}`);
      return j;
    } catch (e) {
      lastErr = e;
      if (attempt < 3) await new Promise(res => setTimeout(res, 1000 * attempt));
    }
  }
  throw new Error(`${label}: failed after 3 attempts (${lastErr.message})\n  ${url}`);
}

const layerUrl = service => `${AGOL}/${encodeURIComponent(service)}/FeatureServer/0`;
const qs = params => new URLSearchParams(params).toString();

async function fetchLayer(layer) {
  const url = layerUrl(layer.service);
  const meta = await getJson(`${url}?f=pjson`, `${layer.key} metadata`);
  const oid = meta.objectIdField || "ObjectId";
  const pageSize = meta.maxRecordCount || 1000;
  const countRes = await getJson(`${url}/query?${qs({ where: layer.where, returnCountOnly: "true", f: "json" })}`, `${layer.key} count`);

  const features = [];
  for (let offset = 0; ; offset += pageSize) {
    const page = await getJson(`${url}/query?${qs({
      where: layer.where,
      outFields: [oid, ...layer.fields].join(","),
      returnGeometry: "true",
      outSR: "4326",
      orderByFields: oid,
      resultOffset: String(offset),
      resultRecordCount: String(pageSize),
      f: "json",
    })}`, `${layer.key} page @${offset}`);
    features.push(...(page.features || []));
    if (!page.exceededTransferLimit && (page.features || []).length < pageSize) break;
  }
  if (features.length !== countRes.count) {
    throw new Error(`${layer.key}: fetched ${features.length} features but the layer reports ${countRes.count}`);
  }
  return {
    features, oid,
    meta: {
      url, where: layer.where,
      source_count: countRes.count,
      last_edit_date: meta.editingInfo?.lastEditDate ? new Date(meta.editingInfo.lastEditDate).toISOString().slice(0, 10) : null,
    },
  };
}

// ── Geometry helpers ────────────────────────────────────────
const round5 = n => Math.round(n * 1e5) / 1e5;

function polygonsOf(geom) {
  if (geom.type === "Polygon") return [geom.coordinates];
  if (geom.type === "MultiPolygon") return geom.coordinates;
  throw new Error(`unexpected geometry ${geom.type}`);
}
function ringContains(ring, x, y) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
function geomContains(geom, x, y) {
  return polygonsOf(geom).some(([outer, ...holes]) =>
    ringContains(outer, x, y) && !holes.some(h => ringContains(h, x, y)));
}
// Approximate distance from a point to a polygon's edges, in km.
function distanceToGeomKm(geom, x, y) {
  const kx = 111.32 * Math.cos((y * Math.PI) / 180), ky = 110.57;
  let best = Infinity;
  for (const poly of polygonsOf(geom)) for (const ring of poly) {
    for (let i = 1; i < ring.length; i++) {
      const ax = (ring[i - 1][0] - x) * kx, ay = (ring[i - 1][1] - y) * ky;
      const bx = (ring[i][0] - x) * kx, by = (ring[i][1] - y) * ky;
      const dx = bx - ax, dy = by - ay, len2 = dx * dx + dy * dy;
      const t = len2 ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / len2)) : 0;
      const d = Math.hypot(ax + t * dx, ay + t * dy);
      if (d < best) best = d;
    }
  }
  return best;
}

function bboxOf(geom) {
  let w = Infinity, s = Infinity, e = -Infinity, n = -Infinity;
  for (const poly of polygonsOf(geom)) for (const [x, y] of poly[0]) {
    if (x < w) w = x; if (x > e) e = x; if (y < s) s = y; if (y > n) n = y;
  }
  return [round5(w), round5(s), round5(e), round5(n)];
}

// Douglas-Peucker on one ring. A ring that would collapse keeps its rounded
// original, so simplification can never drop a feature.
function simplifyRing(ring, tol) {
  const pts = ring.map(([x, y]) => [round5(x), round5(y)]);
  if (pts.length <= 4) return pts;
  const keep = new Uint8Array(pts.length);
  keep[0] = keep[pts.length - 1] = 1;
  const stack = [[0, pts.length - 1]];
  while (stack.length) {
    const [a, b] = stack.pop();
    const [ax, ay] = pts[a], [bx, by] = pts[b];
    const dx = bx - ax, dy = by - ay, len2 = dx * dx + dy * dy;
    let maxD = -1, idx = -1;
    for (let i = a + 1; i < b; i++) {
      const [px, py] = pts[i];
      let t = len2 ? ((px - ax) * dx + (py - ay) * dy) / len2 : 0;
      t = Math.max(0, Math.min(1, t));
      const ex = px - (ax + t * dx), ey = py - (ay + t * dy);
      const d = ex * ex + ey * ey;
      if (d > maxD) { maxD = d; idx = i; }
    }
    if (maxD > tol * tol) { keep[idx] = 1; stack.push([a, idx], [idx, b]); }
  }
  const out = pts.filter((_, i) => keep[i]);
  return out.length >= 4 ? out : pts;
}
function simplifyGeom(geom, tol) {
  const polys = polygonsOf(geom).map(poly => poly.map(r => simplifyRing(r, tol)));
  return polys.length === 1 ? { type: "Polygon", coordinates: polys[0] } : { type: "MultiPolygon", coordinates: polys };
}

// ── Areas ───────────────────────────────────────────────────
async function buildRegions() {
  const j = await getJson(`${REGIONS_URL}/query?${qs({
    where: "STATE='09'",
    outFields: "NAME,GEOID",
    returnGeometry: "true",
    outSR: "4326",
    maxAllowableOffset: "0.0003",
    geometryPrecision: "5",
    f: "geojson",
  })}`, "planning regions");
  return {
    type: "FeatureCollection",
    features: j.features
      .sort((a, b) => a.properties.NAME.localeCompare(b.properties.NAME))
      .map(f => ({ type: "Feature", properties: { name: f.properties.NAME }, geometry: simplifyGeom(f.geometry, 0.0003) })),
  };
}

async function buildDistricts() {
  const src = JSON.parse(await readFile(path.join(ROOT, "baii_data", "baii_districts.geojson"), "utf8"));
  return {
    type: "FeatureCollection",
    features: src.features
      .sort((a, b) => a.properties.name.localeCompare(b.properties.name))
      .map(f => ({ type: "Feature", properties: { name: f.properties.name }, geometry: simplifyGeom(f.geometry, 0.0003) })),
  };
}

function kpis(points) {
  const by_sub_type = Object.fromEntries(SUB_TYPES.map(s => [s.key, 0]));
  const by_category = Object.fromEntries(CATEGORIES.map(c => [c.key, 0]));
  let ratioSum = 0, ratioN = 0;
  for (const p of points) {
    by_sub_type[p.sub_type]++;
    by_category[SUB_TYPE_BY_KEY[p.sub_type].category]++;
    if (p._ratio != null) { ratioSum += p._ratio; ratioN++; }
  }
  return {
    total: points.length,
    by_category,
    by_sub_type,
    schools_with_staff: by_sub_type["School With Library Staff"],
    schools_without_staff: by_sub_type["School Without Library Staff"],
    childcare_licensed: by_sub_type["Child Care Center"] + by_sub_type["Group Child Care Home"],
    childcare_exempt: by_sub_type["Child Care Center Exempt"] + by_sub_type["Youth Camp Exempt"],
    students_per_library_staff_mean: ratioN ? Math.round((ratioSum / ratioN) * 10) / 10 : null,
    students_per_library_staff_n: ratioN,
  };
}

const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

// ── Main ────────────────────────────────────────────────────
async function main() {
  await mkdir(OUT, { recursive: true });
  const log = (...a) => process.stdout.write(a.join(" ") + "\n");

  // 1. Access points
  const points = [];
  const layerMeta = {};
  for (const layer of LAYERS) {
    const { features, oid, meta } = await fetchLayer(layer);
    let noGeom = 0;
    for (const f of features) {
      const g = f.geometry;
      if (!g || !isFinite(g.x) || !isFinite(g.y)) { noGeom++; continue; }
      const rec = layer.map(f.attributes);
      points.push({ id: `${layer.idPrefix}-${f.attributes[oid]}`, ...rec, lng: round5(g.x), lat: round5(g.y) });
    }
    layerMeta[layer.key] = { ...meta, kept: features.length - noGeom, dropped_no_geometry: noGeom };
    log(`fetched ${layer.key}: ${features.length}${noGeom ? ` (${noGeom} without geometry, dropped)` : ""}`);
  }

  const seen = new Set();
  const deduped = [];
  const dupesBySubType = {};
  for (const p of points) {
    // Details are part of the key: same-name records at one spot with
    // different staffing (e.g. two "Center School" rows) are not duplicates.
    const k = `${p.sub_type}|${p.lng}|${p.lat}|${p.name ?? ""}|${JSON.stringify(p.details)}`;
    if (seen.has(k)) { dupesBySubType[p.sub_type] = (dupesBySubType[p.sub_type] || 0) + 1; continue; }
    seen.add(k);
    deduped.push(p);
  }
  const dupeTotal = points.length - deduped.length;
  log(`exact duplicates dropped: ${dupeTotal}`, JSON.stringify(dupesBySubType));

  // 2-3. Areas
  const regions = await buildRegions();
  const districts = await buildDistricts();
  if (regions.features.length !== 9) throw new Error(`expected 9 planning regions, got ${regions.features.length}`);

  const assign = (fc, kind) => {
    const index = fc.features.map(f => ({ name: f.properties.name, geom: f.geometry, bbox: bboxOf(f.geometry) }));
    let none = 0;
    for (const p of deduped) {
      const hit = index.find(a => p.lng >= a.bbox[0] && p.lng <= a.bbox[2] && p.lat >= a.bbox[1] && p.lat <= a.bbox[3] && geomContains(a.geom, p.lng, p.lat));
      p[kind] = hit ? hit.name : null;
      if (!hit) none++;
    }
    return { index, none };
  };
  const reg = assign(regions, "region");
  const dist = assign(districts, "district");

  // The BAII district shapes are dissolved from H3 hexagons, so they leave
  // slivers along rivers and the coast uncovered. A Connecticut point in
  // such a gap goes to the nearest district if it is within SNAP_KM.
  const SNAP_KM = 2;
  let snapped = 0, snapMaxKm = 0;
  for (const p of deduped) {
    if (p.district || !p.region) continue;
    let best = null, bestKm = Infinity;
    for (const a of dist.index) {
      const km = distanceToGeomKm(a.geom, p.lng, p.lat);
      if (km < bestKm) { bestKm = km; best = a; }
    }
    if (best && bestKm <= SNAP_KM) {
      p.district = best.name;
      snapped++;
      snapMaxKm = Math.max(snapMaxKm, bestKm);
      dist.none--;
    }
  }
  log(`points in no planning region: ${reg.none}; snapped to nearest district: ${snapped} (max ${snapMaxKm.toFixed(2)} km); still in no district: ${dist.none}`);

  const areaEntries = [{ id: "statewide", type: "statewide", name: "Connecticut", bbox: [-73.72777, 40.95094, -71.78699, 42.05059], kpis: kpis(deduped) }];
  for (const [kind, idx, key] of [["region", reg.index, "region"], ["district", dist.index, "district"]]) {
    idx.forEach((a, i) => {
      areaEntries.push({ id: `${kind}:${slug(a.name)}`, type: kind, idx: i, name: a.name, bbox: a.bbox, kpis: kpis(deduped.filter(p => p[key] === a.name)) });
    });
  }

  // 4. Write points (details split out if the file gets too big)
  // Category comes from build_meta.sub_types; region and district are
  // indexes into regions.geojson / districts.geojson (and areas.json idx).
  // Null fields are left out to keep the file small.
  const regionIdx = new Map(reg.index.map((a, i) => [a.name, i]));
  const districtIdx = new Map(dist.index.map((a, i) => [a.name, i]));
  const toFeature = (p, withDetails) => {
    const props = { id: p.id, sub_type: p.sub_type };
    if (p.name) props.name = p.name;
    if (p.address) props.address = p.address;
    if (p.town) props.town = p.town;
    if (p.region) props.region = regionIdx.get(p.region);
    if (p.district) props.district = districtIdx.get(p.district);
    if (withDetails && p.details.length) props.details = p.details;
    return { type: "Feature", geometry: { type: "Point", coordinates: [p.lng, p.lat] }, properties: props };
  };
  let pointsJson = JSON.stringify({ type: "FeatureCollection", features: deduped.map(p => toFeature(p, true)) });
  let detailsSplit = false;
  if (Buffer.byteLength(pointsJson) > MAX_POINTS_BYTES) {
    detailsSplit = true;
    pointsJson = JSON.stringify({ type: "FeatureCollection", features: deduped.map(p => toFeature(p, false)) });
    const det = Object.fromEntries(deduped.filter(p => p.details.length).map(p => [p.id, p.details]));
    await writeFile(path.join(OUT, "access_point_details.json"), JSON.stringify(det));
  }
  await writeFile(path.join(OUT, "access_points.geojson"), pointsJson);
  await writeFile(path.join(OUT, "regions.geojson"), JSON.stringify(regions));
  await writeFile(path.join(OUT, "districts.geojson"), JSON.stringify(districts));
  await writeFile(path.join(OUT, "areas.json"), JSON.stringify({ areas: areaEntries }));

  // 5. Build metadata
  await writeFile(path.join(OUT, "build_meta.json"), JSON.stringify({
    build_date: new Date().toISOString().slice(0, 10),
    details_split: detailsSplit,
    categories: CATEGORIES,
    sub_types: SUB_TYPES,
    layers: layerMeta,
    duplicates_dropped: dupeTotal,
    sub_type_counts: Object.fromEntries(SUB_TYPES.map(st => {
      const fetched = points.filter(p => p.sub_type === st.key).length;
      const duplicates = dupesBySubType[st.key] || 0;
      return [st.key, { fetched, duplicates, final: fetched - duplicates }];
    })),
    points_total: deduped.length,
    points_outside_regions: reg.none,
    points_outside_districts: dist.none,
    points_snapped_to_nearest_district: snapped,
    areas: {
      regions: { source: REGIONS_URL, filter: "STATE='09' (2022+ planning regions)" },
      districts: { source: "baii_data/baii_districts.geojson" },
    },
  }, null, 1));

  log(`wrote ${deduped.length} points to ${path.relative(ROOT, OUT)}${detailsSplit ? " (details split out)" : ""}`);
  for (const f of ["access_points.geojson", "access_point_details.json", "regions.geojson", "districts.geojson", "areas.json", "build_meta.json"]) {
    try { log(`  ${f}: ${(await stat(path.join(OUT, f))).size.toLocaleString("en-US")} bytes`); } catch { /* not written */ }
  }
}

main().catch(err => { process.stderr.write(`build-explore-data failed: ${err.stack || err}\n`); process.exit(1); });
