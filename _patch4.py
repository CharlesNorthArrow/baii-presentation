"""
_patch4.py — school district base map + dynamic point sizing

Changes:
  1. Remove countyTopo fetch (counties no longer used)
  2. Remove ctCountyMesh
  3. Replace CT state + county base layers with always-on district fills
  4. Store featherBlur reference for per-zoom stdDeviation adjustment
  5. Store BASE_R per type; rescale points on every zoom tick
  6. Update applyDistrictFilter for new district-always-visible design
  7. Raise scaleExtent max to 18 (small districts need deeper zoom)
"""

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

orig_len = len(html)

# ── 1. Remove countyTopo from Promise.all ─────────────────────────────────────
OLD = """    const [points, stateTopo, countyTopo, districtGeoJSON] = await Promise.all([
      fetch("./points.json").then(r => { if (!r.ok) throw new Error("points.json"); return r.json(); }),
      fetch("./states.json").then(r => { if (!r.ok) throw new Error("states.json"); return r.json(); }),
      fetch("./counties.json").then(r => { if (!r.ok) throw new Error("counties.json"); return r.json(); }),
      fetch("./districts.json").then(r => { if (!r.ok) throw new Error("districts.json"); return r.json(); }),
    ]);"""
NEW = """    const [points, stateTopo, districtGeoJSON] = await Promise.all([
      fetch("./points.json").then(r => { if (!r.ok) throw new Error("points.json"); return r.json(); }),
      fetch("./states.json").then(r => { if (!r.ok) throw new Error("states.json"); return r.json(); }),
      fetch("./districts.json").then(r => { if (!r.ok) throw new Error("districts.json"); return r.json(); }),
    ]);"""
assert OLD in html, "FAIL patch 1 (promise.all)"
html = html.replace(OLD, NEW, 1)

# ── 2. Remove ctCountyMesh ────────────────────────────────────────────────────
OLD = """    const ctCountyMesh = topojson.mesh(
      countyTopo, countyTopo.objects.counties,
      (a, b) => a !== b && Math.floor(a.id / 1000) === 9 && Math.floor(b.id / 1000) === 9
    );

    const W = 1200, H = 800;"""
NEW = """    const W = 1200, H = 800;"""
assert OLD in html, "FAIL patch 2 (ctCountyMesh)"
html = html.replace(OLD, NEW, 1)

# ── 3. Store featherBlur reference ────────────────────────────────────────────
OLD = """    featherFilt.append("feGaussianBlur")
      .attr("in", "SourceGraphic").attr("stdDeviation", 22);"""
NEW = """    const featherBlur = featherFilt.append("feGaussianBlur")
      .attr("in", "SourceGraphic").attr("stdDeviation", 22);"""
assert OLD in html, "FAIL patch 3 (featherBlur)"
html = html.replace(OLD, NEW, 1)

# ── 4. Replace base layers (CT state fill + county lines + old district groups)
#       with always-on district fills + simplified highlight group ──────────────
OLD = """    // CT base + county lines
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
      .attr("stroke", "white").attr("stroke-width", 1.5);"""
NEW = """    // State shadow backdrop
    mapG.append("path").datum(ctFeature).attr("d", pathGen)
      .attr("fill", "#FFFFFF").attr("stroke", "none")
      .attr("filter", "url(#state-shadow)");

    // School districts — always-visible white fill base map
    const districtFeatures = districtGeoJSON.features;
    const districtAllG = mapG.append("g").attr("id", "district-all");
    districtAllG.selectAll("path").data(districtFeatures).join("path")
      .attr("d", pathGen)
      .attr("fill", "#FFFFFF")
      .attr("stroke", "rgba(0,0,0,0.13)")
      .attr("stroke-width", 0.5)
      .attr("vector-effect", "non-scaling-stroke");

    // Selected district highlight border (shown when a district is filtered)
    const districtHlG = mapG.append("g").attr("id", "district-hl").style("display", "none");
    const districtHlPath = districtHlG.append("path")
      .attr("fill", "none")
      .attr("stroke", "rgba(0,0,0,0.6)")
      .attr("stroke-width", 2)
      .attr("vector-effect", "non-scaling-stroke");"""
assert OLD in html, "FAIL patch 4 (base layers)"
html = html.replace(OLD, NEW, 1)

# ── 5. Add BASE_R storage when building point layers ─────────────────────────
OLD = """    const layers = {};
    ALL.forEach(typeName => {
      const meta = TYPE_META[typeName];
      const pts  = projected.filter(d => d.type === typeName);
      const r    = markerRadius(meta.weight);
      const g    = pointsG.append("g")"""
