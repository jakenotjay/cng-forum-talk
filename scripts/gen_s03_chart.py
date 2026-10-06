"""Slide 3: the Indonesian palm oil long tail, redrawn as an inline SVG bar chart.

    uv run --project scripts python scripts/gen_s03_chart.py           # linear y (default)
    uv run --project scripts python scripts/gen_s03_chart.py --log     # log y, for comparison
    uv run --project scripts python scripts/gen_s03_chart.py --redigitise

DATA PROVENANCE (read this before quoting a number off the chart)
-----------------------------------------------------------------
The per-mill values are not available locally (they live in BigQuery,
epoch-geospatial-dev.wwf_codex_palm.facility_period.noncompliance_area_ha, which
needs an interactive gcloud login). So the bars are DIGITISED from Figure 13 of
"Codex Planetarius Pilot Study: Palm in Paradise - A Supply Shed Analysis of
Indonesian Palm Oil" (Epoch, December 2025, page 21 / PDF page 22): the embedded
1475x615 raster "Noncompliance Area Ha by Facility (Highest to Lowest)".

Method: the y scale comes from the chart's own gridlines (0-8,000 ha, 18.0 ha per
pixel); the x scale comes from its 5th/25th/50th/75th/95th percentile lines (1,355
px for 100% of mills). Each pixel column's bar top is read off the raster, then
the curve is resampled to one bar per mill (1,290 mills, the report's "Total
facilities processed"), preserving the total area, and sorted highest to lowest.

Checks against numbers printed in the report (run with --redigitise to see them):
  total noncompliance area   digitised ~192,800 ha  vs report 192,192 ha (140,685 / 73.2%)
  share held by the worst 5% digitised ~72.8%       vs report 73.2%
Resolution: one pixel is ~18 ha, so values under ~20 ha (about half the mills)
are at the limit of what the raster can resolve. The shape is faithful; individual
small values are not.

Writes images/src/s03-fig13-digitised.csv (rank, noncompliance_ha) and
slides/_gen/s03-chart.qmd. Animation lives in styles/s03.scss.
"""

import argparse
import csv
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PDF = Path.home() / "epoch/epoch-mono/ts/apps/epoch-astro/public/static/whitepapers" / (
    "Codex Plantarius Pilot Phase Report_Epoch Analysis of Indonesian Palm Oil.pdf"
)
PAGE = 22  # 1-based PDF page: "4.3 Deforestation", Figure 13
CSV = ROOT / "images" / "src" / "s03-fig13-digitised.csv"
OUT = ROOT / "slides" / "_gen" / "s03-chart.qmd"

N_MILLS = 1290  # report section 4.2.1, "Total facilities processed"
REPORT_TOTAL_HA = 140_685 / 0.732  # worst-5% area / its share, report table p.36
WORST = 0.05
PERCENTILES = (0.05, 0.25, 0.50)

# Chart geometry, in viewBox units (rendered 1:1 inside the card)
W, H = 1010, 640
PX0, PX1 = 150, 975  # plot x range
PY0, PY1 = 128, 612  # plot y range (top, baseline)


# --------------------------------------------------------------------------- digitise
def digitise() -> np.ndarray:
    import pymupdf
    from PIL import Image

    doc = pymupdf.open(PDF)
    page = doc[PAGE - 1]
    # Two rasters on the page: the map (top) and the bar chart (bottom).
    info = max(page.get_image_info(xrefs=True), key=lambda i: i["bbox"][1])
    pix = pymupdf.Pixmap(doc, info["xref"])
    if pix.n - pix.alpha > 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    a = np.asarray(img).astype(float)
    assert a.shape[:2] == (615, 1475), a.shape

    sat = a.max(-1) - a.min(-1)
    grey = a.mean(-1)

    # y: gridline rows at 8,000 ... 1,000 ha (measured on the raster)
    grid_rows = np.array([126, 181.5, 237, 292, 348, 403, 458.5, 514])
    k, _ = np.polyfit(grid_rows, np.arange(8000, 999, -1000), 1)
    ha_per_px = -k  # ~18.05

    # x: bars start at column 92; the 5th..95th percentile lines put 100% at 1,355 px
    x0, span = 92, 1355
    cols = np.arange(x0, x0 + span + 1)
    top_row, base_row = 100, 570  # bars sit on row 569

    s = sat[top_row:base_row, cols].copy()
    s[s < 12] = 0  # compression noise
    # Percentile lines (and their antialiasing) run the full height: skip and interpolate
    band = ((sat[330:520, cols] > 12) | (grey[330:520, cols] < 215)).sum(0)
    bad = (band > 50) & (cols > 140)
    bad = np.convolve(bad, np.ones(7), "same") > 0

    colmax = s.max(0)
    tall = (s > 0.8 * colmax).sum(0) >= 3
    h = np.zeros(len(cols))
    for i in range(len(cols)):
        if tall[i] and not bad[i]:
            ref = colmax[i]
        else:  # bar under ~3 px: take the fill colour from taller neighbours
            lo, hi = max(0, i - 40), i + 41
            m = tall[lo:hi] & ~bad[lo:hi]
            ref = np.median(colmax[lo:hi][m]) if m.any() else 185.0
        c = np.clip(s[::-1, i] / ref, 0, 1)  # from the baseline upwards
        stop = np.nonzero(c < 0.5)[0]
        n = stop[0] if len(stop) else len(c)
        h[i] = n + (c[n] if n < len(c) else 0)  # full pixels + the partial top one
    h[bad] = np.interp(cols[bad], cols[~bad], h[~bad])
    per_px = h * ha_per_px  # ha at each pixel column

    # Resample to one bar per mill, preserving area: integrate, then difference
    edges_px = np.linspace(0, span + 1, N_MILLS + 1)
    cum = np.concatenate([[0], np.cumsum(per_px)])
    per_mill = np.diff(np.interp(edges_px, np.arange(len(cum)), cum)) / np.diff(edges_px)
    per_mill = np.sort(per_mill)[::-1]

    total = per_mill.sum()
    worst = per_mill[: math.ceil(N_MILLS * WORST)].sum()
    print(f"digitised total {total:,.0f} ha (report {REPORT_TOTAL_HA:,.0f}), "
          f"worst 5% share {worst / total:.1%} (report 73.2%), max {per_mill[0]:,.0f} ha")
    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank", "noncompliance_ha"])
        for r, v in enumerate(per_mill, 1):
            w.writerow([r, f"{v:.1f}"])
    print(CSV.relative_to(ROOT), len(per_mill), "rows")
    return per_mill


