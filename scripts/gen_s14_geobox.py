"""Slide 14: an odc-geo style GeoBox card, drawn as inline SVG in the deck theme.

    uv run --project scripts python scripts/gen_s14_geobox.py

Real numbers, computed with odc-geo the way epoch-mono does it:

* Global grid: ``DefaultChunkGridConfig()`` in
  ``epoch-mono/py/packages/ee-icechunk/epoch/ee_icechunk/chunk_grid.py``:
  bounds (-180, -60, 180, 80), res 10 (metres), EPSG:4326, chunk_size (512, 512).
  ``ChunkGrid.get_geobox`` builds a 10 m EPSG:3857 GeoBox and reprojects it to
  EPSG:4326, which gives 4,305,610 x 1,674,406 px at 8.36119e-05 deg (pinned in
  ee-icechunk/tests/test_chunk_grid.py::test_default_grid_config_geobox_unchanged).
* Target GeoBox: the chunk-aligned window of that grid covering a real palm
  supply shed in Kampar, Riau (``~/epoch/data/sample-geojson/palm/shed.geojson``).

Writes slides/_gen/s14-geobox.qmd (a raw-HTML partial).
"""

import json
import math
from pathlib import Path

import shapely
from odc.geo.data import ocean_geom
from odc.geo.geobox import GeoBox
from pyproj import Transformer
from shapely.geometry import box, shape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "slides" / "_gen" / "s14-geobox.qmd"
SHED = Path.home() / "epoch/data/sample-geojson/palm/shed.geojson"

BOUNDS = (-180, -60, 180, 80)  # EPOCH_GLOBAL_BOUNDS
RES_M = 10
CHUNK = 512

INK, MUTED, BLUE, BLUE_SOFT = "#0A1628", "#5B6878", "#376FD0", "#DCE7FB"
GREEN = "#3FB557"


def global_geobox() -> GeoBox:
    """Mirror ChunkGrid.get_geobox for a geographic target CRS."""
    t = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    merc = GeoBox.from_bbox(t.transform_bounds(*BOUNDS), crs="EPSG:3857", resolution=RES_M)
    gbox = merc.to_crs("EPSG:4326")
    assert tuple(gbox.shape) == (1674406, 4305610), gbox.shape
    return gbox


def chunk_window(gbox: GeoBox, geom) -> tuple[GeoBox, int, int, int, int]:
    """Chunk-aligned slice of the global grid that covers geom."""
    inv = ~gbox.affine
    minx, miny, maxx, maxy = geom.bounds
    c0, r0 = inv * (minx, maxy)
    c1, r1 = inv * (maxx, miny)
    cc0, rr0 = math.floor(c0 / CHUNK), math.floor(r0 / CHUNK)
    cc1, rr1 = math.ceil(c1 / CHUNK), math.ceil(r1 / CHUNK)
    win = gbox[rr0 * CHUNK : rr1 * CHUNK, cc0 * CHUNK : cc1 * CHUNK]
    return win, rr0, cc0, rr1 - rr0, cc1 - cc0


def path_d(geom, fx, fy, nd=1) -> str:
    parts = []
    polys = getattr(geom, "geoms", [geom])
    for p in polys:
        if p.is_empty or p.geom_type != "Polygon":
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = [f"{fx(x):.{nd}f},{fy(y):.{nd}f}" for x, y in ring.coords]
            parts.append("M" + "L".join(pts) + "Z")
    return "".join(parts)


def locator_svg(lon: float, lat: float, w: int = 330) -> str:
    h = w // 2
    s = w / 360
    fx = lambda x: (x + 180) * s  # noqa: E731
    fy = lambda y: (90 - y) * s  # noqa: E731
    ocean = ocean_geom().geom.simplify(0.6)
    d = path_d(ocean, fx, fy)
    cx, cy = fx(lon), fy(lat)
    return f"""<svg class="s14-loc" viewBox="0 0 {w} {h}" role="img" aria-label="World locator: Sumatra">
  <rect x="0" y="0" width="{w}" height="{h}" fill="#FBFAF6"/>
  <path d="{d}" fill="{BLUE_SOFT}" fill-rule="evenodd" stroke="#B9C9E6" stroke-width="0.6"/>
  <g class="s14-cross" stroke="{INK}" stroke-width="1.2" stroke-opacity="0.55">
    <line x1="0" y1="{cy:.1f}" x2="{w}" y2="{cy:.1f}"/>
    <line x1="{cx:.1f}" y1="0" x2="{cx:.1f}" y2="{h}"/>
  </g>
  <rect class="s14-loc-mark" x="{cx - 5:.1f}" y="{cy - 5:.1f}" width="10" height="10" fill="{BLUE}" stroke="#fff" stroke-width="1.5"/>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" fill="none" stroke="#C9CFD8"/>
</svg>"""


