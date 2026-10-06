# Slide 7 (`_24-supply-shed`): how a supply shed is made

Spec for the new 15-second animated slide. Section 1 is traced from `~/epoch/epoch-mono` at the
current `HEAD`. All paths below are relative to `py/apps/sco2api/epoch/sco2api/` unless they say
otherwise.

**Short version:** a supply shed is a **travel-time isochrone**. The pipeline builds a friction
surface (seconds per metre) from Overture roads, Copernicus DEM slope, ESA WorldCover land cover,
JRC surface water and the national border. It runs a least-cost (Dijkstra-style) spread outwards
from the mill on a 100 m grid and keeps every cell reachable within the commodity's time budget,
which is **90 minutes for palm**. The result is **one hard-edged polygon, not a probability
surface**. Nothing in the shed step decays with distance, and competing mills are not taken into
account. The "probabilistic" part of the product comes later, when commodity plots are detected
inside the shed (`routers/vector.py::batch_supply_shed` docstring: "generates probabilistic commodity
plots inside them"). The slide should not call the shed itself probabilistic.

---

## 1. How it works

1. **Input: a facility and a commodity.** `flows/compute_isochrone.py::compute_isochrone_task`
   reads the uploaded facility GeoJSON. If every feature is a Point, it computes an isochrone at the
   centroid. If the facility is a polygon, that polygon is used as the shed with no isochrone. The
   commodity comes from `request_data.crop_type`, with a feature's `crop_type` property taking
   precedence, and defaults to `"palm"`. The country comes from a nearest join against the bundled
   `data/countries.parquet`.

2. **Travel-time budget per commodity.** `_DEFAULT_COMMODITY_TRAVEL_TIMES` in
   `flows/compute_isochrone.py` sets palm 90, cocoa 90, coffee 60, shrimp 60, soy 120, rubber 120,
   cattle 180 and timber 180 minutes. An unknown commodity gets 120 (`travel_times_for`). The env
   var `COMMODITY_TRAVEL_TIMES_OVERRIDE` can override these. The rationale is in
   `docs/docs/batch/supply_shed_travel_times.md`. For palm, fresh fruit bunches must reach a mill
   within 24–48 h of harvest before free fatty acids spike, and 90 minutes (about 50 km) is meant to
   cover organised and plasma smallholders. Roadside collectors are deliberately excluded.

3. **Search box and grid.** `routers/vector.py::supply_shed`:
   - If the budget is ≤ 120 min, the radius is `travel_time × 1200` m at 100 m resolution. For
     palm that is 108 km.
   - If the budget is > 120 min, the radius is `× 2400` m at 200 m resolution.

   `isochrone_util/dataloader.py::Dataloader.__init__` buffers the point in its local UTM zone into
   a square (`cap_style=3`) and takes its WGS84 bounds. Every raster is loaded onto one EPSG:3857
   grid at that resolution. The slope raster is loaded first and is the reference grid. For palm
   this is roughly 2,160 × 2,160 cells.

4. **Base layers.** These load in parallel in `isochrone_util/isochrone_util.py::Isochrone.get_friction_raster`.
   The raster layers come from the Planetary Computer STAC, read at a COG overview close to 100 m.

   | Layer | Source (code) | Loader |
   |---|---|---|
   | Elevation → slope (degrees) | Copernicus DEM GLO-30, `cop-dem-glo-30` | `get_elevation_raster`, `get_slope_raster` (`xrspatial.slope`) |
   | Land cover | ESA WorldCover 2021, `esa-worldcover` | `get_landcover_raster` |
   | Water | JRC Global Surface Water 2020 occurrence, `jrc-gsw` | `get_water_raster` |
   | Roads | Overture `transportation/segment`, pinned release `2026-08-19.0` | `iter_road_chunks_parquet` |
   | National border | Exterior ring of the facility's country from bundled `data/countries.parquet` | `get_border_geometry`, `get_border_raster` |

   - **How roads are read.** By default they come from public GeoParquet on S3 through DuckDB
     (`packages/epoch-utils/epoch/epoch_utils/overture.py`). Setting `ISOCHRONE_ROAD_SOURCE=bigquery`
     switches to the BigQuery mirror.
   - **Which roads.** The query keeps `subtype='road'` in the drivable classes. Arterials
     (motorway to tertiary) are fetched across the whole box. Minor roads are fetched only in the
     inner 25% of the box (`_DETAIL_RADIUS_FRACTION`), which is about ±27 km for palm.
   - **Cap.** The fetch stops at 150,000 segments, ordered by class and then by distance from the
     centre (`_MAX_SEGMENTS_PER_SOLVE`).

5. **Road speeds.** These come from `isochrone_util/weights.yml` and
   `isochrone_util.py::road_mapping`. Weights are in **seconds per metre** and are tuned for heavy
   trucks:

   | Class | Weight (s/m) | Speed |
   |---|---|---|
   | motorway | 0.045 | 80 km/h |
   | trunk | 0.055 | 65 km/h |
   | primary | 0.06 | 60 km/h |
   | secondary | 0.07 | 50 km/h |
   | tertiary | 0.08 | 45 km/h |
   | residential | 0.12 | 30 km/h |
   | track | 0.18 | 20 km/h |
   | ferry | 0.25 | 15 km/h |

   - **Surface.** Unpaved surfaces (dirt, gravel, mud and so on) multiply the weight by 1.7.
   - **Posted speed limits** can only slow a road below its class estimate
     (`np.maximum(highways, 3.6/limit)`).
   - **HGV bans.** Roads that deny heavy goods vehicles get a weight of 100, which makes them
     effectively impassable.
   - **Rasterising.** Roads are burnt onto the grid with a 3-cell `maximum_filter`
     (`get_road_raster(padding=2)`) so that they stay connected. They are then multiplied by
     `road_coefficient = 0.92`, which offsets 8-connected paths overstating a straight road. That
     makes the effective speeds about 87, 65, 56, 49 and 33 km/h for motorway down to residential.

6. **Friction surface.** In `get_friction_raster`, each cell's value is in seconds per metre.
   - **Off-road.** The cost is land cover × `landcover_rate = 0.2` plus `slope² / 500`.
     - Land-cover multipliers come from `weights.yml`. Open land, crops and built-up areas are 1,
       which is 0.2 s/m or about 18 km/h. Tree cover and snow are 2, about 9 km/h. Wetland,
       mangrove, moss and water classes are 3, about 6 km/h.
     - A 10° slope adds 0.2 s/m. A 30° slope adds 1.8 s/m.
   - **Water.** Any cell with JRC occurrence > 0, or with no data (`fillna(100)`), becomes
     `water_rate = 20` s/m, about 0.18 km/h. Crossing one 100 m cell costs about 33 minutes.
   - **Precedence.** A road replaces whatever is beneath it, so bridges cross rivers. Otherwise
     water replaces the off-road cost.
   - **Border.** The border (7 cells wide) adds `border_crossing_time = 60` s/m to whatever is
     there.
   - **Scaling to seconds per cell.** The surface is multiplied by `resolution × cos(latitude)` to
     correct for EPSG:3857 scale. At Kampar (0.2° N) the correction is negligible.

7. **Start cell.** `Isochrone.offset_centroid` finds the mill's cell. If that cell is water or
   border (cost ≥ 500 s), it moves the start to the nearest cell that is traversable on all four
   sides. If there is none, the request fails with "confirm it is not on a large water body".

8. **Cumulative travel time.** `Isochrone.get_cumulative_cost` runs
   `skimage.graph.MCP_Geometric(..., fully_connected=True)`, which is a Dijkstra least-cost spread
   with 8 neighbours. Each step costs the mean of the two cells' friction × step length. It spreads
   outwards from the start cell. Zero costs are clamped to 1e-7 and non-finite values fail loudly.
   Cells beyond `max(travel_times) × 60` s are set to ∞. The result is in seconds, and
   `form_isochrones` divides by 60.

9. **Threshold and vectorise.** For each budget, `Isochrone.form_isochrones` builds the mask
   `cumulative_minutes ≤ travel_time`, vectorises it with `contourrs.shapes` and unions the result.
   It then reprojects 3857 → 4326 and simplifies at 0.001° (about 110 m). The output is a
   GeoDataFrame with one (Multi)Polygon per travel time, with columns `latitude`, `longitude`,
   `travel_time` and `geometry`.
   - Several budgets give **nested rings**, but the batch path passes only one (palm `[90]`), so in
     practice there is **one polygon**.
   - Holes are kept. These are water bodies and pockets that cannot be reached in time.
   - Area is measured in local UTM (`routers/vector.py::supply_shed`).

10. **Where it runs.** `routers/vector.py::batch_supply_shed` hands off to the Prefect flow
    `flows/start_batch_supply_shed.py::start_batch_supply_shed`. For point facilities, this triggers
    the `compute-isochrone` flow (`flows/compute_isochrone.py::compute_isochrone_flow`) on
    Kubernetes. That flow has 2 retries for transient MCP and GDAL segfaults and a 2 h timeout. It
    stages the shed and the facility to BigQuery, then fires `export_to_icechunk` over the shed's
    bounds, which in turn fires `detect_plots`. `detect_plots` finds the commodity plots inside the
    shed, and that is where the probability models come in.
    - An alternative `radii` mode on the `/supply_shed` endpoint returns plain UTM circles instead
      of an isochrone.
    - `services/travel_time_units.py` uses the same friction surface for parcel files that have no
      facility. That is a different product, and it is the only place where neighbouring units are
      partitioned so that they never overlap.

**Competing mills:** not modelled for facility sheds. Each mill's shed is computed independently,
and sheds may overlap.

### Uncertain or worth knowing (not for the slide)

- **Sample shed's travel time.** `shed.geojson` carries no `travel_time` property. It was created on
  2026-04-20, and palm has defaulted to `[90]` since at least 2026-03-28 (commit `41e567850f`), so it
  is almost certainly 90 min unless the env override was set. The sample in `fetch_supply_shed.md`
  shows palm at `travel_time_min: 120`, which looks stale.
- **The algorithm has changed since the sample was built.**
  - `road_coefficient` has gone from 0.8 to 0.92, so roads are now about 13% slower.
  - Posted limits can now only slow a road.
  - The cos(latitude) correction was added in 2026-05 (`04c09a3aff`), but it is negligible at the
    equator.

  A rerun today would probably give a somewhat smaller shed. `weights.yml` is unchanged since
  April.
- **Off-road open land is faster than an unpaved track.** Open land comes out at 0.2 s/m (about
  18 km/h), while an unpaved track is 0.18 × 1.7 × 0.92 ≈ 0.28 s/m (about 13 km/h). The comment in
  `weights.yml` ("multiple against walking speed of 0.71 s/m") doesn't match `landcover_rate = 0.2`
  in the code.
- **Borders behave as a wall.** The docs call the border a "crossing time penalty". In practice
  +60 s/m over a 7-cell band is about 100 min per 100 m cell, so the border acts as a wall for any
  budget up to 180 min.
- **Ferry and rail.**
  - `weights.yml` has ferry and railroad weights, but the Parquet query filters
    `subtype = 'road'`. Rail can never appear.
  - Whether Overture ferries ever arrive under `subtype = 'road'` is unverified.
- **Per-request `travel_times`.** `BatchSupplyShedForm` accepts per-request `travel_times`
  (`dependencies/dependencies.py`), but `compute_isochrone_task` never reads it. It uses only
  `travel_times_for(crop_type)`, despite what the docs say. This could be a bug.
- **Stale descriptions in the docs and docstrings.**
  - The workflow diagram (`docs/docs/images/isochrone_workflow.jpg`) says "OpenCV",
    "Overture via BigQuery" and "geoBoundaries API". The code now uses contourrs, Parquet by
    default and a bundled countries file.
  - The `get_border_geometry` docstring still mentions GeoBoundaries.
- **The mill sits in a small hole of the sample shed.** In the sample shed the mill point lies
  about 200 m inside one of 527 small holes. Drop small holes on the slide so the mill sits
  inside.

---

## 2. What's real vs simplified on the slide

**Real:**
- **The shed outline.** Binabaru mill, Kampar, Riau, from `shed.geojson`:
  - The largest part is 6,560 km² (`area_ha` 658,475).
  - The other 30 parts are each under 0.2 km².
- **The mill location:** 101.27548 E, 0.210053 N.
- **The 90-minute palm budget.**
- **The reach figures**, measured from the mill to the outer edge of the main polygon in UTM 47N:
  - About 30 km to the west (270°) and about 31 km to the south-south-east (150°).
  - About 56–57 km to the south (165–180°) and about 53–55 km to the north-east and north-west.
  - Maximum 62 km.
- **The comparison circle.** An equal-area circle would have a radius of 45.7 km.
- **The input datasets named on screen**, and the rounded speeds, which come from `weights.yml`.

**Simplified:**
- **The four layer tiles are schematic patterns, not real rasters.** Overture roads and the
  friction raster for this mill are not cached locally.
- **The spreading front is a radial clip reveal of the final outline, not the true travel-time
  front.** The real front races along roads and stalls in forest and hills. Intermediate 30- and
  60-minute contours weren't computed for this shed. The timer ticking 0 → 90 is illustrative.
- **Holes under about 2 km² and the 30 slivers are dropped.** The outline is simplified at about
  0.003°.
- **The 50 km dashed circle is a comparison device, not part of the pipeline.** It is the docs'
  rough distance for palm and the kind of buffer the `radii` mode returns.
- **The speed key is rounded** and leaves out `road_coefficient`, surface multipliers and the
  border band.

---

## 3. Storyboard (15 s)

**Headline (≤ 8 words):** "Ninety minutes by road from the mill"

Alternatives:
- "A supply shed is a drive-time map"
- "Where a truck gets in ninety minutes"

**Layout.** The slide is 16:9 on cream `#F4F1EA`.
- **Map panel**, left, about 60% width: an equirectangular view of the shed bbox plus about 15%
  margin, roughly 100.65–101.83 E and −0.45–0.78 N. At 0.2° N, cos(lat) ≈ 1, so a plain lon/lat
  scale is fine. If you want context, show faint Sumatra land from `images/src/s07-geometry.json`
  (`land`) in `#E8E3D8` with no stroke.
- **Step rail**, right: four short numbered steps in ink with blue badges, matching slide 5's
  badge style. Each step brightens on its beat and dims to 50% after.

**Colours.**
- Ink `#0A1628` for text and the final outline.
- Blue `#376FD0` for the mill, the badges and the spreading front.
- Green `#3FB557` stroke and `#57D16F` fill (25–30% opacity) for the finished shed.

| Time | Beat | On screen | Step rail |
|---|---|---|---|
| **0–3 s** | The mill | Map panel fades in. A blue mill dot (r ≈ 7 px) at the facility drops in and pulses once. A small label in ink reads "Binabaru mill, Riau · palm". | **1 · Mill + commodity → 90 min** |
| **3–6 s** | Cost surface | Four thin skewed tiles slide in from the right edge of the map and stack: **Roads** (Overture), **Slope** (Copernicus DEM), **Land cover** (ESA WorldCover) and **Water** (JRC). Each is a simple pattern (lines, contour hatching, patchy fills, blue squiggles). At about 5 s they collapse into one tile labelled "seconds per metre". A three-line key fades in under it: "Roads 20–80 km/h", "Off-road slower, slower again on slopes and in forest" and "Water is a barrier unless bridged". | **2 · Roads, terrain, land cover → friction** |
| **6–9 s** | Spread | Tiles and key fade to 0. From the mill, a blue fill (`#376FD0` at 18%) reveals the real shed through an SVG `clipPath` circle whose `r` animates from 0 to 62 km in map units (ease-out). This makes the edge advance unevenly as it meets the real outline. A small mono timer near the mill counts "0 → 90 min" (CSS counter or 4–5 stepped labels). | **3 · Least-cost spread on a 100 m grid** |
| **9–12 s** | Cut at 90 min | The real outline draws on in ink (1.5 px, `stroke-dashoffset`, about 2 s). A dashed ink circle of 50 km (0.45° at this latitude) fades in at 40%, labelled "50 km circle". Two leader-line callouts appear: "~57 km" on the southern lobe (bearing about 170°) and "~30 km" to the west (bearing 270°). | **4 · Cut at 90 minutes → one polygon** |
| **12–14 s** | The shed | The fill cross-fades from blue to green `#57D16F` at 28% and the outline turns `#3FB557`. The circle and callouts fade out. A caption under the map reads "Supply shed · 90 min · 6,560 km²". | All four steps at full ink |
| 14–15 s | Hold | Static final state, so the slide reads cleanly if paused. | |

**Optional extra at 12–14 s.** About 300 real plot polygons, sampled from `plots.geojson`, could
speckle in at 40% green inside the shed as a hand-off to "commodity plots". Skip it if it crowds
the frame. Slide 5 already shows plots.

**Speaker notes** (38 words):

> For each mill we turn the Overture road network, a global elevation model and land cover into a
> travel-time surface, and the supply shed is everywhere a truck can reach within ninety minutes,
> so it follows the roads.

**Build notes.**
- Follow the `scripts/gen_s07_array.py` pattern. Add `scripts/gen_s24_shed.py` and have it write
  `slides/_gen/s24-shed.qmd` and cache the simplified geometry in `images/src/s24-geometry.json`.
  Put keyframes in the existing `styles/s24.scss`, with `--d` delays as on slide 8.
- Geometry prep in shapely:
  1. Take the largest polygon of the MultiPolygon.
  2. Drop interiors under 2 km² (measured in EPSG:32647).
  3. `simplify(0.003)`, which gives about 300–450 exterior vertices.
  4. Project with `x = (lon − lon0) × PX` and `y = (lat1 − lat) × PX`.
- The shed is already in `s07-geometry.json`, which keeps slides 7 and 8 consistent. Check that
  its simplification keeps the lobes.
- Use `clipPath` with an animated `<circle r>` (SMIL `<animate>` or CSS `r` transition, which
  works in Chromium) for the reveal. Use `pathLength="1"` plus `stroke-dasharray` for the outline
  draw.

---

## 4. Data files for the builder

| File | Use |
|---|---|
| `~/epoch/data/sample-geojson/palm/shed.geojson` | Real 90-minute palm shed for Binabaru mill. A MultiPolygon with 31 parts and 527 holes, bbox 100.755–101.724 E, −0.349–0.676 N. |
| `~/epoch/data/sample-geojson/palm/facility.geojson` | Mill point (101.27548, 0.210053) with name and address. |
| `~/epoch/cng-forum-talk/images/src/s07-geometry.json` | Cached simplified `shed`, `facility` and Sumatra `land` already used on slide 8. Reuse for consistency. |
| `~/epoch/data/sample-geojson/palm/plots.geojson` | 190 MB, 29,516 detected plots in this shed. Only for the optional plot speckle. Sample it in the generator, don't ship it. |
| `~/projects/cng-talk/inputs/stage3_supply_shed_src.png` (identical to `images/src/s05-stage3-src.png`) | Reference only. It appears to be the same Binabaru shed with plots over Esri imagery. |
| `~/epoch/epoch-mono/py/apps/sco2api/epoch/sco2api/isochrone_util/weights.yml` | Source of the speed key. |
| `~/epoch/epoch-mono/py/apps/sco2api/docs/docs/images/isochrone_base_rasters.png` | Reference for how the real layers look (landcover, slope, water, road, border, friction, cumulative cost, isochrones). Not Riau. Don't embed it. |

**Reproducing the real intermediate layers.** Nothing is cached locally: there are no Overture
extracts, friction rasters or test fixtures with roads. Two options:

- **Real roads only.** A one-off DuckDB read of Overture `transportation/segment`, release
  `2026-08-19.0`, from the public `s3://overturemaps-us-west-2` bucket for the shed bbox. Keep
  arterial classes only. It is unauthenticated and free, takes about 20 s cold and returns a few
  thousand segments. It is still a network read, so ask before running it.
- **The full friction and cost rasters.** These need Planetary Computer STAC reads. Run
  `Isochrone(longitude=101.27548, latitude=0.210053, radius=108000, resolution=100).form_isochrones([30, 60, 90])`
  from sco2api, which would also give real 30/60/90-minute rings for the spread beat. That is a
  heavier, cloud-backed run of a few minutes and roughly 2 GB of RAM, so it is out of scope unless
  someone asks for it.
