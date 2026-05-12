import re, sys

NEW_SCRIPT = """\
<script>
  const TYPE_META = {
    "Public Library":                   { family: "out-of-school", weight: 5.0, depth: 5, reach: 5 },
    "Bookstore":                        { family: "out-of-school", weight: 0.5, depth: 3, reach: 2 },
    "Museum":                           { family: "out-of-school", weight: 0.5, depth: 3, reach: 2 },
    "School Score 0":                   { family: "in-school",     weight: 1.0, depth: 1, reach: 5, color: "#a9dadc" },
    "School Score 1":                   { family: "in-school",     weight: 2.0, depth: 2, reach: 5, color: "#8db9c1" },
    "School Score 2":                   { family: "in-school",     weight: 3.0, depth: 3, reach: 5, color: "#7198a7" },
    "School Score 3":                   { family: "in-school",     weight: 4.0, depth: 4, reach: 5, color: "#55778c" },
    "School Score 4":                   { family: "in-school",     weight: 5.0, depth: 5, reach: 5, color: "#395671" },
    "School Score 5":                   { family: "in-school",     weight: 6.0, depth: 5, reach: 5, color: "#1c3557" },
    "Read to Grow BFB Birthing Center": { family: "nonprofit",     weight: 2.5, depth: 5, reach: 2 },
    "Book Bank":                        { family: "nonprofit",     weight: 2.0, depth: 5, reach: 2 },
    "Read to Grow BFK Organization":    { family: "nonprofit",     weight: 1.0, depth: 4, reach: 4 },
    "Little Free Library":              { family: "nonprofit",     weight: 0.5, depth: 2, reach: 4 },
    "Laundry Cares":                    { family: "nonprofit",     weight: 0.5, depth: 3, reach: 2 },
    "Child Care Center":                { family: "childcare",     weight: 1.0, depth: 2, reach: 4 },
    "Group Child Care Home":            { family: "childcare",     weight: 1.0, depth: 2, reach: 3 },
    "Child Care Center Exempt":         { family: "childcare",     weight: 1.0, depth: 2, reach: 3 },
    "Youth Camp Exempt":                { family: "childcare",     weight: 1.0, depth: 2, reach: 2 },
    "Family Day Care":                  { family: "childcare",     weight: 0.0, depth: 1, reach: 2 },
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

  const CT_COUNTIES = [
    { id: 9001, name: "Fairfield" },
    { id: 9003, name: "Hartford" },
    { id: 9005, name: "Litchfield" },
    { id: 9007, name: "Middlesex" },
    { id: 9009, name: "New Haven" },
    { id: 9011, name: "New London" },
    { id: 9013, name: "Tolland" },
    { id: 9015, name: "Windham" },
  ];

  const STEPS = [
    { active: [],                                                                                              faded: [], background: [] },
    { active: ["Public Library"],                                                                              faded: [], background: [] },
    { active: ["Bookstore"],                                                                                   faded: ["Public Library"], background: [] },
    { active: ["Museum"],                                                                                      faded: ["Public Library","Bookstore"], background: [] },
    { active: CH1,                                                                                             faded: [], background: [] },
    { active: ["School Score 0"],                                                                              faded: [], background: CH1 },
    { active: ["School Score 1","School Score 2"],                                                             faded: ["School Score 0"], background: CH1 },
    { active: ["School Score 3","School Score 4","School Score 5"],                                           faded: ["School Score 0","School Score 1","School Score 2"], background: CH1 },
    { active: CH2,                                                                                             faded: [], background: CH1 },
    { active: ["Read to Grow BFB Birthing Center"],                                                           faded: [], background: [...CH1,...CH2] },
    { active: ["Book Bank"],                                                                                   faded: ["Read to Grow BFB Birthing Center"], background: [...CH1,...CH2] },
    { active: ["Read to Grow BFK Organization"],                                                              faded: ["Read to Grow BFB Birthing Center","Book Bank"], background: [...CH1,...CH2] },
    { active: ["Little Free Library"],                                                                        faded: ["Read to Grow BFB Birthing Center","Book Bank","Read to Grow BFK Organization"], background: [...CH1,...CH2] },
    { active: ["Laundry Cares"],                                                                              faded: ["Read to Grow BFB Birthing Center","Book Bank","Read to Grow BFK Organization","Little Free Library"], background: [...CH1,...CH2] },
    { active: CH3,                                                                                            faded: [], background: [...CH1,...CH2] },
    { active: ["Child Care Center"],                                                                          faded: [], background: [...CH1,...CH2,...CH3] },
    { active: ["Group Child Care Home","Child Care Center Exempt","Youth Camp Exempt"],                       faded: ["Child Care Center"], background: [...CH1,...CH2,...CH3] },
    { active: ["Family Day Care"],                                                                            faded: ["Child Care Center","Group Child Care Home","Child Care Center Exempt","Youth Camp Exempt"], background: [...CH1,...CH2,...CH3] },
    { active: CH4,                                                                                            faded: [], background: [...CH1,...CH2,...CH3] },
    { active: ALL,                                                                                            faded: [], background: [] },
  ];

  async function init() {
    const [points, stateTopo, countyTopo] = await Promise.all([
      fetch("./points.json").then(r => { if (!r.ok) throw new Error("points.json"); return r.json(); }),
      fetch("./states.json").then(r => { if (!r.ok) throw new Error("states.json"); return r.json(); }),
      fetch("./counties.json").then(r => { if (!r.ok) throw new Error("counties.json"); return r.json(); }),
    ]);

    const ctFeature = topojson.feature(stateTopo, stateTopo.objects.states)
      .features.find(d => +d.id === 9);
    if (!ctFeature) { console.error("CT state not found"); return; }

    const allCtCounties = topojson.feature(countyTopo, countyTopo.objects.counties)
      .features.filter(d => +d.id >= 9000 && +d.id < 10000);
    const ctCountyMap = Object.fromEntries(allCtCounties.map(f => [+f.id, f]));

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
    const pathGen = d3.geoPath().projection(projection);

    // Wrapper group — zoom transforms this, leaving SVG axes unchanged
    const mapG = svg.append("g").attr("id", "map-g");

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
      const pts = projected.filter(d => d.type === typeName);
      const r = markerRadius(meta.weight);

      const g = mapG.append("g")
        .attr("class", "layer").attr("data-type", typeName)
        .style("opacity", 0).style("pointer-events", "none")
        .style("filter", "drop-shadow(0 1px 2px rgba(0,0,0,0.45))");

      if (meta.family === "out-of-school") {
        g.selectAll("circle").data(pts).join("circle")
          .attr("cx", d => d.px).attr("cy", d => d.py).attr("r", r)
          .attr("fill", "#E8B43C").attr("stroke", "white").attr("stroke-width", 1.5);

      } else if (meta.family === "in-school") {
        const side = r * 2;
        g.selectAll("rect").data(pts).join("rect")
          .attr("x", d => d.px - r).attr("y", d => d.py - r)
          .attr("width", side).attr("height", side)
          .attr("fill", meta.color).attr("stroke", "white").attr("stroke-width", 1);

      } else if (meta.family === "nonprofit") {
        g.selectAll("polygon").data(pts).join("polygon")
          .attr("points", d => `${d.px},${d.py-r} ${d.px+r},${d.py} ${d.px},${d.py+r} ${d.px-r},${d.py}`)
          .attr("fill", "#C45A4A").attr("stroke", "white").attr("stroke-width", 1.5);

      } else if (meta.family === "childcare") {
        if (typeName === "Family Day Care") {
          g.selectAll("circle").data(pts).join("circle")
            .attr("cx", d => d.px).attr("cy", d => d.py).attr("r", 4)
            .attr("fill", "none").attr("stroke", "#1c3557")
            .attr("stroke-width", 1.5).attr("stroke-opacity", 0.85);
        } else {
          g.selectAll("circle").data(pts).join("circle")
            .attr("cx", d => d.px).attr("cy", d => d.py).attr("r", r)
            .attr("fill", "#1c3557").attr("fill-opacity", 0.82)
            .attr("stroke", "white").attr("stroke-width", 1);
        }
      }
      layers[typeName] = g;
    });

    // D3 zoom — transforms mapG
    const zoom = d3.zoom()
      .scaleExtent([1, 12])
      .on("zoom", event => mapG.attr("transform", event.transform));
    svg.call(zoom);

    function focusCounty(countyIdStr) {
      if (!countyIdStr) {
        svg.transition().duration(600).call(zoom.transform, d3.zoomIdentity);
        return;
      }
      const feature = ctCountyMap[+countyIdStr];
      if (!feature) return;
      const [[x0, y0], [x1, y1]] = pathGen.bounds(feature);
      const scale = Math.min(12, 0.82 / Math.max((x1 - x0) / W, (y1 - y0) / H));
      const tx = W / 2 - scale * (x0 + x1) / 2;
      const ty = H / 2 - scale * (y0 + y1) / 2;
      svg.transition().duration(600).call(
        zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale)
      );
    }

    // ── Legends, dropdowns, eyebrow pills ───────────────
    const LEGEND_NAMES = {
      "Public Library":                   "Public Library",
      "Bookstore":                        "Bookstore",
      "Museum":                           "Museum",
      "School Score 0":                   "Score 0 — No library staff",
      "School Score 1":                   "Score 1",
      "School Score 2":                   "Score 2",
      "School Score 3":                   "Score 3",
      "School Score 4":                   "Score 4",
      "School Score 5":                   "Score 5 — Full program",
      "Read to Grow BFB Birthing Center": "RTG Birthing Center",
      "Book Bank":                        "Book Bank",
      "Read to Grow BFK Organization":    "RTG Partner Organization",
      "Little Free Library":              "Little Free Library",
      "Laundry Cares":                    "Laundry Cares",
      "Child Care Center":                "Child Care Center",
      "Group Child Care Home":            "Group Child Care Home",
      "Child Care Center Exempt":         "Child Care (Exempt)",
      "Youth Camp Exempt":                "Youth Camp (Exempt)",
      "Family Day Care":                  "Family Day Care (unweighted)",
    };

    function symbolSVG(typeName) {
      const meta = TYPE_META[typeName];
      const r = Math.min(markerRadius(meta.weight), 8);
      const c = 12;
      const shad = `style="filter:drop-shadow(0 1px 2px rgba(0,0,0,0.45))"`;
      if (meta.family === "out-of-school")
        return `<svg width="25" height="25" viewBox="0 0 25 25"><circle cx="${c}" cy="${c}" r="${r}" fill="#E8B43C" stroke="white" stroke-width="1.5" ${shad}/></svg>`;
      if (meta.family === "in-school") {
        const s = r * 2;
        return `<svg width="25" height="25" viewBox="0 0 25 25"><rect x="${c-r}" y="${c-r}" width="${s}" height="${s}" fill="${meta.color}" stroke="white" stroke-width="1" ${shad}/></svg>`;
      }
      if (meta.family === "nonprofit")
        return `<svg width="25" height="25" viewBox="0 0 25 25"><polygon points="${c},${c-r} ${c+r},${c} ${c},${c+r} ${c-r},${c}" fill="#C45A4A" stroke="white" stroke-width="1.5" ${shad}/></svg>`;
      if (typeName === "Family Day Care")
        return `<svg width="25" height="25" viewBox="0 0 25 25"><circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#1c3557" stroke-width="1.5" stroke-opacity="0.85"/></svg>`;
      return `<svg width="25" height="25" viewBox="0 0 25 25"><circle cx="${c}" cy="${c}" r="${r}" fill="#1c3557" fill-opacity="0.82" stroke="white" stroke-width="1" ${shad}/></svg>`;
    }

    // Colour eyebrow pills per family
    const EYEBROW_COLORS = {
      "out-of-school": "#E8B43C",
      "in-school":     "#467c9d",
      "nonprofit":     "#C45A4A",
      "childcare":     "#1c3557",
    };
    document.querySelectorAll(".eyebrow").forEach(el => {
      const t = el.textContent.toLowerCase();
      if (t.includes("out-of-school"))    el.style.background = EYEBROW_COLORS["out-of-school"];
      else if (t.includes("in-school"))   el.style.background = EYEBROW_COLORS["in-school"];
      else if (t.includes("nonprofit"))   el.style.background = EYEBROW_COLORS["nonprofit"];
      else if (t.includes("childcare"))   el.style.background = EYEBROW_COLORS["childcare"];
      // summary / full-picture keep the default pill
    });

    // County dropdown options (reused across all steps)
    const countyOptHTML = CT_COUNTIES
      .map(c => `<option value="${c.id}">${c.name} County</option>`)
      .join("");

    document.querySelectorAll(".step[data-step]").forEach(el => {
      const i = +el.dataset.step;

      // County zoom dropdown
      const sel = document.createElement("select");
      sel.className = "county-select";
      sel.setAttribute("aria-label", "Focus map on county");
      sel.innerHTML = `<option value="">All Connecticut</option>` + countyOptHTML;
      sel.addEventListener("change", e => focusCounty(e.target.value));
      el.appendChild(sel);

      // Legend
      const active = STEPS[i].active;
      if (active.length) {
        const div = document.createElement("div");
        div.className = "legend";
        div.innerHTML = active.map(t =>
          `<div class="legend-item">` +
          `<span class="legend-sym" aria-hidden="true">${symbolSVG(t)}</span>` +
          `<span class="legend-name">${LEGEND_NAMES[t] || t}</span>` +
          `</div>`
        ).join("");
        el.appendChild(div);
      }
    });

    // ── Map state + scrollama ────────────────────────────
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function applyMapState(index) {
      const state = STEPS[Math.min(index, STEPS.length - 1)];
      const dur = reducedMotion ? 0 : 200;
      ALL.forEach(t => {
        const opacity = state.active.includes(t) ? 1 : 0;
        layers[t].style("pointer-events", opacity === 1 ? "auto" : "none");
        layers[t].transition().duration(dur).ease(d3.easeLinear).style("opacity", opacity);
      });
      svg.transition().duration(400).call(zoom.transform, d3.zoomIdentity);
      document.querySelectorAll(".county-select").forEach(s => { s.value = ""; });
    }

    applyMapState(0);

    const scroller = scrollama();
    scroller
      .setup({ step: ".step", offset: 0.55, debug: false })
      .onStepEnter(({ index }) => applyMapState(index));
    window.addEventListener("resize", () => scroller.resize());
  }

  init().catch(err => console.error("Init failed:", err));
</script>"""

path = r"C:\Users\charl\projects\clients\read-to-grow\baii-input-storymap\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

start = content.index("<script>")
end   = content.rindex("</script>") + len("</script>")
new_content = content[:start] + NEW_SCRIPT + content[end:]

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Done. File length: {len(new_content)} chars")
