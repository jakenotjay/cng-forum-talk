"""Inline-SVG partials for slides 10-13 (virtual cube act).

    uv run --project scripts python scripts/gen_s1x_diagrams.py

Writes slides/_gen/s10-refs.qmd, s11-panels.qmd, s12-chunks.qmd, s13-panels.qmd.
Each is a raw-HTML fence included by the slide. Shapes share one icon language
(3 px ink outlines, blue-soft fills, red for problems); per-element delays are
passed as --d and animated in styles/sNN.scss, scoped to section.present.
"""

from __future__ import annotations

import math
from pathlib import Path

from shapely.affinity import rotate
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "slides" / "_gen"

INK = "#0A1628"
MUTED = "#5B6878"
BLUE = "#376FD0"
BLUE_SOFT = "#DCE7FB"
BLUE_MID = "#B9CEF4"
RED = "#D64545"
RED_SOFT = "#F8DCDC"
LINE = "#C9CFD8"


def fence(svg: str) -> str:
    return "```{=html}\n" + svg.strip() + "\n```\n"


def poly_path(geom) -> str:
    """SVG path data for a shapely Polygon/MultiPolygon exterior(s)."""
    polys = getattr(geom, "geoms", [geom])
    out = []
    for p in polys:
        xs = list(p.exterior.coords)
        out.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in xs[:-1]) + "Z")
    return " ".join(out)


# --------------------------------------------------------------------------
# Shared icons (all drawn in a local box, placed with transform)
# --------------------------------------------------------------------------

def doc_icon(x: float, y: float, w: float, h: float, cls: str = "ic-doc", fold: float | None = None) -> str:
    """Document with a folded top-right corner."""
    f = fold if fold is not None else min(w, h) * 0.28
    d = (f"M{x},{y + 6} Q{x},{y} {x + 6},{y} L{x + w - f},{y} L{x + w},{y + f} "
         f"L{x + w},{y + h - 6} Q{x + w},{y + h} {x + w - 6},{y + h} L{x + 6},{y + h} "
         f"Q{x},{y + h} {x},{y + h - 6} Z")
    fold_d = f"M{x + w - f},{y} L{x + w - f},{y + f} L{x + w},{y + f}"
    return (f'<path class="{cls}" d="{d}"/>'
            f'<path class="{cls}-fold" d="{fold_d}"/>')


def grid_lines(x, y, w, h, nx, ny, cls="s13-ic-gridline") -> str:
    parts = []
    for i in range(1, nx):
        xx = x + w * i / nx
        parts.append(f'<line class="{cls}" x1="{xx:.1f}" y1="{y}" x2="{xx:.1f}" y2="{y + h}"/>')
    for j in range(1, ny):
        yy = y + h * j / ny
        parts.append(f'<line class="{cls}" x1="{x}" y1="{yy:.1f}" x2="{x + w}" y2="{yy:.1f}"/>')
    return "".join(parts)


def cloud_path(cx: float, cy: float, w: float, h: float) -> str:
    """A cloud as the union of a rounded base and three puffs, centred on (cx, cy)."""
    sx, sy = w / 300.0, h / 150.0
    base = box(30, 78, 270, 140).buffer(0)
    shapes = [
        base,
        Point(70, 98).buffer(42, quad_segs=24),
        Point(232, 100).buffer(40, quad_segs=24),
        Point(118, 66).buffer(52, quad_segs=24),
        Point(190, 58).buffer(48, quad_segs=24),
    ]
    u = unary_union(shapes)
    # round the flat bottom corners
    u = u.buffer(-10, quad_segs=12).buffer(10, quad_segs=12)
    pts = [((px - 150) * sx + cx, (py - 85) * sy + cy) for px, py in u.exterior.coords]
    return "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts[:-1]) + "Z"


# --------------------------------------------------------------------------
# Slide 10: refs in our bucket -> bytes in provider clouds
# --------------------------------------------------------------------------

