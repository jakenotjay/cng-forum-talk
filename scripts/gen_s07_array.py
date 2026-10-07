"""Slide 7: one global array, filled as we go.

Writes slides/_gen/s07-array.qmd: an inline SVG of central Sumatra with a real
palm supply shed (Binabaru mill, Kampar, Riau), overlaid by a 12 x 8 grid of
0.5 degree chunks (EPSG:4326), plus "data" and "metaarray" mini-grids.

    uv run --project scripts python scripts/gen_s07_array.py

Geometry sources (local, not committed):
  ~/epoch/data/sample-geojson/palm/shed.geojson     real supply shed (6,585 km2)
  ~/epoch/data/sample-geojson/palm/facility.geojson the mill point
  ~/epoch/geovibes/geometries/gadm41_IDN_1.json     GADM 4.1 provinces -> Sumatra land

The simplified geometry is cached in images/src/s07-geometry.json so the slide
can be regenerated without those files.

Animation is driven by classes + inline --d delays; keyframes live in styles/s07.scss.
"""

import json
from pathlib import Path

from shapely.geometry import Point, box, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "slides" / "_gen" / "s07-array.qmd"
CACHE = ROOT / "images" / "src" / "s07-geometry.json"
HOME = Path.home()
SHED_SRC = HOME / "epoch/data/sample-geojson/palm/shed.geojson"
FAC_SRC = HOME / "epoch/data/sample-geojson/palm/facility.geojson"
GADM_SRC = HOME / "epoch/geovibes/geometries/gadm41_IDN_1.json"
SUMATRA = {"Aceh", "SumateraUtara", "SumateraBarat", "Riau", "Jambi", "Bengkulu",
           "SumateraSelatan", "Lampung", "KepulauanRiau", "BangkaBelitung"}

# Region and chunk grid (degrees). 12 x 8 chunks of 0.5 degrees.
LON0, LAT1, COLS, ROWS, STEP = 98.0, 2.0, 12, 8, 0.5
CELL = 80  # px per chunk in the map
MAP_W, MAP_H = COLS * CELL, ROWS * CELL  # 960 x 640
PX = CELL / STEP  # px per degree

# Chunk states before the new shed arrives: F = filled, E = processed but empty.
EARLIER = {
    # shed to the east (Siak / Pekanbaru)
    (1, 7): "F", (1, 8): "E", (2, 7): "F", (2, 8): "F", (3, 7): "F", (3, 8): "F",
    (4, 7): "E", (4, 8): "F",
    # north-west (North Sumatra)
    (0, 3): "F", (0, 4): "F", (1, 3): "F", (1, 4): "E", (0, 2): "E",
    # south-east (Jambi)
    (6, 8): "F", (6, 9): "F", (7, 9): "F", (7, 8): "E", (6, 10): "E", (7, 10): "F",
}
# Result of filling the new shed's missing chunks.
NEW_RESULT = {(2, 5): "F", (2, 6): "F", (3, 5): "E", (3, 6): "F", (4, 5): "E", (4, 6): "F"}

INK, MUTED, BLUE, BLUE_SOFT = "#0A1628", "#5B6878", "#376FD0", "#DCE7FB"
GREEN, GREEN_SOFT, LINE = "#3FB557", "#57D16F", "#C9CFD8"


def load_geometry() -> dict:
    if SHED_SRC.exists() and GADM_SRC.exists():
        shed = unary_union([shape(f["geometry"]) for f in json.loads(SHED_SRC.read_text())["features"]])
        # Close the pixel-stair gaps, keep the main body, smooth for a clean stroke.
        shed = shed.buffer(0.012).buffer(-0.012)
        if shed.geom_type == "MultiPolygon":
            shed = max(shed.geoms, key=lambda g: g.area)
        shed = shed.simplify(0.006)
        fac = shape(json.loads(FAC_SRC.read_text())["features"][0]["geometry"])
        gadm = json.loads(GADM_SRC.read_text())
        land = unary_union([shape(f["geometry"]) for f in gadm["features"]
                            if f["properties"]["NAME_1"] in SUMATRA])
        reg = box(LON0 - 0.2, LAT1 - ROWS * STEP - 0.2, LON0 + COLS * STEP + 0.2, LAT1 + 0.2)
        land = land.intersection(reg).simplify(0.01)
        land = unary_union([g for g in getattr(land, "geoms", [land]) if g.area > 0.0015])
        data = {"shed": mapping(shed), "facility": mapping(fac), "land": mapping(land)}
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(data))
        return data
    return json.loads(CACHE.read_text())


