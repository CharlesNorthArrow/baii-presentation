# BACI view: recon report (Gate 0)

## Gate 0 decisions (2026-11-21): these override PROMPT.md wherever they conflict

Decided by Charles:
- **D1. Layout.** Copy Explore's floating cards over a full-bleed map, not three real columns.
- **D2. Colors.** Section 5 approved as written.
- **D3. Statewide score.** Option (a): the statewide card shows 58 with no class, plus the note "Connecticut as a whole, measured the same way as a district". The comparison table's Connecticut column shows 58 as usual.
- **D4. Children per hexagon come from the BAII.** The only copy is the BAII gpkg (`pop_pre + pop_elementary + pop_middle + pop_high` per hexagon). Over the 16,189 scored hexagons these add up to exactly 758,150, the statewide `child_pop`, and match the four area-type benchmarks exactly. Every tract matches its `child_pop` within 1 child except one (off by 13.4).
- **D5. Area picker.** Add Explore's "Planning region or school district" combobox under the address search. Picking an area zooms to it and outlines it.
- **D6. EdSight vintage.** Grade 3 ELA is the 2024-2025 school year.
- **D7. URL.** Keep Explore's `point=<lng>,<lat>` for map clicks, beside `address` and `sel`.
- **D8. Verifier.** Also checks the formula B highest and lowest district lists.
- **D9. Norwich.** Recorded as a data note for whoever maintains `build_baci.py`: Norwich has no Grade 3 ELA score, so it is flagged `partial_ela` and never appears in a ranked list. Nothing changes on the page.