def zoom_svg(win: GeoBox, shed, nrows: int, ncols: int, size: int = 400) -> tuple[str, int]:
    bb = win.extent.boundingbox
    pad = 0.07 * max(bb.span_x, bb.span_y)
    x0, y0, x1, y1 = bb.left - pad, bb.bottom - pad, bb.right + pad, bb.top + pad
    s = size / max(x1 - x0, y1 - y0)
    w, h = round((x1 - x0) * s), round((y1 - y0) * s)
    fx = lambda x: (x - x0) * s  # noqa: E731
    fy = lambda y: (y1 - y) * s  # noqa: E731

    # Chunks of the window that the shed touches (what a fill would request).
    step_x = CHUNK * win.resolution.x
    step_y = CHUNK * -win.resolution.y
    hit = []
    for r in range(nrows):
        for c in range(ncols):
            cb = box(bb.left + c * step_x, bb.top - (r + 1) * step_y, bb.left + (c + 1) * step_x, bb.top - r * step_y)
            if cb.intersects(shed):
                hit.append((r, c))
    cw, ch = step_x * s, step_y * s
    gx0, gy0 = fx(bb.left), fy(bb.top)
    cells = "".join(
        f'<rect x="{gx0 + c * cw:.1f}" y="{gy0 + r * ch:.1f}" width="{cw:.1f}" height="{ch:.1f}"/>' for r, c in hit
    )
    vlines = "".join(
        f'<line x1="{gx0 + c * cw:.1f}" y1="{gy0:.1f}" x2="{gx0 + c * cw:.1f}" y2="{gy0 + nrows * ch:.1f}"/>'
        for c in range(1, ncols)
    )
    hlines = "".join(
        f'<line x1="{gx0:.1f}" y1="{gy0 + r * ch:.1f}" x2="{gx0 + ncols * cw:.1f}" y2="{gy0 + r * ch:.1f}"/>'
        for r in range(1, nrows)
    )
    shed_d = path_d(shed.simplify(0.004), fx, fy)
    svg = f"""<svg class="s14-zoom" viewBox="0 0 {w} {h}" role="img" aria-label="GeoBox over a Riau palm supply shed, with 512-pixel chunk gridlines">
  <rect x="0" y="0" width="{w}" height="{h}" fill="#FBFAF6"/>
  <path class="s14-shed" d="{shed_d}" fill="{GREEN}" fill-opacity="0.28" fill-rule="evenodd" stroke="{GREEN}" stroke-width="2" stroke-linejoin="round"/>
  <g class="s14-hit" fill="{BLUE}" fill-opacity="0.16">{cells}</g>
  <g class="s14-grid" stroke="{BLUE}" stroke-width="0.9" stroke-opacity="0.55">{vlines}{hlines}</g>
  <rect class="s14-box" x="{gx0:.1f}" y="{gy0:.1f}" width="{ncols * cw:.1f}" height="{nrows * ch:.1f}" fill="none" stroke="{BLUE}" stroke-width="3"/>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" fill="none" stroke="#C9CFD8"/>
</svg>"""
    return svg, len(hit)


def main() -> None:
    gbox = global_geobox()
    feat = json.load(open(SHED))["features"][0]
    # The shed is a pixelated MultiPolygon; close the specks so it reads as one outline.
    shed = shapely.make_valid(shape(feat["geometry"])).buffer(0.003).buffer(-0.003)
    shed = shapely.Polygon(max(getattr(shed, "geoms", [shed]), key=lambda g: g.area).exterior)
    win, r0, c0, nrows, ncols = chunk_window(gbox, shed)
    H, W = win.shape
    res = win.resolution.x
    lon, lat = shed.centroid.x, shed.centroid.y
    zoom, nhit = zoom_svg(win, shed, nrows, ncols)

    rows = [
        ("Dimensions", f"{W:,d}&#8202;×&#8202;{H:,d}"),
        ("EPSG", f"{win.crs.epsg}"),
        ("Resolution", f"{res:.7f}°"),
        ("Cell", f"{CHUNK}&#8202;px"),
    ]
    info = "\n".join(f'    <div class="s14-row"><span>{k}</span><span class="s14-val">{v}</span></div>' for k, v in rows)
    GH, GW = gbox.shape
    html = f"""```{{=html}}
<!-- generated by scripts/gen_s14_geobox.py; do not edit -->
<div class="s14-gb card">
  <div class="s14-gb-head"><span class="s14-gb-title">GeoBox</span><span class="s14-gb-tag">target_geobox</span></div>
  <div class="s14-gb-body">
    <div class="s14-gb-left">
{info}
    {locator_svg(lon, lat)}
    <p class="s14-gb-note">{ncols}&#8202;×&#8202;{nrows} chunks of one global grid<br><span class="s14-val">{GW:,d}&#8202;×&#8202;{GH:,d}</span></p>
    </div>
    <div class="s14-gb-right">
    {zoom}
    <p class="s14-gb-cap"><span class="s14-key-shed"></span>palm supply shed, Riau <span class="s14-key-hit"></span>{nhit} chunks</p>
    </div>
  </div>
</div>
```
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"global {GW}x{GH} res {gbox.resolution.x:.6e}; window rows {r0}+{nrows} cols {c0}+{ncols} -> {W}x{H}; "
          f"shed bbox {tuple(round(v, 3) for v in shed.bounds)}; {nhit} chunks hit; wrote {OUT.relative_to(ROOT)} "
          f"({OUT.stat().st_size / 1024:.0f} KiB)")


if __name__ == "__main__":
    main()
