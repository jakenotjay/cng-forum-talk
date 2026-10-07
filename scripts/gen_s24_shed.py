"""Slide 24 (deck position 7): how a supply shed is made.

Writes slides/_gen/s24-shed.qmd: an inline SVG with the map card on the left
(the real 90-minute palm supply shed for Binabaru mill, Kampar, Riau) and the
input layers stacked on the right. Beats: mill (0-1.5 s) · four layers appear
in place (1.5-3.5 s) · they combine into one friction tile (4.5-5 s) · spread
from the mill with a 0 -> 90 min timer (6.3-9 s) · real outline draws (9-11 s)
· shed turns green with caption (11.5-12.5 s). Timing via classes + inline --d
delays; keyframes live in styles/s24.scss.

    uv run --project scripts python scripts/gen_s24_shed.py

Real: shed outline (largest part, 6,560 km2), mill point, 90-minute budget.
Schematic: the four input-layer tiles and the friction tile (patterns only),
and the spread animation, which grows the final outline about the mill so it
reaches every edge at "90 min" (true 30/60-minute fronts were not computed).

Geometry sources (local, not committed):
  ~/epoch/data/sample-geojson/palm/shed.geojson     real 90-minute palm shed
  ~/epoch/data/sample-geojson/palm/facility.geojson the mill point
Cached in images/src/s24-geometry.json so the slide regenerates without them.
"""

import json
import math
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "slides" / "_gen" / "s24-shed.qmd"
CACHE = ROOT / "images" / "src" / "s24-geometry.json"
HOME = Path.home()
SHED_SRC = HOME / "epoch/data/sample-geojson/palm/shed.geojson"
FAC_SRC = HOME / "epoch/data/sample-geojson/palm/facility.geojson"

TO_UTM = Transformer.from_crs(4326, 32647, always_xy=True).transform

# Map card: equirectangular (cos(0.2 deg) ~ 1), shed bbox centred.
MAP_W, MAP_H = 960, 640  # same card as the next slide (global array)
COL_X = 1012  # right column: input layers
PX = 500.0  # px per degree
KM = PX / 111.32  # px per km at the equator
SHED_C = (101.2397, 0.1635)  # shed bbox centre
LON0 = SHED_C[0] - MAP_W / 2 / PX
LAT1 = SHED_C[1] + MAP_H / 2 / PX

INK, MUTED, BLUE, BLUE_SOFT = "#0A1628", "#5B6878", "#376FD0", "#DCE7FB"
GREEN, GREEN_SOFT, LINE = "#3FB557", "#57D16F", "#C9CFD8"

# Timeline (s)
T_LAYERS, T_FRIC = 1.5, 4.8
T_SPREAD, SPREAD_DUR = 6.3, 2.7


def load_geometry() -> dict:
    if SHED_SRC.exists() and FAC_SRC.exists():
        raw = unary_union([shape(f["geometry"]) for f in json.loads(SHED_SRC.read_text())["features"]])
        main = max(getattr(raw, "geoms", [raw]), key=lambda g: g.area)
        area_km2 = transform(TO_UTM, main).area / 1e6
        # Drop holes under 2 km2 and the 30 slivers; light smoothing of the 100 m stairs.
        holes = [h for h in main.interiors if transform(TO_UTM, Polygon(h)).area > 2e6]
        shed = Polygon(main.exterior, holes).simplify(0.003)
        fac = shape(json.loads(FAC_SRC.read_text())["features"][0]["geometry"])
        assert shed.contains(fac), "mill must sit inside the simplified shed"
        data = {"shed": mapping(shed), "facility": mapping(fac), "area_km2": round(area_km2, 1)}
        CACHE.write_text(json.dumps(data))
        return data
    return json.loads(CACHE.read_text())


def xy(lon: float, lat: float) -> tuple[float, float]:
    return (lon - LON0) * PX, (LAT1 - lat) * PX


def path_d(geom) -> str:
    out = []
    for p in getattr(geom, "geoms", [geom]):
        for ring in [p.exterior, *p.interiors]:
            pts = [xy(*c[:2]) for c in ring.coords]
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(out)