def xy(lon: float, lat: float) -> tuple[float, float]:
    return (lon - LON0) * PX, (LAT1 - lat) * PX


def path_d(geom) -> str:
    polys = getattr(geom, "geoms", [geom])
    out = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = [xy(*c[:2]) for c in ring.coords]
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(out)


def cell_box(r: int, c: int):
    return box(LON0 + c * STEP, LAT1 - (r + 1) * STEP, LON0 + (c + 1) * STEP, LAT1 - r * STEP)


def build() -> str:
    g = load_geometry()
    shed = shape(g["shed"])
    land = shape(g["land"])
    fx, fy = xy(*shape(g["facility"]).coords[0])

    hits = [(r, c) for r in range(ROWS) for c in range(COLS) if cell_box(r, c).intersects(shed)]
    present = [rc for rc in hits if rc in EARLIER]
    missing = [rc for rc in hits if rc not in EARLIER]
    assert set(missing) == set(NEW_RESULT), (missing, NEW_RESULT)

    # Beat timings (seconds into the 15 s slide)
    t_mark = {rc: 3.0 + 0.18 * i for i, rc in enumerate(sorted(hits))}
    t_fill = {rc: 6.2 + 0.42 * i for i, rc in enumerate(sorted(missing))}
    t_out = 8.9
    t_sweep, sweep_dur = 9.6, 1.4

    s = []
    a = s.append
    a('<div class="s07-wrap">')
    a('<svg class="s07-svg" viewBox="0 0 1440 700" role="img" '
      'aria-label="Chunk grid over central Sumatra. A palm supply shed arrives; chunks it needs are '
      'checked against the metaarray, only the missing ones are filled, and data and metaarray are '
      'committed together.">')
    a('<defs>')
    a(f'<pattern id="s07-hatch" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
      f'<rect width="12" height="12" fill="#E6E9EE"/><line x1="0" y1="0" x2="0" y2="12" stroke="#8C97A6" stroke-width="4"/></pattern>')
    a(f'<pattern id="s07-hatch-sm" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
      f'<rect width="6" height="6" fill="#E6E9EE"/><line x1="0" y1="0" x2="0" y2="6" stroke="#8C97A6" stroke-width="2"/></pattern>')
    a(f'<clipPath id="s07-mapclip"><rect width="{MAP_W}" height="{MAP_H}" rx="18"/></clipPath>')
    a(f'<clipPath id="s07-miniclip"><rect width="{COLS * 23}" height="{ROWS * 23}"/></clipPath>')
    a('<linearGradient id="s07-sweep-grad" x1="0" x2="1" y1="0" y2="0">'
      '<stop offset="0" stop-color="#57D16F" stop-opacity="0"/>'
      '<stop offset="0.5" stop-color="#57D16F" stop-opacity="0.8"/>'
      '<stop offset="1" stop-color="#57D16F" stop-opacity="0"/></linearGradient>')
    a('</defs>')

    # ---- Map card ----
    a('<g class="s07-map">')
    a(f'<rect class="s07-card" width="{MAP_W}" height="{MAP_H}" rx="18"/>')
    a('<g clip-path="url(#s07-mapclip)">')
    a(f'<rect width="{MAP_W}" height="{MAP_H}" fill="{BLUE_SOFT}" opacity="0.45"/>')
    a(f'<path class="s07-land" d="{path_d(land)}"/>')
    a(f'<text class="s07-geo" x="{xy(102.55, 1.72)[0]:.0f}" y="{xy(102.55, 1.72)[1]:.0f}">Strait of Malacca</text>')
    a(f'<text class="s07-geo" x="{xy(98.15, -1.55)[0]:.0f}" y="{xy(98.15, -1.55)[1]:.0f}">Indian Ocean</text>')
    a(f'<text class="s07-geo s07-geo-land" x="{xy(100.62, -1.2)[0]:.0f}" y="{xy(100.62, -1.2)[1]:.0f}">SUMATRA</text>')

    # Earlier state
    for (r, c), st in EARLIER.items():
        cls = "s07-filled" if st == "F" else "s07-empty"
        a(f'<rect class="{cls} s07-early" x="{c * CELL}" y="{r * CELL}" width="{CELL}" height="{CELL}"/>')

    # Shed fill + outline (draws on 3-6 s)
    d = path_d(shed)
    a(f'<path class="s07-shed-fill" d="{d}"/>')

    # Newly filled chunks (9-12 s)
    for rc, st in NEW_RESULT.items():
        r, c = rc
        cls = "s07-filled" if st == "F" else "s07-empty"
        a(f'<rect class="{cls} s07-new" style="--d:{t_fill[rc]:.2f}s" x="{c * CELL}" y="{r * CELL}" width="{CELL}" height="{CELL}"/>')

    # Grid lines on top
    grid = []
    for c in range(COLS + 1):
        grid.append(f"M{c * CELL},0V{MAP_H}")
    for r in range(ROWS + 1):
        grid.append(f"M0,{r * CELL}H{MAP_W}")
    a(f'<path class="s07-grid s07-early" d="{"".join(grid)}"/>')

    # Intersect marks (6-9 s)
    for rc in hits:
        r, c = rc
        kind = "s07-mark-present" if rc in present else "s07-mark-missing"
        a(f'<rect class="s07-mark {kind}" style="--d:{t_mark[rc]:.2f}s;--d2:{(t_fill.get(rc, t_out)):.2f}s" '
          f'x="{c * CELL + 4}" y="{r * CELL + 4}" width="{CELL - 8}" height="{CELL - 8}" rx="6"/>')
    # Shed outline on top of everything in the map (draws on 3-6 s)
    a(f'<path class="s07-shed" d="{d}" pathLength="1"/>')
    a('</g>')
    a(f'<rect class="s07-card-edge" width="{MAP_W}" height="{MAP_H}" rx="18"/>')

    # Facility + shed label
    a(f'<g class="s07-fac"><circle cx="{fx:.1f}" cy="{fy:.1f}" r="9" fill="{INK}" stroke="#fff" stroke-width="3.5"/></g>')
    lx, ly = xy(101.24, 0.90); lx -= 118
    a(f'<g class="s07-shed-label"><rect x="{lx:.0f}" y="{ly - 34:.0f}" width="236" height="46" rx="23"/>'
      f'<text x="{lx + 118:.0f}" y="{ly - 3:.0f}" text-anchor="middle">new supply shed</text></g>')

    # Count chips (6-9 s)
    cx0, cy0 = xy(99.53, 0.36)
    a(f'<g class="s07-count" style="--d:4.4s">'
      f'<rect x="{cx0:.0f}" y="{cy0 - 34:.0f}" width="150" height="46" rx="23" fill="#fff" stroke="{GREEN}" stroke-width="3"/>'
      f'<text x="{cx0 + 75:.0f}" y="{cy0 - 3:.0f}" text-anchor="middle">{len(present)} present</text>'
      f'<rect x="{cx0:.0f}" y="{cy0 + 22:.0f}" width="150" height="46" rx="23" fill="{BLUE_SOFT}" stroke="{BLUE}" stroke-width="3" stroke-dasharray="8 5"/>'
      f'<text x="{cx0 + 75:.0f}" y="{cy0 + 53:.0f}" text-anchor="middle" class="s07-count-miss">{len(missing)} missing</text></g>')
    a('</g>')

    # ---- Narration line under the map ----
    beats = [
        (0.6, 3.0, "Earlier sheds already stored some chunks"),
        (3.0, 6.2, "Which of its chunks exist already?"),
        (6.2, 9.6, "Fill only the missing ones"),
        (9.6, None, "Write data and metaarray in one commit"),
    ]
    for i, (t0, t1, text) in enumerate(beats):
        style = f"--d:{t0:.1f}s" + (f";--d2:{t1 - 0.35:.2f}s" if t1 else "")
        cls = "s07-beat" + (" s07-beat-last" if t1 is None else "") + (" s07-beat-first" if i == 0 else "")
        a(f'<g class="{cls}" style="{style}"><circle cx="20" cy="{MAP_H + 40}" r="17" fill="{BLUE}"/>'
          f'<text class="s07-beat-n" x="20" y="{MAP_H + 48}" text-anchor="middle">{i + 1}</text>'
          f'<text class="s07-beat-t" x="50" y="{MAP_H + 49}">{text}</text></g>')

    # ---- Side panel: data + metaarray mini-grids ----
    m = 23  # mini cell
    gx = 1012
    gw, gh = COLS * m, ROWS * m
    panels = [("data", "written", 30), ("metaarray", "processed", 30 + gh + 92)]
    a('<g class="s07-side">')
    # commit box (12 s)
    top = panels[0][2] - 26
    bot = panels[1][2] + 52 + gh + 16
    a(f'<rect class="s07-commit-box" x="{gx - 22}" y="{top}" width="{gw + 44}" height="{bot - top}" rx="18"/>')
    for name, sub, y0 in panels:
        ty = y0 + 4
        a(f'<text class="s07-pname" x="{gx}" y="{ty}">{name}</text>')
        a(f'<text class="s07-psub" x="{gx + gw}" y="{ty}" text-anchor="end">{sub}</text>')
        oy = y0 + 22
        a(f'<g transform="translate({gx},{oy})">')
        a(f'<rect width="{gw}" height="{gh}" rx="4" fill="#fff" stroke="{LINE}" stroke-width="1.5"/>')
        for (r, c), st in EARLIER.items():
            if name == "data" and st == "F":
                a(f'<rect class="s07-m-data" x="{c * m}" y="{r * m}" width="{m}" height="{m}"/>')
            elif name == "metaarray":
                a(f'<rect class="s07-m-meta" x="{c * m}" y="{r * m}" width="{m}" height="{m}"/>')
        for rc, st in NEW_RESULT.items():
            r, c = rc
            if name == "data" and st != "F":
                continue
            kind = "s07-m-data" if name == "data" else "s07-m-meta"
            tc = t_sweep + sweep_dur * (c + 0.5) / COLS
            a(f'<rect class="{kind} s07-m-pend" style="--d:{t_fill[rc]:.2f}s" x="{c * m}" y="{r * m}" width="{m}" height="{m}"/>')
            a(f'<rect class="{kind} s07-m-commit" style="--d:{tc:.2f}s" x="{c * m}" y="{r * m}" width="{m}" height="{m}"/>')
        mg = [f"M{c * m},0V{gh}" for c in range(1, COLS)] + [f"M0,{r * m}H{gw}" for r in range(1, ROWS)]
        a(f'<path class="s07-m-grid" d="{"".join(mg)}"/>')
        a(f'<path class="s07-m-shed" d="{d}" transform="scale({m / CELL})"/>')
        a(f'<g clip-path="url(#s07-miniclip)"><g class="s07-sweep" style="--d:{t_sweep}s;--dur:{sweep_dur}s"><rect x="-80" y="0" width="80" height="{gh}" fill="url(#s07-sweep-grad)"/><rect x="-41.5" y="0" width="3" height="{gh}" fill="{GREEN}"/></g></g>')
        a('</g>')
    # one commit label
    a(f'<g class="s07-commit-label"><rect x="{gx + gw / 2 - 90}" y="{bot - 24}" width="180" height="48" rx="24" fill="{INK}"/>'
      f'<text x="{gx + gw / 2}" y="{bot + 9}" text-anchor="middle">one commit</text></g>')

    # legend
    ly0 = bot + 70
    items = [
        ("s07-lg-filled", "data written"),
        ("s07-lg-empty", "processed, no data"),
        ("s07-lg-none", "not processed"),
        ("s07-lg-missing", "missing"),
    ]
    for i, (cls, label) in enumerate(items):
        col, row = i % 2, i // 2
        x = gx - 22 + col * 226
        y = ly0 + row * 42
        a(f'<rect class="{cls}" x="{x}" y="{y - 20}" width="24" height="24" rx="3"/>')
        a(f'<text class="s07-lg-t" x="{x + 34}" y="{y}">{label}</text>')
    a('</g>')
    a('</svg></div>')
    return "\n".join(s)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("```{=html}\n" + build() + "\n```\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
