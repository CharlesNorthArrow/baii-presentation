"""
_patch5.py — merge licensed/unlicensed childcare slides + add RTG BFK Family

Changes:
  1. points.json  — append 2,340 RTG BFK Family points from CSV
  2. TYPE_META    — add "Read to Grow BFK Family" (childcare, weight 0.0)
  3. CH4 / ALL    — include BFK Family
  4. STEPS[15-17] — merge licensed childcare into step 15; Family Day Care ->16; BFK Family ->17
  5. STEP_DATA    — update keys 15/16/17
  6. CHAPTER_DATA[18] — add BFK Family row, update footer to 6 types / 5,625
  7. CLOSING_DATA — childcare 3,285->5,625; total 9,511->11,851
  8. BASE_R       — BFK Family gets hollow-circle radius (5) like Family Day Care
  9. Point render — BFK Family rendered as hollow ring (same as Family Day Care)
 10. HTML steps 15-19 — updated text + new step 17 for BFK Family
"""

import csv, json

# ── 1. Add BFK Family points to points.json ──────────────────────────────────
with open("points.json") as f:
    pts = json.load(f)

with open("RTG BAII Model Input v1 - Nonprofitv2.csv", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    new_pts = [
        {"type": "Read to Grow BFK Family",
         "lat": float(r["Lat"]), "lng": float(r["Lon"])}
        for r in reader
        if r.get("Type","").strip() == "Read to Grow BFK Family"
           and r.get("Lat","").strip() and r.get("Lon","").strip()
    ]

pts.extend(new_pts)
with open("points.json","w") as f:
    json.dump(pts, f, separators=(",",":"))
print(f"points.json: {len(pts)} total ({len(new_pts)} BFK Family added)")

# ── 2-10. Patch index.html ────────────────────────────────────────────────────
with open("index.html","r",encoding="utf-8") as f:
    html = f.read()

orig_len = len(html)

# ── 2. TYPE_META: add BFK Family ─────────────────────────────────────────────
OLD = '    "Family Day Care":                  { family: "childcare", weight: 0.0, depth: 1, reach: 2 },\n  };'
NEW = ('    "Family Day Care":                  { family: "childcare", weight: 0.0, depth: 1, reach: 2 },\n'
       '    "Read to Grow BFK Family":          { family: "childcare", weight: 0.0, depth: 1, reach: 1 },\n  };')
assert OLD in html, "FAIL 2 (TYPE_META)"
html = html.replace(OLD, NEW, 1)

# ── 3. CH4: add BFK Family ───────────────────────────────────────────────────
OLD = '  const CH4 = ["Child Care Center","Group Child Care Home","Child Care Center Exempt","Youth Camp Exempt","Family Day Care"];'
NEW = '  const CH4 = ["Child Care Center","Group Child Care Home","Child Care Center Exempt","Youth Camp Exempt","Family Day Care","Read to Grow BFK Family"];'
assert OLD in html, "FAIL 3 (CH4)"
html = html.replace(OLD, NEW, 1)

# ── 4. STEPS: merge licensed into step 15; Family Day Care ->16; BFK ->17 ────
OLD = ('    { active: ["Child Care Center"] },\n'
       '    { active: ["Group Child Care Home","Child Care Center Exempt","Youth Camp Exempt"] },\n'
       '    { active: ["Family Day Care"] },\n'
       '    { active: CH4 },')
NEW = ('    { active: ["Child Care Center","Group Child Care Home","Child Care Center Exempt","Youth Camp Exempt"] },\n'
       '    { active: ["Family Day Care"] },\n'
       '    { active: ["Read to Grow BFK Family"] },\n'
       '    { active: CH4 },')
assert OLD in html, "FAIL 4 (STEPS)"
html = html.replace(OLD, NEW, 1)

# ── 5. STEP_DATA: update 15, 16, 17 ──────────────────────────────────────────
OLD = ('    15: { weight: "1.0",     depth: 2, reach: 4,               count: "1,363",\n'
       '          why: "Where the youngest children spend full days. Books are often welcome but rarely the mission." },\n'
       '    16: { weight: "1.0",     depth: 2, reachMin: 2, reachMax: 3, count: "132",\n'
       '          why: "Smaller licensed care settings where books vary by provider — counted, lightly weighted." },\n'
       '    17: { weight: "0.0",     unweighted: true, depth: 1, reach: 2, count: "1,790",\n'
       '          why: "Tiny, home-based, unverified for books. Counted on the map for context; not yet weighted in the index." },')
NEW = ('    15: { weight: "1.0",     depth: 2, reachMin: 2, reachMax: 4, count: "1,495",\n'
       '          why: "Connecticut\'s licensed childcare — centers, group homes, exempt programs — serve children full days at the most formative moment for early literacy. Books are often welcome; a book program is rarely part of the plan." },\n'
       '    16: { weight: "0.0",     unweighted: true, depth: 1, reach: 2, count: "1,790",\n'
       '          why: "Tiny, home-based, unverified for books. Counted on the map for context; not yet weighted in the index." },\n'
       '    17: { weight: "0.0",     unweighted: true, depth: 1, reach: 1, count: "2,340",\n'
       '          why: "RTG\'s book-gifting families: the most intimate access point in the dataset. Behind closed doors, unverifiable at scale, but real. Unweighted today — not because they don\'t matter, but because the infrastructure to count them doesn\'t yet exist." },')
assert OLD in html, "FAIL 5 (STEP_DATA 15-17)"
html = html.replace(OLD, NEW, 1)

# ── 6. CHAPTER_DATA[18]: add BFK Family row, update footer ───────────────────
OLD = ('    18: { title: "In this chapter",\n'
       '          rows: [ { name: "Child Care Center", weight: 1.0 }, { name: "Group Child Care", weight: 1.0 },\n'
       '                  { name: "CC Center Exempt", weight: 1.0 }, { name: "Youth Camp Exempt", weight: 1.0 },\n'
       '                  { name: "Family Day Care", weight: 0.0, hollow: true } ],\n'
       '          footer: "4 types \xb7 3,285 locations" },')
NEW = ('    18: { title: "In this chapter",\n'
       '          rows: [ { name: "Child Care Center", weight: 1.0 }, { name: "Group Child Care", weight: 1.0 },\n'
       '                  { name: "CC Center Exempt", weight: 1.0 }, { name: "Youth Camp Exempt", weight: 1.0 },\n'
       '                  { name: "Family Day Care", weight: 0.0, hollow: true },\n'
       '                  { name: "RTG BFK Family", weight: 0.0, hollow: true } ],\n'
       '          footer: "6 types \xb7 5,625 locations" },')
assert OLD in html, "FAIL 6 (CHAPTER_DATA 18)"
html = html.replace(OLD, NEW, 1)

# ── 7. CLOSING_DATA: childcare count + footer ─────────────────────────────────
OLD = ('      { name: "Childcare",     count: 3285, countStr: "3,285", sub: "The largest and the lightest-weighted family." },\n'
       '    ],\n'
       '    footer: "9,511 access points across Connecticut",\n'
       '    maxCount: 3285,')
NEW = ('      { name: "Childcare",     count: 5625, countStr: "5,625", sub: "The largest and the lightest-weighted family." },\n'
       '    ],\n'
       '    footer: "11,851 access points across Connecticut",\n'
       '    maxCount: 5625,')
assert OLD in html, "FAIL 7 (CLOSING_DATA)"
html = html.replace(OLD, NEW, 1)

# ── 8. BASE_R: include BFK Family in hollow-circle radius override ────────────
OLD = '      BASE_R[typeName] = typeName === "Family Day Care" ? 5 : r;'
NEW = '      BASE_R[typeName] = (typeName === "Family Day Care" || typeName === "Read to Grow BFK Family") ? 5 : r;'
assert OLD in html, "FAIL 8 (BASE_R)"
html = html.replace(OLD, NEW, 1)

# ── 9. Point render: BFK Family as hollow ring like Family Day Care ───────────
OLD = '        if (typeName === "Family Day Care") {'
NEW = '        if (typeName === "Family Day Care" || typeName === "Read to Grow BFK Family") {'
assert OLD in html, "FAIL 9 (hollow ring render)"
html = html.replace(OLD, NEW, 1)

# ── 10a. HTML step 15: merged licensed childcare ──────────────────────────────
OLD = ('    <section class="step" data-step="15" id="ch-15">\n'
       '      <span class="eyebrow">Childcare</span>\n'
       '      <h2>The youngest children\'s daily place</h2>\n'
       '      <p>More than 1,300 licensed child care centers serve Connecticut\'s youngest children. Some have rich book corners; many do not. The index counts them because the children are there — every day, for years, at the most formative moment for early literacy.</p>\n'
       '      \n'
       '    </section>')
NEW = ('    <section class="step" data-step="15" id="ch-15">\n'
       '      <span class="eyebrow">Childcare</span>\n'
       '      <h2>Where the youngest children spend their days</h2>\n'
       '      <p>Connecticut’s 1,495 licensed childcare providers — centers, group homes, and exempt programs — serve children full-time at the most formative moment for early literacy. Books are often welcome. A book program is rarely part of the plan.</p>\n'
       '      \n'
       '    </section>')
assert OLD in html, "FAIL 10a (step 15 HTML)"
html = html.replace(OLD, NEW, 1)

# ── 10b. HTML step 16: now Family Day Care ────────────────────────────────────
OLD = ('    <!-- 16: Other Childcare -->\n'
       '    <section class="step" data-step="16">\n'
       '      <span class="eyebrow">Childcare</span>\n'
       '      <h2>The other licensed care providers</h2>\n'
       '      <p>Smaller, more varied, and less standardized — but children spend full days here. Books are not guaranteed. Books are also not impossible to add.</p>\n'
       '      \n'
       '    </section>')
NEW = ('    <!-- 16: Family Day Care -->\n'
       '    <section class="step" data-step="16">\n'
       '      <span class="eyebrow">Childcare</span>\n'
       '      <h2>On the map, but not yet in the index</h2>\n'
       '      <p>Family Day Cares are home-based and tiny — typically a handful of children. Connecticut has 1,790 of them. They appear on this map because they belong to the conversation. They carry weight zero today: too small, too varied, too unverified to count toward access. But they are exactly the kind of place where a single shelf could change a year of a child’s life.</p>\n'
       '      \n'
       '    </section>')
assert OLD in html, "FAIL 10b (step 16 HTML)"
html = html.replace(OLD, NEW, 1)

# ── 10c. HTML step 17: now RTG BFK Family ────────────────────────────────────
OLD = ('    <!-- 17: Family Day Care -->\n'
       '    <section class="step" data-step="17">\n'
       '      <span class="eyebrow">Childcare</span>\n'
       '      <h2>On the map, but not yet in the index</h2>\n'
       '      <p>Family Day Cares are home-based and tiny — typically a handful of children. Connecticut has 1,790 of them. They appear on this map because they belong to the conversation. They carry weight zero in the model today: too small, too varied, too unverified to count toward access. But they are exactly the kind of place where a single shelf could change a year of a child\'s life.</p>\n'
       '      \n'
       '    </section>')
NEW = ('    <!-- 17: RTG BFK Family -->\n'
       '    <section class="step" data-step="17">\n'
       '      <span class="eyebrow">Childcare</span>\n'
       '      <h2>RTG’s book-gifting families</h2>\n'
       '      <p>These 2,340 households participate in Read to Grow’s Books for Families program — receiving books directly through a trusted relationship. They are the most intimate access point in the dataset: behind closed doors, invisible to conventional mapping, but real. Like Family Day Care, they carry weight zero today. Unlike everything else on this map, they represent a relationship, not just a location.</p>\n'
       '      \n'
       '    </section>')
assert OLD in html, "FAIL 10c (step 17 HTML)"
html = html.replace(OLD, NEW, 1)

# ── 10d. HTML step 18: updated summary count ─────────────────────────────────
OLD = ('    <!-- 18: Ch4 Summary -->\n'
       '    <section class="step" data-step="18">\n'
       '      <span class="eyebrow">Chapter Summary</span>\n'
       '      <h2>3,285 childcare locations — books often welcome, not always present</h2>\n'
       '      <p>Childcare is the largest family of access points in the dataset and the lowest-weighted on average. That tension is the strategic insight: huge reach, shallow depth, enormous opportunity for any program that can deepen book access in places that already have the children.</p>\n'
       '      \n'
       '    </section>')
NEW = ('    <!-- 18: Ch4 Summary -->\n'
       '    <section class="step" data-step="18">\n'
       '      <span class="eyebrow">Chapter Summary</span>\n'
       '      <h2>5,625 childcare locations — books often welcome, not always present</h2>\n'
       '      <p>Childcare is the largest family of access points in the dataset. With RTG’s book-gifting families included, it’s also the most personal: from regulated centers to trusted households, this is where children spend their most formative hours.</p>\n'
       '      \n'
       '    </section>')
assert OLD in html, "FAIL 10d (step 18 HTML)"
html = html.replace(OLD, NEW, 1)

# ── 10e. HTML step 19: updated total ─────────────────────────────────────────
OLD = '      <h2>9,511 access points. Now what?</h2>'
NEW = '      <h2>11,851 access points. Now what?</h2>'
assert OLD in html, "FAIL 10e (step 19 count)"
html = html.replace(OLD, NEW, 1)

with open("index.html","w",encoding="utf-8") as f:
    f.write(html)

print(f"index.html: {orig_len} -> {len(html)} chars")
print("All patches applied.")
