# Prompt: BACI interactive map for the Book Access Index storymap

Paste everything below the line into Claude Code, opened at the root of the `baii-input-storymap` repo.

---

You are adding one new page to this repo: an interactive map of the **Book Access Context Index (BACI)**, the need index that complements the Book Access Index (BAII). The BAII says how many book sources a neighborhood can reach. The BACI says how much that neighborhood needs them. Higher BACI means more need.

The page must look and behave like a sibling of `explore.html`. Read `explore.html`, `docs/explore/SPEC.md` and `docs/explore/RECON.md` before anything else: they define the stack, the layout, the voice and the working method you will reuse here.

## How to work

Work in gates, as the Explore view was built.

1. **Gate 0, recon only.** Read the files listed under "What exists", then write `docs/baci/RECON.md`: what you will reuse from `explore.html`, how you will draw each geography, the open questions, and anything in this prompt that the repo contradicts. Stop and wait for my answers. Change no code in Gate 0.
2. **Gate 1, data.** The build script and its verifier.
3. **Gate 2, the page.** Map, controls, panel.
4. **Gate 3, address lookup, lists, URL state, mobile.**

Stop at the end of each gate with a short report and a list of what to check. Branch from the current branch (`explore-view`) as `baci-view`. Commit in small steps with the repo's existing message style (`feat(baci): ...`, `fix(baci): ...`). Do not push.

## Hard constraints

- No framework, no `package.json`, no bundler. Static HTML with inline CSS and JS, like `explore.html`. Scripts run as `node scripts/<name>.mjs` with zero dependencies.
- The page is `baci.html`. Do not change the behavior of `index.html`, `explore.html` or `methodology.html`. Do not link the new page from their navigation yet, and give it `<meta name="robots" content="noindex">`: Read to Grow has not signed off on publishing the index. Adding the nav link is a one-line change we will make later.
- Do not edit or re-run `baii_data/baci/build_baci.py`, and do not change the BACI JSON files it produced. If the data looks wrong, say so in your report.
- Never commit `baii_data/baii-2026-06-25.gpkg`.
- No runtime requests to ArcGIS feature layers. The Esri basemap that `explore.html` already uses is fine.
- The page never scrolls at 1280x720 and above. Only inner lists scroll.
- UI copy: plain journalistic voice, Read to Grow vocabulary, sentence case, no em dashes, no hype. Labels say what the reader is looking at, not how it was computed.
- **This index measures need, not performance.** Never write "best", "worst", "top" or "bottom" about a place. Use "highest need" and "lowest need". Never rank or shame a named neighborhood in running copy.

## What exists

Stack to reuse (all in `explore.html`): MapLibre GL JS 5.24.0 from unpkg, the color tokens (`--navy`, `--yellow`, `--terra`), the three-column layout (left rail, map, right panel), the address search and its `/api/geocode` proxy (forward and reverse), the area combobox, the "What am I looking at?" dialog, the mobile bottom sheet, the reset button, and the URL state pattern. `index.html` already loads `h3-js@4.1.0` from unpkg; use the same version here.

Geometry already in the repo:

- `baii_data/explore/districts.geojson`: the 158 school districts, real Census boundaries, property `name`. Join to BACI records by `name`.
- `baii_data/explore/regions.geojson`: the 9 planning regions, property `name`.
- `baii_data/ct_boundary.geojson`: the state outline.
- Hexagons have no geometry file. Build them from the H3 index (resolution 8) with h3-js.
- Census tracts have no geometry yet. Gate 1 fetches them (see below).

BACI data, in `baii_data/baci/` (v0.2, already built, read `_meta` in each file first):

