# Book Access Index — Scrollytelling Prototype

**One-shot build spec for Claude Code.** Produce a working scrollytelling web page that walks a reader through the ingredients of Read to Grow's Book Access Infrastructure Index, one access-point family at a time, on a Connecticut map.

This file contains everything you need. Do not search the web, do not ask clarifying questions, do not ask permission. Build the artifact described below end-to-end.

---

## 1. Deliverable

A single static site, runnable by opening `index.html` in a browser or via `python3 -m http.server`. Three files only:

```
/index.html      # markup, all CSS in <style>, all JS in <script>
/points.json     # data (provided alongside this spec)
/ct.geojson      # Connecticut town boundaries — fetch at build time, see §5
```

No build step. No bundler. No npm install. CDN links only.

---

## 2. Stack (use these exact versions)

```html
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script src="https://unpkg.com/scrollama@3.2.0/build/scrollama.min.js"></script>
<script src="https://unpkg.com/topojson-client@3.1.0/dist/topojson-client.min.js"></script>
```

D3 for the map projection and SVG. Scrollama for the scrollytelling step events. TopoJSON client for parsing CT boundaries.

---

## 3. Page architecture

A two-column scrollytelling layout. Left column scrolls (`<article>` with stacked `<section class="step">` elements). Right column is sticky and contains the SVG map. On mobile (<768px), collapse to single column with map sticky at top.

```
┌─────────────────────────────────────┐
│  HEADER (logo, title)               │
├──────────────┬──────────────────────┤
│              │                      │
│  scrolling   │      sticky map      │
│  narrative   │      (CT silhouette  │
│  panels      │       + points)      │
│              │                      │
│              │                      │
└──────────────┴──────────────────────┘
```

Left column: 40% width, padding `4rem 3rem`, narrative steps with `min-height: 90vh` so each step gets its own scroll position. Right column: 60% width, `position: sticky; top: 0; height: 100vh`.

---

## 4. Brand and visual system

**Colors (use exactly these):**
```
--navy:    #1E3A6F   /* page background */
--navy-2:  #16315F   /* darker accent */
--yellow:  #E8B43C   /* primary accent, points, emphasis */
--yellow-2:#F2CB6E   /* lighter yellow for gradients */
--cream:   #F5F1E6   /* off-state schools, faded markers */
--terra:   #C45A4A   /* nonprofit accent ring */
--white:   #FFFFFF   /* body text */
--white-2: rgba(255,255,255,0.7)  /* secondary text */
--white-3: rgba(255,255,255,0.4)  /* tertiary, faded layers */
```

**Typography:**
- Body: system sans (`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`), 17px, line-height 1.55, white.
- Headlines (slide titles): 2.2rem, weight 600, white, line-height 1.15.
- Eyebrow tags: 0.78rem, uppercase, letter-spacing 0.12em, color `--yellow`, weight 700.
- Chip strip: 0.95rem, italic, color `--yellow`, with white separators (` · `).

