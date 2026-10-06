"""Slide 17: Earth Engine spend by month, Dec 2025 - Sep 2026, as an inline SVG bar chart.

    uv run --project scripts python scripts/gen_s17_chart.py

Data: CNG Utah 2026 fact sheet, section 8, "Monthly prod spend" table (Earth Engine
column, GBP thousands, read from the Cloud Billing chart, +/- 0.3k per bar).
No money values go on screen (spec section 2): bars are relative, with month labels only.
Writes slides/_gen/s17-chart.qmd; the animation lives in styles/s17.scss.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "slides" / "_gen" / "s17-chart.qmd"

# month, Earth Engine prod spend in GBP thousands (fact sheet section 8)
DATA = [
    ("Dec", 6.5),
    ("Jan", 9.8),
    ("Feb", 6.3),
    ("Mar", 1.1),
    ("Apr", 1.3),
    ("May", 4.2),
    ("Jun", 12.8),
    ("Jul", 3.7),
    ("Aug", 0.3),
    ("Sep", 0.1),
]
XARRAY_FROM = "Jul"   # the xarray export lane took over in July
SPIKE = "Jun"         # thumbnails + isochrones, not the pipeline
BEFORE = ("Dec", "Jan", "Feb")
AFTER = ("Aug", "Sep")

# Geometry, in viewBox units (rendered 1:1 on the 1600x900 canvas)
W, H = 1600, 740
BASE_Y = 640          # baseline
MAX_H = 520           # bar height for the tallest value
BAR_W = 100
STEP = 150
X0 = 40
R = 8                 # rounded top corners


def bar_path(x: float, y: float, w: float, h: float, r: float) -> str:
    r = min(r, h / 2, w / 2)
    return (
        f"M{x:.1f},{y + h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
        f"H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} V{y + h:.1f} Z"
    )


def mean(months: tuple[str, ...]) -> float:
    vals = dict(DATA)
    return sum(vals[m] for m in months) / len(months)


def main() -> None:
    months = [m for m, _ in DATA]
    scale = MAX_H / max(v for _, v in DATA)
    bx = {m: X0 + i * STEP for i, m in enumerate(months)}   # bar left edge
    top = {m: BASE_Y - max(v * scale, 3) for m, v in DATA}  # bar top

    before, after = mean(BEFORE), mean(AFTER)
    drop = 1 - after / before
    pct = round(drop * 100)

    parts: list[str] = []
    lane = False
    for i, (month, v) in enumerate(DATA):
        lane = lane or month == XARRAY_FROM
        kind = "spike" if month == SPIKE else ("after" if lane else "before")
        x, y = bx[month], top[month]
        cx = x + BAR_W / 2
        delay = 0.2 + i * 0.42
        parts.append(
            f'  <g class="s17-col s17-{kind}" style="--d:{delay:.2f}s">\n'
            f'    <path class="s17-bar" d="{bar_path(x, y, BAR_W, BASE_Y - y, R)}"/>\n'
            f'    <text class="s17-month" x="{cx:.1f}" y="{BASE_Y + 44}">{month}</text>\n'
            f"  </g>"
        )

    baseline = (
        f'  <line class="s17-axis" x1="{X0 - 20}" y1="{BASE_Y}" '
        f'x2="{bx[months[-1]] + BAR_W + 20}" y2="{BASE_Y}"/>'
    )

    # Annotation 1 (6 s): the June spike, text to its left with a short leader
    sx, sy = bx[SPIKE], top[SPIKE]
    note_x = sx - 64
    spike = (
        f'  <g class="s17-note" style="--d:6s">\n'
        f'    <line class="s17-leader" x1="{note_x + 12}" y1="{sy + 22}" x2="{sx - 10}" y2="{sy + 22}"/>\n'
        f'    <text class="s17-note-t" x="{note_x}" y="{sy + 14}">thumbnails + isochrones,</text>\n'
        f'    <text class="s17-note-t" x="{note_x}" y="{sy + 48}">since moved off EE</text>\n'
        f"  </g>"
    )

    # Annotation 2 (7 s): xarray-lane marker in the gap before July, chip as a flag
    mx = bx[XARRAY_FROM] - (STEP - BAR_W) / 2
    chip_w, chip_h, chip_y = 196, 52, 414
    marker = (
        f'  <g class="s17-marker">\n'
        f'    <line class="s17-marker-line" x1="{mx:.1f}" y1="{BASE_Y + 8}" x2="{mx:.1f}" y2="{chip_y}"/>\n'
        f'    <rect class="s17-chip" x="{mx:.1f}" y="{chip_y}" width="{chip_w}" height="{chip_h}" rx="{chip_h / 2}"/>\n'
        f'    <text class="s17-chip-text" x="{mx + chip_w / 2:.1f}" y="{chip_y + chip_h / 2 + 9}">xarray lane</text>\n'
        f"  </g>"
    )

    # Annotation 3 (8 s): the two comparison windows' averages. The winter level runs on,
    # faintly, to the right edge, and a green arrow drops from it to the late-summer level.
    y_before = BASE_Y - before * scale
    y_after = BASE_Y - after * scale
    ax = W - 60
    avgs = "\n".join(
        [
            '  <g class="s17-avgs">',
            f'    <line class="s17-avg s17-avg-before" x1="{bx[BEFORE[0]] - 14}" y1="{y_before:.1f}" '
            f'x2="{bx[BEFORE[-1]] + BAR_W + 14}" y2="{y_before:.1f}"/>',
            f'    <line class="s17-avg s17-avg-after" x1="{bx[AFTER[0]] - 14}" y1="{y_after:.1f}" x2="{ax}" y2="{y_after:.1f}"/>',
            f'    <line class="s17-drop" x1="{ax}" y1="{y_before + 8:.1f}" x2="{ax}" y2="{y_after - 26:.1f}"/>',
            f'    <path class="s17-drop-head" d="M{ax - 14},{y_after - 30:.1f} L{ax + 14},{y_after - 30:.1f} L{ax},{y_after - 8:.1f} Z"/>',
            "  </g>",
        ]
    )

    # Big relative label (9 s), top right above the short late-summer bars
    ghost = (
        f'  <g class="s17-avgs">\n'
        f'    <line class="s17-avg-ghost" x1="{bx[BEFORE[-1]] + BAR_W + 14}" y1="{y_before:.1f}" x2="{ax}" y2="{y_before:.1f}"/>\n'
        f"  </g>"
    )

    big_x = ax + 8
    big = (
        f'  <g class="s17-big">\n'
        f'    <text class="s17-big-num" x="{big_x}" y="150">↓ {pct}%</text>\n'
        f'    <text class="s17-big-sub" x="{big_x}" y="204">Aug–Sep vs Dec–Feb</text>\n'
        f'    <text class="s17-source" x="{big_x}" y="242">monthly average, prod Cloud Billing</text>\n'
        f"  </g>"
    )

    svg = "\n".join(
        [
            f'<svg class="s17-chart" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Bar chart: Earth Engine spend by month, December 2025 to September 2026, '
            f"relative heights only. Spike in June from thumbnails and isochrones, since moved off "
            f'Earth Engine. After the xarray lane in July, August to September average is {pct}% '
            f'below December to February.">',
            ghost,  # behind the bars
            *parts,
            baseline,
            avgs,
            spike,
            marker,
            big,
            "</svg>",
        ]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("```{=html}\n" + svg + "\n```\n")
    print(
        OUT.relative_to(ROOT),
        f"Dec-Feb mean {before:.3f}, Aug-Sep mean {after:.3f}, ratio {after / before:.4f}, "
        f"drop {drop:.2%} -> {pct}%",
    )


if __name__ == "__main__":
    main()
