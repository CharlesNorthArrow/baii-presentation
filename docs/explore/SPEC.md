# Explore view: product spec

## Purpose
A single-screen view where anyone at Read to Grow, or a partner, can browse the book access points behind the BAII. They can narrow to a county or school district, look up an address, and see what sits within a chosen straight-line radius of it. It must feel like a dashboard, not a story: everything is visible at once and the page never scrolls.

## Audience and voice
Read to Grow staff (Kascia must be able to present it without North Arrow in the room), partners, funders. Plain journalistic voice, RTG vocabulary, no hype, no em dashes anywhere in UI copy. Labels describe what the reader is looking at, not how it was computed.

## Layout (desktop, 100dvh, no page scroll)
```
+---------------------------------------------------------------+
| Slim header: title "Explore book access" | What am I looking at? | Back to story |
+-------------------+-------------------------------+-----------+
| LEFT RAIL (~300px) | MAP (flex)                    | RIGHT PANEL (~340px) |
| 1. Address search  |                               | Scope title          |
| 2. Radius chips    |                               | KPI cards (grid)     |
|    1 / 2 / 5 / 10 mi|                              | Nearby list (radius  |
| 3. Area picker     |                               |  mode only, scrolls  |
|    County | District|                              |  inside the panel)   |
| 4. Layers = legend |                               |                      |
|    (checkbox per   |                               |                      |
|    access type,    |                               |                      |
|    grouped by the  |                               |                      |
|    4 categories)   |                               |                      |
| 5. BAII hex toggle |                               |                      |
|    Off | Car | Transit |                          |                      |
| Reset              |                               |                      |
+-------------------+-------------------------------+-----------+
```
Only the inner lists (layer list, nearby list) may scroll, and only inside their own panels. The page itself never scrolls at viewports of 1280x720 and above.

Mobile (<768px): full-screen map, a compact search bar on top, and a bottom sheet with three tabs (Filters, Numbers, Nearby). Page scroll is still not allowed.

## Scope model (one scope at a time, it drives everything)
- Statewide (default)
- Area: one county OR one school district, chosen from the Area picker (searchable list)
- Radius: an address plus a radius in miles. This overrides the Area scope while it is active. Clearing the address returns to the previous scope.
The scope title in the right panel always says what is in view, e.g. "Middlesex County", "Deep River School District", "Within 5 miles of 150 Main St, Deep River".

## Access point typology (do not redefine)
Use the storymap's existing four categories and sub-types exactly as they appear in baii_access_points.json and on the storymap Access Points section. For reference, the methodology groups are:
- In-school: public school libraries (weight 0 if no library staff; 1 to 5 by inverted quintile of students per library staff)
- Out-of-school: public libraries (4), bookstores (0.5), museums: children's 1, art/history/natural history/science 0.5
- Childcare: childcare centers, licensed and exempt (1). Family childcare is NOT in the model and is not shown.
- Nonprofit and community: Little Free Libraries (0.5), RTG Books for Kids partner organizations (1), Books for Babies partners (2.5), book banks (2), LaundryCares (0.5)
Weights are shown only in the point detail card, labeled "Weight in the index".

## Data source per access type
Point details come from the ArcGIS feature layers below, fetched at BUILD time by scripts/build-explore-data.mjs and saved as a static file. The BAII file baii_access_points.json (type and location only) is used to reconcile counts, and as the source for types that have no ArcGIS layer.

| Access type | Source | Filter |
|---|---|---|
| School libraries (with and without staff) | Book_Access_Schools_with_Library_Staff/FeatureServer/0 | none; split on Total_Library_staff = 0 vs > 0 |
| Public libraries | CT_Libraries_2026_(240_Libraries)/FeatureServer/0 | none |
| Childcare centers, licensed | Book_Access_Child_Care_Centers/FeatureServer/0 | none |
| Childcare centers, exempt | Book_Access___Child_Care_Center_Exempt/FeatureServer/0 | none |
| Bookstores | Book_Access_OVERTURE_Bookstores_/FeatureServer/0 | none |
| Museums | MuseumFile2018_File1_Nulls/FeatureServer/0 | ADSTATE = 'CT' AND DISCIPL IN ('ART','HST','SCI','CMU','NAT') |
| Little Free Libraries | Mapped_Little_Free_Libraries___Connecticut/FeatureServer/0 | none |
| RTG Books for Kids partner organizations | Active_Partners_Org_N_Families_Oct_24_to_25/FeatureServer/0 | organizations only; NEVER CustomerType = 'Family' |
| Books for Babies partners, book banks, LaundryCares, Reach Out & Read | baii_access_points.json (no ArcGIS layer) | as in the BAII file |

All services live under https://services5.arcgis.com/IJjAyk93TGaMwoTf/arcgis/rest/services/.

Never fetched: RTG families (household-level), Family Day Care (home addresses, not in the model).

Each point keeps a small, curated set of display fields with plain-English labels, decided in RECON.md. Raw source codes (FSCS_SEQ, C_OUT_TY, LOCALE and similar) never reach the UI.

## KPI cards (right panel, recomputed for the current scope)
1. School libraries: "With library staff" count and "Without library staff" count, side by side (the "without" card uses the alert color).
2. Students per library staff: mean ratio across schools in scope that have staff, with "State average 434" as the comparison line. Use the mean to stay consistent with the methodology brief.
3. Public libraries: count.
4. Childcare centers: count, with a small "Licensed · Exempt" split.
5. Other out-of-school places: bookstores and museums, as counts.
6. Nonprofit and community: count, with a small split by sub-type.
In radius mode only, add a seventh card at the top: "BAII score at this address", showing the hexagon's car and transit scores with the storymap's existing labels ("Book access by car (Connecticut scale)", "Book access by transit (Connecticut scale)") and its gap category name. Link it to the storymap's Your Neighborhood section via the existing deep link.

## Radius tool
- The address search reuses the storymap's existing /api/geocode endpoint and the same search component pattern as the Your Neighborhood section.
- Radius chips: 1, 2, 5, 10 miles (default 2).
- Draw the radius circle on the map, fit the map to it, and dim points outside it.
- Nearby list: access points inside the radius, sorted by distance, showing name, type, and distance ("0.8 mi"). Clicking an item flies to the point and opens its card.
- A fixed caption under the chips: "Straight-line distance. The index itself is based on travel time by car and by transit."

## Map
- MapLibre GL JS with the storymap's existing basemap and style tokens.
- Access points: circle layers colored by the four categories (reuse storymap colors). School libraries without staff use the alert color so the gap reads at a glance.
- School district and county outlines appear only for the selected area. A thin statewide outline is always on.
- BAII hexagon layer: off by default. The toggle switches between car and transit (Connecticut scale fields). It reuses the storymap's existing hex color ramp and legend. The hex layer sits under the points at reduced opacity.
- Click a point to open a small card: name, type, address, town, the curated detail fields for that type (for example: school library staff count, students per library staff or "No library staff reported", enrollment; childcare license type and capacity; museum discipline), and weight in the index. Fields with no value are hidden, not shown as blank or "null".

## URL state (shareable)
Extend the storymap's existing URL param pattern: section=explore, address, radius, area (county:<name> or district:<name>), layers (comma list of hidden sub-types), hex (off|car|transit).

## Out of scope for v1
RTG families or any household-level data; family childcare; KEI, ELA or any outcome data; census population layers; per pupil expenditure; weight editing; any new index computation; live ArcGIS queries at runtime.