**CT silhouette:** use `--navy-2` fill for towns, `rgba(255,255,255,0.08)` stroke 0.5px, plus a soft drop shadow on the outer state outline (SVG `feDropShadow` filter, dx=0, dy=4, stdDeviation=6, flood-color=#000, flood-opacity=0.4). Match the reference scrollytelling on Read to Grow's site.

**Map dimensions:** the SVG fills the sticky column. Use `d3.geoMercator().fitSize([width, height], ctGeoJSON)` so CT scales to the panel.

---

## 5. Data

### 5.1 `points.json` (provided)
Array of objects, ~6,981 records:
```json
[{"type":"Public Library","lat":41.7658,"lng":-72.6734}, ...]
```

### 5.2 `ct.geojson` (fetch at build time)
Use Connecticut town boundaries from the U.S. Census TIGER simplified set. Download once during the build:

```bash
curl -L -o ct.geojson "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/connecticut.geojson"
```

If that URL fails, fall back to drawing CT as a single state outline using the Census state TopoJSON:
```bash
curl -L "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json" -o states.json
# then in JS, filter to FIPS 09 (Connecticut)
```

Either source works. Towns is preferred (more visual texture) but state-only is acceptable.

---

## 6. Asset families and weights (the index ingredients)

Eighteen access-point types group into four families. Symbology is **consistent within a family, distinct across families**.

| Family | Marker | Color | Sized by |
|---|---|---|---|
| Out-of-School | Filled CIRCLE | `--yellow` | aggregate weight |
| In-School | Filled SQUARE | cream→yellow gradient by school score | school score |
| Nonprofit & Community | Filled DIAMOND | `--yellow` fill, `--terra` 1.5px stroke | aggregate weight |
| Childcare | Small DOT (filled, except Family Day Care = hollow ring) | `--cream` at 70% opacity | aggregate weight |

**Marker size formula** (radius in px on a 1200×800 viewbox):
- weight 5 or 6 → 11px
- weight 2.5 → 8px
- weight 2 → 7px
- weight 1 → 5px
- weight 0.5 → 3.5px
- weight 0 → 3px

For squares and diamonds, treat the size as the half-width / radius.

---

## 7. Type → family → weight → Depth → Reach lookup

Use this exact table in JS as a `TYPE_META` object keyed by `type`. The Depth and Reach columns are storytelling devices on a 1–5 scale (rendered as ●○ glyphs in the chip strip).

| type | family | weight | depth | reach |
|---|---|---:|---:|---:|
| Public Library | out-of-school | 5.0 | 5 | 5 |
| Bookstore | out-of-school | 0.5 | 3 | 2 |
| Museum | out-of-school | 0.5 | 3 | 2 |
| School Score 0 | in-school | 1.0 | 1 | 5 |
| School Score 1 | in-school | 2.0 | 2 | 5 |
| School Score 2 | in-school | 3.0 | 3 | 5 |
| School Score 3 | in-school | 4.0 | 4 | 5 |
| School Score 4 | in-school | 5.0 | 5 | 5 |
| School Score 5 | in-school | 6.0 | 5 | 5 |
| Read to Grow BFB Birthing Center | nonprofit | 2.5 | 5 | 2 |
| Book Bank | nonprofit | 2.0 | 5 | 2 |
| Read to Grow BFK Organization | nonprofit | 1.0 | 4 | 4 |
| Little Free Library | nonprofit | 0.5 | 2 | 4 |
| Laundry Cares | nonprofit | 0.5 | 3 | 2 |
| Child Care Center | childcare | 1.0 | 2 | 4 |
| Group Child Care Home | childcare | 1.0 | 2 | 3 |
| Child Care Center Exempt | childcare | 1.0 | 2 | 3 |
| Youth Camp Exempt | childcare | 1.0 | 2 | 2 |
| Family Day Care | childcare | 0.0 | 1 | 2 |

School score colors (cream → yellow gradient):
- Score 0 → `#EFE6CC`
- Score 1 → `#EDD79B`
- Score 2 → `#ECC97A`
- Score 3 → `#EABE5C`
- Score 4 → `#E8B43C`
- Score 5 → `#D89A1F`

---

## 8. Scrollytelling steps

24 steps total. Each `<section class="step" data-step="N">` triggers a map state change when it enters the viewport (Scrollama with `offset: 0.55`).

For each step below: **Eyebrow** is the small uppercase tag. **Title** is the H2. **Body** is the paragraph. **Chip** is the italic stat strip. **Map state** describes what changes on the map when this step activates.

**Visibility rule:** when a step activates, set the active type(s) to `opacity: 1` and `pointer-events: auto`. All previously-shown layers from earlier steps stay on the map at reduced opacity (per the chapter rule below). Layers from steps not yet reached are hidden entirely (`opacity: 0`).

**Chapter fade rule:**
- Within the active chapter, prior subtypes fade to 0.35 opacity when a new subtype activates.
- When a chapter summary slide activates, all subtypes in that chapter return to 1.0 opacity.
- When a new chapter begins, all prior chapter layers fade to 0.15 opacity (still visible as texture).

### Step 0 — Cover
- Eyebrow: *(none — this is the cover)*
- Title: **What goes into a Book Access Index?**
- Body: A tour of the places where Connecticut kids find books — and the ones where they should. Scroll to begin.
- Chip: *(none)*
- Map state: empty CT (no points).

### Chapter 1 — Out-of-School

#### Step 1
- Eyebrow: OUT-OF-SCHOOL
- Title: **Public libraries — the gold standard**
- Body: Free. Permanent. Purpose-built for reading. The public library is the highest-weighted access point in the index because it does what no other place does at the same time: lends books for free, to anyone, with a person on hand to help.
- Chip: 240 sites · Depth ●●●●● · Reach ●●●●● · Weight 5.0
- Map: show `Public Library` only.

#### Step 2
- Eyebrow: OUT-OF-SCHOOL
- Title: **Bookstores — books for sale**
- Body: Bookstores have books on every shelf. They count, but they count less: cost is a real barrier for many families, and bookstores cluster in places that already have a lot of other access points.
- Chip: 247 sites · Depth ●●●○○ · Reach ●●○○○ · Weight 0.5
- Map: add `Bookstore`. Public Library fades to 0.35.

#### Step 3
- Eyebrow: OUT-OF-SCHOOL
- Title: **Museums — where stories live**
- Body: Children's, art, history, and science museums won't lend you a book, but they put kids inside stories. They count as access points because they do something the index otherwise misses: they make reading feel like a place you go.
- Chip: 21 sites · Depth ●●●○○ · Reach ●●○○○ · Weight 0.5
- Map: add `Museum`. Public Library + Bookstore at 0.35.

#### Step 4 — Chapter 1 summary
- Eyebrow: CHAPTER SUMMARY
- Title: **508 out-of-school access points**
- Body: Connecticut's out-of-school book infrastructure is dense in some places and thin in others. Public libraries do most of the heavy lifting; bookstores and museums add texture. This is the layer most people picture when they think "books in the community."
- Chip: 3 types · 508 access points
- Map: all three out-of-school types at full opacity.

### Chapter 2 — In-School

#### Step 5
- Eyebrow: IN-SCHOOL
- Title: **700 schools — and no library on staff**
- Body: Nearly half of Connecticut's schools show up here: no library, no librarian, no media specialist. The children attend every day. The infrastructure for reading does not.
- Chip: 700 sites · Depth ●○○○○ · Reach ●●●●● · Weight 1.0
- Map: Chapter 1 fades to 0.15. Show `School Score 0` only.

#### Step 6
- Eyebrow: IN-SCHOOL
- Title: **Some staffing — but not a librarian**
- Body: These schools have someone who handles books and media, but no certified librarian or full library program. Better than nothing; a long way from a library.
- Chip: 317 sites · Depth ●●○○○ to ●●●○○ · Reach ●●●●● · Weight 2.0–3.0
- Map: add `School Score 1` and `School Score 2`. Score 0 fades to 0.35.

#### Step 7
- Eyebrow: IN-SCHOOL
- Title: **A library and a librarian**
- Body: These are the schools doing it the way schools used to: a library, a librarian, sometimes a full media support team. A child who attends one of these schools sees books at the center of their day, every day.
- Chip: 477 sites · Depth ●●●●○ to ●●●●● · Reach ●●●●● · Weight 4.0–6.0
- Map: add `School Score 3`, `School Score 4`, `School Score 5`. Scores 0–2 at 0.35.

#### Step 8 — Chapter 2 summary
- Eyebrow: CHAPTER SUMMARY
- Title: **1,494 schools — every shade of in-school book access**
- Body: Squares scaled and colored by school score reveal a state where in-school book access is dramatically uneven. Where a child goes to school changes how often a book reaches their hands.
- Chip: 6 staffing levels · 1,494 schools
- Map: all six school score levels at full opacity.

### Chapter 3 — Nonprofit & Community

#### Step 9
- Eyebrow: NONPROFIT — RTG
- Title: **A book for every newborn**
- Body: RTG's Books for Babies program places a book directly in the hands of new parents at the moment a child is born. The window is narrow and the moment is everything — that's why birthing centers carry one of the highest depth scores in the index.
- Chip: 61 sites · Depth ●●●●● · Reach ●●○○○ · Weight 2.5
- Map: Chapters 1+2 at 0.15. Show `Read to Grow BFB Birthing Center` only.

#### Step 10
- Eyebrow: NONPROFIT
- Title: **Book Banks — books in, books out**
- Body: Book Banks are exactly what they sound like: places that collect and redistribute children's books at scale, for free. The depth is unmatched — but Connecticut has only seven of them.
- Chip: 7 sites · Depth ●●●●● · Reach ●●○○○ · Weight 2.0
- Map: add `Book Bank`. BFB at 0.35.

#### Step 11
- Eyebrow: NONPROFIT — RTG
- Title: **Where RTG's books actually arrive**
- Body: 574 active partner organizations across Connecticut request and distribute Read to Grow books to the families they serve. This is the shape of RTG's reach: not a building, but a network.
- Chip: 574 sites · Depth ●●●●○ · Reach ●●●●○ · Weight 1.0
- Map: add `Read to Grow BFK Organization`. Earlier nonprofit layers at 0.35.

#### Step 12
- Eyebrow: NONPROFIT
- Title: **A library on every block**
- Body: Little Free Libraries are tiny, neighbor-stocked, and unpredictable — but there are more than a thousand of them in Connecticut. They aren't a substitute for a public library. They are something else: book access at the scale of a sidewalk.
- Chip: 1,044 sites · Depth ●●○○○ · Reach ●●●●○ · Weight 0.5
- Map: add `Little Free Library`. Earlier nonprofit layers at 0.35.

#### Step 13
- Eyebrow: NONPROFIT
- Title: **Books where families already wait**
- Body: Laundry Cares puts a reading nook inside a laundromat. A small footprint with a clever insight: meet families where they already spend time, not where you wish they did.
- Chip: 8 sites · Depth ●●●○○ · Reach ●●○○○ · Weight 0.5
- Map: add `Laundry Cares`. Earlier nonprofit layers at 0.35.

#### Step 14 — Chapter 3 summary
- Eyebrow: CHAPTER SUMMARY
- Title: **1,694 community access points — the network behind the buildings**
- Body: Stacked together, the nonprofit and community layer is the densest in Connecticut. It is also the most distributed, the most informal, and the most volunteer-dependent — which is the strategic reality the index has to capture.
- Chip: 5 types · 1,694 access points
- Map: all five nonprofit subtypes at full opacity.

### Chapter 4 — Childcare

#### Step 15
- Eyebrow: CHILDCARE
- Title: **The youngest children's daily place**
- Body: More than 1,300 licensed child care centers serve Connecticut's youngest children. Some have rich book corners; many do not. The index counts them because the children are there — every day, for years, at the most formative moment for early literacy.
- Chip: 1,363 sites · Depth ●●○○○ · Reach ●●●●○ · Weight 1.0
- Map: Chapters 1+2+3 at 0.15. Show `Child Care Center` only.

#### Step 16
- Eyebrow: CHILDCARE
- Title: **The other licensed care providers**
- Body: Smaller, more varied, and less standardized — but children spend full days here. Books are not guaranteed. Books are also not impossible to add.
- Chip: 132 sites · Depth ●●○○○ · Reach ●●○○○ to ●●●○○ · Weight 1.0
- Map: add `Group Child Care Home`, `Child Care Center Exempt`, `Youth Camp Exempt`. CCC at 0.35.

#### Step 17
- Eyebrow: CHILDCARE
- Title: **On the map, but not yet in the index**
- Body: Family Day Cares are home-based and tiny — typically a handful of children. Connecticut has 1,790 of them. They appear on this map because they belong to the conversation. They carry weight zero in the model today: too small, too varied, too unverified to count toward access. But they are exactly the kind of place where a single shelf could change a year of a child's life.
- Chip: 1,790 sites · Depth ●○○○○ · Reach ●●○○○ · Weight 0.0 (counted, not weighted)
- Map: add `Family Day Care` as HOLLOW dots (stroke only, no fill). Other childcare at 0.35.

#### Step 18 — Chapter 4 summary
- Eyebrow: CHAPTER SUMMARY
- Title: **3,285 childcare locations — books often welcome, not always present**
- Body: Childcare is the largest family of access points in the dataset and the lowest-weighted on average. That tension is the strategic insight: huge reach, shallow depth, enormous opportunity for any program that can deepen book access in places that already have the children.
- Chip: 4 types · 3,285 locations
- Map: all four childcare subtypes at full opacity.

### Step 19 — Closing
- Eyebrow: THE FULL PICTURE
- Title: **9,511 access points. Now what?**
- Body: This is what the Book Access Index sees. Every type, every weight, every place a Connecticut child might find a book — assembled into a single layer. But places aren't the whole story. A library nearby is less useful to a parent working two jobs. The next chapter of this map adds the barriers: who can actually reach what's there.
- Chip: 18 types · 9,511 access points across Connecticut
- Map: ALL families at full chapter symbology, full opacity.

---

## 9. Implementation details

### 9.1 Layout HTML skeleton
```html
<body>
  <header class="topbar">
    <div class="brand">READ TO GROW × NORTH ARROW</div>
  </header>
  <main class="scrolly">
    <article class="narrative">
      <section class="step" data-step="0">…</section>
      <!-- 19 more sections -->
    </article>
    <figure class="map-sticky">
      <svg id="ct-map" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid meet"></svg>
    </figure>
  </main>
</body>
```

### 9.2 SVG layer order (back to front)
1. Defs (drop shadow filter)
2. CT towns/state geometry — back layer
3. One `<g class="layer" data-type="...">` per access-point type — 18 groups total
4. Within each group, one shape (`<circle>`, `<rect>`, or `<polygon>` for diamond) per point

Each group starts with `opacity: 0`. Step transitions adjust group opacity via D3 transitions (200ms ease).

### 9.3 Diamond marker
SVG diamond as a rotated square or a polygon: `<polygon points="0,-r r,0 0,r -r,0">` translated to (cx, cy).

### 9.4 Family Day Care hollow style
`fill: none; stroke: var(--cream); stroke-width: 1px; stroke-opacity: 0.7;` Radius 3px.

### 9.5 Step → state mapping in JS
Define a single `STEPS` array, one entry per step, each containing:
```js
{
  active: ["Public Library"],          // types fully visible
  faded: [],                            // types at 0.35 (within current chapter)
  background: [],                       // types at 0.15 (prior chapters)
}
```
Compute the state for each step at load. On `scrollama` `onStepEnter`, transition each layer's opacity to the value implied by the active step.

### 9.6 Scrollama setup
```js
const scroller = scrollama();
scroller
  .setup({ step: ".step", offset: 0.55, debug: false })
  .onStepEnter(({ index }) => applyMapState(index));
window.addEventListener("resize", () => scroller.resize());
```

### 9.7 Mobile (≤768px)
- Single column. Map sticks to top, height 50vh.
- Narrative panels reduce padding to `2rem 1.5rem`, font-size 16px.
- Chip strip wraps to multiple lines.

### 9.8 Performance
- 6,981 SVG nodes is fine. No clustering needed.
- Use `pointer-events: none` on faded/background layers.
- Animate opacity only — never animate positions.

### 9.9 Accessibility
- `<section>` for each step. The visible eyebrow + title + body + chip is the screen-reader content.
- Chip strip: render `●` and `○` inside `<span aria-hidden="true">` and provide `<span class="sr-only">Depth: 5 of 5. Reach: 5 of 5.</span>` for screen readers.
- Map is decorative for screen readers (`role="img"` with an `aria-label="Map of Connecticut showing book access points"`).
- Respect `prefers-reduced-motion`: skip opacity transitions, snap directly.

---

## 10. Acceptance criteria

The artifact is correct if all of the following are true:

1. Opening `index.html` from a static server shows a navy page with the RTG eyebrow and the cover step at the top, an empty CT silhouette on the right.
2. Scrolling smoothly advances through 20 steps. The map updates as each step crosses the 55% viewport line.
3. Step 1 shows 240 large yellow circles only. Step 2 adds 247 smaller yellow circles and fades step 1's circles to 35%. Step 3 adds 21 museum circles. Step 4 brings all three sublayers back to full opacity.
4. Step 5 fades all out-of-school markers to 15% (still visible) and shows 700 cream squares for `School Score 0`. Steps 6–7 progressively add darker, larger squares. Step 8 shows all 1,494 schools at full opacity.
5. Steps 9–13 add the five nonprofit/community types one at a time, with the diamond shape and terracotta stroke. Step 14 shows all five together.
6. Steps 15–17 add childcare types as small cream dots; step 17's `Family Day Care` markers are hollow rings.
7. Step 19 shows ALL 18 types at full opacity simultaneously, on top of the CT silhouette, with the four families clearly distinguishable by shape (circle / square / diamond / dot).
8. The eyebrow tag and chip strip use the brand yellow `#E8B43C`.
9. The page is responsive: at 375px viewport width, the layout stacks vertically and the map is at the top.
10. No console errors. No broken external resources.

---

## 11. What NOT to do

- Do not invent a build step or framework — pure HTML/CSS/JS with three CDN scripts.
- Do not change the copy in §8. The narrative voice is intentional and approved.
- Do not change the marker shapes or family-to-shape mapping in §6.
- Do not introduce new colors. Stick to the palette in §4.
- Do not add controls (legend, filters, dropdowns). This is a linear narrative.
- Do not animate position, only opacity.
- Do not use a tile basemap (no Mapbox, no Leaflet). The styled SVG silhouette is the brand-correct treatment.
- Do not add analytics, cookies, or external trackers.

---

## 12. Build sequence (recommended)

1. Fetch `ct.geojson` (see §5.2) and save to project root.
2. Write `index.html` skeleton with `<style>` and `<script>` placeholders.
3. Add CSS: variables, layout (grid for two columns), typography, step styling, mobile breakpoint.
4. Write the markup for all 20 `<section class="step">` blocks using the copy in §8.
5. JS: load `points.json` and `ct.geojson` in parallel, then render the CT silhouette and 18 layer groups (one per type).
6. JS: define `STEPS` array (computed from §8's "Map state" rules — write a small helper to expand the 4-chapter fade rule into per-step layer opacities).
7. JS: wire up Scrollama and `applyMapState(index)` which calls `d3.selectAll(".layer").transition().duration(200).style("opacity", ...)`.
8. Test: scroll top to bottom, confirm each acceptance criterion in §10.
9. Test mobile: open DevTools, set viewport to iPhone 12, confirm layout stacks and map sticks to top.
10. Done. No README needed. No deploy step. Hand back the three files.

---

## 13. Closing

Build it once, build it tight. The reference for visual quality is the existing RTG scrollytelling at rtgdata.north-arrow.org — same navy, same yellow, same calm pace. If a decision is not specified above, default to the choice that most closely matches that reference.
