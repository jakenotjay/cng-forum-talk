"""Slide 20: QR code to Epoch's open data on Source Coop, as an inline SVG (ink on transparent).

    uv run --project scripts python scripts/gen_s20_qr.py

Writes slides/_gen/s20-qr.qmd. One <path> of unit squares, so it scales crisply.
"""

from pathlib import Path

import qrcode

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "slides" / "_gen" / "s20-qr.qmd"
URL = "https://source.coop/epoch"
QUIET = 2  # modules; the slide's cream card adds more margin


def main() -> None:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=QUIET)
    qr.add_data(URL)
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    # Merge horizontal runs into one rect each to keep the path short
    d: list[str] = []
    for y, row in enumerate(m):
        x = 0
        while x < n:
            if row[x]:
                x1 = x
                while x < n and row[x]:
                    x += 1
                d.append(f"M{x1} {y}h{x - x1}v1h-{x - x1}z")
            else:
                x += 1
    svg = (
        f'<svg class="s20-qr" viewBox="0 0 {n} {n}" shape-rendering="crispEdges" '
        f'role="img" aria-label="QR code linking to {URL}">'
        f'<path fill="#0A1628" d="{"".join(d)}"/></svg>'
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("```{=html}\n" + svg + "\n```\n")
    print(OUT.relative_to(ROOT), f"{n}x{n} modules, version {qr.version}")


if __name__ == "__main__":
    main()
