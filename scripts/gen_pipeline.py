"""Pipeline diagram family for slides 6, 8, 9 and 19.

    uv run --project scripts python scripts/gen_pipeline.py

One parametrised generator for the London-style pipeline:

    Customer supply shed -> [Prefect jobs · Kubernetes:
        export to icechunk -> zonal stats -> normalise to Postgres] -> Served to customer

with service boxes (source, Icechunk, BigQuery, Postgres) linked to the jobs.
Emits inline-SVG partials into slides/_gen/. Every element carries stable,
slide-prefixed classes (e.g. .s06-job-export, .s19-svc-bq, .s08-src) so the
per-slide stylesheet (styles/sNN.scss) animates them; draw order is exposed
as a --i custom property on each element.

Variants:
  s06  full layout, neutral GEE source
  s08  compact strip (slide-8 header), GEE neutral in markup (CSS turns it red)
       plus the "500 requests, 4 lanes" queue diagram
  s09  full horizontal layout (as s06), GEE (red, "before") cross-fading to
       virtual icechunk (green, "after"), with a before/after chip left of the
       source and a "references live with us" caption beneath it
  s19  full layout, virtual icechunk source, bottleneck marker, rewrite
       outline and the "≤ 5 minutes" target chip
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "slides" / "_gen"

INK = "#0A1628"
MUTED = "#5B6878"
BLUE = "#376FD0"
BLUE_SOFT = "#DCE7FB"
GREEN = "#3FB557"
GREEN_DARK = "#23863A"
GREEN_BG = "#E6F6EA"
RED = "#D64545"
RED_BG = "#FBE7E7"
CREAM = "#F4F1EA"
CARD = "#FFFFFF"
LINK = "#9AA6B6"
FONT = "'Google Sans', 'Google Sans Text', system-ui, sans-serif"

Line = tuple[str, int, int]  # text, font size, weight


@dataclass
class Node:
    key: str            # class suffix, e.g. "job-export"
    x: float
    y: float
    w: float
    h: float
    kind: str           # io | job | svc | src-gee | src-gee-red | src-vic
    lines: list[Line]
    i: float = 0.0      # draw order
    extra_cls: str = ""

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def r(self) -> float:
        return self.x + self.w

    @property
    def b(self) -> float:
        return self.y + self.h


@dataclass
class Layout:
    width: int
    height: int
    nodes: dict[str, Node] = field(default_factory=dict)
    group: tuple[float, float, float, float] = (0, 0, 0, 0)
    group_label: tuple[float, float, int] = (0, 0, 24)  # x, baseline y, size
    arrows: list[tuple[tuple[float, float], tuple[float, float], float]] = field(default_factory=list)
    links: list[tuple[str, str, str, float]] = field(default_factory=list)  # svc, job, path d, i
    vertical: bool = False
    pad_x: int = 0  # extra viewBox margin left of x=0 (room for the s09 pop)


# --------------------------------------------------------------------------
# styles per node kind
# --------------------------------------------------------------------------
KIND = {
    #            fill        stroke   sw   text
    "io":       (CARD,      MUTED,   2.5, MUTED),
    "job":      (BLUE,      BLUE,    0,   "#FFFFFF"),
    "svc":      (CARD,      BLUE,    2.5, INK),
    "src-gee":  (CARD,      BLUE,    2.5, INK),
    "src-gee-red": (RED_BG, RED,     3.5, RED),
    "src-vic":  (GREEN_BG,  GREEN,   3.5, GREEN_DARK),
}
LINK_COLOUR = {"src-gee": LINK, "src-gee-red": RED, "src-vic": GREEN}


def src_lines(kind: str, compact: bool) -> list[Line]:
    if kind == "src-vic":
        return [("virtual icechunk", 24, 700), ("refs in GCS", 22, 400)]
    return [("GEE", 30 if not compact else 24, 700)]


# --------------------------------------------------------------------------
# layouts
# --------------------------------------------------------------------------
def horizontal(src_kind: str, compact: bool = False, src_w: float | None = None) -> Layout:
    """Left-to-right pipeline on a 1600-wide canvas (full or compact strip)."""
    if compact:
        svc_y, svc_h = 0, 58
        grp_y, grp_h = 92, 104
        job_y, job_h = 108, 72
        io_y, io_h = 108, 72
        job_fs, io_fs, svc_fs = 24, 22, 24
        label_y, label_fs = 226, 22
        height = 236
    else:
        svc_y, svc_h = 20, 96
        grp_y, grp_h = 222, 236
        job_y, job_h = 270, 140
        io_y, io_h = 280, 120
        job_fs, io_fs, svc_fs = 32, 26, 28
        label_y, label_fs = 498, 24
        height = 520

    L = Layout(1600, height)
    N = L.nodes
    jw, xs = 290, [300, 655, 1010]

    def io_lines(a: str, b: str) -> list[Line]:
        return [(a, io_fs, 500), (b, io_fs, 500)]

    def job_lines(a: str, b: str) -> list[Line]:
        if compact:
            return [(f"{a} {b}", job_fs, 700)]
        return [(a, job_fs, 700), (b, job_fs, 700)]

    N["in"] = Node("in", 10, io_y, 200, io_h, "io", io_lines("Customer", "supply shed"), 0)
    N["export"] = Node("job-export", xs[0], job_y, jw, job_h, "job", job_lines("export to", "icechunk"), 2)
    N["zonal"] = Node("job-zonal", xs[1], job_y, jw, job_h, "job", job_lines("zonal", "stats"), 4)
    N["normalise"] = Node("job-normalise", xs[2], job_y, jw, job_h, "job", job_lines("normalise to", "Postgres"), 6)
    N["out"] = Node("out", 1390, io_y, 200, io_h, "io", io_lines("Served to", "customer"), 8)

    sw = src_w or (250 if src_kind == "src-vic" else 220)
    N["src"] = Node("src", 415 - sw / 2, svc_y, sw, svc_h, src_kind, src_lines(src_kind, compact), 2.4)
    N["icechunk"] = Node("svc-icechunk", 565, svc_y, 200, svc_h, "svc", [("Icechunk", svc_fs, 500)], 3.4)
    N["bq"] = Node("svc-bq", 875, svc_y, 200, svc_h, "svc", [("BigQuery", svc_fs, 500)], 5.4)
    N["pg"] = Node("svc-pg", 1100, svc_y, 200, svc_h, "svc", [("Postgres", svc_fs, 500)], 6.4)

    L.group = (262, grp_y, 1076, grp_h)
    L.group_label = (262, label_y, label_fs)

    cy = job_y + job_h / 2
    L.arrows = [((216, cy), (294, cy), 1), ((596, cy), (649, cy), 3),
                ((951, cy), (1004, cy), 5), ((1306, cy), (1384, cy), 7)]

    def down(svc: Node, x0: float, job: Node, x1: float) -> str:
        return f"M{x0:.1f},{svc.b:.1f} L{x1:.1f},{job.y:.1f}"

    s, ic, bq, pg = N["src"], N["icechunk"], N["bq"], N["pg"]
    ex, zs, nm = N["export"], N["zonal"], N["normalise"]
    L.links = [
        ("src", "export", down(s, s.cx, ex, s.cx), 2.4),
        ("icechunk", "export", down(ic, ic.cx, ex, ex.r - 45), 3.4),
        ("icechunk", "zonal", down(ic, ic.cx, zs, zs.x + 80), 3.4),
        ("bq", "zonal", down(bq, bq.cx, zs, zs.r - 45), 5.4),
        ("bq", "normalise", down(bq, bq.cx, nm, nm.x + 45), 5.4),
        ("pg", "normalise", down(pg, pg.cx, nm, pg.cx), 6.4),
    ]
    return L


def vertical(src_kind: str) -> Layout:
    """Top-to-bottom pipeline for the right-hand column of slide 9."""
    L = Layout(950, 740, vertical=True, pad_x=24)
    N = L.nodes
    jx, jw, jh = 330, 300, 96
    ys = [150, 300, 450]
    N["in"] = Node("in", jx, 0, jw, 64, "io", [("Customer supply shed", 26, 500)], 0)
    N["export"] = Node("job-export", jx, ys[0], jw, jh, "job", [("export to", 30, 700), ("icechunk", 30, 700)], 2)
    N["zonal"] = Node("job-zonal", jx, ys[1], jw, jh, "job", [("zonal stats", 30, 700)], 4)
    N["normalise"] = Node("job-normalise", jx, ys[2], jw, jh, "job", [("normalise to", 30, 700), ("Postgres", 30, 700)], 6)
    N["out"] = Node("out", jx, 676, jw, 64, "io", [("Served to customer", 26, 500)], 8)

    N["src"] = Node("src", 0, ys[0] + 3, 250, 90, src_kind, src_lines(src_kind, False), 2.4)
    N["icechunk"] = Node("svc-icechunk", 735, 228, 200, 76, "svc", [("Icechunk", 28, 500)], 3.4)
    N["bq"] = Node("svc-bq", 735, 378, 200, 76, "svc", [("BigQuery", 28, 500)], 5.4)
    N["pg"] = Node("svc-pg", 735, 520, 200, 76, "svc", [("Postgres", 28, 500)], 6.4)

    L.group = (300, 120, 360, 466)
    L.group_label = (284, 560, 24)  # right-aligned, left of the group (see pipeline_svg)
    cx = jx + jw / 2
    L.arrows = [((cx, 68), (cx, 144), 1), ((cx, ys[0] + jh + 4), (cx, ys[1] - 6), 3),
                ((cx, ys[1] + jh + 4), (cx, ys[2] - 6), 5), ((cx, ys[2] + jh + 4), (cx, 670), 7)]

    def side(svc: Node, y0: float, job: Node, y1: float) -> str:
        return f"M{svc.x:.1f},{y0:.1f} L{job.r:.1f},{y1:.1f}"

    s, ic, bq, pg = N["src"], N["icechunk"], N["bq"], N["pg"]
    ex, zs, nm = N["export"], N["zonal"], N["normalise"]
    L.links = [
        ("src", "export", f"M{s.r:.1f},{ex.cy:.1f} L{ex.x:.1f},{ex.cy:.1f}", 2.4),
        ("icechunk", "export", side(ic, ic.cy, ex, ex.b - 22), 3.4),
        ("icechunk", "zonal", side(ic, ic.cy, zs, zs.y + 22), 3.4),
        ("bq", "zonal", side(bq, bq.cy, zs, zs.b - 22), 5.4),
        ("bq", "normalise", side(bq, bq.cy, nm, nm.y + 22), 5.4),
        ("pg", "normalise", side(pg, pg.cy, nm, nm.b - 22), 6.4),
    ]
    return L


# --------------------------------------------------------------------------
# SVG emitters
# --------------------------------------------------------------------------
def text_block(cx: float, cy: float, lines: list[Line], colour: str, p: str) -> str:
    gap = 1.18
    heights = [sz * gap for _, sz, _ in lines]
    top = cy - sum(heights) / 2
    out = [f'<text class="{p}-label" text-anchor="middle" fill="{colour}">']
    y = top
    for (t, sz, wt), hgt in zip(lines, heights):
        base = y + hgt / 2 + sz * 0.36  # visual centre of x-height/caps
        out.append(f'<tspan x="{cx:.1f}" y="{base:.1f}" font-size="{sz}" font-weight="{wt}">{t}</tspan>')
        y += hgt
    out.append("</text>")
    return "".join(out)


def node_svg(n: Node, p: str, rx: float, cls: str = "") -> str:
    fill, stroke, sw, tc = KIND[n.kind]
    kind_cls = n.kind.split("-")[0]
    sw_attr = f' stroke="{stroke}" stroke-width="{sw}"' if sw else ""
    classes = " ".join(c for c in (f"{p}-el", f"{p}-node", f"{p}-{kind_cls}", f"{p}-{n.key}", cls, n.extra_cls) if c)
    return (
        f'<g class="{classes}" style="--i:{n.i}">'
        + f'<rect class="{p}-box" x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" height="{n.h:.1f}" '
        f'rx="{rx}" fill="{fill}"{sw_attr}/>'
        + text_block(n.cx, n.cy, n.lines, tc, p)
        + "</g>"
    )


def arrow_svg(a: tuple[float, float], b: tuple[float, float], i: float, p: str, k: int) -> str:
    (x0, y0), (x1, y1) = a, b
    hl, hw = 20, 13  # head length, half width
    if abs(y1 - y0) < 1e-6:  # horizontal
        d = 1 if x1 > x0 else -1
        bx = x1 - d * hl
        head = f"{x1:.1f},{y1:.1f} {bx:.1f},{y1 - hw:.1f} {bx:.1f},{y1 + hw:.1f}"
        shaft = f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{bx:.1f}" y2="{y1:.1f}"/>'
    else:
        d = 1 if y1 > y0 else -1
        by = y1 - d * hl
        head = f"{x1:.1f},{y1:.1f} {x1 - hw:.1f},{by:.1f} {x1 + hw:.1f},{by:.1f}"
        shaft = f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{by:.1f}"/>'
    return (
        f'<g class="{p}-el {p}-arrow {p}-arrow-{k}" style="--i:{i}" stroke="{BLUE}" stroke-width="5" '
        f'stroke-linecap="round" fill="{BLUE}">{shaft}<polygon points="{head}" stroke="none"/></g>'
    )


def pipeline_svg(L: Layout, p: str, *, src_swap: bool = False, extras: tuple[str, ...] = (),
                 aria: str = "") -> str:
    N = L.nodes
    rx_job = 20 if not L.vertical else 18
    parts: list[str] = []
    parts.append(
        f'<svg class="{p}-pl" viewBox="{-L.pad_x} 0 {L.width + L.pad_x} {L.height}" role="img" aria-label="{aria}" '
        f'font-family="{FONT}" xmlns="http://www.w3.org/2000/svg">'
    )

    # group
    gx, gy, gw, gh = L.group
    lx, ly, lfs = L.group_label
    parts.append(
        f'<g class="{p}-el {p}-group" style="--i:1.5">'
        f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" rx="28" fill="none" stroke="{MUTED}" '
        f'stroke-width="3" stroke-dasharray="14 10"/>'
        + (
            f'<text x="{lx}" y="{ly}" font-size="{lfs}" font-weight="700" fill="{MUTED}" text-anchor="end">'
            f'<tspan x="{lx}">Prefect jobs</tspan><tspan x="{lx}" dy="{lfs * 1.25}">Kubernetes</tspan></text></g>'
            if L.vertical else
            f'<text x="{lx}" y="{ly}" font-size="{lfs}" font-weight="700" fill="{MUTED}">'
            f'Prefect jobs · Kubernetes</text></g>'
        )
    )

    # links (behind boxes)
    src_kind = N["src"].kind
    for svc, job, d, i in L.links:
        colour = LINK_COLOUR.get(src_kind, LINK) if svc == "src" else LINK
        width = 4 if (svc == "src" and src_kind != "src-gee") else 3
        if svc == "src" and src_swap:
            for state, c in (("before", RED), ("after", GREEN)):
                parts.append(
                    f'<path class="{p}-el {p}-link {p}-link-src-{job} {p}-{state}" style="--i:{i}" d="{d}" '
                    f'stroke="{c}" stroke-width="4" fill="none" pathLength="1"/>'
                )
            continue
        parts.append(
            f'<path class="{p}-el {p}-link {p}-link-{svc}-{job}" style="--i:{i}" d="{d}" stroke="{colour}" '
            f'stroke-width="{width}" fill="none" stroke-linecap="round" pathLength="1"/>'
        )

    # halos behind jobs (hidden; slide CSS lights them)
    for key in ("export", "zonal", "normalise"):
        n = N[key]
        parts.append(
            f'<rect class="{p}-halo {p}-halo-{key}" x="{n.x - 10:.1f}" y="{n.y - 10:.1f}" '
            f'width="{n.w + 20:.1f}" height="{n.h + 20:.1f}" rx="{rx_job + 10}" fill="{BLUE_SOFT}" '
            f'stroke="{BLUE}" stroke-opacity="0.35" stroke-width="3" opacity="0"/>'
        )

    # nodes
    for key in ("in", "export", "zonal", "normalise", "out", "icechunk", "bq", "pg"):
        parts.append(node_svg(N[key], p, rx_job if N[key].kind == "job" else 16))
    if src_swap:
        s = N["src"]
        after = Node(s.key, s.x, s.y, s.w, s.h, "src-vic",
                     src_lines("src-vic", False), s.i)
        before = Node(s.key, s.x, s.y, s.w, s.h, "src-gee-red", src_lines("src-gee-red", False), s.i)
        parts.append(node_svg(before, p, 16, f"{p}-before"))
        parts.append(node_svg(after, p, 16, f"{p}-after"))
        # state chips left of the source box
        cx = s.x - 100
        for state, c, bg, label in (("before", RED, RED_BG, "before"), ("after", GREEN_DARK, GREEN_BG, "after")):
            parts.append(
                f'<g class="{p}-chip {p}-{state}"><rect x="{cx - 60:.1f}" y="{s.cy - 22:.1f}" width="120" '
                f'height="44" rx="22" fill="{bg}" stroke="{c}" stroke-width="2"/>'
                f'<text x="{cx:.1f}" y="{s.cy + 8:.1f}" text-anchor="middle" font-size="24" '
                f'font-weight="700" fill="{c}">{label}</text></g>'
            )
    else:
        parts.append(node_svg(N["src"], p, 16))

    # arrows
    for k, (a, b, i) in enumerate(L.arrows):
        parts.append(arrow_svg(a, b, i, p, k))

    # caption beneath-left of the source box (s09), clear of its link down to export
    if "refs-caption" in extras:
        s = N["src"]
        x, y = s.cx - 22, s.b + 44
        parts.append(
            f'<text class="{p}-caption" x="{x:.1f}" y="{y:.1f}" text-anchor="end" font-size="24" '
            f'font-weight="500" fill="{GREEN_DARK}">'
            f'<tspan x="{x:.1f}">references live with us;</tspan>'
            f'<tspan x="{x:.1f}" dy="31">bytes stay with the provider</tspan></text>'
        )

    # "rewriting" bracket under zonal + normalise (s19); slide CSS also dashes those boxes
    if "rewrite" in extras:
        zs, nm = N["zonal"], N["normalise"]
        gb = L.group[1] + L.group[3]
        y0, y1 = gb + 10, gb + 22
        mid = (zs.x + nm.r) / 2
        parts.append(
            f'<g class="{p}-rewrite">'
            f'<path d="M{zs.x + 4:.1f},{y0:.1f} V{y1:.1f} H{nm.r - 4:.1f} V{y0:.1f}" fill="none" stroke="{BLUE}" '
            f'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<rect x="{mid - 70:.1f}" y="{y1 - 4:.1f}" width="140" height="40" rx="20" fill="{BLUE}"/>'
            f'<text x="{mid:.1f}" y="{y1 + 24:.1f}" text-anchor="middle" font-size="24" font-weight="700" '
            f'fill="#FFFFFF">rewriting</text></g>'
        )

    # bottleneck marker (s19): red ring + pill on the export job; CSS slides it to zonal
    if "bottleneck" in extras:
        ex, zs = N["export"], N["zonal"]
        dx = zs.x - ex.x
        parts.append(
            f'<g class="{p}-bneck" style="--dx:{dx:.0f}px">'
            f'<rect x="{ex.x - 7:.1f}" y="{ex.y - 7:.1f}" width="{ex.w + 14:.1f}" height="{ex.h + 14:.1f}" '
            f'rx="{rx_job + 7}" fill="none" stroke="{RED}" stroke-width="6"/>'
            f'<rect x="{ex.cx - 82:.1f}" y="{ex.b - 14:.1f}" width="164" height="44" rx="22" fill="{RED}"/>'
            f'<text x="{ex.cx:.1f}" y="{ex.b + 16:.1f}" text-anchor="middle" font-size="24" font-weight="700" '
            f'fill="#FFFFFF">bottleneck</text></g>'
        )

    # target chip under the output (s19)
    if "target" in extras:
        o = N["out"]
        parts.append(
            f'<g class="{p}-target"><rect x="{o.cx - 92:.1f}" y="{o.b + 26:.1f}" width="184" height="52" '
            f'rx="26" fill="{GREEN_BG}" stroke="{GREEN}" stroke-width="3"/>'
            f'<text x="{o.cx:.1f}" y="{o.b + 61:.1f}" text-anchor="middle" font-size="28" font-weight="700" '
            f'fill="{GREEN_DARK}">≤ 5 minutes</text></g>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


# --------------------------------------------------------------------------
# slide 8: HVE pipe feeding four facility lanes, with a growing queue
# --------------------------------------------------------------------------
def factory(x: float, y: float, s: float, colour: str) -> str:
    """Small factory glyph, top-left at (x, y), roughly s x s."""
    pts = [(0, 1), (0, 0.42), (0.28, 0.6), (0.28, 0.42), (0.56, 0.6), (0.56, 0.12),
           (0.74, 0.12), (0.74, 0.05), (0.88, 0.05), (0.88, 0.12), (1, 0.12), (1, 1)]
    pts_s = " ".join(f"{x + px * s:.1f},{y + py * s:.1f}" for px, py in pts)
    return f'<polygon points="{pts_s}" fill="{colour}"/>'


def hve_svg(p: str = "s08") -> str:
    W, H = 1050, 470
    lanes = [110, 210, 310, 410]
    pipe_x0, pipe_x1, pipe_y, pipe_h = 190, 460, 228, 64
    src_x, src_w, src_h = 0, 170, 110
    act_x, act_w, act_h = 572, 92, 76
    q_x0, q_dx, q_w = 690, 66, 54
    n_queue = 5  # waiting blocks per lane

    out = [
        f'<svg class="{p}-hve" viewBox="0 0 {W} {H}" role="img" font-family="{FONT}" '
        f'aria-label="Earth Engine high-volume endpoint: 500 concurrent requests feeding four facility lanes, '
        f'with a growing queue of waiting facilities" xmlns="http://www.w3.org/2000/svg">'
    ]

    # column labels
    out.append(
        f'<text class="{p}-hve-cap" x="{act_x + act_w / 2:.0f}" y="40" text-anchor="middle" font-size="24" '
        f'font-weight="700" fill="{BLUE}">4 at a time</text>'
        f'<text class="{p}-hve-cap {p}-hve-waitcap" x="{q_x0 + ((n_queue - 1) * q_dx + q_w) / 2:.0f}" y="40" text-anchor="middle" '
        f'font-size="24" font-weight="700" fill="{MUTED}">waiting…</text>'
    )

    # source: Earth Engine
    sy = pipe_y + pipe_h / 2 - src_h / 2
    out.append(
        f'<g class="{p}-hve-src"><rect x="{src_x}" y="{sy:.0f}" width="{src_w}" height="{src_h}" rx="16" '
        f'fill="{RED_BG}" stroke="{RED}" stroke-width="3.5"/>'
        f'<text x="{src_x + src_w / 2:.0f}" y="{sy + 47:.0f}" text-anchor="middle" font-size="26" '
        f'font-weight="700" fill="{RED}">Earth</text>'
        f'<text x="{src_x + src_w / 2:.0f}" y="{sy + 80:.0f}" text-anchor="middle" font-size="26" '
        f'font-weight="700" fill="{RED}">Engine</text></g>'
    )

    # manifold: pipe end fans into four lanes
    py_mid = pipe_y + pipe_h / 2
    lane_paths = []
    for ly in lanes:
        d = (f"M{src_x + src_w},{py_mid} L{pipe_x1},{py_mid} "
             f"C{pipe_x1 + 60},{py_mid} {act_x - 70},{ly} {act_x},{ly}")
        lane_paths.append(d)
        out.append(
            f'<path d="M{pipe_x1 - 4},{py_mid} C{pipe_x1 + 60},{py_mid} {act_x - 70},{ly} {act_x},{ly}" '
            f'stroke="{RED}" stroke-opacity="0.55" stroke-width="10" fill="none" stroke-linecap="round"/>'
        )
    out.append(
        f'<line x1="{src_x + src_w}" y1="{py_mid}" x2="{pipe_x0}" y2="{py_mid}" stroke="{RED}" '
        f'stroke-opacity="0.55" stroke-width="10"/>'
    )

    # the pipe
    out.append(
        f'<g class="{p}-hve-pipe"><rect x="{pipe_x0}" y="{pipe_y}" width="{pipe_x1 - pipe_x0}" height="{pipe_h}" '
        f'rx="{pipe_h / 2}" fill="{RED_BG}" stroke="{RED}" stroke-width="4"/>'
        f'<text x="{(pipe_x0 + pipe_x1) / 2:.0f}" y="{pipe_y - 50}" text-anchor="middle" font-size="26" '
        f'font-weight="700" fill="{INK}">HVE</text>'
        f'<text x="{(pipe_x0 + pipe_x1) / 2:.0f}" y="{pipe_y - 18}" text-anchor="middle" font-size="24" '
        f'fill="{INK}">500 concurrent requests</text></g>'
    )

    # request dots (subtle SMIL loop: independent of slide timing, so it just keeps flowing)
    dots = []
    for li, d in enumerate(lane_paths):
        for k in range(3):
            begin = -(k * 0.6 + li * 0.15)
            dots.append(
                f'<circle r="6" fill="{RED}"><animateMotion dur="1.8s" repeatCount="indefinite" '
                f'begin="{begin:.2f}s" path="{d}"/></circle>'
            )
    out.append(f'<g class="{p}-hve-dots">' + "".join(dots) + "</g>")

    # active facility per lane
    for li, ly in enumerate(lanes):
        out.append(
            f'<g class="{p}-hve-active" style="--k:{li}"><rect x="{act_x}" y="{ly - act_h / 2}" width="{act_w}" '
            f'height="{act_h}" rx="14" fill="{BLUE}"/>'
            + factory(act_x + 24, ly - 22, 44, "#FFFFFF")
            + "</g>"
        )

    # queue: blocks join lane by lane, round-robin, so every lane's queue grows together
    t0, step = 1.6, 0.42
    for k in range(n_queue):
        for li, ly in enumerate(lanes):
            n = k * len(lanes) + li
            x = q_x0 + k * q_dx
            out.append(
                f'<g class="{p}-hve-wait" style="--d:{t0 + n * step:.2f}s">'
                f'<rect x="{x}" y="{ly - q_w / 2}" width="{q_w}" height="{q_w}" rx="12" fill="{CARD}" '
                f'stroke="{LINK}" stroke-width="2.5"/>'
                + factory(x + 13, ly - 14, 28, LINK)
                + "</g>"
            )
    # ellipsis beyond the queue
    for li, ly in enumerate(lanes):
        out.append(
            f'<text class="{p}-hve-more" style="--d:{t0 + (n_queue * 4 + li * 0.3) * step:.2f}s" '
            f'x="{q_x0 + n_queue * q_dx - 6}" y="{ly + 10}" font-size="36" font-weight="700" '
            f'fill="{LINK}">…</text>'
        )

    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------
def write(name: str, svg: str) -> None:
    path = GEN / name
    path.write_text(
        "<!-- generated by scripts/gen_pipeline.py; do not edit -->\n```{=html}\n" + svg + "\n```\n"
    )
    print(path.relative_to(ROOT))


def main() -> None:
    GEN.mkdir(parents=True, exist_ok=True)
    write("pipeline-s06.qmd", pipeline_svg(
        horizontal("src-gee"), "s06",
        aria="Pipeline: customer supply shed, then Prefect jobs on Kubernetes (export to icechunk, zonal stats, "
             "normalise to Postgres), then served to customer. Services: GEE, Icechunk, BigQuery, Postgres."))
    write("pipeline-s08.qmd", pipeline_svg(
        horizontal("src-gee", compact=True), "s08",
        aria="The same pipeline, with Earth Engine highlighted as the problem."))
    write("s08-hve.qmd", hve_svg("s08"))
    write("pipeline-s09.qmd", pipeline_svg(
        horizontal("src-gee-red", src_w=250), "s09", src_swap=True, extras=("refs-caption",),
        aria="The same pipeline: only the export step's source changes, from GEE to virtual icechunk with "
             "refs in GCS."))
    write("pipeline-s19.qmd", pipeline_svg(
        horizontal("src-vic"), "s19", extras=("bottleneck", "rewrite", "target"),
        aria="The pipeline with virtual icechunk as the source. The bottleneck moves from export to zonal "
             "stats; zonal stats and normalise are being rewritten; target five minutes or less."))


if __name__ == "__main__":
    main()
