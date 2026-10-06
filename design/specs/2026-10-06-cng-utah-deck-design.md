# CNG Forum Utah deck: design spec

Date: 2026-10-06. Talk: Thursday 8 Oct 2026, 2:51 PM, plenary lightning session, Snowbird.
Source of truth for content: `~/epoch/epoch-obsidian/presentations/CNG Forum Utah.md` ("Slide plan v2" and "Script v2"), plus the decisions below.

## 1. What we're building

A 5-minute Ignite talk: title slide (untimed) + 20 content slides that auto-advance every 15 s + the existing applause slide. Quarto RevealJS, in this repo, rendered locally to `docs/index.html`.

Core idea: Epoch left Earth Engine for a virtual cube, framed by the WWF "so what". Acts:

1. Why it matters (slides 1–5)
2. The engine and its ceiling (6–8)
3. The virtual cube (9–16)
4. So what (17–20)

## 2. Deck-wide decisions

| Topic | Decision |
|---|---|
| Visuals | Rebuild everything. London visuals (`~/projects/cng-talk/out/`, generator code in `~/projects/cng-talk/*.py`) are inspiration only. |
| Animation | Inline SVG + CSS keyframes, scoped to `section.present` so they replay on each visit, timed inside the 15 s slide. No pre-rendered video. A GIF is allowed (slide 9); CNG's no-animation rule was for Google Slides. |
| Theme | London theme: cream `#F4F1EA` content background, ink `#0A1628`, muted `#5B6878`, blue `#376FD0`, blue-soft `#DCE7FB`, green `#3FB557`, green-soft `#57D16F`, problem red `#D64545` (London callout red). Headings Space Grotesk (`fonts/SpaceGrotesk.ttf`), body Google Sans, code Berkeley Mono (already loaded from the Radiant CDN in `custom.scss`). Title slide stays dark imagery as built. |
| Headlines | Mixed: most slides get a Space Grotesk headline top-left; image-led slides (9) may drop it. |
| Problem colour | Red marks problems/limits (slides 8, 11, 12, 15). |
| Speaker notes | Every slide carries its script in `::: notes`. |
| Generators | New `scripts/` folder, its own uv project. Generators write into `slides/_gen/` (inline SVG partials) and `images/gen/` (rasters). |
| Customers | Logos only on slide 1. Never on the slide 2 funnel (we don't call out any customer for poor traceability). |
| Numbers on screen | No EE spend or EECU figures. "2× quicker" and "64 concurrent jobs" are the speaker's call and stay. |

## 3. Architecture

```
index.qmd                     frontmatter, title, 20 includes, applause slide
custom.scss                   existing theme; body bg → cream; shared components
styles/sNN.scss               one per content slide, own scss:rules section (listed in the theme array)
slides/_NN-<slug>.qmd         one slide each: heading + content + ::: notes
slides/_gen/<name>.qmd        generated inline SVG, wrapped in a ```{=html} fence; included by the slide
images/logos/                 customer logos (copied from epoch-mono epoch-astro brands)
images/gen/                   generated rasters
images/src/                   source rasters (screenshots, gif, report chart crops)
scripts/pyproject.toml        uv project for generators + verification
scripts/gen_<slug>.py         generators (one per slide or slide family)
scripts/render.sh             render with a lock dir so parallel builders don't collide
scripts/shoot.py              Playwright (system Chrome) screenshots of slide N at given seconds
design/review/                screenshots for review
```

Rules:

- Partials start with `_` so `quarto render` does not render them as pages. Include with `{{< include slides/_NN-slug.qmd >}}`.
- Slide ids stay `#slide-01` … `#slide-20` (the countdown bar and template CSS key off these).
- Each slide's CSS lives in its own `styles/sNN.scss`. Shared components (cards, headline, stat tile, logo grid, code block) go in `custom.scss`, in the Epoch block.
- Inline SVGs use a `viewBox`, no fixed pixel size, and classes prefixed `sNN-` to avoid collisions.
- Animation timing: the slide is 15 s. Main beats by 12 s, nothing new after 13 s. Use `--d` delays with the existing `.a-fade` / `.a-rise`, or slide-specific keyframes in `styles/sNN.scss`.
- Text readable at the back of a ballroom: body ≥ 28 px and labels ≥ 22 px on the 1600×900 canvas.

## 4. Slides

Each slide below lists: on screen · visual · animation · notes (script) · assets · acceptance.

### 0 · Title (built, untouched)
Agenda title "From Days to Minutes: A Just-in-Time Pipeline for Plot-Level Supply-Chain Analytics", Jake Wilkins, Epoch logo, 4K embeddings background. Untimed.

### 1 · Mapping & quantifying
- **On screen:** headline "Mapping & quantifying". Logo wall below.
- **Visual:** 9 logos in a tidy grid (5 + 4 or 3 × 3), single colour (ink) via CSS filter, consistent optical height: WWF, Altana, Resilinc, Sphera, GAR, 11 Foundry, Lujeri, Assent, Infor. Source: `~/epoch/epoch-mono/ts/apps/epoch-astro/public/static/img/brands/` (`WWF_logo.png, Altana_logo.png, Resilinc_logo.svg, Sphera-logo.png, GAR_logo.png, 11Foundry_logo.svg, Lujeri_logo.png, Assent-Logo.svg, Infor_logo.png`). No sub-line.
- **Animation:** none.
- **Notes:** script line 1.
- **Acceptance:** all 9 logos legible, none dominates, single colour.

### 2 · Minimal visibility into the first mile
- **On screen:** headline "Minimal visibility into the first mile".
- **Visual:** redrawn in our theme: five tiers left to right (Brand → Manufacturer → Trader → Refinery/Mill → Farm), each a progressively more transparent block or funnel segment with more nodes per tier, the last tier fading almost to nothing. No logos and no customer names.
- **Animation:** tiers appear left to right about 1.5 s apart, opacity dropping per tier; ends with the last tier barely visible.
- **Notes:** script line 2.

### 3 · 5% → 73%
- **On screen:** "5%" of facilities → "73%" of post-2020 tropical deforestation; smaller "78% of LUC emissions". Source line: "Epoch × WWF, Codex Planetarius report".
- **Visual:** the long-tail "noncompliance area by facility" chart from the report (`~/Downloads/Epoch × Codex Planetarius — Mapping environmental risk to the firstmile_latest.pdf`). We don't have the underlying data, so don't fabricate bars: extract the chart from the PDF at high resolution and place it in a rounded card. Then overlay our own 5th-percentile marker and label in Epoch blue, or keep the chart's own marker if it's clean. Check the PDF for the figures and use the PDF's numbers if they differ from 5 / 73 / 78. No map for now.
- **Animation:** chart fades in, then the 5% marker highlights about 3 s in, then the big numbers rise.
- **Notes:** script line 3.

### 4 · TRACE
- **On screen:** headline "TRACE: from the brand down to the facility".
- **Visual:** schematic: brand at the top, tiers fanning down to mills/facilities. Three source chips feed in from the side: "web sources", "media", "proprietary sources". No real example. Don't mention launch status.
- **Animation:** tiers appear tier by tier, top-down, about 2 s apart. Source chips pulse into the tree. Ends with facilities highlighted green.
- **Notes:** script line 4 (amended, see §5).

### 5 · Addresses in, plot-level risk out
- **On screen:** headline "Addresses in, plot-level risk out".
- **Visual:** five rounded image cards in a row (or 3 + 2) with numbered blue step badges and captions: 1 Locations & addresses · 2 Geocode & verify (keep the AlphaEarth inset) · 3 Supply sheds · 4 Commodity plots · 5 Environmental metrics. Rebuild from the source images in `~/projects/cng-talk/inputs/` (`stage1_locations_src.jpeg`, `stage2_facility_src.png`, `stage2_embedding_src.png`, `stage3_supply_shed_src.png`, `stage4_plots_src.png`, `stage5_metrics_src.png`). Use `~/projects/cng-talk/stages.py` as reference for the crops and overlays. Captions are HTML in ink on cream.
- **Animation:** cards reveal in sync with the script: about 1 s, 3.5 s, 6 s, 8.5 s, 11 s.
- **Notes:** script line 5.

### 6 · Computed on demand
- **On screen:** headline "Computed on demand, per supply shed".
- **Visual:** SVG pipeline in the London style: Customer supply shed → [Prefect jobs on Kubernetes: export to icechunk → zonal stats → normalise to Postgres] → Served to customer. Service boxes above: **GEE** (feeds export), Icechunk (export + zonal), BigQuery, Postgres. GEE is a neutral box here. Built as one parametrised generator, so slides 8, 9 and 19 reuse it.
- **Animation:** pipeline draws left to right (0–4 s), then "export to icechunk" glows and the other job boxes mute (about 9 s, "that first step").
- **Notes:** script line 6.

### 7 · One global array, filled as we go
- **On screen:** headline "One global array, filled as we go".
- **Visual:** regional view of Sumatra with a real palm supply-shed outline (use the stage 3 source, or a real shed geometry if one is available locally). Overlay a ~12 × 8 chunk grid. Chunk states: filled (green), processed-but-empty (hatched grey, from the metaarray), unprocessed (outline only). A side panel shows two small grids, "data" and "metaarray".
- **Animation:**
  - 0–3 s: grid with some chunks already filled from earlier sheds.
  - 3–6 s: supply shed outline draws on.
  - 6–9 s: intersecting chunks marked (present vs missing).
  - 9–12 s: missing chunks fill (green or hatched).
  - 12–14 s: "commit" pulse across both the data and metaarray panels together, label "one commit".
- **Notes:** script line 7.

### 8 · Earth Engine: 500 requests, 4 facilities
- **On screen:** headline "Earth Engine: 500 requests, 4 facilities".
- **Visual:**
  - The slide 6 pipeline, small, at the top, with GEE now highlighted red.
  - Main area: one pipe labelled "HVE · 500 concurrent requests" feeding exactly four facility lanes, with a queue of waiting facility blocks behind it.
  - Right-hand limits list, in red bullets: unexplained costs · unstable costs · no visibility into processing · not enough throughput.
  - No cost numbers.
- **Animation:** GEE turns red (0.5 s). Requests flow through the pipe as a subtle loop while the queue grows. Limits appear one by one at about 6, 8, 10 and 12 s.
- **Notes:** script line 8.

### 9 · The cuuube
- **On screen:** no headline.
- **Visual:**
  - 0–5 s: `what-is-zarr.gif` (copy from `~/Desktop/what-is-zarr.gif` into `images/src/`, used as-is) large and centred.
  - Then it shrinks left, and a before/after pipeline appears right. Before: the GEE box (red). After: "virtual icechunk · refs in GCS" (green). Everything else is unchanged.
- **Animation:** as above. Before/after cross-fade about 6–9 s.
- **Notes:** script line 9.

### 10 · 20+ datasets, virtualised in place
- **On screen:** headline "20+ datasets, virtualised in place".
- **Visual:** a central "our GCS bucket · virtual refs" node, with arrows out to six origin clouds: Source Coop, AWS Open Data, Copernicus, UMD / Hansen GCS, Wasabi, OpenGeoHub. Caption: "references live with us; bytes stay with the provider".
- **Animation:** arrows draw out one by one about 1 s apart, starting at 2 s.
- **Notes:** script line 10.

### 11 · TIFFs, though
- **On screen:** headline "TIFFs, though".
- **Visual:** three drawn panels, red accents:
  1. UTM zones: a strip of zone columns with tiles in different CRSs, captioned "ForTy".
  2. Ragged 10° tiles: a tile grid where the last row and column are short, captioned "JRC TMF, GFC".
  3. Overwritten in place: a file icon with versions swapping, captioned "level 2 products".
- **Animation:** panels appear about 1, 5 and 9 s, in sync with the script.
- **Notes:** script line 11.

### 12 · Ragged tiles ≠ one array
- **On screen:** headline "Ragged tiles ≠ one array".
- **Visual:**
  - Left: our redraw of regular vs rectilinear chunk grids, credited in small text "after Earthmover".
  - Right: a cropped screenshot of VirtualiZarr issue #1078 ("Dangling pixel concatenation (variable-length chunks)", filed by @jakenotjay). Include Tom Nicholas's comment linking #1111 ("Concatenate arrays with padded final chunks"): https://github.com/zarr-developers/VirtualiZarr/issues/1078#issuecomment-5878245870.
  - Capture it with Playwright, light theme, cropped to the title plus the comment.
- **Animation:** diagram first, screenshot fades in at about 7 s.
- **Notes:** script line 12.

### 13 · Three families
- **On screen:** headline "Three families".
- **Visual:** three panels, each with a small icon flow:
  - A, static global manifest: one stitched manifest → crop. Hansen, JRC GFC.
  - B, tiled static manifests: discover tiles → open persisted manifests → merge. JRC TMF.
  - C, dynamic virtual stores: STAC / listing query → build byte-range refs on the fly → mosaic. GLAD, OPERA DIST, ForTy.
  - Names from `epoch-mono/py/packages/virtual-icechunk/epoch/virtual_icechunk/dataset_source.py`.
- **Animation:** panels appear at about 1, 5 and 9 s.
- **Notes:** script line 13.

### 14 · One protocol
- **On screen:** headline "One protocol: open(geobox, dates) → xarray".
- **Visual:**
  - Left: code block (Berkeley Mono) of the real `VirtualDatasetSource` protocol, trimmed to about 8–10 lines:
    ```python
    class VirtualDatasetSource(Protocol):
        async def open(
            self,
            *,
            target_geobox: GeoBox,
            start_date: datetime | None = None,
            end_date: datetime | None = None,
        ) -> xr.Dataset:
            """Raw bands, lazily reprojected onto target_geobox."""
    ```
  - Right: our own odc-geo style GeoBox card. Show dimensions, EPSG 4326, resolution (~10 m / 0.0000898°), cell/chunk size (read the real chunk size from the epoch-mono grid config), a world locator, and the box drawn over a real supply shed with chunk gridlines.
  - Generate it with a script using odc-geo for the real numbers, then draw it as SVG in our theme.
- **Animation:** code fades in, then the card at about 4 s.
- **Notes:** script line 14.

### 15 · Some data won't play
- **On screen:** headline "Some data won't play".
- **Visual:** Playwright screenshot of the JRC TMF download page (https://forobs.jrc.ec.europa.eu/TMF/data, the click-a-tile-to-download UI) in a browser-frame card, with a red annotation "one tile at a time". If the page can't be captured, render a faithful placeholder card and log it in the build report.
- **Animation:** screenshot in, annotation at about 5 s.
- **Notes:** script line 15.

### 16 · Epoch open data on Source Coop
- **On screen:** headline "Epoch open data on Source Coop".
- **Visual:**
  - A styled grid of the seven datasets with sizes: JRC GFC 2020 (38 GiB) · JRC GFT 2020 (73.8 GiB) · JRC GSW (416 GiB) · JRC TMF (117 GiB) · ForTy (311 GiB) · WRI forest-loss drivers · Xiao natural & planted forests. Sizes come from the fact sheet; omit sizes we don't have.
  - Callout: "every palm oil concession · on a laptop · ~60 s".
  - QR code to https://source.coop/epoch. No people credited on screen.
- **Animation:** grid in, callout at about 8 s.
- **Notes:** script line 16.

### 17 · EE hours per facility ↓ 5–10×
- **On screen:** headline "Earth Engine hours per new facility".
- **Visual:**
  - Bar chart, Mar–Sep 2026, EE hours per new collection: Mar 15, Apr 4.8, May 5.0, Jun 2.1, Jul 0.8, Aug 0.9, Sep 1.9 (fact sheet §8). Jan/Feb are excluded (bulk load / reprocessing).
  - Bars Mar–Jun in muted ink, Jul–Sep green, with a vertical marker at Jul labelled "xarray lane".
  - Big label "↓ 5–10×". Small source note "pipeline EE hours ÷ new facility collections".
- **Animation:** bars grow in sequence (0–5 s), marker at 6 s, label at 8 s.
- **Notes:** script line 17.

### 18 · Results
- **On screen:** four stat tiles: "2× quicker" · "64 concurrent jobs (from 4)" · "Stable under load" · "EE costs ↓". No EE number.
- **Animation:** tiles appear in sync with the script, about 1, 4.5, 8 and 11 s.
- **Notes:** script line 18.

### 19 · We've shifted the bottleneck
- **On screen:** headline "We've shifted the bottleneck".
- **Visual:** the slide 6 pipeline again, with GEE replaced by virtual icechunk (green). A red "bottleneck" marker sits on export, then slides to zonal stats. Target chip "≤ 5 minutes" at the end. No zonal-stats numbers.
- **Animation:** marker slides at about 3 s, zonal stats + normalise boxes get a "rewriting" dashed outline at about 7 s, "≤ 5 minutes" at about 10 s.
- **Notes:** script line 19.

### 20 · Come and chat
- **On screen:** "Come and chat" · Jake Wilkins · GitHub `jakenotjay` · epoch.blue · QR to source.coop/epoch · Epoch logo. No hiring line. No email (the speaker adds one if they want it).
- **Animation:** none.
- **Notes:** script line 20.

## 5. Script (speaker notes)

Use "Script v2" from the Obsidian doc, lines 1–20, with this change for slide 4 (no launch status, real source types):

> 4. TRACE does that tracing for them. We start from the CPG company and work our way down the tiers, aggregating web sources, media and proprietary sources, until we get to the facilities actually sourcing the commodity.

## 6. Verification

- `scripts/render.sh` renders cleanly (`uv run quarto render index.qmd`) with no warnings about missing files.
- `scripts/shoot.py --slide N --at 1,7,14` captures each slide at three moments to `design/review/sNN-tX.png`. Every slide gets reviewed for: nothing clipped at 1600×900, text legible, animation states correct at each timestamp, theme colours only.
- The deck has exactly 20 timed content slides (`#slide-01`–`#slide-20`) between the title and applause slides.
- The preview opens locally (`uv run quarto preview`) for the speaker's review.

## 7. Out of scope (first pass)

Publishing to GitHub Pages, sending the URL to CNG, a final timing rehearsal, the speaker's contact email.

---

## 8. Review 1 changes (2026-10-06 morning)

Slide **files and ids are now stable names, not positions.** The order lives only in `index.qmd`, and `scripts/shoot.py --slide N` takes a *position* (0 = title).

| Pos | File | Change |
|---|---|---|
| 0 | title | Fixed: white type, name, Epoch logo. The template renames `#title-slide` at runtime, so CSS targets `section.quarto-title-block`. |
| 1 | `_01-epoch` | Title "Mapping & quantifying the first mile"; fix GAR logo horizontal alignment |
| 2 | `_02-visibility` | Title "Supply chains remain obscure" |
| 3 | `_03-wwf` | Rework (see below) |
| 4 | `_04-trace` | Hint that tiers continue (6–7 deep), not just 3 |
| 5 | `_05-process` | Squarer image crops (less cut off: facility, supply shed, metrics) |
| 6 | `_06-pipeline` | Unchanged |
| 7 | `_24-supply-shed` | **New**: how a supply shed is generated, animated (spec from epoch-mono source first) |
| 8 | `_07-global-array` | Fade out "new supply shed" label as soon as the shed is drawn |
| 9 | `_08-earth-engine` | Unchanged for now (speaker will revisit after practice runs) |
| 10 | `_09-cube` | Title "The solution: VirtualiZarr"; gif plays then goes; final state is the horizontal before/after pipeline (GEE → virtual icechunk). Fix the clipped bottom edge of "Served to customer". Script absorbs old slide 10's point (refs in GCS, bytes stay with the provider). |
| — | `_10-virtualised` | **Dropped** from the deck (file kept) |
| 11 | `_11-tiffs` | "Overwritten in place" is the alerts datasets (OPERA DIST, Global Forest Watch alerts…), not "level 2 products"; verify in code |
| 12 | `_12-rectilinear` | Fix the confusing "after Earthmover" label |
| 13 | `_13-families` | Every family ends by reprojecting onto the target geobox: A = crop + reproject; B/C = mosaic + reproject. Show the shared final step. |
| 14 | `_14-protocol` | Unchanged |
| 15 | `_15-wont-play` | TMF was behind a Python-script download endpoint that wouldn't even take range requests, not SFTP; update the chip and notes |
| 16 | `_16-open-data` | Verify every size; find WRI drivers size; callout "Computed deforestation in every Indonesian palm oil concession in 60 s on a laptop" |
| 17 | `_17-ee-hours` | Replace with EE **spend** over time (no £ axis values), annotated with the xarray lane and relative change |
| 18–20 | `_21/_22/_23-ai-*` | **New AI section** replacing old 18 (results), 19 (bottleneck): how AI-assisted development (a virtualisation meta-skill in the repo) let one engineer build an Earth Engine alternative: one-shot virtualisation + protocol implementation, verified pixel-perfect against the EE version |
| end | `_20-close` | Now the untimed end slide (replaces the template applause slide): contact + QR |
| — | `_18-results`, `_19-bottleneck` | **Dropped** (files kept) |

### Slide 3 rework
- Slide headline: "A case study: Indonesian palm oil".
- Chart has a title (with 2,594 mills in it), a y axis "Noncompliance area (ha)", 5th / 25th / 50th percentile markers, no "most-deforested mills" x label.
- Try a log y axis; use it if it reads better.
- Use real per-facility data if obtainable; otherwise tell the speaker plainly what the chart is based on.
- Source line, no centre dot: "Source: Codex Planetarius Pilot Study: Palm in Paradise - A Supply Shed Analysis of Indonesian Palm Oil".
- Calmer, conventional layout.

### Speaker-notes tone
British English. Plain, conversational, first person, longer flowing sentences, mildly understated. No punchy fragments ("So data access is everything."), no stage directions, no marketing aphorisms, no "·" separators in prose. About 35–40 words per slide (15 s). Match the existing notes in `slides/_0*.qmd`.
