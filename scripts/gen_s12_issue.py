"""Light-theme crop of VirtualiZarr issue #1078 for slide 12.

    uv run --project scripts python scripts/gen_s12_issue.py

Captures the issue title + author line and Tom Nicholas's comment (which links
#1111), and stacks the two crops into images/src/s12-issue.png.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images" / "src" / "s12-issue.png"
URL = "https://github.com/zarr-developers/VirtualiZarr/issues/1078"
COMMENT_ID = "issuecomment-5878245870"

VIEW_W = 460       # narrow layout: sidebar drops below, text is larger relative to the crop
SCALE = 2
TARGET_W = 1280    # final pixel width (about 2x its on-slide width)
GAP = 48           # px between the two crops in the composite, at SCALE

HIDE_CSS = """
header, .AppHeader, .js-header-wrapper, footer, .footer, #repository-container-header,
.cookie-consent-banner, [data-testid="cookie-banner"], .js-notification-shelf,
.flash-full, .signup-prompt-bg, [aria-label="Sign up for free"] { display: none !important; }
"""


def shot(page, box: dict) -> Image.Image:
    png = page.screenshot(clip=box, full_page=True)
    return Image.open(io.BytesIO(png)).convert("RGB")


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        ctx = browser.new_context(viewport={"width": VIEW_W, "height": 1000},
                                  device_scale_factor=SCALE, color_scheme="light")
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        page.add_style_tag(content=HIDE_CSS)
        # drop the "Last edited by ..." menus, which truncate in a narrow layout
        page.evaluate("""() => {
          for (const el of document.querySelectorAll('button, span, div')) {
            if (el.children.length < 4 && /^\\s*Last edited by/.test(el.textContent)) {
              (el.closest('button') || el).style.visibility = 'hidden';
            }
          }
        }""")
        page.wait_for_timeout(500)

        title = page.locator("[data-testid='issue-title']").first.bounding_box()
        body = page.locator("[data-testid='issue-body']").first.bounding_box()
        viewer = page.locator("[data-testid='issue-body-viewer']").first.bounding_box()
        # Tom Nicholas's comment: the outer comment box that contains the anchor id
        comment = page.locator(
            f"[data-testid^='comment-viewer-outer-box']:has([id='{COMMENT_ID}'])").first
        cb = comment.bounding_box()
        link = comment.locator("a", has_text="#1111").first.bounding_box()
        print("title", title, "body", body, "comment", cb)

        # title + state + labels + the author row of the opening post
        top = title["y"] - 10
        crop1 = shot(page, {"x": body["x"], "y": top,
                            "width": body["width"], "height": viewer["y"] - top + 1})
        crop2 = shot(page, {"x": cb["x"] - 1, "y": cb["y"] - 1,
                            "width": cb["width"] + 2, "height": cb["height"] + 2})
        browser.close()

    w = max(crop1.width, crop2.width)
    comp = Image.new("RGB", (w, crop1.height + GAP + crop2.height), "white")
    comp.paste(crop1, (0, 0))
    comp.paste(crop2, (0, crop1.height + GAP))
    # red ring around the #1111 link in the comment
    from PIL import ImageDraw
    dr = ImageDraw.Draw(comp)
    oy = crop1.height + GAP
    lx0 = (link["x"] - (cb["x"] - 1)) * SCALE
    ly0 = (link["y"] - (cb["y"] - 1)) * SCALE + oy
    pad = 4 * SCALE
    dr.rounded_rectangle((lx0 - pad, ly0 - pad * 0.6, lx0 + link["width"] * SCALE + pad,
                          ly0 + link["height"] * SCALE + pad * 0.6),
                         radius=8 * SCALE, outline="#D64545", width=3 * SCALE)
    # three dots marking the elided issue body
    cy = crop1.height + GAP // 2
    for k in (-1, 0, 1):
        cx = 40 * SCALE + k * 14 * SCALE
        dr.ellipse((cx - 4 * SCALE // 2, cy - 4 * SCALE // 2, cx + 4 * SCALE // 2, cy + 4 * SCALE // 2), fill="#9AA5B4")
    if comp.width > TARGET_W:
        h = round(comp.height * TARGET_W / comp.width)
        comp = comp.resize((TARGET_W, h), Image.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    comp.save(OUT, optimize=True)
    print(OUT.relative_to(ROOT), comp.size, OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
