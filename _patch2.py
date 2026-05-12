# -*- coding: utf-8 -*-
import re

path = r"C:\Users\charl\projects\clients\read-to-grow\baii-input-storymap\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# ── 1. Strip all <div class="stat-card...">...</div> from HTML ──────────────
def remove_stat_cards(html):
    out = []
    i, n = 0, len(html)
    marker = '<div class="stat-car'
    while i < n:
        if html[i:i+20] == marker:
            depth, j = 0, i
            while j < n:
                if html[j:j+4] == "<div":
                    depth += 1; j += 4
                elif html[j:j+6] == "</div>":
                    depth -= 1; j += 6
                    if depth == 0:
                        break
                else:
                    j += 1
            i = j
        else:
            out.append(html[i]); i += 1
    return "".join(out)

content = remove_stat_cards(content)

# ── 2. New <style> block ────────────────────────────────────────────────────
NEW_STYLE = """<style>
    :root {
      --navy:    #1E3A6F;
      --yellow:  #E8B43C;
      --terra:   #C45A4A;
      --white:   #FFFFFF;
      --white-2: rgba(255,255,255,0.7);
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--navy);
      color: var(--white);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 17px;
      line-height: 1.55;
    }

    .topbar {
      padding: 1.2rem 2rem;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      background: var(--navy);
      position: relative; z-index: 10;
    }
    .brand {
      font-size: 0.78rem; text-transform: uppercase;
      letter-spacing: 0.12em; color: var(--yellow); font-weight: 700;
    }

    /* ── Layout ──────────────────────────────────────────── */
    .scrolly { display: flex; align-items: flex-start; }
    .narrative { width: 40%; position: relative; z-index: 1; }
    .map-sticky {
      width: 60%; height: 100vh;
      position: sticky; top: 0;
      display: flex; align-items: center; justify-content: center;
      margin: 0; padding: 0;
    }
    #ct-map { width: 100%; height: 100%; display: block; }

    /* ── Step panels ─────────────────────────────────────── */
    .step {
      min-height: 90vh; padding: 4rem 3rem;
      display: flex; flex-direction: column; justify-content: center;
    }
    .step h2 {
      font-size: 2.2rem; font-weight: 600; line-height: 1.15;
      color: var(--white); margin-bottom: 1.25rem;
    }
    .step p { color: var(--white-2); margin-bottom: 0; max-width: 38ch; }

    /* ── Eyebrow pill ────────────────────────────────────── */
    .eyebrow {
      display: inline-block; font-size: 0.7rem;
      text-transform: uppercase; letter-spacing: 0.1em;
      color: #fff; font-weight: 700; margin-bottom: 0.85rem;
      padding: 0.25em 0.8em; border-radius: 999px;
      background: rgba(255,255,255,0.15);
    }

    /* ── Weight Block ────────────────────────────────────── */
    .weight-block {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 6px; padding: 1.5rem; margin-top: 1.75rem;
    }
    .wb-top { display: flex; align-items: flex-start; gap: 1.5rem; }
    .wb-numeral { flex-shrink: 0; }
    .wb-num {
      font-size: 3.5rem; font-weight: 700; color: var(--yellow);
      line-height: 1; display: flex; align-items: center;
      gap: 0.45rem; flex-wrap: wrap;
    }
    .wb-num.range { font-size: 2.5rem; }
    .wb-num-label {
      font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
      color: rgba(255,255,255,0.4); margin-top: 0.3rem;
    }
    .wb-unweighted-pill {
      display: inline-block; background: rgba(255,255,255,0.1);
      color: var(--yellow); font-size: 0.68rem; padding: 2px 8px;
      border-radius: 999px; font-weight: 600; vertical-align: middle;
    }
    .wb-bars {
      flex: 1; display: flex; flex-direction: column;
      gap: 0.65rem; padding-top: 0.55rem;
    }
    .wb-bar-row { display: flex; align-items: center; gap: 0.55rem; }
    .wb-bar-label {
      font-size: 0.67rem; text-transform: uppercase; letter-spacing: 0.08em;
      color: rgba(255,255,255,0.48); width: 3rem; flex-shrink: 0;
    }
    .wb-bar-track {
      display: flex; gap: 2px; height: 10px;
      width: 130px; flex-shrink: 0;
    }
    .wb-seg { flex: 1; border-radius: 2px; }
    .wb-seg.filled { background: var(--yellow); }
    .wb-seg.empty  { background: rgba(255,255,255,0.14); }
    .wb-bar-score {
      font-size: 0.8rem; color: rgba(255,255,255,0.7); white-space: nowrap;
    }
    .wb-divider {
      border: none; border-top: 1px solid rgba(255,255,255,0.12);
      margin: 1rem 0 0.65rem;
    }
    .wb-why-label {
      font-size: 0.67rem; text-transform: uppercase; letter-spacing: 0.1em;
      color: var(--yellow); margin-bottom: 0.3rem;
    }
    .wb-why-text {
      font-size: 0.92rem; color: var(--white);
      line-height: 1.55; margin: 0; max-width: 38ch;
    }

    /* ── Footer stat ─────────────────────────────────────── */
    .footer-stat {
      font-size: 0.85rem; color: rgba(255,255,255,0.5);
      font-weight: 400; margin-top: 1rem;
    }

    /* ── Chapter / closing bar chart ─────────────────────── */
    .chapter-chart {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 6px; padding: 1.5rem; margin-top: 1.75rem;
    }
    .cc-title {
      font-size: 0.67rem; text-transform: uppercase;
      letter-spacing: 0.11em; color: var(--yellow);
      font-weight: 700; margin-bottom: 1rem;
    }
    .cc-rows { display: flex; flex-direction: column; gap: 0.52rem; }
    .cc-row { display: flex; align-items: center; gap: 0.6rem; }
    .cc-name {
      font-size: 0.88rem; color: rgba(255,255,255,0.88);
      width: 10rem; flex-shrink: 0; line-height: 1.3;
    }
    .cc-bar-track {
      flex: 1; max-width: 190px; height: 10px;
      border-radius: 2px; background: rgba(255,255,255,0.08);
      position: relative; overflow: hidden; flex-shrink: 0;
    }
    .cc-bar-fill {
      position: absolute; left: 0; top: 0;
      height: 100%; border-radius: 2px; background: var(--yellow);
    }
    .cc-bar-fill.hollow {
      background: repeating-linear-gradient(
        45deg,
        rgba(232,180,60,0.55) 0px, rgba(232,180,60,0.55) 3px,
        transparent 3px, transparent 6px
      );
      width: 100% !important;
    }
    .cc-weight {
      font-size: 0.88rem; color: var(--yellow);
      font-weight: 600; width: 2.5rem;
      text-align: right; flex-shrink: 0;
    }
    .cc-footer { font-size: 0.82rem; color: rgba(255,255,255,0.48); margin-top: 1rem; }

    /* ── Closing chart overrides (step 19) ───────────────── */
    .closing-chart .cc-row {
      flex-direction: column; align-items: stretch;
      gap: 0.18rem; padding-bottom: 0.6rem;
    }
    .closing-chart .cc-row-top { display: flex; align-items: center; gap: 0.6rem; }
    .closing-chart .cc-sub {
      font-size: 0.77rem; color: rgba(255,255,255,0.36);
      font-style: italic; line-height: 1.4; padding-left: 10.6rem;
    }
    .closing-chart .cc-weight {
      color: rgba(255,255,255,0.55); font-weight: 400;
      font-size: 0.82rem; width: auto; white-space: nowrap;
    }

    /* ── Accessibility ───────────────────────────────────── */
    .sr-only {
      position: absolute; width: 1px; height: 1px;
      padding: 0; margin: -1px; overflow: hidden;
      clip: rect(0,0,0,0); white-space: nowrap; border: 0;
    }
    .narrative-end { height: 50vh; }

    @media (prefers-reduced-motion: reduce) {
      .layer { transition: none !important; }
    }

    /* ── Mobile ─────────────────────────────────────────── */
    @media (max-width: 768px) {
      .scrolly { flex-direction: column; }
      .narrative { width: 100%; order: 2; }
      .map-sticky { width: 100%; height: 50vh; position: sticky; top: 0; order: 1; }
      .step { min-height: auto; padding: 2rem 1.5rem; font-size: 16px; }
      .step h2 { font-size: 1.7rem; }
      .weight-block { padding: 1rem; }
      .wb-top { flex-direction: column; gap: 0.85rem; }
      .wb-bar-track { width: 100%; }
      .cc-bar-track { max-width: none; }
      .cc-name { width: 8rem; }
      .closing-chart .cc-sub { padding-left: 8.6rem; }
    }
  </style>"""