| File | Contents |
|---|---|
| `baci_h3.json` | 16,189 scored hexagons. Row layout is in `_meta.cell_fields`: h3 index, `baci_a`, `baci_b`, `cls_a`, `cls_b`, four raw values, four `p_*` scores, `district_idx`, `flags` (bit 1 = partial ELA, bit 2 = small sample), `tract_idx`, `typ`. |
| `baci_tracts.json` | 843 census tracts: `idx`, `geoid` (11 digits, 2022 planning-region codes), `name`, `region`, `district_idx` (the district holding most of the tract's children), `typ`, `child_pop`, raw values, `p_*`, `z_*`, `baci_a`, `baci_b`, `cls_a`, `cls_b`, `rank_a`, `rank_b`, `partial_ela`, `small_n`. |
| `baci_districts.json` | 158 districts, same fields, `idx` matches `baii_districts.json`. |
| `baci_benchmarks.json` | `state`, `regions` (9), `area_types` (4), same fields. |
| `build_baci.py` | How the data was made. Its docstring is the method note. |

The four components, each oriented so that higher means more need:

| Key | Reader-facing label | Raw value shown as |
|---|---|---|
| `noHS` | Adult literacy | "12% of adults have no high school diploma" |
| `LEA` | Language access | "9% of adults speak limited English" |
| `ELA` | Grade 3 reading | "Grade 3 reading index: 63 of 100" (raw `ELA_PI`, higher is better; `p_ELA` and `z_ELA` are already flipped) |
| `hardship` | Economic hardship | "15% of people live below 150% of the poverty line" |

Things to know about the data:

- **Two formulas, both shipped.** Formula A (`baci_a`, components `p_*`) is a 0 to 100 percentile score. Formula B (`baci_b`, components `z_*`) is a standardized score centered on 0. We have not chosen between them. The page needs a small, clearly temporary "Formula A | Formula B" switch that drives every color, number, class and ranking. Default A. Build it so removing the switch and one formula later is a small change.
- **Classes.** `cls_a` and `cls_b` run 1 to 5 with the labels in `_meta.class_labels` ("Lowest need" to "Highest need"); 0 means not scored. The breaks in `_meta.class_breaks` are shared by every geography.
- **Area type.** `typ` is 0 Rural, 1 Suburban, 2 Urban Periphery, 3 Urban Core (`_meta.typ_labels`). 16 hexagons have no type (`null`).
- **Flags.** 17 districts and 29 tracts have no Grade 3 reading score, so their index is the average of three components (`partial_ela`). One tract has a very small sample (`small_n`). Flagged units have `rank_a` and `rank_b` set to `null` and must never appear in the highest or lowest lists. `_meta.n_ranked` gives the denominators (813 tracts, 141 districts).
- **Hexagon and tract values overlap.** Three components come from the census tract, so every hexagon in a tract shares them. Grade 3 reading comes from the school district. A hexagon and its tract differ only when the tract straddles two districts.
- **Unscored places.** Hexagons not in `baci_h3.json` are unpopulated or have no census data. 36 of the 879 Connecticut tracts are not in `baci_tracts.json`. Draw them in a neutral "No data" style.
- **Benchmarks.** Each benchmark's `baci_a` / `baci_b` is built the way a district's is, so district, region and state compare like with like. The statewide `baci_a` is 58.0, not 50, because of that method. `child_mean_a` / `child_mean_b` (statewide 50.0) is the need level of the average child's neighborhood. Use `baci_a` / `baci_b` and the component fields for all comparisons, and raise in RECON.md whether the statewide 58 will confuse readers.

## Gate 1: data build

Write `scripts/build-baci-data.mjs` (zero dependencies, same conventions as `scripts/build-explore-data.mjs`) and `scripts/verify-baci-data.mjs`.

The build fetches census tract boundaries once and saves them as a static file:

- Layer: `https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/ACS_English_Ability_and_Linguistic_Isolation_View_Boundaries/FeatureServer/2`
- POST to `/query` with `where=GEOID LIKE '09%'`, `outFields=GEOID`, `outSR=4326`, `geometryPrecision=5`, `maxAllowableOffset=0.0002`, `resultRecordCount=2000`, `f=geojson`. One request returns all 879 tracts, about 1 MB. Check `exceededTransferLimit` anyway.
- This layer uses the same 2022 planning-region GEOIDs as `baci_tracts.json` (prefixes 09110 to 09190). Join on `GEOID`.
- Fallback if that layer is unavailable: `https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Census_Tracts/FeatureServer/0`, `where=STATE_FIPS='09'`, field `FIPS`. Its IDs use the old county codes (09001 to 09015), so join on the last 6 digits, which are unique across the state in both sources (879 of 879 match).
- Write `baii_data/baci/tracts.geojson` with one property per feature: `idx` from `baci_tracts.json`, or `-1` for the 36 unscored tracts. Keep the file under 1.5 MB.

Decide in RECON.md whether hexagon polygons are built in the browser with h3-js at load, or prebuilt by this script into a static file. Pick whichever keeps first paint under about 2 seconds on a mid-range laptop and say why.

The verifier must fail loudly unless all of these hold:

- 16,189 hexagons, 843 tracts, 158 districts, 9 regions, 4 area types.
- `class_breaks.A` = [26.104, 38.608, 56.514, 77.582]; `class_breaks.B` = [-0.786, -0.369, 0.171, 0.892].
- `n_ranked` = 813 tracts, 141 districts.
- Statewide `baci_a` 58.0, `child_mean_a` 50.0.
- Highest need districts, formula A, in order: Hartford 90.8, Bridgeport 87.2, New Britain 84.7, New Haven 82.9, New London 82.5.
- Lowest need districts, formula A, in order: New Hartford 9.9, Madison 10.6, Weston 11.5, Regional School District 18 12.7, Andover 13.8.
- Every `tract_idx` in the hexagon file exists in the tract file; every tract and district `name` or `geoid` joins to a geometry; all 158 district names match `districts.geojson`.

## Gates 2 and 3: the page

### Layout

Same three columns as `explore.html`, same header bar (title, "What am I looking at?", "Back to the story").

```
+--------------------------------------------------------------------------+
| Header: page title              | What am I looking at? | Back to the story |
+----------------------+---------------------------------+-----------------+
| LEFT RAIL            | MAP                             | RIGHT PANEL     |
| 1 Address search     |                                 | In view (scope) |
| 2 Show by            |                                 | Need score card |
|   Neighborhood |     |                                 | Components vs   |
|   Tract | District   |                                 |  benchmarks     |
| 3 What to show       |                                 | Highest need 5  |
|   Overall need       |                                 | Lowest need 5   |
|   + 4 components     |                                 |                 |
| 4 Area type          |                                 |                 |
|   4 checkboxes       |                                 |                 |
| 5 Formula A | B      |                                 |                 |
| Legend, Reset        |  (legend may sit on the map)    |                 |
+----------------------+---------------------------------+-----------------+
```

Propose the page title in RECON.md. Working title: "Explore where book access matters most".

### 1. Three geographies

A three-way switch: Neighborhood (hexagons), Census tract, School district. One fill layer is visible at a time. Thin state outline always on. The selected unit gets a navy outline. Hover shows a small tooltip with the unit's name and need class; click selects the unit and fills the right panel.

Name tracts for readers as "Tract 5002, Hartford" (tract number plus the `district_idx` district's name without "School District"). Hexagons are "a neighborhood in <district>".

### 2. Overall index and its components

A five-option radio: Overall need, Adult literacy, Language access, Grade 3 reading, Economic hardship.

- Overall need colors by `cls_a` or `cls_b`.
- A component colors by its own score in five steps: under formula A, `p_*` cut at 20, 40, 60, 80; under formula B, `z_*` cut at -0.84, -0.25, 0.25, 0.84.
- One color scale everywhere: dark blue, light blue, near white, light red, deep red, from lowest to highest need. Take the exact hex values from `explore.html`'s tokens where they fit and propose the rest in RECON.md. The legend names the two ends in words ("Lowest need", "Highest need") and includes "No data".
- Flagged units get a visible but quiet mark (a hatch or a dashed outline) and a legend line: "Missing Grade 3 reading, based on three measures".

### 3. Address lookup with benchmarks

Reuse the Explore address search and the click-anywhere-on-the-map behavior. An address resolves to a hexagon with `h3.latLngToCell(lat, lng, 8)`, then to its tract (`tract_idx`), district (`district_idx`) and region (the tract's `region`).

The right panel then shows:

- A headline card: the need score and class for the place, with the three geographies on one line ("Neighborhood 62 · Tract 58 · District 49"). When the hexagon and tract are identical, show them once as "Neighborhood and tract".
- A comparison table, one row for overall need and one per component, with columns for the place (at the geography chosen in "Show by"), its district, its planning region and Connecticut. Each cell shows the raw value in its own unit (percent, or the reading index) with a small bar positioned by the component score, so the reader sees both the real number and where it sits. Label the region column "Planning region"; Connecticut's eight historical counties are not used anywhere in this repo.
- If the address falls in an unscored hexagon, or outside Connecticut, say so in one plain sentence and still show the district and region rows when they exist.

With no address and no selection, the panel shows the statewide figures and the two lists.

### 4. Area type filter

Four checkboxes: Urban core, Urban periphery, Suburban, Rural, all on by default. Unticking a type fades those units to a pale neutral rather than removing them, so the state keeps its shape. The filter applies to whichever geography is showing and to the two lists. Show the count of children in view next to the scope title.

### 5. Highest and lowest need

Two short lists of five in the right panel.

- They list districts in district view and tracts in tract view. In neighborhood view they list tracts, with a one-line note saying so.
- They follow the formula switch, the "What to show" choice (ranked by the chosen component's score when a component is selected) and the area-type filter.
- Flagged units never appear. Break ties by name.
- Each row shows the name, the score and the area type. Clicking a row flies to the unit, outlines it and selects it. A "Show on map" control outlines all ten at once.
- Headings are "Highest need" and "Lowest need", with the count they are drawn from ("of 141 districts").

### Shared behavior

- **URL state**, following Explore's pattern: `geo` (hex | tract | district), `show` (overall | noHS | LEA | ELA | hardship), `formula` (a | b), `types` (comma list of hidden types), `address`, and `sel` (the selected unit). Reload and shared links restore the view.
- **Reset** returns to statewide, district view, overall need, formula A, all types.
- **"What am I looking at?"** explains in four short paragraphs: what the index is and that higher means more need; the four measures in plain words; that it describes places, not the families or schools in them; and what the hatch mark means. Draft the copy and flag it for my review, it will go to Read to Grow before release.
- **Mobile** (under 768px): same bottom-sheet pattern as Explore, with tabs Filters, Numbers, Lists.
- **Accessibility**: every control reachable by keyboard, `aria-pressed` on toggles, the live region announces scope changes as Explore does, and color is never the only signal (class names appear in tooltips, cards and lists).
- **Data as of** line in the panel footer, naming the American Community Survey 5-year vintage, the EdSight Grade 3 school year and "Index version 0.2". I have not confirmed either vintage: look them up in Gate 0 (the ACS layer's metadata, and the storymap's methodology page for EdSight) and list them in RECON.md for me to approve.

## Out of scope

Access points, drive-time zones and anything else from the BAII; the need-versus-access cross view and the neighborhood typology from the correlates study; any new index computation in the browser beyond sorting and filtering; editing weights; household-level data of any kind.

## Definition of done

- `node scripts/build-baci-data.mjs` then `node scripts/verify-baci-data.mjs` pass from a clean checkout.
- `baci.html` works from a static server with `/api/geocode` available, at 1280x720, 1920x1080 and 390x844.
- Every number in the right panel can be traced to a field in `baii_data/baci/`.
- Switching geography, measure, formula or area type takes under 200 ms after first load.
- `docs/baci/RECON.md` records every decision made at the gates.
