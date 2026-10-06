# Explore view: recon report

## Gate 0 decisions (2026-10-06): these override SPEC.md wherever they conflict

Decided by Charles:
- **D1. Separate URL.** Explore is its own page, `explore.html`. `index.html?section=explore` redirects to it, the same way `section=method` redirects to `methodology.html`.
- **D2. No weights.** Weights do not appear anywhere in the app: no "Weight in the index" line in point cards, and the build does not compute weights.
- **D3. Show the ArcGIS feature layers as they are, no more and no less.** The build does not match records against the BAII and does not trim to the BAII counts. Expected totals:
  - Schools: 1,494
  - Public libraries: 240
  - Licensed childcare: 1,392
  - Exempt childcare: 104
  - Bookstores: 315
  - Museums: 85 (spec filter)
  - Little Free Libraries: 1,131
  - Read to Grow partner organizations: 443
- **D4. Areas are the 9 planning regions, not the 8 legacy counties.** The area picker groups are "Planning regions" and "School districts". The `area` URL param uses `region:<name>`.
- **D5. School districts are the 158 in `baii_data/baii_districts.geojson`.** Geometry and name only; nothing is fetched.
- **D5 update (2026-10-06, Charles):** district outlines and point-in-district assignment now use the real Census (TIGER) boundaries from the bundled `districts.json`, not the hexagon-dissolved BAII shapes. The district list is still the same 158 BAII names. The 8 overlapping regional high school districts and the "School District Not Defined" filler are left out.
- **D6. No reference to the BAII anywhere in the app.** It only displays access points. Dropped from SPEC.md:
  - the BAII hex toggle (left rail item 5) and the `hex` URL param
  - the "BAII score at this address" card and its deep link to Your Neighborhood
  - the "Index computed" half of the data-as-of line
  - index wording in the radius caption and the "What am I looking at?" copy
- **D6 exception (2026-10-06, Charles):** the page title reads "Explore all the book access points that make up our index". That is the only place the index is mentioned. Below 940px it shortens to "Explore book access".
- **D7. Out-of-scope storymap issues stay as listed below.**
  - The arcgisonline.com basemap is acceptable at runtime. The QA check becomes "no requests to the ArcGIS feature layers at runtime".
  - Childcare is grouped as licensed / exempt and schools as with staff / without staff, as proposed in §7 items 5 and 6.
  - The alert color is approved.

Assumptions made by Claude to follow from these decisions (change any of them before Prompt 1):
- **A1. Types with no ArcGIS layer are dropped:** book banks (7), LaundryCares (8) and Reach Out & Read (0). This follows D3.
- **A2. Read to Grow partners are split by `ProgramType` into three legend rows under Nonprofit and community.** The rows are Books for Kids (289), Books for Babies (50) and Bookmobile stops (104), all with `CustomerType='Organization'` only. Books for Babies sites therefore come from the partners layer (50), not the BAII file (61).
- **A3. Unfiltered layers stay unfiltered.**
  - Bookstores show all 315, including the non-bookstore categories (comic, gift, psychic, law office and so on); the card shows the store type.
  - Little Free Libraries show all 1,131, including about 10 points outside Connecticut.
  - If you want either cleaned up, fix it in the source layer.
- **A4. MapLibre GL JS is loaded from a CDN on `explore.html` only.** This is a new dependency.
  - The build script runs as `node scripts/build-explore-data.mjs` with zero dependencies.
  - No `package.json` is added, so Vercel's static detection is not affected.
  - SPEC asks for an `npm run build:explore` script. That would need a `package.json`, so it is left out.
- **A5. Schools without library staff are drawn as hollow terra (`#C45A4A`) rings.** Nonprofit points stay solid terra.
- **A6. The radius caption is "Straight-line distance."** This replaces the index sentence, per D6.
- **A7. The Middlesex County reference numbers from the dashboard can no longer be checked directly.** Middlesex is not a planning region; most of it falls in Lower Connecticut River Valley. Statewide numbers are the check instead (794 / 700 / 434.1, etc.).

---

Audit date: 2026-10-06. Read-only. Repo at commit `ac2b095` (main). ArcGIS figures come from live metadata, counts, distinct values, statistics and 3-feature samples on that date. No family records were fetched from the RTG partners layer.

---

## 1. Stack and routing

- **No framework and no build system.** The storymap is a set of static pages deployed to Vercel as-is:
  - `index.html` (about 287 KB) holds the story, all of its CSS inline, and all of its JS inline.
  - `methodology.html` is the methodology page.
  - `gap_classes.js` holds the shared gap category table (`window.GAP_CLASSES`).
  - `api/geocode.js` is the only serverless function (CommonJS).