NEW = """    const BASE_R = {};
    const layers = {};
    ALL.forEach(typeName => {
      const meta = TYPE_META[typeName];
      const pts  = projected.filter(d => d.type === typeName);
      const r    = markerRadius(meta.weight);
      BASE_R[typeName] = typeName === "Family Day Care" ? 5 : r;
      const g    = pointsG.append("g")"""
assert OLD in html, "FAIL patch 5 (BASE_R)"
html = html.replace(OLD, NEW, 1)

# ── 6. Replace zoom handler with one that rescales points each tick ───────────
OLD = """    // Zoom
    const zoom = d3.zoom()
      .scaleExtent([1, 12])
      .on("zoom", event => mapG.attr("transform", event.transform));
    svg.call(zoom);"""
NEW = """    // Zoom — rescale points on every tick so markers stay a consistent screen size
    function rescalePoints(k) {
      ALL.forEach(typeName => {
        const meta = TYPE_META[typeName];
        const r    = BASE_R[typeName] / k;
        const g    = layers[typeName];
        if (meta.family === "in-school") {
          g.selectAll("rect")
            .attr("x", d => d.px - r).attr("y", d => d.py - r)
            .attr("width", r * 2).attr("height", r * 2);
        } else if (meta.family === "nonprofit") {
          g.selectAll("polygon")
            .attr("points", d =>
              `${d.px},${d.py - r} ${d.px + r},${d.py} ${d.px},${d.py + r} ${d.px - r},${d.py}`);
        } else {
          g.selectAll("circle").attr("r", r);
        }
      });
      // Keep feather edge ~20 screen px regardless of zoom level
      featherBlur.attr("stdDeviation", 20 / k);
    }

    const zoom = d3.zoom()
      .scaleExtent([1, 18])
      .on("zoom", event => {
        mapG.attr("transform", event.transform);
        rescalePoints(event.transform.k);
      });
    svg.call(zoom);"""
assert OLD in html, "FAIL patch 6 (zoom handler)"
html = html.replace(OLD, NEW, 1)

# ── 7. Remove the old districtBgG draw + districtFeatures const ──────────────
OLD = """    // ── District filter ─────────────────────────────────────
    const districtFeatures = districtGeoJSON.features;

    // Draw all district outlines (shown only when a district is selected)
    districtBgG.selectAll("path").data(districtFeatures).join("path")
      .attr("d", pathGen)
      .attr("fill", "none")
      .attr("stroke", "rgba(255,255,255,0.28)")
      .attr("stroke-width", 0.6);

    // Populate select"""
NEW = """    // ── District filter ─────────────────────────────────────
    // Populate select"""
assert OLD in html, "FAIL patch 7 (remove districtBgG draw)"
html = html.replace(OLD, NEW, 1)

# ── 8. Update applyDistrictFilter for new design ─────────────────────────────
OLD = """    function applyDistrictFilter(idx) {
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
    }"""
NEW = """    function applyDistrictFilter(idx) {
      activeDistrictIdx = idx === "" ? null : +idx;

      if (activeDistrictIdx === null) {
        pointsG.attr("mask", null);
        maskPath.attr("d", "");
        districtAllG.style("opacity", null);
        districtHlG.style("display", "none");
        svg.transition().duration(600).call(zoom.transform, d3.zoomIdentity);
        return;
      }

      const feature = districtFeatures[activeDistrictIdx];
      maskPath.attr("d", pathGen(feature));
      pointsG.attr("mask", "url(#district-fade-mask)");

      // Dim all districts; highlight just the selected one
      districtAllG.style("opacity", 0.35);
      districtHlG.style("display", null);
      districtHlPath.attr("d", pathGen(feature));

      // Zoom to district bounds
      const [[x0, y0], [x1, y1]] = pathGen.bounds(feature);
      const scale = Math.min(18, 0.78 / Math.max((x1 - x0) / W, (y1 - y0) / H));
      const tx = W / 2 - scale * (x0 + x1) / 2;
      const ty = H / 2 - scale * (y0 + y1) / 2;
      svg.transition().duration(600).call(
        zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale)
      );
    }"""
assert OLD in html, "FAIL patch 8 (applyDistrictFilter)"
html = html.replace(OLD, NEW, 1)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Done. {orig_len} → {len(html)} chars")