def slide10() -> str:
    W, H = 1600, 650
    node = dict(x=580, y=230, w=440, h=180)
    ncx, ncy = node["x"] + node["w"] / 2, node["y"] + node["h"] / 2
    cw, ch = 340, 155
    lx, rx = 40 + cw / 2, W - 40 - cw / 2
    ys = [90, 320, 550]
    # (label lines, side, row) in the order the arrows draw
    clouds = [
        (["Source Coop"], "L", 0),
        (["AWS Open Data"], "R", 0),
        (["Copernicus"], "L", 1),
        (["UMD / Hansen", "GCS"], "R", 1),
        (["Wasabi"], "L", 2),
        (["OpenGeoHub"], "R", 2),
    ]
    parts = [f'<svg class="s10-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
             'role="img" aria-label="Our GCS bucket holds virtual references; arrows point out to '
             'the provider clouds that hold the bytes: Source Coop, AWS Open Data, Copernicus, '
             'UMD / Hansen GCS, Wasabi, OpenGeoHub">']

    arrows, heads, cl = [], [], []
    for i, (lines, side, row) in enumerate(clouds):
        d = 2.0 + i * 1.0
        cx = lx if side == "L" else rx
        cy = ys[row]
        # start on the node's side edge, spread vertically
        sy = ncy + (row - 1) * 56
        if side == "L":
            sx, ex = node["x"], cx + cw / 2 - 4
            hx = ex + 2
        else:
            sx, ex = node["x"] + node["w"], cx - cw / 2 + 4
            hx = ex - 2
        ey = cy + 12
        mx = (sx + ex) / 2
        path = f"M{sx},{sy:.0f} C{mx:.0f},{sy:.0f} {mx:.0f},{ey:.0f} {hx + (16 if side == 'L' else -16):.0f},{ey:.0f}"
        arrows.append(f'<path class="s10-arrow" pathLength="1" d="{path}" style="--d:{d:.1f}s"/>')
        # arrowhead pointing outwards (horizontal end tangent)
        if side == "L":
            tri = f"{hx},{ey} {hx + 20},{ey - 11} {hx + 20},{ey + 11}"
        else:
            tri = f"{hx},{ey} {hx - 20},{ey - 11} {hx - 20},{ey + 11}"
        heads.append(f'<polygon class="s10-head" points="{tri}" style="--d:{d + 0.65:.2f}s"/>')
        txt = []
        n = len(lines)
        for k, ln in enumerate(lines):
            ty = cy + 22 + (k - (n - 1) / 2) * 30
            txt.append(f'<text class="s10-cloud-text" x="{cx:.0f}" y="{ty:.0f}" text-anchor="middle">{ln}</text>')
        cl.append(f'<g class="s10-cloud" style="--d:{d + 0.6:.2f}s">'
                  f'<path class="s10-cloud-shape" d="{cloud_path(cx, cy, cw, ch)}"/>{"".join(txt)}</g>')

    parts += cl + arrows + heads

    # central node: bucket icon + label
    x, y, w, h = node["x"], node["y"], node["w"], node["h"]
    parts.append(f'<rect class="s10-node" x="{x}" y="{y}" width="{w}" height="{h}" rx="24"/>')
    bx, by = x + 44, y + 52
    parts.append(
        f'<g class="s10-bucket">'
        f'<path d="M{bx},{by} L{bx + 10},{by + 78} Q{bx + 40},{by + 90} {bx + 70},{by + 78} L{bx + 80},{by} Z"/>'
        f'<ellipse cx="{bx + 40}" cy="{by}" rx="40" ry="12"/>'
        f'</g>')
    # refs as small bracketed lines in the bucket
    parts.append(f'<text class="s10-node-title" x="{x + 150}" y="{y + 82}">our GCS bucket</text>')
    parts.append(f'<text class="s10-node-sub" x="{x + 150}" y="{y + 122}">virtual refs</text>')
    parts.append("</svg>")
    return "\n".join(parts)


# --------------------------------------------------------------------------
# Slide 11: three TIFF wrinkles
# --------------------------------------------------------------------------