- There is no `package.json`, no npm and no React.
- **Libraries are CDN scripts:** d3 7.9.0 (jsdelivr), scrollama 3.2.0, topojson-client 3.1.0 and h3-js 4.1.0 (unpkg).
- **No MapLibre, Mapbox GL or Leaflet.** Every map is drawn by hand:
  - **Hero:** a canvas.
  - **Access Points:** a d3 SVG, `#ct-map`, with a 1200x800 viewBox.
  - **Findings:** a canvas of H3 hexes.
  - **Your Neighborhood:** a d3 SVG, `#yn-map`.
- **Basemap:** static images from Esri's World Light Gray Canvas `MapServer/export`, fetched at runtime from `services.arcgisonline.com` (`index.html:2594`, `index.html:5387`). There are no tiles.
- **Routing:** one long scrolling page. Sections are addressed by `?section=` and scrolled into view:
  - The mapping lives in `SECTION_TO_URL` / `URL_TO_SECTION` (`index.html:5162`): intro→hero, ingredients, index, neighborhood→your-neighborhood, barriers.
  - The legacy `section=method` redirects to `methodology.html` (`index.html:5224`).
- **Other URL params:**
  - `address` is geocoded on load and passed to `window.__resolveAddress`.
  - `district` is matched to the nav `<select>` option text (a BAII district name such as "Deep River School District").
  - `INITIAL` snapshots the params at first load.
  - Writes go through `window.__urlState` (`setSection`, `setAddress`, `setDistrict`) and **always use `history.replaceState`**. There is no pushState anywhere.
  - A device location is never written into the URL.
- **Nav** (`index.html:2162`): tabs for Access Points, Findings, Your Neighborhood and Methodology (an external page), plus a global "Find my address" search, a "Zoom to School District" select and a Share button.
- **Body scroll:** the whole page scrolls (`html { scroll-behavior: smooth }`, sticky nav and map panels). That makes a 100dvh no-scroll view hard to host as a section of `index.html`; see Section 7.

## 2. Data files

### `baii_data/baii_access_points.json` (118 KB)
- **`_meta` fields:**
  - `purpose`: "In-index access points for straight-line radius counts (5/10/20 mi, cumulative)."
  - `labels`: 10 type labels (listed below).
  - `point_fields`: `["lat","lng","label_idx"]`.
  - `n`: 5191.
  - `state_avg`: per-radius mean counts per label, for 5, 10 and 20 miles.
  - `state_avg_def`: how `state_avg` was computed.
- **`points`:** an array of `[lat, lng, label_idx]`, e.g. `[41.46372, -72.56216, 6]`. Coordinates have 5 decimals.
- **There is no name, no id, no category and no sub-type.** The only typing is the label index, and there is no school staffing split and no licensed/exempt split.
- **651 extra rows sit at exactly the same coordinates as another row of the same type** (e.g. several childcare centers at one address).

| idx | label | count |
|---|---|---|
| 0 | Public library | 240 |
| 1 | School library | 1,494 |
| 2 | Read to Grow partner | 574 |
| 3 | Read to Grow Books for Babies site | 61 |
| 4 | Book bank | 7 |
| 5 | Laundry Cares site | 8 |
| 6 | Childcare center | 1,495 |
| 7 | Museum | 21 |
| 8 | Bookstore | 247 |
| 9 | Little Free Library | 1,044 |
| | **total** | **5,191** |

**There is no "Reach Out & Read" label.** The spec lists it as a BAII-only type, but the BAII file has no such points. The methodology page names it (`methodology.html:740`), but it has no points.

### The storymap's own category and sub-type keys
The Access Points section does not read `baii_access_points.json`.
- It reads root `points.json`, a list of 9,321 `{type, lat, lng}` records.
- It reads `baii_data/ingredients_assets.json` for the roster.
- `TYPE_META` (`index.html:2844`) maps each type to its family and weight.

These are the real "existing sub-type keys":

