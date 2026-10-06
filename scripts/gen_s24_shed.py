"""Slide 24 (deck position 7): how a supply shed is made.

Writes slides/_gen/s24-shed.qmd: an inline SVG map of the real 90-minute palm
supply shed for Binabaru mill (Kampar, Riau) with a four-step rail. The beats
(mill, friction inputs, spread, cut at 90 min, final shed) are driven by
classes + inline --d delays; keyframes live in styles/s24.scss.

    uv run --project scripts python scripts/gen_s24_shed.py

Real: shed outline (largest part, 6,560 km2), mill point, 90-minute budget,
reach callouts (measured in UTM 47N), 50 km comparison circle, Pekanbaru.
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
from shapely.geometry import LineString, Point, Polygon, mapping, shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "slides" / "_gen" / "s24-shed.qmd"
CACHE = ROOT / "images" / "src" / "s24-geometry.json"
HOME = Path.home()
SHED_SRC = HOME / "epoch/data/sample-geojson/palm/shed.geojson"
FAC_SRC = HOME / "epoch/data/sample-geojson/palm/facility.geojson"

TO_UTM = Transformer.from_crs(4326, 32647, always_xy=True).transform
PEKANBARU = (101.4478, 0.5071)

# Map card: equirectangular (cos(0.2 deg) ~ 1), shed bbox centred.
MAP_W, MAP_H = 860, 640
PX = 500.0  # px per degree
KM = PX / 111.32  # px per km at the equator
SHED_C = (101.2397, 0.1635)  # shed bbox centre
LON0 = SHED_C[0] - MAP_W / 2 / PX
LAT1 = SHED_C[1] + MAP_H / 2 / PX

INK, MUTED, BLUE, BLUE_SOFT = "#0A1628", "#5B6878", "#376FD0", "#DCE7FB"
GREEN, GREEN_SOFT, LINE = "#3FB557", "#57D16F", "#C9CFD8"

# Timeline (s)
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


def reach_km(shed, fac, bearing: float) -> float:
    """Distance (km, UTM 47N) from the mill to the outer edge along a bearing."""
    poly = transform(TO_UTM, Polygon(shed.exterior))
    m = transform(TO_UTM, fac)
    b = math.radians(bearing)
    ray = LineString([(m.x, m.y), (m.x + 90000 * math.sin(b), m.y + 90000 * math.cos(b))])
    parts = getattr(ray.intersection(poly), "geoms", [ray.intersection(poly)])
    return max(p.length for p in parts if p.distance(m) < 1) / 1000


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

    # Reach callouts (real distances to the outer edge)
    # West (shortest side) and the broad southern lobe; 176 deg avoids the 62 km spike at 172 deg.
    callouts = [(270, reach_km(shed, fac, 270)), (176, reach_km(shed, fac, 176))]
    for b, r in callouts:
        print(f"reach {b} deg: {r:.1f} km")
    print(f"area {g['area_km2']} km2")

    s = []
    a = s.append
    a('<div class="s24-wrap">')
    a('<svg class="s24-svg" viewBox="0 0 1440 700" role="img" '
      'aria-label="Map of the 90-minute palm supply shed for Binabaru mill in Riau. Input layers combine into a '
      'friction surface, a least-cost spread grows from the mill, and the shed is cut at 90 minutes: one polygon of '
      '6,560 square kilometres.">')
    a('<defs>')
    a(f'<clipPath id="s24-mapclip"><rect width="{MAP_W}" height="{MAP_H}" rx="18"/></clipPath>')
    a('</defs>')

    # ---------------- Map card ----------------
    a('<g class="s24-map">')
    a('<g clip-path="url(#s24-mapclip)">')
    a(f'<rect class="s24-land" width="{MAP_W}" height="{MAP_H}"/>')
    # Equator
    _, ey = xy(0, 0.0)
    a(f'<path class="s24-eq" d="M0,{ey:.1f}H{MAP_W}"/>')
    a(f'<text class="s24-geo" x="18" y="{ey - 10:.1f}">Equator</text>')

    # Spread (blue, grows from the mill), final fills, outlines
    org = f"transform-origin:{fx:.1f}px {fy:.1f}px"
    a(f'<path class="s24-spread" style="{org}" d="{d}"/>')
    a(f'<path class="s24-front" style="{org}" d="{d}"/>')
    a(f'<path class="s24-final" d="{d}"/>')

    # 50 km comparison circle
    rc = 50 * KM
    a(f'<circle class="s24-circle" cx="{fx:.1f}" cy="{fy:.1f}" r="{rc:.1f}"/>')
    lb = math.radians(103)
    cx_l, cy_l = fx + (rc + 14) * math.sin(lb), fy - (rc + 14) * math.cos(lb)
    a(f'<text class="s24-circle-t" x="{cx_l:.0f}" y="{cy_l + 8:.0f}">50 km radius</text>')

    # Real outline (draws on at 9 s)
    a(f'<path class="s24-outline" d="{d}" pathLength="1"/>')

    # Pekanbaru (context)
    px_, py_ = xy(*PEKANBARU)
    a(f'<g class="s24-city"><circle cx="{px_:.1f}" cy="{py_:.1f}" r="6"/>'
      f'<text x="{px_ - 14:.1f}" y="{py_ + 8:.1f}" text-anchor="end">Pekanbaru</text></g>')

    # Reach callouts
    for i, (b, r) in enumerate(callouts):
        br = math.radians(b)
        ex, ey2 = fx + r * KM * math.sin(br), fy - r * KM * math.cos(br)
        nx, ny = math.cos(br), math.sin(br)  # perpendicular for end tick
        dl = 0.6 * i
        a(f'<g class="s24-callout" style="--d:{10.0 + dl:.1f}s">')
        a(f'<path class="s24-co-line" pathLength="1" d="M{fx:.1f},{fy:.1f}L{ex:.1f},{ey2:.1f}"/>')
        a(f'<path class="s24-co-tick" d="M{ex - 9 * nx:.1f},{ey2 - 9 * ny:.1f}L{ex + 9 * nx:.1f},{ey2 + 9 * ny:.1f}"/>')
        label = f"~{round(r)} km"
        if b == 270:
            tx, ty, anc = ex - 16, ey2 + 9, "end"
            rx0 = tx - 92
        else:
            tx, ty, anc = ex + 20, ey2 + 26, "start"
            rx0 = tx - 12
        a(f'<rect class="s24-co-bg" x="{rx0:.0f}" y="{ty - 28:.0f}" width="104" height="40" rx="20"/>')
        a(f'<text class="s24-co-t" x="{rx0 + 52:.0f}" y="{ty:.0f}" text-anchor="middle">{label}</text>')
        a('</g>')

    # Scale bar
    sb = 20 * KM
    a(f'<g class="s24-scale"><path d="M28,{MAP_H - 44}v10H{28 + sb:.1f}v-10"/>'
      f'<text x="{28 + sb + 12:.1f}" y="{MAP_H - 28}">20 km</text></g>')
    a('</g>')
    a(f'<rect class="s24-card-edge" width="{MAP_W}" height="{MAP_H}" rx="18"/>')

    # ---- Input tiles (schematic), 3-6.8 s ----
    TX, TW, TH, SW, SKEW = 498, 332, 76, 110, -14
    k = math.tan(math.radians(SKEW))
    ys = [86, 176, 266, 356]
    ymid = ys[0]  # the stack collapses into the top tile
    tiles = [("roads", "Roads", "Overture"), ("slope", "Slope", "Copernicus DEM"),
             ("land", "Land cover", "ESA WorldCover"), ("water", "Water", "JRC surface water")]
    a('<g class="s24-tiles">')
    a(f'<text class="s24-tiles-h" x="{TX + TW / 2}" y="{ys[0] - 22}" text-anchor="middle">input layers (schematic)</text>')

    def tile(kind: str, name: str, sub: str, y: float, cls: str, style: str) -> None:
        sx = -k * TH  # skew shifts the top edge right
        a(f'<g class="{cls}" style="{style}">')
        a(f'<g transform="translate({TX},{y}) skewX({SKEW}) translate({sx:.1f},0)">')
        a(f'<clipPath id="s24-sw-{kind}"><rect width="{SW}" height="{TH}"/></clipPath>')
        a(f'<rect class="s24-tile-bg" width="{TW}" height="{TH}" rx="4"/>')
        a(f'<g clip-path="url(#s24-sw-{kind})">{tile_pattern(kind, SW, TH)}</g>')
        a(f'<rect class="s24-tile-edge" width="{TW}" height="{TH}" rx="4"/>')
        a(f'<path class="s24-tile-edge" d="M{SW},0V{TH}"/>')
        a('</g>')
        lx = TX + SW + 26
        a(f'<text class="s24-tile-n" x="{lx}" y="{y + 33}">{name}</text>')
        a(f'<text class="s24-tile-s" x="{lx}" y="{y + 61}">{sub}</text>')
        a('</g>')

    for i, ((kind, name, sub), y) in enumerate(zip(tiles, ys)):
        tile(kind, name, sub, y, "s24-tile", f"--d:{3.0 + 0.28 * i:.2f}s;--dy:{ymid - y:.0f}px")
    tile("friction", "Friction", "seconds per metre", ymid, "s24-fric", "--d:4.75s")

    # Speed key under the friction tile
    ky = ymid + TH + 52
    keys = [
        ("road", ["Roads 20–80 km/h"]),
        ("off", ["Off-road slower, more so", "on slopes and in forest"]),
        ("water", ["Water is a barrier", "unless bridged"]),
    ]
    y = ky
    for i, (kind, lines) in enumerate(keys):
        a(f'<g class="s24-key" style="--d:{5.0 + 0.2 * i:.1f}s">')
        if kind == "road":
            a(f'<path d="M{TX + 4},{y - 8}h28" stroke="{INK}" stroke-width="5"/>')
        elif kind == "off":
            a(f'<rect x="{TX + 6}" y="{y - 20}" width="22" height="22" rx="3" fill="#2E8B47"/>')
        else:
            a(f'<path d="M{TX + 4},{y - 8} q7,-7 14,0 t14,0" stroke="{BLUE}" stroke-width="4" fill="none"/>')
        for j, line in enumerate(lines):
            a(f'<text class="s24-key-t" x="{TX + 44}" y="{y + j * 29}">{line}</text>')
        a('</g>')
        y += 29 * len(lines) + 14
    a('</g>')

    # ---- Mill, label, timer ----
    a(f'<circle class="s24-pulse" cx="{fx:.1f}" cy="{fy:.1f}" r="10" style="transform-origin:{fx:.1f}px {fy:.1f}px"/>')
    a(f'<g class="s24-mill" style="transform-origin:{fx:.1f}px {fy:.1f}px">'
      f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="10" fill="{BLUE}" stroke="#fff" stroke-width="4"/></g>')
    lw = 300
    for cls, txt, w in [("s24-mill-l s24-mill-l1", "Binabaru mill, Riau · palm", lw),
                        ("s24-mill-l s24-mill-l2", "Binabaru mill", 168)]:
        x0 = fx - 22 - w
        a(f'<g class="{cls}"><rect x="{x0:.0f}" y="{fy - 23:.0f}" width="{w}" height="46" rx="23"/>'
          f'<text x="{x0 + w / 2:.0f}" y="{fy + 8:.0f}" text-anchor="middle">{txt}</text></g>')
    # timer above the mill: 0 -> 90 min in 10-minute steps, synced with the spread
    tw = 132
    a(f'<g class="s24-timer"><rect x="{fx - tw / 2:.0f}" y="{fy - 76:.0f}" width="{tw}" height="44" rx="22"/>')
    steps = list(range(0, 100, 10))
    for i, m in enumerate(steps):
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

    # ---------------- Step rail ----------------
    RX = 924
    rail = [
        (0.5, 3.0, "Mill + commodity", "palm gets a 90-minute budget"),
        (3.0, T_SPREAD - 0.1, "Friction surface", "roads, slope, land cover, water"),
        (T_SPREAD - 0.1, 9.0, "Least-cost spread", "outwards on a 100 m grid"),
        (9.0, None, "Cut at 90 minutes", "one hard-edged polygon"),
    ]
    a('<g class="s24-rail">')
    y0, gap = 70, 150
    a(f'<path class="s24-rail-line" d="M{RX + 25},{y0 + 25}V{y0 + 3 * gap + 25}"/>')
    for i, (t0, t1, title, sub) in enumerate(rail):
        y = y0 + i * gap
        style = f"--d:{t0:.1f}s" + (f";--d2:{t1:.1f}s" if t1 else "")
        cls = "s24-step" + ("" if t1 else " s24-step-last")
        a(f'<g class="{cls}" style="{style}">')
        a(f'<rect class="s24-badge" x="{RX}" y="{y}" width="50" height="50" rx="10"/>')
        a(f'<text class="s24-badge-n" x="{RX + 25}" y="{y + 36}" text-anchor="middle">{i + 1}</text>')
        a(f'<text class="s24-step-t" x="{RX + 74}" y="{y + 26}">{title}</text>')
        a(f'<text class="s24-step-s" x="{RX + 74}" y="{y + 60}">{sub}</text>')
        a('</g>')
    a('</g>')
    a('</svg></div>')
    return "\n".join(s)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("```{=html}\n" + build() + "\n```\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
