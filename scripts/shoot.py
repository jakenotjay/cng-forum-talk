"""Screenshot rendered slides at given moments, for review.

    uv run --project scripts python scripts/shoot.py --slide 7 --at 1,7,14

Serves docs/ over HTTP, opens each slide with auto-advance off, and saves
design/review/sNN-tX.png at each timestamp (seconds after the slide opens).
Run scripts/render.sh first.
"""

import argparse
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "design" / "review"


def serve() -> int:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
    handler.log_message = lambda *a, **k: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd.server_address[1]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slide", required=True, help="slide positions (0 = title), e.g. 7 or 1,2,3 or 1-20")
    p.add_argument("--at", default="1,7,14", help="seconds after the slide opens")
    args = p.parse_args()

    slides: list[int] = []
    for part in args.slide.split(","):
        a, _, b = part.partition("-")
        slides += list(range(int(a), int(b or a) + 1))
    times = sorted(float(t) for t in args.at.split(","))

    OUT.mkdir(parents=True, exist_ok=True)
    port = serve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        for n in slides:
            # Slides are addressed by position (0 = title), so reordering the
            # deck in index.qmd never breaks this. Entering the slide fresh
            # starts its .present animations from zero.
            page.goto(f"http://127.0.0.1:{port}/index.html?autoSlide=0")
            page.wait_for_load_state("networkidle")
            page.evaluate(f"() => {{ Reveal.slide({n + 1 if n == 0 else n - 1}); Reveal.slide({n}); }}")
            page.wait_for_timeout(50)
            elapsed = 0.0
            for t in times:
                page.wait_for_timeout(int((t - elapsed) * 1000))
                elapsed = t
                path = OUT / f"s{n:02d}-t{t:g}.png"
                page.screenshot(path=str(path))
                print(path.relative_to(ROOT))
        browser.close()


if __name__ == "__main__":
    main()
