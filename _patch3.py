# -*- coding: utf-8 -*-
path = r"C:\Users\charl\projects\clients\read-to-grow\baii-input-storymap\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# ── 1. Update chapter nav CSS ───────────────────────────────────────────────
OLD_NAV_CSS = """    /* ── Chapter nav ─────────────────────────────────────── */
    .chapter-nav {
      position: sticky;
      top: 0;
      z-index: 30;
      background: var(--navy);
      border-bottom: 1px solid rgba(255,255,255,0.08);
      display: flex;
      gap: 0;
      padding: 0 2rem;
      overflow-x: auto;
    }
    .chapter-nav a {
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: rgba(255,255,255,0.5);
      font-weight: 600;
      padding: 0.65rem 1.1rem;
      text-decoration: none;
      border-bottom: 2px solid transparent;
      white-space: nowrap;
      transition: color 0.15s, border-color 0.15s;
    }
    .chapter-nav a:hover { color: var(--white); }
    .chapter-nav a.active { color: var(--yellow); border-bottom-color: var(--yellow); }"""

NEW_NAV_CSS = """    /* ── Chapter nav ─────────────────────────────────────── */
    .chapter-nav {
      position: sticky;
      top: 0;
      z-index: 30;
      background: var(--navy);
      border-bottom: 1px solid rgba(255,255,255,0.08);
      display: flex;
      align-items: stretch;
      justify-content: space-between;
      overflow-x: auto;
    }
    .ch-tabs { display: flex; }
    .chapter-nav a {
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: rgba(255,255,255,0.92);
      font-weight: 600;
      padding: 0.65rem 1.15rem;
      text-decoration: none;
      border-bottom: 3px solid transparent;
      white-space: nowrap;
      filter: brightness(0.68);
      transition: filter 0.15s, border-color 0.15s;
    }
    .chapter-nav a:hover { filter: brightness(0.85); }
    .chapter-nav a.active { filter: brightness(1.1); border-bottom-color: rgba(255,255,255,0.55); }
    .nav-right {
      display: flex;
      align-items: center;
      padding: 0 1.5rem 0 1rem;
      flex-shrink: 0;
      border-left: 1px solid rgba(255,255,255,0.08);
      gap: 0.5rem;
    }
    .nav-right label {
      font-size: 0.65rem;
      text-transform: uppercase;
      letter-spacing: 0.09em;
      color: rgba(255,255,255,0.4);
      white-space: nowrap;
    }
    .district-select {
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.18);
      border-radius: 4px;
      color: rgba(255,255,255,0.82);
      font-size: 0.72rem;
      font-family: inherit;
      padding: 0.28rem 0.55rem;
      cursor: pointer;
      max-width: 210px;
      outline: none;
    }
    .district-select:focus { border-color: rgba(255,255,255,0.4); }
    .district-select option { background: #1E3A6F; color: #fff; }"""

content = content.replace(OLD_NAV_CSS, NEW_NAV_CSS, 1)

# ── 2. Update nav HTML ──────────────────────────────────────────────────────
OLD_NAV_HTML = """<nav class="chapter-nav" aria-label="Chapter navigation">
  <a href="#ch-1">Out-of-School</a>
  <a href="#ch-5">In-School</a>
  <a href="#ch-9">Nonprofit</a>
  <a href="#ch-15">Childcare</a>
</nav>"""

NEW_NAV_HTML = """<nav class="chapter-nav" aria-label="Chapter navigation">
  <div class="ch-tabs">
    <a href="#ch-1"  style="background:#E8B43C">Out-of-School</a>
    <a href="#ch-5"  style="background:#467c9d">In-School</a>
    <a href="#ch-9"  style="background:#C45A4A">Nonprofit</a>
    <a href="#ch-15" style="background:#1c3557">Childcare</a>
  </div>
  <div class="nav-right">
    <label for="district-select">School district</label>
    <select class="district-select" id="district-select">
      <option value="">All Connecticut</option>
    </select>
  </div>
</nav>"""