| Category (menu key / family) | Sub-type key (`type`) | Weight in storymap | Count |
|---|---|---|---|
| Out-of-School / `out-of-school` | Public Library | **5** | 240 |
| | Bookstore | 0.5 | 247 |
| | Museum | 0.5 (flat; methodology text says children's museums count 1) | 21 |
| In-School / `in-school` | School Score 0 (no library staff) | **1** | 700 |
| | School Score 1 | 2 | 158 |
| | School Score 2 | 3 | 159 |
| | School Score 3 | 4 | 157 |
| | School Score 4 | 5 | 161 |
| | School Score 5 | 6 | 159 |
| Nonprofit / `nonprofit` | Read to Grow BFB Birthing Center | 2.5 | 61 |
| | Book Bank | 2 | 7 |
| | Read to Grow BFK Organization | 1 | 574 |
| | Little Free Library | 0.5 | 1,044 |
| | Laundry Cares | 0.5 | 8 |
| Childcare / `childcare` | Child Care Center | 1 | 1,363 |
| | Group Child Care Home | 1 | 29 |
| | Child Care Center Exempt | 1 | 89 |
| | Youth Camp Exempt | 1 | 14 |
| Honorary (not in index) | Read to Grow BFK Family | 0 | 2,340 |
| | Family Day Care | 0 | 1,790 |

The category colors (`CAT_COLOR`, `index.html:3500`) are:
- Out-of-School `#E8B43C`
- In-School `#467c9d`
- Nonprofit `#C45A4A`
- Childcare `#1c3557`

Score 4 and 5 schools also use `#1c3557`. Score 0 schools are drawn hollow.

### `baii_data/baii_snapshot.json` (952 KB)
- **`_meta`:**
  - `shared_denominator` is 1468.185, and `norm = raw / 1468.185 * 100` for both modes ("Connecticut's scale", with the car max = 100).
  - `typology_codes`: 0 Rural, 1 Suburban, 2 Urban Periphery, 3 Urban Core.
  - `gap_labels` and `bin_labels` (car: No data…Very high; pt: No transit access…Very high).
- **`hex`:** an object keyed by H3 res-8 index (17,654 hexes). Each value is an array in `hex_fields` order: `[norm_car, norm_pt, typ, st_pct_car, st_pct_pt, ty_pct_car, ty_pct_pt, car_bin, pt_bin, gap, didx]`.
  - Example: `"882a1012e3fffff": [0.0, 0.0, -1, -1, -1, -1, -1, 0, 0, 0, -1]`.
  - `car_bin = -1` means unpopulated.
- **`districts`:** a list of 158 records, e.g. `{idx:0, name:"Andover School District", typ:0, norm_car:41.7, norm_pt:0.3, car_bin:4, pt_bin:3, gap:3, st_pct_car:55, ..., child_pop:504}`.
- **`typology`:** `codes`, `hex_ref`, `district_ref` and `state_ref` percentiles.
- **No build or index date is stored in the snapshot `_meta`.** See Section 7.

### Other index files
- **`baii_data/baii_h3.json`** (520 KB): `cells` as `[h3, car_bin, pt_bin, district_idx, gap_class]`, with thresholds per mode. Car: 208.85, 374.06, 539.3, 780.88. Transit: 1.16, 3.52, 7.13, 16.59.
- **`baii_data/baii_districts.json`**: 158 districts with bins, `gap_class`, `n_pts` and coverage shares (`cov_car`, `cov_pt`).

## 2b. ArcGIS layer audit

All layers are public, and no token was needed. Base: `https://services5.arcgis.com/IJjAyk93TGaMwoTf/arcgis/rest/services/`. Every layer's maxRecordCount is 1000, except the SD layer at 2000.

### Schools: `Book_Access_Schools_with_Library_Staff/FeatureServer/0`
- **Basics:** 1,494 features. Last edit 2025-11-24.
- **Staffing split:** `Total_Library_staff` = 0 for **700**, > 0 for **794**, null for 0.
- **Students per library staff, where staff > 0:** n 794, **mean 434.1**, min 0, max 2,224.
- **Zero values in students per staff:**
  - When staff = 0, the ratio is 0. That 0 means "no staff", not a good ratio.
  - 2 schools have staff > 0 but a ratio of 0 (no enrollment). The next-lowest ratio is 17.

**Fields** (name | alias | sample):
- `F2024_25_District` | "2024-25 District" | "1090". **Broken:** it holds student counts, not district names.
- `F2024_25_School` | School | "Achievement First Bridgeport Academy"
- `Library___Media___Specialists__Certified_` | certified specialists | 0
- `Non_Certified` | non-certified staff | "0" (a string)
- `Total_Library_staff` | 0
- `Num_students_per_library_staff` | 0
- `Total_students` | "1090" (a string; includes "*")
- `Total_Special_Ed_students` | "149"
- `F__Special_Ed` | "14%"
- `Street` | "655 Stillman St."
- `City` | "Bridgeport"
- `Zip` | "06608-1331"
- `State` | "CT"
- `Country` | "USA"
- `Total_Students_123` | always null
- `TotalStudents123` | 1090 (an integer; 123 rows are 0)
- `TotalStudentsMidStep` | "1090"

**Proposed curated display:**
- Name = `F2024_25_School`, Address = `Street`, Town = `City`
- Detail fields:
  - "Library staff" = `Total_Library_staff`. When it is 0, show "No library staff reported".
  - "Students per library staff" = `Num_students_per_library_staff`. Hide it when staff = 0 or the value is 0.
  - "Certified library media specialists" = `Library___Media___Specialists__Certified_`
  - "Students enrolled" = `TotalStudents123`. Hide it when 0.

**Weight fields:** `Total_Library_staff` and `Num_students_per_library_staff`.

**Anomaly:** 20 duplicate school name + street pairs (programs sharing a building).

### Public libraries: `CT_Libraries_2026_%28240_Libraries%29/FeatureServer/0`
- **Basics:** 240 features. Last edit 2026-09-17. No duplicates, all in CT.
- **Fields:** all aliases equal the field names.
  - `FSCSKEY` "CT0098" (191 systems)
  - `FSCS_SEQ` 2
  - `LIBNAME` "NEW BRITAIN PUBLIC LIBRARY"
  - `ADDRESS` "20 HIGH ST."
  - `CITY` "NEW BRITAIN"
  - `STABR` "CT"
  - `ZIP` "6051" (the leading zero is lost)
  - `PHONE` 8602243155
  - `C_OUT_TY` "CE"
  - `STATUS` "Active"
  - `STATSTRU` 0
  - `LATITUDE` and `LONGITUD`
  - `CNTY` "HARTFORD"
  - `LOCALE` 21
- **Codes:**
  - `C_OUT_TY`: CE Central 190, BR Branch 45, BS Bookmobile 5. That gives 190 central libraries, the source of "190/191".
  - `STATUS`: Active 226, Non-Respondent 12, Temporarily Closed 2.
- **Proposed curated display:**
  - Name = `LIBNAME` (title case), Address = `ADDRESS` (title case), Town = `CITY` (title case)
  - Detail fields:
    - "Library type" = `C_OUT_TY` decoded to Main library / Branch / Bookmobile
    - "Status" = `STATUS`, shown only when it is "Temporarily Closed"
    - "Phone" = `PHONE`, formatted
- **Weight:** a constant.

### Childcare, licensed: `Book_Access_Child_Care_Centers/FeatureServer/0`
- **Basics:** 1,392 features. Last edit 2025-11-18.
- **Fields:**
  - `Type` "Child Care Center" (1,363) / "Group Child Care Home" (29)
  - `License__`
  - `Name`
  - `Address`
  - `City`
  - `Zip`
  - `Phone`
  - `Email`
  - `Ages_Served` "12 months-12 years"
  - `Total_Capacity` 112
  - `Capacity_Under_3` 16
  - `Expiration_Date`
  - `Legal_Operator__LO_` and the operator's address fields
  - `Coordinates`
  - `Lat` and `Long`
- **Proposed curated display:**
  - Name, Address, Town = `City` (all title case)
  - Detail fields:
    - "Program type" = `Type`
    - "License" = the constant "Licensed"
    - "Ages served" = `Ages_Served`
    - "Capacity" = `Total_Capacity`
    - "Spots for children under 3" = `Capacity_Under_3`
  - Never shown: email, phone, license number, operator.
- **Weight:** a constant 1.
- **Anomaly:** 399 records have an `Expiration_Date` before today. Do not show the expiration date.

### Childcare, exempt: `Book_Access___Child_Care_Center_Exempt/FeatureServer/0`
- **Basics:** 104 features. Last edit 2025-11-18.
- **Type split:** `Type` "Child Care Center Exempt" (89) / "Youth Camp Exempt" (15).
- **`Exemption_Type`:** Public School 79, Municipal Agency 14, Private School 11.
- **Fields:** the same as the licensed layer, minus the capacity and expiry fields.
- **Proposed curated display:**
  - Name, Address, Town (all title case)
  - Detail fields:
    - "Program type" = `Type`
    - "License" = "License-exempt"
    - "Run by" = `Exemption_Type`, e.g. "Public school"
    - "Ages served" = `Ages_Served`
- **Anomaly:** 1 point falls outside the CT bounding box.

### Bookstores: `Book_Access_OVERTURE_Bookstores_/FeatureServer/0`
- **Basics:** 315 features. Last edit 2025-11-18.
- **Fields:**
  - `id` (Overture GUID)
  - `name`
  - `primary_category`
  - `operating_status` (all "open")
  - `confidence`
  - `Lat` and `Lon`. **These field names are swapped.** Use the geometry.
- **No address and no town fields.**
- **`primary_category` covers 27 values:** bookstore 179, comic_books_store 59, library 11, academic_bookstore 8, and noise such as psychic, adult_entertainment and divorce_and_family_law.
- Filtering to bookstore, comic_books_store and academic_bookstore gives **246**, which is within 1 of the BAII's 247. This is very likely the filter the BAII used; confirm with whoever built the index.
- **Proposed curated display:**
  - Name = `name`
  - Town: needs a point-in-polygon join to a town layer (not bundled). Otherwise it is omitted.
  - Detail fields: "Store type" = Bookstore / Comic book store / College bookstore
- **Weight:** a constant 0.5.

### Museums: `MuseumFile2018_File1_Nulls/FeatureServer/0`
- **Counts:**
  - National: 7,431.
  - All CT: 106.
  - **With the spec filter: 85.** By `DISCIPL`: ART 36, HST 19, SCI 15, CMU 11, NAT 4. The filter excludes BOT 17 and ZAW 4.
- **The BAII has 21.** See 2c.
- **Data quality:**
  - The data is from 2018.
  - Blank strings are stored as `" "`.
  - 0 means missing in several numeric fields.
  - 3 filtered records are geocoded to an out-of-state IRS address, and 2 of them fall outside CT.
- **Useful fields:**
  - `COMMONNAME`
  - `ADSTREET`
  - `ADCITY`
  - `ADZIP`
  - `DISCIPL`
  - `WEBURL`
  - `LOCALE4`
  - `FIPSCO`
  - `LATITUDE` and `LONGITUDE`
  - Plus about 50 IRS and source-flag fields that must never be shown.
- **Proposed curated display:**
  - Name = `COMMONNAME` (title case), Address = `ADSTREET`, Town = `ADCITY`
  - Detail fields:
    - "Museum type" = `DISCIPL` decoded: Art museum, History museum, Science center, Children's museum, Natural history museum
    - "Website" = `WEBURL`, lowercased
- **Weight:** `DISCIPL` (CMU 1, others 0.5).

### Little Free Libraries: `Mapped_Little_Free_Libraries___Connecticut/FeatureServer/0`
- **Basics:** 1,131 features. Last edit 2025-09-29.
- **Fields:** only `Latitude`, `Longitude` and `ObjectId`. **There are no names or addresses.**
- **Anomaly:** 10 points fall outside the CT bounding box.
- **Proposed curated display:** title "Little Free Library", with no details.
- **Weight:** 0.5.

### RTG partners: `Active_Partners_Org_N_Families_Oct_24_to_25/FeatureServer/0`
- **Basics:** last edit 2025-12-05.
- **`CustomerType` distinct values:** exactly `Family` (1,270) and `Organization` (443). There are no nulls, **so the two separate cleanly.** Use `where=CustomerType='Organization'` (a positive match, never `<> 'Family'`).
- **Organization fields:**
  - `Organization_Name`
  - `ProgramType`: Books for Kids 289, Bookmobile 104, Books for Babies 50
  - `OrganizationType`: School 130, Early Childhood 107, Community Organization 96, Health Care Provider 74, Library 12, Government 9, Business 7, Philanthropic 7, null 1
  - `Address`
  - `City`
  - `Zipcode`
  - `SUM_of_SumOfQty` (books)
  - `COUNTA_of_Organization_Name`
  - `Lat` and `Lon`
- **Data quality:** 6 organizations have a null name, and 51 names repeat (multi-site organizations).
- **Proposed curated display:**
  - Name = `Organization_Name`, Address = `Address`, Town = `City`
  - Detail fields:
    - "Partner type" = `OrganizationType`
    - "Read to Grow program" = `ProgramType`
  - Books distributed are omitted by default. Decide at Gate 0 whether partners are comfortable with that number being public.
- **Weight:** a constant 1.
- **Privacy:** this layer is public on ArcGIS Online with family home addresses. See Section 7.

### Weight fields, summary
- **Schools:** `Total_Library_staff` and `Num_students_per_library_staff`.
- **Museums:** `DISCIPL`.
- **Childcare:** licensed vs exempt is decided by the source layer. `Type` gives the storymap's four childcare sub-types.

## 2c. Reconciliation preview

| Access type | ArcGIS (filtered) | BAII file | Diff | Flag | Likely reason |
|---|---|---|---|---|---|
| School libraries | 1,494 (794 with staff / 700 without) | 1,494 (storymap 794 / 700) | 0 | | |
| Public libraries | 240 | 240 | 0 | | The "190/191" figure counts central libraries only (CE = 190) |
| Childcare, licensed | 1,392 (1,363 centers + 29 group homes) | 1,392 (1,363 + 29) | 0 | | |
| Childcare, exempt | 104 (89 centers + 15 youth camps) | 103 (89 + 14) | 1 | | Probably the point outside CT |
| Childcare, all (BAII label 6) | 1,496 | 1,495 | 1 | | |
| Bookstores | 315 (246 with the category filter) | 247 | 68 (1) | **YES** unfiltered | The BAII filtered on Overture category |
| Museums | 85 (spec filter) | 21 | 64 | **YES** | The BAII used a much narrower list. See below |
| Little Free Libraries | 1,131 | 1,044 | 87 (7.7%) | **YES** | Probably the out-of-CT clip plus de-duplication, or an older vintage |
| RTG BFK organizations | 443 organizations, all programs | 574 | −131 | **YES** | Different vintage: the BAII predates the Oct 2024 to Oct 2025 layer. The layer's 50 "Books for Babies" organizations may overlap the BAII's 61 Books for Babies sites |
| Books for Babies sites | (no layer; 50 Books for Babies organizations in the partners layer) | 61 | | | |
| Book banks | none | 7 | | | |
| LaundryCares | none | 8 | | | |
| Reach Out & Read | none | **0** | | | Not in the BAII file at all |

Museums: 21 in the BAII against 85 under the spec filter is the largest gap. Possible explanations:
- the BAII used children's museums plus a hand-picked list
- a different museum source
- a confidence or geocode filter

**Decision needed:** should Explore show the 85 museums, which are not all in the index, or only the 21 that are? Showing points that are not in the index would contradict "the data that is already in the BAII".

## 3. Hex data

- **Storage:** hexes are H3 res 8, stored by index with no geometry. Polygons come from `h3.cellToBoundary` in the browser (h3-js is already loaded).
- **Fields:**
  - `baii_snapshot.json` `hex[h3][0]` = `norm_car` and `[1]` = `norm_pt`, the shared "Connecticut scale" (0 to 100, car max = 100).
  - Gap category = `hex[h3][9]`, with labels from `window.GAP_CLASSES` (`gap_classes.js`).
  - Bins = `[7]` and `[8]`.
- **How the existing maps color hexes** (Findings, `colorForCell`, `index.html:4121`):
  - They use **per-mode quintile bins** (`car_bin` / `pt_bin`) on the RdBu ramp `ACC = ["#5A6478","#B2182B","#EF8A62","#F7E8C3","#67A9CF","#2166AC"]` (`index.html:3945`).
  - Other colors: `UNPOP #A7A29A`, `NO_TRANSIT #3B4252`, and `GAP_CLASSES` colors in gap view.
  - The legend caption reads "binned within {mode} access only".
  - The maps are canvas paths, not layers with ids. There is no reusable legend component; legends are HTML strings built inline (`index.html:4850` and nearby).
- **Labels:**
  - Hero toggle: "By car" / "By public transit".
  - Neighborhood map legend: "Car index" / "Public transit index".
  - Tooltip: "On Connecticut's scale: car **N** / 100".
  - The label "Book access by car (Connecticut scale)" **does not exist** in the storymap.

## 4. Geography

- **Statewide outline:** `baii_data/ct_boundary.geojson`, 1 feature, `name`.
- **School districts:** two bundled files that disagree.
  - Root `districts.json`: 167 features, `NAME` (e.g. "Andover School District"), TIGER 2024 school districts. This is the same set as the ArcGIS SD layer (167: 115 unified, 44 elementary, 8 secondary). Elementary and secondary districts overlap.
  - `baii_data/baii_districts.geojson`: **158** features, properties `idx, name, county, child_pop, car_raw, pt_raw, car_bin, pt_bin`. This is the set the storymap uses everywhere: the nav select, `district=` deep links and the Findings ranking.
  - Its `county` field holds the **9 planning regions** (e.g. "Capitol Planning Region"), not counties.
- **Counties:** root `counties.json` is a US-wide TopoJSON with 3,231 counties, quantized. It includes the 8 legacy CT counties (FIPS 09001 to 09015, `name` e.g. "Middlesex"). The ArcGIS county layer is also the 8 legacy counties (`COUNTY`). No planning-region polygons are bundled, though they could be dissolved from `baii_districts.geojson` by `county`.

## 5. Geocoding

- **Endpoint:** `api/geocode.js`, a Vercel function written in CommonJS. It proxies Mapbox Geocoding v6.
- **Env var:** `MAPBOX_TOKEN`. Without it, the endpoint returns 500 `{error}`. It is offline under a plain local static server.
- **Forward:** `GET /api/geocode?q=<text>`.
  - Fewer than 3 characters returns `{features: []}`.
  - Results are restricted by the CT bbox `-73.7277,40.9509,-71.7869,42.0506`, with proximity `-72.7,41.6` and limit 5.
- **Reverse:** `GET /api/geocode?lat=&lng=`, CT only. It returns a neighborhood or town, never a street address.
- **Response:** `{ features: [{ name, full_address, coordinates: [lng, lat], feature_type }] }`.
- **Callers:**
  - The nav search `#addr-input` (`index.html:2682`). Its out-of-state message is "That address is outside Connecticut."
  - The Your Neighborhood form `#yn-search-form` / `#yn-search-input`, with a suggestions listbox and a `#yn-search-status` live region (`index.html:6311` and nearby).
  - "Use my location" (reverse, `index.html:6443`).
  - URL restore (`index.html:5135`).
  - All callers filter results with an `inCT(lng, lat)` check.
- **Shared state:** `window.__userLoc` (subscribe/set) and `window.__resolveAddress({address, lat, lng})`.

## 6. Reusable UI

- **Tokens** (`:root`, `index.html:34`):
  - `--navy #1E3A6F` (page background)
  - `--yellow #E8B43C`
  - `--terra #C45A4A` (closest thing to an alert color)
  - `--white`
  - `--white-2` (rgba 0.7)
  - `--nav-h 48px`
- **Fonts:** the system stack (`-apple-system, Segoe UI`). **The storymap does not use Poppins or Open Sans.**
- **Patterns:**
  - `.b-tag` eyebrow pill
  - `.b-title` / `.b-lede`
  - `.yn-scope-toggle` / `.yn-map-mode` segmented radiogroups (the "5 mi / 10 mi / 20 mi" chips are a direct model for the radius chips)
  - `.yn-search-*` input, suggestions and status
  - `.map-tooltip`
  - `.share-btn` and `.share-toast`
  - `GAP_CLASSES`
  - `escHtml` / `escapeHtml` helpers
- **Your Neighborhood:** all of it is inline in `index.html`, with no separate files. Markup is at `index.html:2352` to `2447` and logic at about `index.html:5360` to `6460`. The deep link is `?section=neighborhood&address=<text>`.
- **Existing radius tool:** YN already has a straight-line 5/10/20 mi radius count using `baii_access_points.json` and `state_avg`.

## 7. Gaps against SPEC.md, with the smallest fix

1. **Stack.**
   - **Gap:** the spec assumes MapLibre, React-like components, an npm build and a "public data folder". The repo is static HTML plus d3/canvas with CDN scripts.
   - **Fix:** build Explore as a new static page, `explore.html`, next to `methodology.html`. Make MapLibre GL JS a new CDN dependency (unpkg or jsdelivr), loaded only on that page. Write data to `baii_data/explore/`.
2. **Section routing.**
   - **Gap:** `section=explore` cannot be a no-scroll 100dvh view inside a scrolling page.
   - **Fix:** add `explore: → explore.html` the same way `section=method` redirects to `methodology.html`. Explore keeps its own params on `explore.html`.
3. **npm script.**
   - **Gap:** there is no `package.json`. Adding one changes how Vercel detects the project.
   - **Fix:** run the script as `node scripts/build-explore-data.mjs` with zero dependencies. If you want `npm run build:explore`, add a minimal `package.json` with only that script (no `build` script), and confirm on a preview deploy.
   - **Simplification:** not needed. `districts.json` and the county TopoJSON are already simplified, and point-in-polygon is about 30 lines of code.
4. **Weights.**
   - **Gap:** the spec's list (public library 4, schools 0 to 5) does not match what the storymap and the methodology page publish (public library **5**, schools **1 to 6**, no-staff school = 1).
   - **Fix:** use the storymap's weights, as Prompt 1 already instructs, and report the difference.
   - **Also:** the storymap treats every museum as 0.5 in code, while the methodology says children's museums count 1. Decide which one the card shows.
5. **Childcare sub-types.**
   - **Gap:** the storymap has four (Child Care Center, Group Child Care Home, Child Care Center Exempt, Youth Camp Exempt), not two.
   - **Fix:** keep the four as legend rows. The KPI card shows Licensed (center + group home) · Exempt (exempt center + youth camp).
6. **School sub-types.**
   - **Gap:** the storymap splits schools into Score 0 to 5. The spec wants with staff / without staff.
   - **Fix:** two legend rows (with library staff = Score 1 to 5, without = Score 0), keeping the score in the card.
7. **Reach Out & Read.**
   - **Gap:** no points exist in the BAII or in ArcGIS.
   - **Fix:** drop it from v1.
8. **Point names for BAII-only types** (Books for Babies, book banks, LaundryCares).
   - **Gap:** the BAII file has no names or addresses, so cards would show only the type. Books for Babies could come from the partners layer (`ProgramType='Books for Babies'`, 50 organizations), but that makes 50 where the BAII has 61.
   - **Fix:** use BAII coordinates with the title set to the type name, and decide at Gate 0 whether to use the partners layer for Books for Babies.
9. **Museums (21 vs 85) and Little Free Libraries (1,044 vs 1,131).**
   - **Gap:** the ArcGIS sets are larger than the index.
   - **Fix:** in the build, match ArcGIS records to BAII coordinates and keep only the matches, so Explore shows exactly what is in the index with ArcGIS details attached. Report unmatched points both ways.
10. **Bookstores.**
    - **Gap:** the spec's "no filter" brings in psychics, law firms and similar.
    - **Fix:** filter `primary_category IN ('bookstore','comic_books_store','academic_bookstore')`, which gives 246 against the BAII's 247. No town field exists, so the card shows the name only. A town would need a bundled town layer.
11. **School district field.** The schools layer's `F2024_25_District` holds student counts. Use point-in-polygon (already in the plan).
12. **District set (167 vs 158).**
    - **Gap:** the ArcGIS/TIGER set has 167 overlapping elementary and secondary districts. The storymap and the BAII use 158.
    - **Fix:** use `baii_districts.geojson` (158). Names then match `district=` deep links and the Findings section, and nothing needs fetching.
13. **Counties vs planning regions.**
    - **Gap:** CT abolished counties in 2022. The BAII and Census now use the 9 planning regions. The old dashboard and the spec use the 8 legacy counties.
    - **Fix:** use the 8 legacy counties from the bundled `counties.json` (no fetch), since the dashboard references (Middlesex) depend on them. Planning regions are the alternative. **Decide at Gate 0.**
14. **Hex scale.**
    - **Gap:** the spec says to use the "Connecticut scale" fields so car and transit compare, *and* to reuse the existing ramp. Those conflict. The existing ramp colors per-mode quintile bins. On the shared scale, transit values are tiny: the Urban Core median is 6.3/100 against 75 by car, so a transit map on the shared scale would be almost uniformly the lowest color.
    - **Fix:** color by the existing per-mode bins with the existing ramp and legend ("binned within … access only"). Show the shared-scale numbers in the address card, as the tooltips already do.
15. **Card labels.**
    - **Gap:** "Book access by car (Connecticut scale)" does not exist.
    - **Fix:** reuse the tooltip phrasing: "By car: N / 100 on Connecticut's scale" and "By public transit: N / 100". The gap category name comes from `GAP_CLASSES[n].label`.
16. **Out-of-index message.**
    - **Gap:** there is no single existing message. YN handles unpopulated hexes by falling back to the district, and handles out-of-state addresses with "That address is outside Connecticut."
    - **Fix:** use "That address is outside Connecticut." for out-of-state addresses. For an unpopulated hex, say "No children live in this neighborhood, so it has no index score."
17. **Index date.**
    - **Gap:** the snapshot has no date in `_meta`.
    - **Fix:** the build script writes `index_date` into `build_meta.json`, from the gpkg file name `baii-2026-06-25` or a constant, without touching the snapshot.
18. **"No arcgis.com requests at runtime" (Prompt 7, QA item 4).** The storymap already loads its basemap images from `services.arcgisonline.com` at runtime. MapLibre needs a basemap. Choose one of:
    - a raster source from the same Esri Light Gray tiles (`.../World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}`), which still hits arcgisonline.com
    - no basemap tiles, with CT and district outlines on navy, which matches the storymap's look
    - a CARTO/OSM style
   
    Recommendation: the Esri Light Gray tiles, which keep the existing look, and the QA item is reworded to "no requests to services5.arcgis.com feature layers at runtime".
19. **Light basemap vs navy page.**
    - **Gap:** the spec says "access points on a light basemap". The storymap's chrome is navy, and its YN map already offers a light "Basemap" style.
    - **Fix:** use a light map inside navy panels.
20. **Alert color.** None is named. Use `--terra #C45A4A`. It is also the Nonprofit category color, so the without-staff school dots need a different shape or outline, or the Nonprofit dots need a change. **Decide at Gate 0.**
21. **Local verification.** `/api/geocode` does not work under `python -m http.server`. Address tests rely on `window.__resolveAddress`-style hooks or the preview deploy.

### Privacy flags (outside Explore, but found during recon)
- **Root `points.json` is deployed publicly** and contains **2,340 "Read to Grow BFK Family" points and 1,790 "Family Day Care" points** with 5-decimal coordinates (about 1 m). The Access Points section loads them. The Honorary types are hidden on the ingredients map, but the file is downloadable. Explore will never read this file, but the existing site already publishes household-level locations.
- **The ArcGIS layer `Active_Partners_Org_N_Families_Oct_24_to_25` is public** and includes family home addresses. RTG may want it restricted to their organization, or the families split into a private layer.