def s11_utm() -> str:
    W, H = 400, 320
    top, bot = 46, 316
    zones = ["32N", "33N", "34N"]
    zw = W / len(zones)
    parts = [f'<svg class="s11-art" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    tiles = []
    for i, z in enumerate(zones):
        cx = zw * i + zw / 2
        for j, cy in enumerate([top + 66, top + 200]):
            ang = (-7 if i % 2 == 0 else 7) * (1 if j == 0 else 0.85)
            t = rotate(box(cx - 72, cy - 62, cx + 72, cy + 62), ang, origin=(cx, cy))
            tiles.append((i, t))
    for i, t in tiles:
        parts.append(f'<path class="s11-tile" d="{poly_path(t)}"/>')
    # overlaps between neighbouring zones, in red
    ov = []
    for a in range(len(tiles)):
        for b in range(a + 1, len(tiles)):
            ia, ta = tiles[a]
            ib, tb = tiles[b]
            if abs(ia - ib) == 1:
                g = ta.intersection(tb)
                if not g.is_empty and g.area > 4:
                    ov.append(g)
    if ov:
        parts.append(f'<path class="s11-overlap" d="{poly_path(unary_union(ov))}"/>')
    for i in range(1, len(zones)):
        xx = zw * i
        parts.append(f'<line class="s11-zone" x1="{xx}" y1="{top - 6}" x2="{xx}" y2="{bot}"/>')
    for i, z in enumerate(zones):
        parts.append(f'<text class="s11-lbl" x="{zw * i + zw / 2}" y="26" text-anchor="middle">{z}</text>')
    parts.append("</svg>")
    return "".join(parts)


def s11_ragged() -> str:
    W, H = 400, 320
    blk, short = 40, 18
    tile = 3 * blk + short
    gap = 10
    total = 2 * tile + gap
    x0 = (W - total) / 2
    y0 = 48
    parts = [f'<svg class="s11-art" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    # 10 degree dimension
    parts.append(f'<line class="s11-dim" x1="{x0}" y1="28" x2="{x0 + tile}" y2="28"/>'
                 f'<line class="s11-dim" x1="{x0}" y1="20" x2="{x0}" y2="36"/>'
                 f'<line class="s11-dim" x1="{x0 + tile}" y1="20" x2="{x0 + tile}" y2="36"/>')
    parts.append(f'<text class="s11-lbl" x="{x0 + tile / 2}" y="20" text-anchor="middle">10°</text>')
    sizes = [blk, blk, blk, short]
    for ti in range(2):
        for tj in range(2):
            tx = x0 + ti * (tile + gap)
            ty = y0 + tj * (tile + gap)
            yy = ty
            for r, hgt in enumerate(sizes):
                xx = tx
                for c, wid in enumerate(sizes):
                    bad = r == 3 or c == 3
                    cls = "s11-blk-bad" if bad else ("s11-blk" if (r + c) % 2 == 0 else "s11-blk2")
                    parts.append(f'<rect class="{cls}" x="{xx}" y="{yy}" width="{wid}" height="{hgt}"/>')
                    xx += wid
                yy += hgt
            parts.append(f'<rect class="s11-tile-frame" x="{tx}" y="{ty}" width="{tile}" height="{tile}" rx="3"/>')
    parts.append("</svg>")
    return "".join(parts)


def s11_overwrite() -> str:
    W, H = 400, 320
    parts = [f'<svg class="s11-art" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    # the file
    fx, fy, fw, fh = 240, 80, 156, 230
    parts.append(doc_icon(fx, fy, fw, fh, cls="s11-file"))
    parts.append(f'<text class="s11-fname" x="{fx + fw / 2}" y="{fy + 130}" text-anchor="middle">tile.tif</text>')
    # version pill, text swaps
    px, py = fx + fw / 2, fy + 180
    parts.append(f'<rect class="s11-vpill" x="{px - 40}" y="{py - 23}" width="80" height="36" rx="18"/>')
    for k, v in enumerate(["v1", "v2", "v3"]):
        parts.append(f'<text class="s11-ver s11-ver{k + 1}" x="{px}" y="{py + 4}" text-anchor="middle">{v}</text>')
    # rewrite arrows above the file
    cx, cy, r = fx + fw / 2, 38, 22
    parts.append(f'<g class="s11-spin" style="transform-origin:{cx}px {cy}px">'
                 f'<path class="s11-redarc" d="M{cx - r},{cy} A{r},{r} 0 1 1 {cx + r * math.cos(math.radians(40)):.1f},{cy + r * math.sin(math.radians(40)):.1f}"/>'
                 f'<polygon class="s11-redhead" points="{cx - r - 9},{cy - 4} {cx - r + 9},{cy - 4} {cx - r},{cy + 10}"/>'
                 f'</g>')
    # a virtual ref pointing at a byte range of the file
    rx_, ry_ = 6, 160
    parts.append(f'<rect class="s11-ref" x="{rx_}" y="{ry_}" width="96" height="54" rx="12"/>')
    parts.append(f'<text class="s11-reftext" x="{rx_ + 48}" y="{ry_ + 35}" text-anchor="middle">ref</text>')
    parts.append(f'<path class="s11-reflink" d="M{rx_ + 96},{ry_ + 27} L{fx - 8},{ry_ + 27}"/>')
    parts.append(f'<polygon class="s11-refhead" points="{fx - 4},{ry_ + 27} {fx - 20},{ry_ + 18} {fx - 20},{ry_ + 36}"/>')
    # broken: red cross over the link
    mx, my = (rx_ + 96 + fx - 20) / 2, ry_ + 27
    parts.append(f'<g class="s11-broken"><circle cx="{mx}" cy="{my}" r="18"/>'
                 f'<path d="M{mx - 7},{my - 7} L{mx + 7},{my + 7} M{mx + 7},{my - 7} L{mx - 7},{my + 7}"/></g>')
    parts.append(f'<text class="s11-stale" x="{mx}" y="{my + 56}" text-anchor="middle">stale ref</text>')
    parts.append("</svg>")
    return "".join(parts)


def slide11() -> str:
    panels = [
        (1.0, s11_utm(), "UTM zones", "every zone its own CRS", ["ForTy"]),
        (5.0, s11_ragged(), "Ragged 10° tiles", "last block row and column short", ["JRC TMF", "GFC"]),
        (9.0, s11_overwrite(), "Overwritten in place", "alerts: same path, new bytes daily", ["GLAD-L", "GLAD-S2"]),
    ]
    out = ['<div class="s11-grid">']
    for d, art, title, sub, chips in panels:
        chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
        out.append(
            f'<div class="card s11-panel a-rise" style="--d:{d:.0f}s">'
            f'<div class="s11-artbox">{art}</div>'
            f'<div class="s11-title">{title}</div>'
            f'<div class="s11-sub">{sub}</div>'
            f'<div class="s11-chips">{chip_html}</div>'
            f'</div>')
    out.append("</div>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Slide 12: regular vs rectilinear chunk grids (adapted from Earthmover)
# --------------------------------------------------------------------------

def chunk_grid(x0, y0, rows, cols, unit, red_cols=(), red_rows=()) -> str:
    parts = []
    nrows, ncols = sum(rows), sum(cols)
    yy = y0
    for r, rh in enumerate(rows):
        xx = x0
        for c, cw in enumerate(cols):
            bad = c in red_cols or r in red_rows
            cls = "s12-c-bad" if bad else ("s12-c1" if (r + c) % 2 == 0 else "s12-c2")
            parts.append(f'<rect class="{cls}" x="{xx}" y="{yy}" width="{cw * unit}" height="{rh * unit}"/>')
            xx += cw * unit
        yy += rh * unit
    parts.append(grid_lines(x0, y0, ncols * unit, nrows * unit, ncols, nrows, cls="s12-px"))
    # chunk boundaries
    xx = x0
    for cw in cols[:-1]:
        xx += cw * unit
        parts.append(f'<line class="s12-cb" x1="{xx}" y1="{y0}" x2="{xx}" y2="{y0 + nrows * unit}"/>')
    yy = y0
    for rh in rows[:-1]:
        yy += rh * unit
        parts.append(f'<line class="s12-cb" x1="{x0}" y1="{yy}" x2="{x0 + ncols * unit}" y2="{yy}"/>')
    parts.append(f'<rect class="s12-frame" x="{x0}" y="{y0}" width="{ncols * unit}" height="{nrows * unit}"/>')
    # size ticks
    xx = x0
    for cw in cols:
        parts.append(f'<text class="s12-tick" x="{xx + cw * unit / 2}" y="{y0 + nrows * unit + 30}" text-anchor="middle">{cw}</text>')
        xx += cw * unit
    yy = y0
    for rh in rows:
        parts.append(f'<text class="s12-tick" x="{x0 - 14}" y="{yy + rh * unit / 2 + 8}" text-anchor="end">{rh}</text>')
        yy += rh * unit
    return "".join(parts)


def slide12() -> str:
    W, H = 780, 690
    unit = 28
    gx = [52, 450]
    gy = 110
    parts = [f'<svg class="s12-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
             'aria-label="A regular chunk grid of four equal chunks next to a rectilinear grid whose last '
             'column is one pixel wide; below, two stitched tiles give chunk sizes 4 4 2 4 4 2">']
    # regular
    parts.append(f'<g class="s12-reg a-fade" style="--d:0.6s">'
                 f'<text class="s12-h" x="{gx[0] + 140}" y="40" text-anchor="middle">regular</text>'
                 f'<text class="s12-code" x="{gx[0] + 140}" y="76" text-anchor="middle">(5, 5)</text>'
                 + chunk_grid(gx[0], gy, [5, 5], [5, 5], unit) + "</g>")
    parts.append(f'<g class="s12-rect a-fade" style="--d:2.2s">'
                 f'<text class="s12-h" x="{gx[1] + 140}" y="40" text-anchor="middle">rectilinear</text>'
                 f'<text class="s12-code" x="{gx[1] + 140}" y="76" text-anchor="middle">[[6,4], [3,3,3,1]]</text>'
                 + chunk_grid(gx[1], gy, [6, 4], [3, 3, 3, 1], unit, red_cols=(3,)) + "</g>")
    # credit sits directly under the two grids it refers to (the strip below is ours)
    cx = (gx[0] + gx[1] + 10 * unit) / 2
    parts.append(f'<text class="s12-credit a-fade" style="--d:2.2s" x="{cx}" y="{gy + 10 * unit + 72}" '
                 f'text-anchor="middle">Grids adapted from Earthmover\u2019s blog on variable-length chunks</text>')
    # stitched strip
    sy = 540
    sizes = [4, 4, 2, 4, 4, 2]
    su = 36
    total = sum(sizes) * su
    sx0 = (W - total) / 2 + 10
    strip = [f'<text class="s12-strip-h" x="{sx0}" y="{sy - 20}">two 10° tiles, stitched: chunk sizes along x</text>']
    xx = sx0
    for k, s in enumerate(sizes):
        bad = s == 2
        cls = "s12-c-bad" if bad else ("s12-c1" if k % 2 == 0 else "s12-c2")
        strip.append(f'<rect class="{cls}" x="{xx}" y="{sy}" width="{s * su}" height="64"/>')
        strip.append(f'<text class="s12-num{" s12-num-bad" if bad else ""}" x="{xx + s * su / 2}" y="{sy + 42}" text-anchor="middle">{s}</text>')
        xx += s * su
    xx = sx0
    for k, s in enumerate(sizes[:-1]):
        xx += s * su
        strip.append(f'<line class="{"s12-tileb" if k == 2 else "s12-cb"}" x1="{xx}" y1="{sy - (10 if k == 2 else 0)}" x2="{xx}" y2="{sy + 64 + (10 if k == 2 else 0)}"/>')
    strip.append(f'<rect class="s12-frame" x="{sx0}" y="{sy}" width="{total}" height="64"/>')
    mid = sx0 + 9 * su
    strip.append(f'<text class="s12-note" x="{mid}" y="{sy + 108}" text-anchor="middle">irregular chunk mid-array</text>')
    strip.append(f'<path class="s12-note-arrow" d="M{mid},{sy + 84} L{mid},{sy + 70}"/>')
    parts.append(f'<g class="s12-strip a-fade" style="--d:4.2s">{"".join(strip)}</g>')
    parts.append("</svg>")
    return "\n".join(parts)


# --------------------------------------------------------------------------
# Slide 13: three families of virtual source
# --------------------------------------------------------------------------

def icon(kind: str, x: float, y: float, s: float = 76) -> str:
    """Line icons in a s x s box at (x, y)."""
    p = []
    if kind == "manifest":
        p.append(doc_icon(x + 8, y + 2, s - 16, s - 4, cls="s13-ic-doc"))
        for k in range(3):
            yy = y + 30 + k * 13
            p.append(f'<line class="s13-ic-ref" x1="{x + 20}" y1="{yy}" x2="{x + s - 22}" y2="{yy}"/>')
    elif kind == "array":
        p.append(f'<rect class="s13-ic-fill" x="{x + 6}" y="{y + 6}" width="{s - 12}" height="{s - 12}" rx="6"/>')
        p.append(grid_lines(x + 6, y + 6, s - 12, s - 12, 4, 4, cls="s13-ic-gridline-b"))
    elif kind == "crop":
        p.append(f'<rect class="s13-ic-box" x="{x + 6}" y="{y + 6}" width="{s - 12}" height="{s - 12}" rx="6"/>')
        p.append(grid_lines(x + 6, y + 6, s - 12, s - 12, 4, 4))
        p.append(f'<rect class="s13-ic-sel" x="{x + 22}" y="{y + 24}" width="{s * 0.42:.0f}" height="{s * 0.34:.0f}" rx="3"/>')
    elif kind == "tiles":
        c = (s - 12) / 3
        for i in range(3):
            for j in range(3):
                hit = (i, j) in {(1, 1), (2, 1)}
                p.append(f'<rect class="{"s13-ic-tile-hit" if hit else "s13-ic-tile"}" x="{x + 6 + i * c + 2:.1f}" y="{y + 6 + j * c + 2:.1f}" width="{c - 4:.1f}" height="{c - 4:.1f}" rx="3"/>')
    elif kind == "manifests":
        p.append(doc_icon(x + 26, y + 2, 44, 56, cls="s13-ic-doc-back"))
        p.append(doc_icon(x + 6, y + 18, 44, 56, cls="s13-ic-doc"))
        for k in range(2):
            yy = y + 44 + k * 12
            p.append(f'<line class="s13-ic-ref" x1="{x + 14}" y1="{yy}" x2="{x + 40}" y2="{yy}"/>')
    elif kind == "merge":
        p.append(f'<rect class="s13-ic-fill" x="{x + 4}" y="{y + 18}" width="34" height="40" rx="4"/>')
        p.append(f'<rect class="s13-ic-fill" x="{x + 38}" y="{y + 18}" width="34" height="40" rx="4"/>')
        p.append(f'<line class="s13-ic-seam" x1="{x + 38}" y1="{y + 12}" x2="{x + 38}" y2="{y + 64}"/>')
    elif kind == "query":
        for k in range(3):
            yy = y + 14 + k * 16
            p.append(f'<line class="s13-ic-ref" x1="{x + 6}" y1="{yy}" x2="{x + 44}" y2="{yy}"/>')
        p.append(f'<circle class="s13-ic-lens" cx="{x + 46}" cy="{y + 44}" r="17"/>')
        p.append(f'<line class="s13-ic-handle" x1="{x + 58}" y1="{y + 56}" x2="{x + 72}" y2="{y + 70}"/>')
    elif kind == "bytes":
        p.append(f'<rect class="s13-ic-box" x="{x + 4}" y="{y + 26}" width="{s - 8}" height="26" rx="4"/>')
        for k in range(1, 6):
            xx = x + 4 + k * (s - 8) / 6
            p.append(f'<line class="s13-ic-gridline" x1="{xx:.1f}" y1="{y + 26}" x2="{xx:.1f}" y2="{y + 52}"/>')
        seg = (s - 8) / 6
        p.append(f'<rect class="s13-ic-sel-solid" x="{x + 4 + seg:.1f}" y="{y + 26}" width="{seg:.1f}" height="26"/>')
        p.append(f'<rect class="s13-ic-sel-solid" x="{x + 4 + 4 * seg:.1f}" y="{y + 26}" width="{seg:.1f}" height="26"/>')
        p.append(f'<path class="s13-ic-bracket" d="M{x + 4 + seg:.1f},{y + 18} L{x + 4 + seg:.1f},{y + 12} L{x + 4 + 2 * seg:.1f},{y + 12} L{x + 4 + 2 * seg:.1f},{y + 18}"/>')
        p.append(f'<path class="s13-ic-bracket" d="M{x + 4 + 4 * seg:.1f},{y + 18} L{x + 4 + 4 * seg:.1f},{y + 12} L{x + 4 + 5 * seg:.1f},{y + 12} L{x + 4 + 5 * seg:.1f},{y + 18}"/>')
    elif kind == "mosaic":
        a = rotate(box(x + 6, y + 10, x + 46, y + 50), -8, origin="centroid")
        b = rotate(box(x + 28, y + 24, x + 68, y + 64), 8, origin="centroid")
        p.append(f'<path class="s13-ic-fill" d="{poly_path(a)}"/>')
        p.append(f'<path class="s13-ic-fill" d="{poly_path(b)}"/>')
    return "".join(p)


def s13_flow(steps: list[tuple[str, list[str]]], d0: float) -> str:
    W, H = 400, 380
    s = 76
    rows = [6, 150, 294]
    parts = [f'<svg class="s13-flow" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for k, (kind, label) in enumerate(steps):
        y = rows[k]
        d = d0 + 0.4 + k * 0.6
        lines = "".join(
            f'<text class="s13-step" x="{s + 30}" y="{y + s / 2 + 9 + (i - (len(label) - 1) / 2) * 30:.0f}">{ln}</text>'
            for i, ln in enumerate(label))
        parts.append(f'<g class="s13-row" style="--d:{d:.1f}s">{icon(kind, 4, y, s)}{lines}</g>')
        if k < len(steps) - 1:
            y1, y2 = y + s + 10, rows[k + 1] - 10
            cx = 4 + s / 2
            parts.append(f'<g class="s13-row" style="--d:{d + 0.3:.1f}s">'
                         f'<line class="s13-arrow" x1="{cx}" y1="{y1}" x2="{cx}" y2="{y2 - 10}"/>'
                         f'<polygon class="s13-arrowhead" points="{cx},{y2} {cx - 9},{y2 - 13} {cx + 9},{y2 - 13}"/></g>')
    parts.append("</svg>")
    return "".join(parts)


def slide13() -> str:
    fams = [
        (1.0, "A", "Static global manifest",
         [("manifest", ["one stitched manifest"]), ("array", ["open as one array"]), ("crop", ["crop + reproject"])],
         ["Hansen", "JRC GFC"]),
        (5.0, "B", "Tiled static manifests",
         [("tiles", ["discover tiles"]), ("manifests", ["open persisted", "manifests"]), ("merge", ["mosaic + reproject"])],
         ["JRC TMF"]),
        (9.0, "C", "Dynamic virtual stores",
         [("query", ["STAC / listing query"]), ("bytes", ["build byte-range", "refs on the fly"]), ("mosaic", ["mosaic + reproject"])],
         ["GLAD", "OPERA DIST", "ForTy"]),
    ]
    out = ['<div class="s13-grid">']
    for d, letter, title, steps, chips in fams:
        chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
        out.append(
            f'<div class="card s13-panel a-rise" style="--d:{d:.0f}s">'
            f'<div class="s13-head"><span class="s13-badge">{letter}</span><span class="s13-title">{title}</span></div>'
            f'{s13_flow(steps, d)}'
            f'<div class="s13-chips a-fade" style="--d:{d + 2.0:.1f}s">{chip_html}</div>'
            f'</div>')
    out.append("</div>")
    # Shared final step: every family finishes with the same reproject (dataset_source.py:
    # Family A crops/reprojects a slice; DiscoveringSource B/C "both finish with the shared
    # reproject"). One arrow per card feeds a full-width bar, last beat at ~11 s.
    arrow = ('<svg class="s13-down" viewBox="0 0 30 34" xmlns="http://www.w3.org/2000/svg">'
             '<line x1="15" y1="2" x2="15" y2="20"/><polygon points="15,32 6,18 24,18"/></svg>')
    geobox = ('<svg class="s13-geobox" viewBox="0 0 56 56" xmlns="http://www.w3.org/2000/svg">'
              '<rect x="4" y="4" width="48" height="48" rx="5"/>'
              + "".join(f'<line x1="{4 + 12 * k}" y1="4" x2="{4 + 12 * k}" y2="52"/>'
                        f'<line x1="4" y1="{4 + 12 * k}" x2="52" y2="{4 + 12 * k}"/>' for k in range(1, 4))
              + '</svg>')
    out.append('<div class="s13-final a-rise" style="--d:11s">'
               f'<div class="s13-downs">{arrow * 3}</div>'
               f'<div class="s13-bar">{geobox}<span>reprojected onto the target geobox</span></div>'
               '</div>')
    return "\n".join(out)


def main() -> None:
    GEN.mkdir(parents=True, exist_ok=True)
    for name, fn in [("s10-refs", slide10), ("s11-panels", slide11),
                     ("s12-chunks", slide12), ("s13-panels", slide13)]:
        path = GEN / f"{name}.qmd"
        path.write_text(fence(fn()))
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
