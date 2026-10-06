"""Slide 4 (TRACE): brand-to-facility tree with three source chips.

    uv run --project scripts python scripts/gen_s04_trace.py

Writes slides/_gen/s04-trace.qmd, an inline SVG (viewBox 1600x680) inside a
```{=html} fence. Timing lives in styles/s04.scss; each element carries its
own delay in --d (seconds after the slide opens), so the schedule is set here.

The tree shows Tier 1 and Tier 2 solid, then two fading rows and dotted
connectors (tiers 3, 4, 5 ...) to say the chain can run 6-7 tiers deep before
it reaches Tier N, the mills and facilities.

Beats: brand 0.4 s, chips 1.0 s, Tier 1 / 2 at 2.0 / 3.4 s, fading tiers at
4.8 / 5.6 s, dotted continuation 6.2 s, Tier N at 7.2 s (dots fly from the
sources to each solid tier just before it appears, with a chip pulse), edges
trace blue at 8.2 s, facilities turn green from 8.6 s, all done by ~9.7 s.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "slides" / "_gen" / "s04-trace.qmd"

W, H = 1600, 680
CX = 790  # tree centre line

# rows: brand, T1, T2, T3 (fading), T4 (fading more), TN (facilities)
ROW_Y = [46, 160, 274, 384, 460, 616]
ROW_T = [0.4, 2.0, 3.4, 4.8, 5.6, 7.2]  # when each row's nodes land
CONT_T = 6.2  # dotted continuation between the fading rows and Tier N
DOT_ROWS = (1, 2, 5)  # rows that get flying source dots and a chip pulse
DOT_FLIGHT = 0.55  # seconds a dot takes from the sources to a node
GREEN_T = 8.6
GREEN_STEP = 0.05

T1 = [CX - 250, CX, CX + 250]
T2 = [CX + dx for dx in (-325, -195, -65, 65, 195, 325)]
T3 = [CX + dx for dx in range(-350, 351, 100)]  # 8, fading
T4 = [CX + dx for dx in range(-352, 353, 88)]  # 9, fading more
TN = [CX + dx for dx in range(-351, 352, 78)]  # 10 facilities

# (parent index, child index) per tier step; a few cross links so it reads as
# a network rather than a strict tree
E1 = [(0, 0), (0, 1), (0, 2)]
E2 = [(0, 0), (0, 1), (1, 2), (1, 3), (2, 4), (2, 5), (0, 2), (2, 3)]
E3 = [(0, 0), (0, 1), (1, 1), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), (4, 5), (5, 6), (5, 7), (1, 2)]
E4 = [(0, 0), (1, 1), (1, 2), (2, 3), (3, 3), (3, 4), (4, 5), (5, 5), (5, 6), (6, 7), (7, 8), (6, 6)]

# node (w, h) per row and the fading rows' opacity
NODE = {1: (76, 46), 2: (76, 46), 3: (66, 40), 4: (56, 34)}
FADE = {3: 0.55, 4: 0.26}
BRAND_W, BRAND_H = 230, 76
FAC_TOP = 26  # facility glyph extends this far above its row line

# Sources column
CHIP_X = 1262
CHIPS = ["web sources", "media", "proprietary sources"]
CHIP_Y = [212, 292, 372]
CHIP_H = 54
BRACKET_X = 1232
SRC = (1196, 292)  # arrow tip: dots launch from here


def chip_w(label: str) -> int:
    return int(len(label) * 14.2 + 48)


def edge_path(x0, y0, x1, y1) -> str:
    ym = (y0 + y1) / 2
    return f"M{x0:.0f},{y0:.0f} C{x0:.0f},{ym:.0f} {x1:.0f},{ym:.0f} {x1:.0f},{y1:.0f}"


def factory(x: float, y: float) -> str:
    """Factory glyph centred on (x, y), about 52 x 48."""
    pts = [(-26, 22), (-26, -2), (-12, -12), (-12, -2), (2, -12), (2, -2), (14, -10),
           (14, -26), (24, -26), (24, 22)]
    d = "M" + " L".join(f"{x + px:.0f},{y + py:.0f}" for px, py in pts) + " Z"
    return d


def main() -> None:
    parts: list[str] = []
    a = parts.append
    a(f'<svg class="s04-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
      f'role="img" aria-label="Tree from a brand down through up to six or seven tiers of suppliers '
      f'to mills, fed by web, media and proprietary sources">')

    rows = [[CX], T1, T2, T3, T4]
    edges = [None, E1, E2, E3, E4]

    # Dotted continuation fades in from the fading rows down to Tier N
    cont_top, cont_bot = ROW_Y[4] + NODE[4][1] / 2 + 14, ROW_Y[5] - FAC_TOP - 10
    a('<defs><linearGradient id="s04-cont-grad" gradientUnits="userSpaceOnUse" '
      f'x1="0" y1="{cont_top:.0f}" x2="0" y2="{cont_bot:.0f}">'
      '<stop offset="0" stop-color="#376FD0" stop-opacity="0"/>'
      '<stop offset="1" stop-color="#376FD0" stop-opacity="0.9"/></linearGradient></defs>')

    # --- tier labels (left column) ---
    labels = {1: ("Tier 1", "Manufacturers", ""), 2: ("Tier 2", "Traders & refiners", ""),
              3: ("Tier 3, 4, 5 …", "up to 6–7 tiers deep", " s04-label-cont"),
              5: ("Tier N", "Mills & facilities", " s04-label-final")}
    for k, (tier, name, extra) in labels.items():
        y = (ROW_Y[3] + ROW_Y[4]) / 2 if k == 3 else ROW_Y[k]
        a(f'<g class="s04-label s04-pop-fade{extra}" style="--d:{ROW_T[k]:.2f}s">'
          f'<text class="s04-tier" x="70" y="{y - 10:.0f}">{tier}</text>'
          f'<text class="s04-tiername" x="70" y="{y + 26:.0f}">{name}</text></g>')

    # --- edges (drawn as each child tier arrives); fading rows sit in faded groups ---
    for k in range(1, 5):
        prow, crow = rows[k - 1], rows[k]
        ph = BRAND_H if k == 1 else NODE[k - 1][1]
        ch = NODE[k][1]
        op = f' opacity="{FADE[k]}"' if k in FADE else ""
        a(f'<g class="s04-edges"{op}>')
        for pi, ci in edges[k]:
            d = edge_path(prow[pi], ROW_Y[k - 1] + ph / 2, crow[ci], ROW_Y[k] - ch / 2)
            delay = ROW_T[k] - 0.25 + ci * 0.04
            a(f'<path class="s04-edge" pathLength="1" d="{d}" style="--d:{delay:.2f}s"/>')
        a('</g>')

    # --- dotted continuation into each facility ---
    a(f'<g class="s04-pop-fade" style="--d:{CONT_T:.2f}s">')
    for x in TN:
        a(f'<path class="s04-cont" d="M{x},{cont_top:.0f} V{cont_bot:.0f}"/>')
    a('</g>')

    # --- source dots: fly from the sources' arrow tip to each new solid-tier node ---
    a('<g class="s04-dots">')
    for k in DOT_ROWS:
        row = TN if k == 5 else rows[k]
        for i, x in enumerate(row):
            launch = ROW_T[k] - DOT_FLIGHT + i * 0.04
            dx, dy = x - SRC[0], ROW_Y[k] - SRC[1]
            a(f'<circle class="s04-dot" cx="{SRC[0]}" cy="{SRC[1]}" r="8" '
              f'style="--d:{launch:.2f}s;--dx:{dx:.0f}px;--dy:{dy:.0f}px"/>')
    a('</g>')

    # --- nodes ---
    bx, by = CX, ROW_Y[0]
    a(f'<g class="s04-node s04-pop" style="--d:{ROW_T[0]:.2f}s">'
      f'<rect class="s04-brand" x="{bx - BRAND_W / 2:.0f}" y="{by - BRAND_H / 2:.0f}" '
      f'width="{BRAND_W}" height="{BRAND_H}" rx="16"/>'
      f'<text class="s04-brand-text" x="{bx}" y="{by + 10}" text-anchor="middle">CPG brand</text></g>')
    for k in (1, 2, 3, 4):
        nw, nh = NODE[k]
        op = f' opacity="{FADE[k]}"' if k in FADE else ""
        a(f'<g{op}>')
        for i, x in enumerate(rows[k]):
            delay = ROW_T[k] + i * 0.04
            a(f'<g class="s04-node s04-pop" style="--d:{delay:.2f}s">'
              f'<rect class="s04-mid" x="{x - nw / 2:.0f}" y="{ROW_Y[k] - nh / 2:.0f}" '
              f'width="{nw}" height="{nh}" rx="{nh * 0.26:.0f}"/></g>')
        a('</g>')
    for i, x in enumerate(TN):
        delay = ROW_T[5] + i * 0.04
        g = GREEN_T + i * GREEN_STEP
        a(f'<g class="s04-node s04-pop" style="--d:{delay:.2f}s">'
          f'<circle class="s04-halo" cx="{x}" cy="{ROW_Y[5]}" r="38" style="--g:{g:.2f}s"/>'
          f'<path class="s04-fac" d="{factory(x, ROW_Y[5])}" style="--g:{g:.2f}s"/></g>')

    # --- sources: label, chips, bracket and arrow into the tree ---
    a(f'<g class="s04-pop-fade" style="--d:1.0s">')
    a(f'<text class="s04-src-head" x="{CHIP_X}" y="{CHIP_Y[0] - 50}">Aggregated from</text>')
    top, bot = CHIP_Y[0], CHIP_Y[-1]
    a(f'<path class="s04-bracket" d="M{BRACKET_X + 18},{top} H{BRACKET_X} V{bot} H{BRACKET_X + 18} '
      f'M{BRACKET_X + 18},{CHIP_Y[1]} H{SRC[0] + 6}"/>')
    a(f'<path class="s04-arrow" d="M{SRC[0] + 14},{SRC[1] - 10} L{SRC[0]},{SRC[1]} L{SRC[0] + 14},{SRC[1] + 10} Z"/>')
    a('</g>')
    for j, (label, y) in enumerate(zip(CHIPS, CHIP_Y)):
        w = chip_w(label)
        # one pulse per solid tier, just before its dots launch
        halos = "".join(
            f'<rect class="s04-chip-halo" x="{CHIP_X - 6}" y="{y - CHIP_H / 2 - 6:.0f}" width="{w + 12}" '
            f'height="{CHIP_H + 12}" rx="{(CHIP_H + 12) / 2:.0f}" style="--p:{ROW_T[k] - DOT_FLIGHT - 0.3:.2f}s"/>'
            for k in DOT_ROWS)
        a(f'<g class="s04-chip s04-pop-fade" style="--d:{1.0 + j * 0.2:.2f}s">{halos}'
          f'<rect class="s04-chip-bg" x="{CHIP_X}" y="{y - CHIP_H / 2:.0f}" width="{w}" height="{CHIP_H}" rx="{CHIP_H / 2:.0f}"/>'
          f'<text class="s04-chip-text" x="{CHIP_X + w / 2:.0f}" y="{y + 9}" text-anchor="middle">{label}</text></g>')

    a('</svg>')
    svg = "\n".join(parts)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("```{=html}\n" + svg + "\n```\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