content = content.replace(OLD_NAV_HTML, NEW_NAV_HTML, 1)

# ── 3. Replace the entire <script> block ────────────────────────────────────
NEW_SCRIPT = """<script>
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
    1:  { weight: "5.0",     depth: 5, reach: 5,               count: "240",
          why: "Free, permanent, staffed, purpose-built for reading — and serves everyone in the community." },
    2:  { weight: "0.5",     depth: 3, reach: 2,               count: "247",
          why: "Books are everywhere on the shelf, but you have to pay for them — and bookstores cluster where access is already strongest." },
    3:  { weight: "0.5",     depth: 3, reach: 2,               count: "21",
          why: "A museum won't lend you a book. It earns its weight by making reading feel like a place a child goes." },
    5:  { weight: "1.0",     depth: 1, reach: 5,               count: "700",
          why: "Children attend every day, but with no library and no librarian, the building isn't doing the work." },
    6:  { weight: "2.0–3.0", depthMin: 2, depthMax: 3, reach: 5, count: "317",
          why: "Some staff support for books, but no certified library program — partial credit for partial infrastructure." },
    7:  { weight: "4.0–6.0", depthMin: 4, depthMax: 5, reach: 5, count: "477",
          why: "A real library, with a real librarian, where books anchor the school day. The highest-weighted in-school score." },
    9:  { weight: "2.5",     depth: 5, reach: 2,               count: "61",
          why: "Places a book in the hands of a new parent at the moment a child is born — the deepest possible act of book access." },
    10: { weight: "2.0",     depth: 5, reach: 2,               count: "7",
          why: "Direct, free, large-scale book distribution. Pure depth — limited only by how few sites exist." },
    11: { weight: "1.0",     depth: 4, reach: 4,               count: "574",
          why: "An active partner that requests and distributes RTG books. Where the program's reach actually lands." },
    12: { weight: "0.5",     depth: 2, reach: 4,               count: "1,044",
          why: "Free books on a sidewalk: shallow depth per site, but Connecticut has a thousand of them." },
    13: { weight: "0.5",     depth: 3, reach: 2,               count: "8",
          why: "A reading nook where families already wait — small footprint, smart placement." },
    15: { weight: "1.0",     depth: 2, reach: 4,               count: "1,363",
          why: "Where the youngest children spend full days. Books are often welcome but rarely the mission." },
    16: { weight: "1.0",     depth: 2, reachMin: 2, reachMax: 3, count: "132",
          why: "Smaller licensed care settings where books vary by provider — counted, lightly weighted." },
    17: { weight: "0.0",     unweighted: true, depth: 1, reach: 2, count: "1,790",
          why: "Tiny, home-based, unverified for books. Counted on the map for context; not yet weighted in the index." },
  };

  const CHAPTER_DATA = {
    4:  { title: "In this chapter",
          rows: [ { name: "Public Library", weight: 5.0 }, { name: "Bookstore", weight: 0.5 }, { name: "Museum", weight: 0.5 } ],
          footer: "3 types · 508 access points" },
    8:  { title: "In this chapter",
          rows: [ { name: "Score 5 — Full program", weight: 6.0 }, { name: "Score 4", weight: 5.0 }, { name: "Score 3", weight: 4.0 },
                  { name: "Score 2", weight: 3.0 }, { name: "Score 1", weight: 2.0 }, { name: "Score 0 — No library", weight: 1.0 } ],
          footer: "6 staffing levels · 1,494 schools" },
    14: { title: "In this chapter",
          rows: [ { name: "RTG Birthing Center", weight: 2.5 }, { name: "Book Bank", weight: 2.0 },
                  { name: "RTG Partner Org", weight: 1.0 }, { name: "Little Free Library", weight: 0.5 }, { name: "Laundry Cares", weight: 0.5 } ],
          footer: "5 types · 1,694 access points" },
    18: { title: "In this chapter",
          rows: [ { name: "Child Care Center", weight: 1.0 }, { name: "Group Child Care", weight: 1.0 },
                  { name: "CC Center Exempt", weight: 1.0 }, { name: "Youth Camp Exempt", weight: 1.0 },
                  { name: "Family Day Care", weight: 0.0, hollow: true } ],
          footer: "4 types · 3,285 locations" },
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
    const [points, stateTopo, countyTopo, districtGeoJSON] = await Promise.all([
      fetch("./points.json").then(r => { if (!r.ok) throw new Error("points.json"); return r.json(); }),
      fetch("./states.json").then(r => { if (!r.ok) throw new Error("states.json"); return r.json(); }),
      fetch("./counties.json").then(r => { if (!r.ok) throw new Error("counties.json"); return r.json(); }),
      fetch("./districts.json").then(r => { if (!r.ok) throw new Error("districts.json"); return r.json(); }),
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

    // State shadow filter
    const shadowFilt = defs.append("filter")
      .attr("id", "state-shadow").attr("x", "-20%").attr("y", "-20%")
      .attr("width", "140%").attr("height", "140%");
    shadowFilt.append("feDropShadow")
      .attr("dx", 0).attr("dy", 4).attr("stdDeviation", 8)
      .attr("flood-color", "#000").attr("flood-opacity", 0.35);

    // District feather filter — blurs white shape in the mask to create soft edge
    const featherFilt = defs.append("filter")
      .attr("id", "feather-filt")
      .attr("x", "-60%").attr("y", "-60%")
      .attr("width", "220%").attr("height", "220%");
    featherFilt.append("feGaussianBlur")
      .attr("in", "SourceGraphic").attr("stdDeviation", 22);

    // District mask: black background + blurred white district shape
    // Applied to pointsG (inside mapG) so coordinates are in mapG local space
    const districtMask = defs.append("mask").attr("id", "district-fade-mask");
    districtMask.append("rect")
      .attr("x", -600).attr("y", -600)
      .attr("width", W + 1200).attr("height", H + 1200)
      .attr("fill", "black");
    const maskPath = districtMask.append("path")
      .attr("fill", "white")
      .attr("filter", "url(#feather-filt)");

    const projection = d3.geoMercator().fitSize([W, H], ctFeature);
    const pathGen    = d3.geoPath().projection(projection);
    const mapG       = svg.append("g").attr("id", "map-g");

    // CT base + county lines
    mapG.append("g").attr("class", "ct-base")
      .append("path").datum(ctFeature).attr("d", pathGen)
      .attr("fill", "#FFFFFF").attr("stroke", "#4A7CB5").attr("stroke-width", 1)
      .attr("filter", "url(#state-shadow)");

    mapG.append("path").datum(ctCountyMesh).attr("d", pathGen)
      .attr("fill", "none").attr("stroke", "#4A7CB5")
      .attr("stroke-width", 0.6).attr("stroke-opacity", 0.55);

    // District layers (below points)
    const districtBgG  = mapG.append("g").attr("id", "district-bg").style("display", "none");
    const districtHlG  = mapG.append("g").attr("id", "district-hl").style("display", "none");
    const districtHlPath = districtHlG.append("path")
      .attr("fill", "rgba(255,255,255,0.1)")
      .attr("stroke", "white").attr("stroke-width", 1.5);

    // pointsG — all point layers live here; mask applied when district selected
    const pointsG = mapG.append("g").attr("id", "points-g");

    const projected = points.map(d => {
      const [px, py] = projection([d.lng, d.lat]);
      return { type: d.type, px, py, lng: d.lng, lat: d.lat };
    });

    const layers = {};
    ALL.forEach(typeName => {
      const meta = TYPE_META[typeName];
      const pts  = projected.filter(d => d.type === typeName);
      const r    = markerRadius(meta.weight);
      const g    = pointsG.append("g")
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

    // Zoom
    const zoom = d3.zoom()
      .scaleExtent([1, 12])
      .on("zoom", event => mapG.attr("transform", event.transform));
    svg.call(zoom);

    // ── District filter ─────────────────────────────────────
    const districtFeatures = districtGeoJSON.features;

    // Draw all district outlines (shown only when a district is selected)
    districtBgG.selectAll("path").data(districtFeatures).join("path")
      .attr("d", pathGen)
      .attr("fill", "none")
      .attr("stroke", "rgba(255,255,255,0.28)")
      .attr("stroke-width", 0.6);

    // Populate select
    const districtSelect = document.getElementById("district-select");
    districtFeatures.forEach((f, i) => {
      const opt = document.createElement("option");
      opt.value = i;
      opt.textContent = f.properties.District_Name_1;
      districtSelect.appendChild(opt);
    });

    let activeDistrictIdx = null;

    function applyDistrictFilter(idx) {
      activeDistrictIdx = idx === "" ? null : +idx;

      if (activeDistrictIdx === null) {
        // Clear filter
        pointsG.attr("mask", null);
        maskPath.attr("d", "");
        districtBgG.style("display", "none");
        districtHlG.style("display", "none");
        svg.transition().duration(600).call(zoom.transform, d3.zoomIdentity);
        return;
      }

      const feature = districtFeatures[activeDistrictIdx];

      // Update feather mask path (in mapG local = unzoomed SVG coordinates)
      maskPath.attr("d", pathGen(feature));
      pointsG.attr("mask", "url(#district-fade-mask)");

      // Show district layers
      districtBgG.style("display", null);
      districtHlG.style("display", null);
      districtHlPath.attr("d", pathGen(feature));

      // Zoom to district bounds
      const [[x0, y0], [x1, y1]] = pathGen.bounds(feature);
      const scale = Math.min(12, 0.78 / Math.max((x1 - x0) / W, (y1 - y0) / H));
      const tx = W / 2 - scale * (x0 + x1) / 2;
      const ty = H / 2 - scale * (y0 + y1) / 2;
      svg.transition().duration(600).call(
        zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale)
      );
    }

    districtSelect.addEventListener("change", e => applyDistrictFilter(e.target.value));

    // ── Eyebrow pill coloring ───────────────────────────────
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
        ? `${d.depthMin}–${d.depthMax} / 5` : `${d.depth} / 5`;
      const rScore    = d.reachMax !== undefined
        ? `${d.reachMin}–${d.reachMax} / 5` : `${d.reach} / 5`;
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
    const navLinks  = Array.from(document.querySelectorAll(".chapter-nav a"));
    const chStarts  = [1, 5, 9, 15];

    function updateNav(index) {
      let active = -1;
      for (let i = chStarts.length - 1; i >= 0; i--) {
        if (index >= chStarts[i]) { active = i; break; }
      }
      navLinks.forEach((a, i) => a.classList.toggle("active", i === active));
    }

    function applyMapState(index) {
      const state = STEPS[Math.min(index, STEPS.length - 1)];
      const dur   = reducedMotion ? 0 : 200;
      ALL.forEach(t => {
        const opacity = state.active.includes(t) ? 1 : 0;
        layers[t].style("pointer-events", opacity === 1 ? "auto" : "none");
        layers[t].transition().duration(dur).ease(d3.easeLinear).style("opacity", opacity);
      });
      // Reset zoom only if no district filter is active
      if (activeDistrictIdx === null) {
        svg.transition().duration(400).call(zoom.transform, d3.zoomIdentity);
      }
    }

    applyMapState(0);

    const scroller = scrollama();
    scroller
      .setup({ step: ".step", offset: 0.55, debug: false })
      .onStepEnter(({ index }) => { applyMapState(index); updateNav(index); });
    window.addEventListener("resize", () => scroller.resize());
  }

  init().catch(err => console.error("Init failed:", err));
</script>"""

script_start = content.index("<script>")
script_end   = content.rindex("</script>") + len("</script>")
content = content[:script_start] + NEW_SCRIPT + content[script_end:]

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done. File length: {len(content)} chars")