def tile_pattern(kind: str, w: float, h: float) -> str:
    """Schematic swatch contents in a w x h box (unskewed coordinates)."""
    s = []
    if kind == "roads":
        s.append(f'<rect width="{w}" height="{h}" fill="#fff"/>')
        s.append(f'<path d="M-5,{h * .78} C{w * .3},{h * .6} {w * .55},{h * .45} {w + 5},{h * .2}" stroke="{INK}" stroke-width="5" fill="none"/>')
        s.append(f'<path d="M{w * .35},-5 L{w * .45},{h + 5} M{w * .7},{h * .32} L{w * .85},{h + 5} M-5,{h * .25} L{w * .38},{h * .45}" '
                 f'stroke="{MUTED}" stroke-width="2.5" fill="none"/>')
        s.append(f'<path d="M{w * .12},{h * .5} L{w * .2},{h + 5} M{w * .55},{h * .48} L{w * .62},-5" stroke="#9AA4B2" stroke-width="1.5" fill="none"/>')
    elif kind == "slope":
        s.append(f'<rect width="{w}" height="{h}" fill="#F7F2E6"/>')
        for i in range(6):
            r = 10 + i * 14
            s.append(f'<ellipse cx="{w * .62}" cy="{h * .55}" rx="{r * 1.5}" ry="{r * .8}" fill="none" stroke="#A8916A" stroke-width="1.8" opacity="{1 - i * .1:.2f}"/>')
    elif kind == "land":
        s.append(f'<rect width="{w}" height="{h}" fill="#E8DDB8"/>')
        for x, y, rw, rh, c in [(0, 0, .45, .55, "#2E8B47"), (.45, 0, .3, .4, "#8FD19A"), (.75, 0, .25, .7, "#2E8B47"),
                                (0, .55, .3, .45, "#8FD19A"), (.3, .55, .25, .45, "#2E8B47"), (.62, .7, .38, .3, "#57D16F")]:
            s.append(f'<rect x="{x * w:.1f}" y="{y * h:.1f}" width="{rw * w:.1f}" height="{rh * h:.1f}" fill="{c}"/>')
    elif kind == "water":
        s.append(f'<rect width="{w}" height="{h}" fill="#fff"/>')
        s.append(f'<path d="M-5,{h * .35} C{w * .2},{h * .1} {w * .3},{h * .7} {w * .5},{h * .5} S{w * .8},{h * .1} {w + 5},{h * .45}" '
                 f'stroke="{BLUE}" stroke-width="7" fill="none"/>')
        for i in range(3):
            y = h * (.72 + i * .1)
            s.append(f'<path d="M{w * .1},{y:.1f} q8,-6 16,0 t16,0 t16,0" stroke="{BLUE}" stroke-width="1.8" fill="none" opacity=".7"/>')
    elif kind == "friction":
        # low cost along roads (light), higher off-road, highest on water (dark)
        s.append(f'<rect width="{w}" height="{h}" fill="#8C97A6"/>')
        s.append(f'<rect x="{w * .45}" width="{w * .3}" height="{h * .4}" fill="#5B6878"/>')
        s.append(f'<rect x="{w * .75}" width="{w * .25}" height="{h * .7}" fill="#5B6878"/>')
        s.append(f'<rect x="{w * .3}" y="{h * .55}" width="{w * .25}" height="{h * .45}" fill="#5B6878"/>')
        s.append(f'<path d="M-5,{h * .35} C{w * .2},{h * .1} {w * .3},{h * .7} {w * .5},{h * .5} S{w * .8},{h * .1} {w + 5},{h * .45}" '
                 f'stroke="{INK}" stroke-width="7" fill="none"/>')
        s.append(f'<path d="M-5,{h * .78} C{w * .3},{h * .6} {w * .55},{h * .45} {w + 5},{h * .2}" stroke="#F4F1EA" stroke-width="6" fill="none"/>')
        s.append(f'<path d="M{w * .35},-5 L{w * .45},{h + 5} M{w * .7},{h * .32} L{w * .85},{h + 5}" stroke="#DCDFE4" stroke-width="3" fill="none"/>')
    return "".join(s)