Assumptions made by Claude to follow from these (change any of them before Gate 2):
- **A1. Hexagon children are written to a small committed file.** The gpkg must never be committed, so `build-baci-data.mjs` reads it with Node's built-in `node:sqlite` when it is present. It writes `baii_data/baci/hex_children.json`: one number per hexagon, in `baci_h3.json` order, rounded to 0.01 (most hexagons hold a fraction of a child, so 0.1 would lose too much). From a clean checkout without the gpkg, the build keeps the committed file and says so. That way the build still runs with zero dependencies, and the verifier checks the file against `baci_h3.json` and the statewide total. `node:sqlite` prints an "experimental" warning on Node 24; the script hides it.
- **A2. ACS vintage.** Gate 1 already queries the ACS layer for tract boundaries. The build also reads that layer's metadata once and writes what it says to `baii_data/baci/build_meta.json`. I'll report the vintage for your approval before it reaches the page.
- **A3. Area picker plus selection.** Picking a region or district zooms and outlines it, and sets the panel to that area. For a district, that is the same as selecting it (`sel=district:<idx>`). For a region, the panel shows the region benchmark (`area=region:<slug>`, Explore's param). Clearing it returns to statewide.

## Gate 1 record (2026-11-21)

- **Files.** `scripts/build-baci-data.mjs` writes `baii_data/baci/tracts.geojson`, `hex_children.json` and `build_meta.json`. `scripts/verify-baci-data.mjs` runs 46 checks and exits 1 if any fails; a deliberately broken `hex_children.json` failed 3 checks with exit code 1. The BACI JSON files and `build_baci.py` are committed as delivered and unchanged.
- **Tracts.** One POST to the primary ACS layer returned all 879 Connecticut tracts, with no transfer limit. 843 joined to `baci_tracts.json` on `GEOID` and 36 are unscored (`idx` −1). The file is 943 KB. The layer's `maxRecordCount` is 1000, so the brief's `resultRecordCount=2000` is capped at 1000, which is still more than 879. The fallback layer was checked but not used: 879 tracts, unique 6-digit keys, and all 843 scored tracts join.
- **ACS vintage: 2020-2024 (approved by Charles 2026-11-21 for the footer).** The Living Atlas item description says "Current Vintage : 2020-2024", updated 2026-05-26. The committed `ct_tracts_B16004_limited_english.csv` matches the live layer exactly for all 879 tracts, so the language access measure is 2020-2024. **I have not confirmed** that the other two census measures (no high school diploma, B15002; hardship, C17002) are the same vintage. They come from the BAII gpkg, which records no year. The gpkg is dated 2026-06-25, after the 2020-2024 release, so 2020-2024 is likely but not proven.
- **Hexagon children.** Read from the gpkg: 758,150 in total, and each area type matches its benchmark exactly.
- **Guardrail.** Added `*.gpkg` to `.gitignore`, so the BAII gpkg can't be committed by accident.
- **Clean checkout.** Build then verify pass in a fresh detached worktree with no gpkg; the build keeps the committed `hex_children.json`.

## Gate 3 record (2026-11-21)

Decided by Charles: the right panel gets **Numbers** and **Lists** tabs, so the lists don't have to fit under the table at 1280x720. The tabs are the same two as on the phone, where the bottom sheet has Filters, Numbers and Lists.

What was added:
- **Address search.** The same flow and messages as Explore, through `/api/geocode`. An address in the Connecticut box but outside the state outline gets "That address is outside Connecticut." A map click shows "A point on the map", then the reverse-geocoded "A point in <place>".
- **Area picker (D5).** Planning regions and school districts. A district is selected like any other unit. A region shows its benchmark: score and class, plus a table with Planning region and Connecticut columns.
- **Highest and lowest need.**
  - Five each: districts in district view, tracts in tract and neighborhood views, with a note in neighborhood view.
  - Each list follows the formula, the measure and the area types, and is headed by its denominator ("of 141 districts", "of 471 census tracts" with only urban types shown).
  - Flagged units are excluded, and ties sort by name.
  - Clicking a row selects the unit and zooms to it. "Show on map" outlines all ten with a dashed line and fits the map to them.
- **URL state.** The params are `geo`, `show`, `formula`, `types`, `address`, `point`, `sel` (`tract:<geoid>` or `district:<slug>`) and `area` (`region:<slug>`).
  - Defaults are left out of the URL.
  - Toggles replace the history entry; a new place pushes one, so Back walks through places.
  - Reload, shared links and Back were each checked in headless Chrome.
- **Phone layout (under 768px).** Explore's bottom sheet. The search and area boxes float at the top, and the Filters tab holds the controls and the legend. A map click opens the Numbers tab; a list row closes the sheet so the map shows.

Changes to earlier assumptions:
- **Selections persist across views.** A district or tract picked from a list or the area picker stays selected when "Show by" changes. The panel keeps describing it, and the outline stays. Section 6 had said list selections clear on a geography switch; keeping them felt less surprising once the area picker existed. Map clicks and addresses still resolve to the view on screen.
- **Short title.** Below 940px the title is now "Where books matter most". "Where book access matters most" was cut off at 390px.

Measured, headless Chrome on Intel Iris Xe:
- Every switch takes 8 to 69 ms.
- First paint (district view) is 1.4 s on a cold cache and 0.35 s on a warm cache; all three views are ready by 1.7 s cold.
- No page scroll at 1280x720, 1920x1080 or 390x844.
- The live `/api/geocode` was then checked on the Vercel preview: suggestions, picking, reload restore and the reverse-geocoded click label all work.
- **Fix found on the preview.** "Springfield Massachusetts" returned a Massachusetts street that Mapbox placed at 42.026°N, just inside the Connecticut line, so the page showed it as an Enfield place. Address results must now also name Connecticut in their address; otherwise the reader sees "That address is outside Connecticut." `explore.html` has the same weakness. It is not changed here, per the brief.

## Gate 2 record (2026-11-21)

What `baci.html` does now:
- **Map.** Three geographies, five measures, the formula switch, the area-type filter, the hatch for missing Grade 3 reading and "No data".
- **Interaction.** A hover tooltip (name, class, area type). A click sets a point that resolves to neighborhood, tract, district and planning region.
- **Panel.** A headline card and a comparison table, the statewide card with no class (D3), and the "Data as of" line, read from `build_meta.json`.
- **Chrome.** Reset, and the "What am I looking at?" dialog, whose four paragraphs are a **draft for Read to Grow's review**.

Decisions made while building, open to change:
- **Colors come from feature state, not paint expressions.** Each unit's class goes in feature state, and all three views stay laid out, with the inactive ones made transparent. Changing a data-driven paint expression made MapLibre rebuild every tile: 300 to 500 ms for the hexagons. Toggling layer visibility rebuilt a view every time it reappeared: about 400 ms.
- **Measured switch times.** Headless Chrome on this laptop's Intel Iris Xe GPU, at 1280x720, from the call to the finished frame:
  - Neighborhood view: 46 to 97 ms.
  - Measure, formula or area type: 39 to 89 ms.
  - Tract or district view: 11 to 29 ms.
  - Panning and zooming in neighborhood view: median frame 6 ms, 95th percentile 11 ms.
- **First paint.** The district view is drawn in about 2.0 s on a cold cache, including MapLibre from unpkg, and 0.7 s on a warm cache. h3-js now loads beside the hexagon data instead of before first paint.
- **Panel.** It is 360px wide, not 340px; with four value columns, 340px broke the headers mid-word.
- **Comparison table.**
  - The place's column is headed "Here", because the scope title above it names the place.
  - The Grade 3 reading cell shows the bare index ("51"), and the row label says "Reading index out of 100, higher is better".
  - Connecticut's overall bar is neutral white, with no class color, to match D3.
- **Small sample.** The one `small_n` tract says "Based on a small census sample, so treat this score with care." in its card. The brief only asked that it be left out of rankings.
- **Hexagons with no district.** For the 13 hexagons outside every district shape, the District column uses the tract's district.
- **Local testing.** `python -m http.server` sometimes leaves two of the five first-paint requests hanging forever, in the browser pane and in headless Chrome. The same page loads every time from a minimal Node static server, so this is the dev server, not the page. Vercel serves static files normally. Use the `storymap-node-baci` launch config for local checks.

Open for Gate 3:
- **Lists won't fit below the table at 1280x720.** With a place selected, the table card ends about 650 px down. That leaves no room for two lists of five, even as an inner scroll region. Options:
  - (a) Tabs inside the panel, "Numbers" and "Lists", matching the mobile sheet.
  - (b) A compact table that drops the sub-labels into a tooltip.
  - (c) Lists that show only when no place is selected.

Audit date: 2026-11-21. Read-only. Repo on branch `explore-view` at `c916b34`. Nothing was fetched and no code was changed. Every number below comes from the files in `baii_data/baci/` (v0.2), `baii_data/explore/` and `explore.html` as they are in the repo today.

Status: the questions in section 9 were answered on 2026-11-21; see "Gate 0 decisions" above.

---

## 1. What the prompt gets right, checked against the data

These all hold today, so the Gate 1 verifier can assert them as written:

- 16,189 hexagons, 843 tracts, 158 districts, 9 regions, 4 area types.
- `class_breaks.A` = [26.104, 38.608, 56.514, 77.582], `class_breaks.B` = [-0.786, -0.369, 0.171, 0.892].
- `n_ranked` = 813 tracts, 141 districts. 29 tracts are `partial_ela`, 1 is `small_n` (Tract 4173, New Britain), and they don't overlap, so 30 tracts are unranked. 17 districts are `partial_ela`.
- Statewide `baci_a` 58.0, `child_mean_a` 50.0.
- Highest need districts, formula A: Hartford 90.8, Bridgeport 87.2, New Britain 84.7, New Haven 82.9, New London 82.5.
- Lowest need districts, formula A: New Hartford 9.9, Madison 10.6, Weston 11.5, Regional School District 18 12.7, Andover 13.8.
- District `idx` matches `baii_districts.json`, and the 158 names match `baii_data/explore/districts.geojson` exactly. The geojson's feature order is also the `idx` order, which Explore already relies on (`fc.features[area.idx]`).
- The 9 benchmark region names match `regions.geojson` exactly.
- Tract GEOIDs use the 2022 planning-region county codes 09110 to 09190, and their last 6 digits are unique (843 of 843), so the fallback join in the prompt works.
- 16 hexagons have no area type (`typ` null).
- Every hexagon's three census measures (`noHS`, `LEA`, `hardship` and their `p_*`) equal its tract's, and its `ELA_PI` / `p_ELA` equal its district's. 0 mismatches.

For formula B, the district lists differ from formula A. Highest: Hartford 1.38, Bridgeport 1.31, New Britain 1.25, New Haven 1.10, **Waterbury** 1.09. Lowest: New Hartford −1.38, Madison −1.34, **Andover** −1.28, **Weston** −1.27, **Bethany** −1.24. The verifier can check both if you want; the prompt only asks for A.

## 2. Where the repo contradicts the prompt

1. **`explore.html` is not a three-column layout.** The map fills the whole body. The left rail is a floating stack (`.ex-left`, 280px) and the right panel is a set of floating navy cards (`.ex-panel`, 340px) over the map. `fitPadding()` keeps zooms centered in the visible gap between them. The ASCII drawing in the prompt shows three real columns. **I plan to copy Explore's floating layout**, since the prompt says the page must look like a sibling of `explore.html`. That means the legend sits inside the left stack, not on the map. Say so if you want real columns instead.
2. **Tract `idx` is not the array position.** `baci_tracts.json` has 843 rows, but `idx` runs from 0 to 848 with gaps at 222, 236, 237, 238, 239 and 709 (presumably the tracts dropped for missing census data). Every hexagon `tract_idx` does exist as an `idx` (0 missing), so the data is fine, but code must join through a lookup on `idx`, never `tracts[tract_idx]`. The verifier will check this explicitly.
3. **Hexagons carry no formula B components.** `cell_fields` has `p_*` but no `z_*`. To color a hexagon by a component under formula B, the page will read `z_noHS`, `z_LEA` and `z_hardship` from the hexagon's tract and `z_ELA` from its district. Section 1 shows this lookup is exact for formula A (0 mismatches), so it is the same number, not a new computation. Gate 1 will check the `p_*` side of that equality so a future data build can't break it silently.
4. **Hexagons carry no child counts.** The prompt asks for "the count of children in view next to the scope title". Tracts, districts and benchmarks have `child_pop`; hexagons don't. See question 4.
5. **13 hexagons have `district_idx` = −1.** They sit in 12 tracts in different districts. They are all flagged `partial_ela` (no district means no Grade 3 score). Their address card will have no district row, and the region comes from the tract.
6. **Hexagon and tract are almost always the same number.** 16,088 of 16,189 hexagons (99.4%) have exactly their tract's `baci_a`, `baci_b` and class. The other 101 are in tracts that straddle districts. So the "Neighborhood and tract" merged headline will be the normal case, and the neighborhood view will look like a finer-grained copy of the tract view. That matches the method; I flag it only so it doesn't surprise anyone in review.
7. **The statewide score falls in a need class.** Connecticut's `baci_a` 58.0 has `cls_a` 4, "High". So does `cls_b`. A statewide card would read "Connecticut: 58, High". Four of nine planning regions are also "High". At the same time, district classes skew low (41, 50, 42, 18, 7 districts in classes 1 to 5) because the breaks are child-weighted hexagon quintiles. Tracts split evenly: about 151,000 children in each class. See question 3.
8. **No data vintages are recorded anywhere in the repo.** `build_baci.py`, its `_meta`, the gpkg (`gpkg_contents` has an empty description and no metadata table) and `methodology.html` never name an ACS year or an EdSight school year. `methodology.html` doesn't mention EdSight or the ACS at all. You told me not to fetch in Gate 0, so I haven't read the ACS layer metadata. See question 6.
9. **"Unscored hexagons" have no geometry to draw.** Hexagons not in `baci_h3.json` aren't in any file. Rather than generating every Connecticut cell, the page will fill the state outline in the "No data" style underneath the index layer. Any gap (unpopulated hexagons, the 36 unscored tracts) then reads as "No data" in every view at no extra cost.
10. **The prompt lists the area combobox as reusable, but the layout has no place for it.** See question 5.
11. **Explore's verifier prints and does not fail.** `verify-explore-data.mjs` logs results for a human to read. The BACI verifier will exit with code 1 on any failed check, as the prompt asks.
12. **URL state.** Explore stores a map click as `point=<lng>,<lat>` and a typed address as `address=<text>`, and uses `pushState` for scope changes and `replaceState` for toggles. The prompt lists `address` and `sel` but not `point`. See section 6.

## 3. What I will reuse from `explore.html`

Copied, then trimmed to what this page needs. No shared file is extracted, so `explore.html` stays untouched.

- **Head:** MapLibre GL JS 5.24.0 CSS and JS from unpkg, the favicon set and theme color, and `preload` links for the first-paint data. Plus `<meta name="robots" content="noindex">` and h3-js 4.1.0 from unpkg (same URL as `index.html`).
- **Tokens and base CSS:** `--navy #1E3A6F`, `--yellow #E8B43C`, `--terra #C45A4A`, `--white`, `--white-2`, `--line`, `--line-2`, `--map-bg`, `--panel-w`, `--sheet-tabs-h`. Also the no-page-scroll root grid, `.site-nav` header, `.ex-title` with long and short titles, and the header actions.
- **Controls:** the `.ex-toggle` segmented control with `aria-pressed` (for Show by and Formula), `.ex-input`, `.ex-combo` and `.ex-combo-list` (address suggestions), `.ex-label`, `.ex-hint` and `.ex-addr-status`.
- **Map:** the inline Esri Light Gray base and reference raster style, `NavigationControl` top right, compact attribution, `fitPadding()`, the state outline layer, and `reducedMotion`-aware `fitBounds` and `flyTo`.
- **Address search:** `initAddressSearch()` as it is: debounced `/api/geocode?q=`, CT bounding-box filter, keyboard listbox, and the same status messages ("Searching…", "No matches in Connecticut.", "Search is offline.", "That address is outside Connecticut."). Also the click-anywhere handler, the `inState()` check, and reverse-geocoded labels. Drive-time zones, radius chips, isochrones and the nearby list are left out.
- **Right panel:** the `.ex-scope` title (navy text with a white halo on desktop), navy cards on the map, the `#ex-announce` live region and `announceScope()`.
- **Dialog:** the `<dialog>` "What am I looking at?" and its open and close wiring.
- **Mobile:** the bottom sheet as is (`data-sheet`, `data-tab`, `setSheet`, Escape closes). The tabs become Filters, Numbers and Lists.
- **Reset:** the round reset button in the legend header.
- **URL:** `urlFromState()`, `writeUrl("push" | "replace")`, `applyUrl()` on load and on `popstate`, and the `restoreToken` guard for address restores.

The build script copies `scripts/build-explore-data.mjs` conventions: ES module, `node:` built-ins only, `getJson` with 3 retries and ArcGIS error detection, the `ROOT` / `OUT` constants, and `main().catch(... process.exit(1))`.

## 4. How each geography is drawn

**Default view and first paint.** The default view is districts. The page waits only for `ct_boundary.geojson`, `explore/districts.geojson` (297 KB), `baci_districts.json` (70 KB) and `baci_benchmarks.json` (10 KB), about 380 KB raw. The hexagon and tract files load in the background right after first paint. The address lookup waits for the hexagon file if it hasn't arrived yet. This keeps first paint well under 2 seconds without prebuilding anything.

**Districts.** Source: `baii_data/explore/districts.geojson`. At load, each feature gets `idx` (its position, which equals district `idx`) plus the fields the paint expressions need: `baci_a`, `baci_b`, `cls_a`, `cls_b`, `p_*`, `z_*`, `typ` and `partial_ela`. All of them are copied from `baci_districts.json`.

**Tracts.** Source: `baii_data/baci/tracts.geojson` from Gate 1, one property `idx` (−1 for the 36 unscored tracts). At load, the page copies the same fields from `baci_tracts.json` through an `idx` lookup. Unscored tracts get no score fields and draw as "No data".

**Neighborhoods (hexagons).** Built in the browser from `baci_h3.json` with `h3.cellToBoundary(h, true)`, after first paint. Why not prebuild:
- A prebuilt GeoJSON of 16,189 hexagons is about 2.5 to 3 MB, on top of the 1.3 MB `baci_h3.json` the page needs anyway for the address lookup.
- Building in the browser costs one pass of `cellToBoundary`. I expect a few hundred milliseconds on a mid-range laptop, off the critical path. Gate 2 will measure it and report.
- The storymap's Findings section already does exactly this (`index.html:4065`).

Each hexagon feature carries its row's fields plus `z_noHS`, `z_LEA` and `z_hardship` from its tract and `z_ELA` from its district (section 2, item 3).

**One fill layer per geography, three sources.** All three sources are added once. Switching geography flips `visibility`. Switching measure or formula is a single `setPaintProperty("fill-color", …)` with a `step` expression on the right field. The area-type filter is a `case` on `typ` in the same expression. None of these rebuilds a source, which keeps every switch under 200 ms.

**Layers, bottom to top:**
1. Basemap.
2. The "No data" underlay (the state polygon).
3. The active fill.
4. The hatch overlay: a `fill-pattern` layer filtered to flagged units. It has to be a separate layer because a fill layer takes one pattern.
5. Unit borders (thin white for districts and tracts, none for hexagons at state zoom).
6. The state outline.
7. The selected-unit outline.
8. The "Show on map" outlines for the ten listed units.
9. Basemap labels.

**Hover and click.** Hover uses `queryRenderedFeatures` on the active fill layer for the tooltip (name and need class). A click resolves through a point (see section 6).

## 5. Proposed color scale

The prompt asks for dark blue, light blue, near white, light red, deep red, from lowest to highest need. Explore's own tokens don't contain a five-step diverging scale. The storymap's Findings hexagon ramp (`ACC`, `index.html:3954`) does, and it is the scale readers have already seen on this site. In that ramp red means low book access and blue means high, so "red means more concern" carries over to "red means more need".

| Class | Label | Hex | Source |
|---|---|---|---|
| 1 | Lowest need | `#2166AC` | storymap `ACC` |
| 2 | Low | `#67A9CF` | storymap `ACC` |
| 3 | Moderate | `#F7F7F7` | new: near white. The storymap's `#F7E8C3` cream would read as a warm tint, not neutral |
| 4 | High | `#EF8A62` | storymap `ACC` |
| 5 | Highest need | `#B2182B` | storymap `ACC` |
| | No data | `#A7A29A` at 55% opacity | storymap `UNPOP` |
| | Area type turned off | `#E4E6EA`, with the unit border kept | new: pale neutral, lighter than "No data" so the two never read as one |
| | Selected unit | `--navy #1E3A6F`, 3px, over a 5px white casing | navy alone vanishes against class 1 |
| | Hatch (missing Grade 3 reading) | navy diagonal lines at 35% opacity, 6px spacing | |

I am not using `--navy` for class 1, because the selected outline and the page chrome are navy. I am not using `--terra` for class 5 either: it sits too close to `#EF8A62` to tell the top two classes apart.

## 6. Behavior details I am assuming unless you say otherwise

- **Clicking the map.** A click inside Connecticut behaves like an address, as in Explore. It sets a point, which resolves to a hexagon, then its tract, its district and the tract's region. The panel shows the place at the "Show by" geography. The point survives a geography switch, because all three are known. It goes in the URL as `point=<lng>,<lat>`, Explore's existing param (the prompt's list doesn't have it).
- **`sel`.** Used only for a unit picked from the highest or lowest lists, as `sel=district:<idx>` or `sel=tract:<geoid>`. A list selection has no point, so it clears when the geography changes. A tract selected in neighborhood view (whose lists are tracts) is shown as the tract.
- **Push or replace.** A new point, address, selection or reset pushes, so Back walks through places. Toggles (geography, measure, formula, types) replace. Same split as Explore.
- **Type filter on hexagons with no type.** The 16 typeless hexagons are never faded and never count toward a filter.
- **Lists in neighborhood view.** They filter tracts by the tract's own `typ`, which is the type holding most of its children. A tract can therefore stay in a list while some of its hexagons are faded on the map. The one-line note says the list shows census tracts.
- **Ties.** Sort by the score of the measure in view, descending (ascending for lowest), then by display name. The data has 18 tied `baci_a` values among ranked districts and 273 among ranked tracts.
- **Region of a place.** Always the tract's `region`, including for the 13 hexagons with no district.
- **Bars in the comparison table.** Each bar shows where the component score sits on a fixed axis: 0 to 100 for formula A, and −2.5 to +2.5 for formula B with the center marked. The cell's text is always the raw value. Grade 3 reading's bar runs the same way as the others (longer means more need), even though its raw number reads the other way. The row label says "higher is better" in small type so the two don't seem to contradict each other.
- **Number formats.** Percentages with no decimals ("12%"), the reading index as "63 of 100", formula A scores with no decimals ("62"), formula B scores with a sign and two decimals ("+0.41").

## 7. Page title (proposal)

- Long: **"Explore where book access matters most"** (your working title). It is short enough for the header at 1280px.
- Short, under 940px: **"Where book access matters most"**.
- Browser tab: "Where book access matters most · Read to Grow".

An alternative that names the measure plainly: "Explore the need for book access across Connecticut". I prefer the working title, because the header has to read as a sibling of "Explore all the book access points that make up our index".

## 8. Fit at 1280x720

Map body height is 720 − 48 = 672px, minus 24px of gaps.

**Left stack (280px wide).** My estimates:
- Search: 70px.
- Show by: 50px.
- What to show (five radio rows): 160px.
- Area type, as a 2 by 2 grid of checkboxes: 70px.
- Formula: 50px.
- Legend (five classes, No data, hatch line): 150px.

That totals about 550px plus padding, so it fits with a little room. If it doesn't, the measures list shrinks before anything else.

**Right panel (340px wide).**
- Scope title and child count: 50px.
- Headline card: 90px.
- Comparison table: 200px (header plus five rows, four value columns).
- Two lists of five: about 340px.

That comes to about 680px, over budget when a place is selected. The lists block will be the inner scroll region, which the constraints allow. With no selection, the table is replaced by the statewide figures and everything fits.

Four value columns in 340px leaves about 58px per column for a value and a bar. That is tight but readable with column heads "Here", "District", "Planning region" (wrapping to two lines) and "Connecticut". If it reads badly in Gate 2, I'll widen the panel to 380px on screens 1440px and wider.

## 9. Questions before Gate 1

See the summary in chat. The full list:

1. **Layout.** Copy Explore's floating panels over a full-bleed map (my recommendation), or build three real columns as drawn in the prompt?
2. **Color scale.** Approve the five colors in section 5 (storymap `ACC` ends, a new near white `#F7F7F7` in the middle), plus the No data, turned-off and selected styles?
3. **Statewide 58 and "High".** I think it will confuse readers. Options:
   - (a) The statewide card shows the score with no class, and a one-line note: "Connecticut as a whole, measured the same way as a district".
   - (b) Lead with `child_mean_a` 50: "The average child's neighborhood: 50".
   - (c) Show 58 and "High" as the data says.

   I recommend (a): districts, regions and the state still compare like with like, which is the reason for the method. The table column stays "Connecticut 58".
4. **Children in view.** Hexagons have no child counts. Options:
   - (a) In neighborhood view, count children from the tracts the lists use, labeled "children in these tracts".
   - (b) Show the count in tract and district view only.
   - (c) Leave the count out.

   Also, totals differ slightly by tier with every type on: tracts 758,156, districts 760,145, state benchmark 758,150. I'd show the sum of the units in view, rounded to the nearest hundred.
5. **Area combobox.** Explore has a "Planning region or school district" picker. The prompt lists it as reusable, but the left rail has no slot for it. Leave it out (my default), or add it under the address search to zoom to a district or region?
6. **Data vintages.** May I fetch the ACS layer's metadata at the start of Gate 1 to read the ACS 5-year vintage? For EdSight there is nothing in the repo. Do you know the Grade 3 ELA school year (2023-24 or 2024-25?), or should I ask whoever built the gpkg? Until then the footer reads "Index version 0.2" with the two vintages marked as pending.
7. **`point` in the URL.** OK to keep Explore's `point=<lng>,<lat>` for map clicks, beside `address` and `sel` (section 6)?
8. **Verifier scope.** Also check the formula B highest and lowest lists (section 1)? It costs nothing and guards against a data rebuild reshuffling them.
9. **Norwich.** Norwich is one of the 17 districts with no Grade 3 reading score, so it is flagged and drops out of every ranked list. For a city its size that may surprise Read to Grow. This is a data question for whoever runs `build_baci.py`. The gpkg value is either blank or 0 (the build treats 0 as missing), and I haven't checked which. Nothing changes on the page.
