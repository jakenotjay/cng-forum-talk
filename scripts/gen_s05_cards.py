"""Slide 5 (process): crop the five stage images (plus the AlphaEarth inset).

    uv run --project scripts python scripts/gen_s05_cards.py

Reads the London source rasters from ~/projects/cng-talk/inputs/ (copied to
images/src/ on first run so the deck repo keeps its own sources) and writes
web-sized JPGs to images/gen/s05-stageN.jpg at 2x the on-screen card size.
Cards are 4:3 (like the London process sheet) so each subject sits fully in
frame. A crop box is either cover-cropped to 4:3 ("cover") or, when the whole
subject is squarer than 4:3 (Sumatra's points, the supply shed), fitted
inside the card over a blurred, darkened copy of itself ("fit"). Boxes skip
the basemap attribution and the Forest Data Partnership watermark.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
LONDON = Path.home() / "projects" / "cng-talk" / "inputs"
SRC = ROOT / "images" / "src"
GEN = ROOT / "images" / "gen"

# On-screen card image is 360 x 270 (see styles/s05.scss); export at 2x.
CARD_W, CARD_H = 720, 540
INSET = 400  # square inset, shown at ~132 px

# key -> (London input name, local source name, crop box in source pixels (l, t, r, b), mode)
# where mode is "cover" (cover-crop to 4:3) or a float: fit, padding dimmed by that factor
SOURCES = {
    # all of Sumatra's points, top tip to the southern ones; fitted (padding is sea)
    "stage1": ("stage1_locations_src.jpeg", "s05-stage1-src.jpeg", (0, 20, 1435, 1218), 1.0),
    # the whole mill: settling ponds, sheds, bare pad; AlphaEarth inset sits top right over forest
    "stage2": ("stage2_facility_src.png", "s05-stage2-src.png", (110, 120, 1000, 788), "cover"),
    "stage2-inset": ("stage2_embedding_src.png", "s05-stage2-inset-src.png", (120, 120, 880, 880), "cover"),
    # the whole shed, every lobe; fitted (padding is blurred forest)
    "stage3": ("stage3_supply_shed_src.png", "s05-stage3-src.png", (0, 0, 1167, 1207), 0.62),
    # plots and village grid, below the FDP watermark and above the "tomatic" credit
    "stage4": ("stage4_plots_src.png", "s05-stage4-src.png", (0, 168, 1000, 918), "cover"),
    # the whole concession block and its dark forest ring
    "stage5": ("stage5_metrics_src.png", "s05-stage5-src.png", (0, 130, 2024, 1648), "cover"),
}


def cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    """Centre cover-crop to exactly tw x th."""
    w, h = im.size
    s = max(tw / w, th / h)
    nw, nh = round(w * s), round(h * s)
    im = im.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - tw) // 2, (nh - th) // 2
    return im.crop((l, t, l + tw, t + th))


def fit(im: Image.Image, tw: int, th: int, dim: float) -> Image.Image:
    """Fit the whole image inside tw x th. The side padding is the image's own
    edge, mirrored and blurred (dimmed by `dim`), and the image is feathered
    into it so there is no hard seam."""
    w, h = im.size
    s = min(tw / w, th / h)
    fg = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    px, py = (tw - fg.width) // 2, (th - fg.height) // 2
    a = np.asarray(fg)
    pad = ((py, th - fg.height - py), (px, tw - fg.width - px), (0, 0))
    bg = Image.fromarray(np.pad(a, pad, mode="symmetric"))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(14))).enhance(dim)
    # feathered mask: opaque inside, ramping to 0 over `f` px at the fitted edges
    f = 28
    xs = np.arange(fg.width, dtype=float)
    ys = np.arange(fg.height, dtype=float)
    rx = np.clip(np.minimum(xs, fg.width - 1 - xs) / f, 0, 1) if px else np.ones_like(xs)
    ry = np.clip(np.minimum(ys, fg.height - 1 - ys) / f, 0, 1) if py else np.ones_like(ys)
    mask = Image.fromarray((np.outer(ry, rx) * 255).astype(np.uint8))
    bg.paste(fg, (px, py), mask)
    return bg


def main() -> None:
    SRC.mkdir(parents=True, exist_ok=True)
    GEN.mkdir(parents=True, exist_ok=True)
    for key, (london_name, local_name, box, mode) in SOURCES.items():
        local = SRC / local_name
        if not local.exists():
            shutil.copy2(LONDON / london_name, local)
        im = Image.open(local).convert("RGB").crop(box)
        if key == "stage3":
            # The shed's southern tip reaches the bottom edge, so paint over the
            # basemap credit in the corner with the forest just above it.
            im.paste(im.crop((1020, 1166, 1167, 1186)), (1020, 1187))
        if key == "stage2-inset":
            out = cover(im, INSET, INSET)
        else:
            out = cover(im, CARD_W, CARD_H) if mode == "cover" else fit(im, CARD_W, CARD_H, mode)
            # The London sources are a touch dark on a cream slide; lift slightly.
            out = ImageEnhance.Brightness(out).enhance(1.06)
        path = GEN / f"s05-{key}.jpg"
        out.save(path, quality=86, optimize=True, progressive=True)
        print(f"{path.relative_to(ROOT)}  {out.size[0]}x{out.size[1]}  {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