def load() -> np.ndarray:
    with CSV.open() as f:
        return np.array([float(r["noncompliance_ha"]) for r in csv.DictReader(f)])


# --------------------------------------------------------------------------- draw
def fmt(v: float) -> str:
    return f"{v:,.0f}"


def build(vals: np.ndarray, log: bool) -> str:
    n = len(vals)
    bw = (PX1 - PX0) / n
    if log:
        lo, hi = 1.0, 10_000.0
        ticks = [1, 10, 100, 1_000, 10_000]

        def y(v: float) -> float:
            v = max(v, lo)
            return PY1 - (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (PY1 - PY0)
    else:
        hi = 9_000.0
        ticks = [0, 2_000, 4_000, 6_000, 8_000]

        def y(v: float) -> float:
            return PY1 - v / hi * (PY1 - PY0)

    def bars_path(i0: int, i1: int) -> str:
        """One closed step path for bars i0..i1-1 (sub-pixel bars read as one area)."""
        pts = [f"M{PX0 + i0 * bw:.2f},{PY1}"]
        for i in range(i0, i1):
            yy = y(vals[i])
            pts.append(f"V{yy:.2f}H{PX0 + (i + 1) * bw:.2f}")
        pts.append(f"V{PY1}Z")
        return "".join(pts)

    k = math.ceil(n * WORST)
    out: list[str] = []
    out.append(
        f'<svg class="s03-chart" viewBox="0 0 {W} {H}" role="img" aria-label="Bar chart: '
        f"noncompliance area for {n:,} Indonesian palm oil mills, ranked highest to lowest"
        f'{" on a log scale" if log else ""}. The worst 5% of mills hold almost all of it; '
        f'the median mill is near zero.">'
    )
    # Title + axis label (static, fade in with the card)
    out.append(
        f'  <text class="s03-title" x="0" y="40">Noncompliance area of {n:,} palm oil mills, '
        f"ranked highest to lowest</text>"
    )
    out.append(
        f'  <text class="s03-ylab" transform="translate(22 {(PY0 + PY1) / 2:.0f}) rotate(-90)">'
        f"Noncompliance area (ha{', log scale' if log else ''})</text>"
    )
    # Grid + ticks
    out.append('  <g class="s03-grid">')
    for t in ticks:
        yy = y(t)
        cls = "s03-base" if (t == 0 or (log and t == ticks[0])) else "s03-gl"
        out.append(f'    <line class="{cls}" x1="{PX0}" y1="{yy:.1f}" x2="{PX1}" y2="{yy:.1f}"/>')
        out.append(f'    <text class="s03-tick" x="{PX0 - 14}" y="{yy + 8:.1f}">{fmt(t)}</text>')
    out.append("  </g>")
    # 5% band (behind the bars), shown with the highlight
    bx1 = PX0 + k * bw
    out.append(
        f'  <rect class="s03-band" x="{PX0 - 4}" y="{PY0 - 6}" width="{bx1 - PX0 + 8:.1f}" '
        f'height="{PY1 - PY0 + 6}" rx="8"/>'
    )
    # Bars: the worst 5% and the rest, so the highlight can recolour the first group
    out.append('  <g class="s03-bars">')
    out.append(f'    <path class="s03-rest" d="{bars_path(k, n)}"/>')
    out.append(f'    <path class="s03-worst" d="{bars_path(0, k)}"/>')
    out.append("  </g>")
    # Percentile markers
    for j, p in enumerate(PERCENTILES):
        x = PX0 + p * (PX1 - PX0)
        cls = "s03-pct s03-pct-5" if p == WORST else "s03-pct"
        label = f"{round(p * 100)}th percentile"
        out.append(
            f'  <g class="{cls}" style="--d:{3.4 + j * 0.45:.2f}s">'
            f'<line x1="{x:.1f}" y1="{PY0 - 22}" x2="{x:.1f}" y2="{PY1}"/>'
            f'<text x="{x:.1f}" y="{PY0 - 32}">{label}</text></g>'
        )
    # Highlight label beside the band
    out.append(
        f'  <g class="s03-hl"><text class="s03-hl-t" x="{bx1 + 20:.1f}" y="{PY0 + 76}">worst 5%</text>'
        f'<text class="s03-hl-t" x="{bx1 + 20:.1f}" y="{PY0 + 108}">of mills</text></g>'
    )
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", action="store_true", help="log y axis")
    ap.add_argument("--redigitise", action="store_true", help="re-read Figure 13 from the PDF")
    args = ap.parse_args()
    vals = digitise() if args.redigitise or not CSV.exists() else load()
    svg = build(vals, args.log)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("```{=html}\n" + svg + "\n```\n")
    print(OUT.relative_to(ROOT), "log" if args.log else "linear")


if __name__ == "__main__":
    main()