# ── 3. New <script> block ───────────────────────────────────────────────────
# Note: en-dash character – used directly in string literals below
ENDASH = "–"

NEW_SCRIPT = (
"""<script>
  const TYPE_META = {
    "Public Library":                   { family: "out-of-school", weight: 5.0, depth: 5, reach: 5 },
    "Bookstore":                        { family: "out-of-school", weight: 0.5, depth: 3, reach: 2 },
    "Museum":                           { family: "out-of-school", weight: 0.5, depth: 3, reach: 2 },
    "School Score 0":                   { family: "in-school", weight: 1.0, depth: 1, reach: 5, color: "#a9dadc" },
    "School Score 1":                   { family: "in-school", weight: 2.0, depth: 2, reach: 5, color: "#8db9c1" },
    "School Score 2":                   { family: "in-school", weight: 3.0, depth: 3, reach: 5, color: "#7198a7" },
    "School Score 3":                   { family: "in-school", weight: 4.0, depth: 4, reach: 5, color: "#55778c" },
    "School Score 4":                   { family: "in-school", weight: 5.0, depth: 5, reach: 5, color: "#395671" },
    "School Score 5":                   { family: "in-school", weight: 6.0, depth: 5, reach: 5, color: "#1c3557" },
    "Read to Grow BFB Birthing Center": { family: "nonprofit", weight: 2.5, depth: 5, reach: 2 },
    "Book Bank":                        { family: "nonprofit", weight: 2.0, depth: 5, reach: 2 },
    "Read to Grow BFK Organization":    { family: "nonprofit", weight: 1.0, depth: 4, reach: 4 },
    "Little Free Library":              { family: "nonprofit", weight: 0.5, depth: 2, reach: 4 },
    "Laundry Cares":                    { family: "nonprofit", weight: 0.5, depth: 3, reach: 2 },
    "Child Care Center":                { family: "childcare", weight: 1.0, depth: 2, reach: 4 },
    "Group Child Care Home":            { family: "childcare", weight: 1.0, depth: 2, reach: 3 },
    "Child Care Center Exempt":         { family: "childcare", weight: 1.0, depth: 2, reach: 3 },
    "Youth Camp Exempt":                { family: "childcare", weight: 1.0, depth: 2, reach: 2 },
    "Family Day Care":                  { family: "childcare", weight: 0.0, depth: 1, reach: 2 },
  };

  function markerRadius(weight) {
    if (weight >= 5)    return 11;
    if (weight === 2.5) return 8;
    if (weight === 2)   return 7;
    if (weight === 1)   return 5;
    if (weight === 0.5) return 3.5;
    return 3;
  }

  const CH1 = ["Public Library","Bookstore","Museum"];
  const CH2 = ["School Score 0","School Score 1","School Score 2","School Score 3","School Score 4","School Score 5"];
  const CH3 = ["Read to Grow BFB Birthing Center","Book Bank","Read to Grow BFK Organization","Little Free Library","Laundry Cares"];
  const CH4 = ["Child Care Center","Group Child Care Home","Child Care Center Exempt","Youth Camp Exempt","Family Day Care"];
  const ALL = [...CH1,...CH2,...CH3,...CH4];

  const STEPS = [
    { active: [] },
    { active: ["Public Library"] },
    { active: ["Bookstore"] },
    { active: ["Museum"] },
    { active: CH1 },
    { active: ["School Score 0"] },
    { active: ["School Score 1","School Score 2"] },
    { active: ["School Score 3","School Score 4","School Score 5"] },
    { active: CH2 },
    { active: ["Read to Grow BFB Birthing Center"] },
    { active: ["Book Bank"] },
    { active: ["Read to Grow BFK Organization"] },
    { active: ["Little Free Library"] },
    { active: ["Laundry Cares"] },
    { active: CH3 },
    { active: ["Child Care Center"] },
    { active: ["Group Child Care Home","Child Care Center Exempt","Youth Camp Exempt"] },
    { active: ["Family Day Care"] },
    { active: CH4 },
    { active: ALL },
  ];

  const STEP_DATA = {
    1:  { weight: "5.0",          depth: 5, reach: 5,                             count: "240",
          why: "Free, permanent, staffed, purpose-built for reading — and serves everyone in the community." },
    2:  { weight: "0.5",          depth: 3, reach: 2,                             count: "247",
          why: "Books are everywhere on the shelf, but you have to pay for them — and bookstores cluster where access is already strongest." },
    3:  { weight: "0.5",          depth: 3, reach: 2,                             count: "21",
          why: "A museum won’t lend you a book. It earns its weight by making reading feel like a place a child goes." },
    5:  { weight: "1.0",          depth: 1, reach: 5,                             count: "700",
          why: "Children attend every day, but with no library and no librarian, the building isn’t doing the work." },
    6:  { weight: "2.0–3.0", depthMin: 2, depthMax: 3, reach: 5,            count: "317",
          why: "Some staff support for books, but no certified library program — partial credit for partial infrastructure." },
    7:  { weight: "4.0–6.0", depthMin: 4, depthMax: 5, reach: 5,            count: "477",
          why: "A real library, with a real librarian, where books anchor the school day. The highest-weighted in-school score." },
    9:  { weight: "2.5",          depth: 5, reach: 2,                             count: "61",
          why: "Places a book in the hands of a new parent at the moment a child is born — the deepest possible act of book access." },
    10: { weight: "2.0",          depth: 5, reach: 2,                             count: "7",
          why: "Direct, free, large-scale book distribution. Pure depth — limited only by how few sites exist." },
    11: { weight: "1.0",          depth: 4, reach: 4,                             count: "574",
          why: "An active partner that requests and distributes RTG books. Where the program’s reach actually lands." },
    12: { weight: "0.5",          depth: 2, reach: 4,                             count: "1,044",
          why: "Free books on a sidewalk: shallow depth per site, but Connecticut has a thousand of them." },
    13: { weight: "0.5",          depth: 3, reach: 2,                             count: "8",
          why: "A reading nook where families already wait — small footprint, smart placement." },
    15: { weight: "1.0",          depth: 2, reach: 4,                             count: "1,363",
          why: "Where the youngest children spend full days. Books are often welcome but rarely the mission." },
    16: { weight: "1.0",          depth: 2, reachMin: 2, reachMax: 3,            count: "132",
          why: "Smaller licensed care settings where books vary by provider — counted, lightly weighted." },
    17: { weight: "0.0",          unweighted: true, depth: 1, reach: 2,          count: "1,790",
          why: "Tiny, home-based, unverified for books. Counted on the map for context; not yet weighted in the index." },
  };

  const CHAPTER_DATA = {
    4: {
      title: "In this chapter",
      rows: [
        { name: "Public Library", weight: 5.0 },
        { name: "Bookstore",      weight: 0.5 },
        { name: "Museum",         weight: 0.5 },
      ],
      footer: "3 types · 508 access points",
    },
    8: {
      title: "In this chapter",
      rows: [
        { name: "Score 5 — Full program", weight: 6.0 },
        { name: "Score 4",                     weight: 5.0 },
        { name: "Score 3",                     weight: 4.0 },
        { name: "Score 2",                     weight: 3.0 },
        { name: "Score 1",                     weight: 2.0 },
        { name: "Score 0 — No library",   weight: 1.0 },
      ],
      footer: "6 staffing levels · 1,494 schools",
    },
    14: {
      title: "In this chapter",
      rows: [
        { name: "RTG Birthing Center", weight: 2.5 },
        { name: "Book Bank",           weight: 2.0 },
        { name: "RTG Partner Org",     weight: 1.0 },
        { name: "Little Free Library", weight: 0.5 },
        { name: "Laundry Cares",       weight: 0.5 },
      ],
      footer: "5 types · 1,694 access points",
    },
    18: {
      title: "In this chapter",
      rows: [
        { name: "Child Care Center",  weight: 1.0 },
        { name: "Group Child Care",   weight: 1.0 },
        { name: "CC Center Exempt",   weight: 1.0 },
        { name: "Youth Camp Exempt",  weight: 1.0 },
        { name: "Family Day Care",    weight: 0.0, hollow: true },
      ],
      footer: "4 types · 3,285 locations",
    },
  };

  const CLOSING_DATA = {
    title: "The full picture",
    families: [
      { name: "Out-of-School", count: 508,  countStr: "508",   sub: "Libraries do most of the heavy lifting." },
      { name: "In-School",     count: 1494, countStr: "1,494", sub: "Reach is universal; depth depends on staffing." },
      { name: "Nonprofit",     count: 1694, countStr: "1,694", sub: "Densest, most distributed, most volunteer-built." },
      { name: "Childcare",     count: 3285, countStr: "3,285", sub: "The largest and the lightest-weighted family." },
    ],
    footer: "9,511 access points across Connecticut",
    maxCount: 3285,
  };

  async function init() {
    const [points, stateTopo, countyTopo] = await Promise.all([
      fetch("./points.json").then(r => { if (!r.ok) throw new Error("points.json"); return r.json(); }),
      fetch("./states.json").then(r => { if (!r.ok) throw new Error("states.json"); return r.json(); }),
      fetch("./counties.json").then(r => { if (!r.ok) throw new Error("counties.json"); return r.json(); }),
    ]);

    const ctFeature = topojson.feature(stateTopo, stateTopo.objects.states)
      .features.find(d => +d.id === 9);
    if (!ctFeature) { console.error("CT state not found"); return; }

    const ctCountyMesh = topojson.mesh(
      countyTopo, countyTopo.objects.counties,
      (a, b) => a !== b && Math.floor(a.id / 1000) === 9 && Math.floor(b.id / 1000) === 9
    );

    const W = 1200, H = 800;
    const svg = d3.select("#ct-map");

    const defs = svg.append("defs");
    const filt = defs.append("filter")
      .attr("id", "state-shadow").attr("x", "-20%").attr("y", "-20%")
      .attr("width", "140%").attr("height", "140%");
    filt.append("feDropShadow")
      .attr("dx", 0).attr("dy", 4).attr("stdDeviation", 8)
      .attr("flood-color", "#000").attr("flood-opacity", 0.35);

    const projection = d3.geoMercator().fitSize([W, H], ctFeature);
    const pathGen    = d3.geoPath().projection(projection);
    const mapG       = svg.append("g").attr("id", "map-g");

    mapG.append("g").attr("class", "ct-base")
      .append("path").datum(ctFeature).attr("d", pathGen)
      .attr("fill", "#FFFFFF").attr("stroke", "#4A7CB5").attr("stroke-width", 1)
      .attr("filter", "url(#state-shadow)");

    mapG.append("path").datum(ctCountyMesh).attr("d", pathGen)
      .attr("fill", "none").attr("stroke", "#4A7CB5")
      .attr("stroke-width", 0.6).attr("stroke-opacity", 0.55);

    const projected = points.map(d => {
      const [px, py] = projection([d.lng, d.lat]);
      return { type: d.type, px, py };
    });

    const layers = {};
    ALL.forEach(typeName => {
      const meta = TYPE_META[typeName];
      const pts  = projected.filter(d => d.type === typeName);
      const r    = markerRadius(meta.weight);
      const g    = mapG.append("g")
        .attr("class", "layer").attr("data-type", typeName)
        .style("opacity", 0).style("pointer-events", "none")
        .style("filter", "drop-shadow(0 1px 2px rgba(0,0,0,0.45))");

      if (meta.family === "out-of-school") {
        g.selectAll("circle").data(pts).join("circle")
          .attr("cx", d => d.px).attr("cy", d => d.py).attr("r", r)
          .attr("fill", "#E8B43C").attr("stroke", "rgba(0,0,0,0.25)").attr("stroke-width", 1.5);
      } else if (meta.family === "in-school") {
        const side = r * 2;
        g.selectAll("rect").data(pts).join("rect")
          .attr("x", d => d.px - r).attr("y", d => d.py - r)
          .attr("width", side).attr("height", side)
          .attr("fill", meta.color).attr("stroke", "rgba(0,0,0,0.25)").attr("stroke-width", 1);
      } else if (meta.family === "nonprofit") {
        g.selectAll("polygon").data(pts).join("polygon")
          .attr("points", d => `${d.px},${d.py-r} ${d.px+r},${d.py} ${d.px},${d.py+r} ${d.px-r},${d.py}`)
          .attr("fill", "#C45A4A").attr("stroke", "rgba(0,0,0,0.25)").attr("stroke-width", 1.5);
      } else if (meta.family === "childcare") {
        if (typeName === "Family Day Care") {
          g.selectAll("circle").data(pts).join("circle")
            .attr("cx", d => d.px).attr("cy", d => d.py).attr("r", 5)
            .attr("fill", "none").attr("stroke", "#1c3557")
            .attr("stroke-width", 1.5).attr("stroke-opacity", 0.85);
        } else {
          g.selectAll("circle").data(pts).join("circle")
            .attr("cx", d => d.px).attr("cy", d => d.py).attr("r", r)
            .attr("fill", "#1c3557").attr("fill-opacity", 0.82)
            .attr("stroke", "rgba(0,0,0,0.25)").attr("stroke-width", 1);
        }
      }
      layers[typeName] = g;
    });

    const zoom = d3.zoom()
      .scaleExtent([1, 12])
      .on("zoom", event => mapG.attr("transform", event.transform));
    svg.call(zoom);

    // Eyebrow pill coloring
    const EYEBROW_COLORS = {
      "out-of-school": "#E8B43C",
      "in-school":     "#467c9d",
      "nonprofit":     "#C45A4A",
      "childcare":     "#1c3557",
    };
    document.querySelectorAll(".eyebrow").forEach(el => {
      const t = el.textContent.toLowerCase();
      if (t.includes("out-of-school"))  el.style.background = EYEBROW_COLORS["out-of-school"];
      else if (t.includes("in-school")) el.style.background = EYEBROW_COLORS["in-school"];
      else if (t.includes("nonprofit")) el.style.background = EYEBROW_COLORS["nonprofit"];
      else if (t.includes("childcare")) el.style.background = EYEBROW_COLORS["childcare"];
    });

    // ── Panel builders ───────────────────────────────────────
    function segs(filled) {
      let h = "";
      for (let k = 0; k < 5; k++)
        h += `<div class="wb-seg ${k < filled ? "filled" : "empty"}"></div>`;
      return h;
    }

    function makeWeightBlock(d) {
      const isRange   = String(d.weight).indexOf("–") !== -1;
      const depthFill = d.depthMax !== undefined ? d.depthMax : d.depth;
      const reachFill = d.reachMax !== undefined ? d.reachMax : d.reach;
      const dScore    = d.depthMax !== undefined
        ? `${d.depthMin}–${d.depthMax} / 5`
        : `${d.depth} / 5`;
      const rScore    = d.reachMax !== undefined
        ? `${d.reachMin}–${d.reachMax} / 5`
        : `${d.reach} / 5`;
      const numHtml   = d.unweighted
        ? `<div class="wb-num">${d.weight}<span class="wb-unweighted-pill">unweighted</span></div>`
        : `<div class="wb-num${isRange ? " range" : ""}">${d.weight}</div>`;
      return `
        <div class="weight-block">
          <div class="wb-top">
            <div class="wb-numeral">
              ${numHtml}
              <div class="wb-num-label">weight</div>
            </div>
            <div class="wb-bars">
              <div class="wb-bar-row">
                <div class="wb-bar-label">Depth</div>
                <div class="wb-bar-track">${segs(depthFill)}</div>
                <div class="wb-bar-score">${dScore}</div>
              </div>
              <div class="wb-bar-row">
                <div class="wb-bar-label">Reach</div>
                <div class="wb-bar-track">${segs(reachFill)}</div>
                <div class="wb-bar-score">${rScore}</div>
              </div>
            </div>
          </div>
          <hr class="wb-divider">
          <div class="wb-why-label">Why this weight?</div>
          <p class="wb-why-text">${d.why}</p>
        </div>`;
    }

    function makeChapterChart(ch) {
      const rows = ch.rows.map(r => {
        const pct      = r.hollow ? 0 : +(r.weight / 6.0 * 100).toFixed(1);
        const fillHtml = r.hollow
          ? `<div class="cc-bar-fill hollow"></div>`
          : `<div class="cc-bar-fill" style="width:${pct}%"></div>`;
        return `
          <div class="cc-row">
            <div class="cc-name">${r.name}</div>
            <div class="cc-bar-track">${fillHtml}</div>
            <div class="cc-weight">${r.hollow ? "0.0" : r.weight.toFixed(1)}</div>
          </div>`;
      }).join("");
      return `
        <div class="chapter-chart">
          <div class="cc-title">${ch.title}</div>
          <div class="cc-rows">${rows}</div>
          <div class="cc-footer">${ch.footer}</div>
        </div>`;
    }

    function makeClosingChart(cl) {
      const rows = cl.families.map(f => {
        const pct = +(f.count / cl.maxCount * 100).toFixed(1);
        return `
          <div class="cc-row">
            <div class="cc-row-top">
              <div class="cc-name">${f.name}</div>
              <div class="cc-bar-track"><div class="cc-bar-fill" style="width:${pct}%"></div></div>
              <div class="cc-weight">${f.countStr} sites</div>
            </div>
            <div class="cc-sub">${f.sub}</div>
          </div>`;
      }).join("");
      return `
        <div class="chapter-chart closing-chart">
          <div class="cc-title">${cl.title}</div>
          <div class="cc-rows">${rows}</div>
          <div class="cc-footer">${cl.footer}</div>
        </div>`;
    }

    document.querySelectorAll(".step[data-step]").forEach(el => {
      const i = +el.dataset.step;
      if (STEP_DATA[i]) {
        const d = STEP_DATA[i];
        el.insertAdjacentHTML("beforeend", makeWeightBlock(d));
        el.insertAdjacentHTML("beforeend",
          `<p class="footer-stat">${d.count} sites in Connecticut</p>`);
      } else if (CHAPTER_DATA[i]) {
        el.insertAdjacentHTML("beforeend", makeChapterChart(CHAPTER_DATA[i]));
      } else if (i === 19) {
        el.insertAdjacentHTML("beforeend", makeClosingChart(CLOSING_DATA));
      }
    });

    // ── Map state + Scrollama ─────────────────────────────────
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function applyMapState(index) {
      const state = STEPS[Math.min(index, STEPS.length - 1)];
      const dur   = reducedMotion ? 0 : 200;
      ALL.forEach(t => {
        const opacity = state.active.includes(t) ? 1 : 0;
        layers[t].style("pointer-events", opacity === 1 ? "auto" : "none");
        layers[t].transition().duration(dur).ease(d3.easeLinear).style("opacity", opacity);
      });
      svg.transition().duration(400).call(zoom.transform, d3.zoomIdentity);
    }

    applyMapState(0);

    const scroller = scrollama();
    scroller
      .setup({ step: ".step", offset: 0.55, debug: false })
      .onStepEnter(({ index }) => applyMapState(index));
    window.addEventListener("resize", () => scroller.resize());
  }

  init().catch(err => console.error("Init failed:", err));
</script>""")

# ── Apply style replacement ─────────────────────────────────────────────────
style_start = content.index("<style>")
style_end   = content.index("</style>") + len("</style>")
content = content[:style_start] + NEW_STYLE + content[style_end:]

# ── Apply script replacement ────────────────────────────────────────────────
script_start = content.index("<script>")
script_end   = content.rindex("</script>") + len("</script>")
content = content[:script_start] + NEW_SCRIPT + content[script_end:]

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done. File length: {len(content)} chars")
