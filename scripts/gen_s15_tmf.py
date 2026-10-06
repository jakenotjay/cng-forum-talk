"""Slide 15: capture the JRC TMF tile-download page (map + one clicked tile).

    uv run --project scripts python scripts/gen_s15_tmf.py

Opens https://forobs.jrc.ec.europa.eu/TMF/data in system Chrome, declines
non-essential cookies, clicks the N10_E90 tile (Sumatra / Malay peninsula) so
its list of per-file download links shows, and crops the map plus that list.
Writes images/src/s15-tmf.png and prints the clicked tile's box as % of the
crop, for the red ring on the slide.
"""

import io
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images" / "src" / "s15-tmf.png"
URL = "https://forobs.jrc.ec.europa.eu/TMF/data"
TILE = "N10_E90"
DPR = 2


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1440, "height": 1300}, device_scale_factor=DPR)
        page.goto(URL, wait_until="networkidle", timeout=90_000)
        try:
            page.get_by_text("Accept only essential cookies").click(timeout=5000)
        except Exception:
            pass
        tile = page.locator(f'.tile[title="{TILE}"]')
        tile.scroll_into_view_if_needed()
        tile.click()
        page.wait_for_timeout(1500)
        page.evaluate(
            "window.scrollTo(0, document.querySelector('#map').getBoundingClientRect().top + scrollY - 40)"
        )
        page.wait_for_timeout(800)
        n_tiles = page.locator(".tile").count()
        mapbox = page.locator("#map").bounding_box()
        tbox = tile.bounding_box()
        last = page.locator("#map").get_by_text("Undisturbed and degraded").first.bounding_box()
        x0, x1 = mapbox["x"] - 6, mapbox["x"] + mapbox["width"] + 6
        y0 = mapbox["y"] + 150
        y1 = last["y"] + last["height"] + 14
        png = page.screenshot(clip={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0})
        browser.close()

    im = Image.open(io.BytesIO(png)).convert("RGB")
    # Mostly flat page colours: a 64-colour palette keeps it crisp and small.
    im = im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, optimize=True)
    w, h = x1 - x0, y1 - y0
    print(f"wrote {OUT.relative_to(ROOT)} {im.size} {OUT.stat().st_size / 1024:.0f} KiB; {n_tiles} tiles on map")
    print(
        "tile ring %: left={:.2f} top={:.2f} width={:.2f} height={:.2f}".format(
            100 * (tbox["x"] - x0) / w,
            100 * (tbox["y"] - y0) / h,
            100 * tbox["width"] / w,
            100 * tbox["height"] / h,
        )
    )
    print(f"aspect {w / h:.4f}")


if __name__ == "__main__":
    main()