def build() -> str:
    g = load_geometry()
    shed = shape(g["shed"])
    fac = shape(g["facility"])
    fx, fy = xy(*fac.coords[0])
    d = path_d(shed)
    print(f"area {g['area_km2']} km2")

    s = []
    a = s.append
    a('<div class="s24-wrap">')
    a('<svg class="s24-svg" viewBox="0 0 1440 700" role="img" '
      'aria-label="Map of the 90-minute palm supply shed for Binabaru mill in Riau. Four input layers (roads, '
      'slope, land cover, water) combine into a friction surface; a spread from the mill reaches 90 minutes and '
      'the shed is one polygon of 6,560 square kilometres.">')
    a('<defs>')
    a(f'<clipPath id="s24-mapclip"><rect width="{MAP_W}" height="{MAP_H}" rx="18"/></clipPath>')
    a('</defs>')

    # ---------------- Map card (left) ----------------
    a('<g class="s24-map">')
    a('<g clip-path="url(#s24-mapclip)">')
    a(f'<rect class="s24-land" width="{MAP_W}" height="{MAP_H}"/>')

    # Spread (blue, grows from the mill), final fill, outline
    org = f"transform-origin:{fx:.1f}px {fy:.1f}px"
    a(f'<path class="s24-spread" style="{org}" d="{d}"/>')
    a(f'<path class="s24-front" style="{org}" d="{d}"/>')
    a(f'<path class="s24-final" d="{d}"/>')
    a(f'<path class="s24-outline" d="{d}" pathLength="1"/>')

    # Scale bar
    sb = 20 * KM
    a(f'<g class="s24-scale"><path d="M28,{MAP_H - 44}v10H{28 + sb:.1f}v-10"/>'
      f'<text x="{28 + sb + 12:.1f}" y="{MAP_H - 28}">20 km</text></g>')
    a('</g>')
    a(f'<rect class="s24-card-edge" width="{MAP_W}" height="{MAP_H}" rx="18"/>')

    # Mill, pill, timer
    a(f'<circle class="s24-pulse" cx="{fx:.1f}" cy="{fy:.1f}" r="10" style="transform-origin:{fx:.1f}px {fy:.1f}px"/>')
    a(f'<g class="s24-mill" style="transform-origin:{fx:.1f}px {fy:.1f}px">'
      f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="10" fill="{BLUE}" stroke="#fff" stroke-width="4"/></g>')
    lw = 236
    x0 = fx - 24 - lw
    a(f'<g class="s24-mill-l"><rect x="{x0:.0f}" y="{fy - 23:.0f}" width="{lw}" height="46" rx="23"/>'
      f'<text x="{x0 + lw / 2:.0f}" y="{fy + 8:.0f}" text-anchor="middle">Binabaru mill, Riau</text></g>')
    # timer above the mill: 0 -> 90 min in 10-minute steps, synced with the spread
    tw = 132
    a(f'<g class="s24-timer"><rect x="{fx - tw / 2:.0f}" y="{fy - 76:.0f}" width="{tw}" height="44" rx="22"/>')
    for m in range(0, 100, 10):
        t0 = T_SPREAD + SPREAD_DUR * m / 90
        t1 = T_SPREAD + SPREAD_DUR * (m + 10) / 90
        cls = "s24-tick" + (" s24-tick-last" if m == 90 else "")
        a(f'<text class="{cls}" style="--d:{t0:.2f}s;--d2:{t1:.2f}s" x="{fx:.0f}" y="{fy - 45:.0f}" '
          f'text-anchor="middle">{m} min</text>')
    a('</g>')

    # Caption under the map (final)
    cy = MAP_H + 46
    a(f'<g class="s24-caption"><rect x="2" y="{cy - 24}" width="30" height="30" rx="5"/>'
      f'<text x="46" y="{cy}"><tspan class="s24-cap-b">Supply shed</tspan> · 90 min · {round(g["area_km2"], -1):,.0f} km²</text></g>')
    a('</g>')

    # ---------------- Input layers (right, schematic) ----------------
    TX, TW, TH, SW, SKEW = COL_X, 392, 76, 110, -14
    k = math.tan(math.radians(SKEW))
    sx = -k * TH  # skew shifts the top edge right
    ys = [44 + i * (TH + 12) for i in range(4)]
    tiles = [("roads", "Roads", "Overture"), ("slope", "Slope", "Copernicus DEM"),
             ("land", "Land cover", "ESA WorldCover"), ("water", "Water", "JRC surface water")]
    a('<g class="s24-tiles">')
    a(f'<text class="s24-tiles-h" x="{TX}" y="{ys[0] - 16}">input layers (schematic)</text>')

    def tile(kind: str, name: str, sub: str, y: float, cls: str, style: str) -> None:
        a(f'<g class="{cls}" style="{style}">')
        a(f'<g transform="translate({TX},{y}) skewX({SKEW}) translate({sx:.1f},0)">')
        a(f'<clipPath id="s24-sw-{kind}"><rect width="{SW}" height="{TH}"/></clipPath>')
        a(f'<rect class="s24-tile-bg" width="{TW}" height="{TH}" rx="4"/>')
        a(f'<g clip-path="url(#s24-sw-{kind})">{tile_pattern(kind, SW, TH)}</g>')
        a(f'<rect class="s24-tile-edge" width="{TW}" height="{TH}" rx="4"/>')
        a(f'<path class="s24-tile-div" d="M{SW},0V{TH}"/>')
        a('</g>')
        lx = TX + SW + 30
        a(f'<text class="s24-tile-n" x="{lx}" y="{y + 33}">{name}</text>')
        a(f'<text class="s24-tile-s" x="{lx}" y="{y + 61}">{sub}</text>')
        a('</g>')

    for i, ((kind, name, sub), y) in enumerate(zip(tiles, ys)):
        tile(kind, name, sub, y, "s24-tile", f"--d:{T_LAYERS + 0.5 * i:.1f}s")

    # Bracket: the four layers combine into one friction tile below
    top = ys[-1] + TH + 12
    fy0 = top + 58
    mid = TX + sx / 2 + TW / 2
    a(f'<path class="s24-join" pathLength="1" d="M{TX + 8:.0f},{top}v12H{TX + TW + sx - 8:.0f}v-12"/>')
    a(f'<path class="s24-join" pathLength="1" d="M{mid:.0f},{top + 12}V{fy0 - 8}"/>')
    a(f'<path class="s24-join-head" d="M{mid - 9:.0f},{fy0 - 18}L{mid:.0f},{fy0 - 6}L{mid + 9:.0f},{fy0 - 18}"/>')
    tile("friction", "Friction", "seconds per metre", fy0, "s24-fric", f"--d:{T_FRIC:.1f}s")
    a(f'<text class="s24-key" x="{TX}" y="{fy0 + TH + 40}">pale = fast · dark = slow</text>')
    a('</g>')
    a('</svg></div>')
    return "\n".join(s)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("```{=html}\n" + build() + "\n```\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
