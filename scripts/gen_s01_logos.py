"""Slide 1: single-colour logo masks.

The slide tints every logo to ink with a CSS filter that keeps only the alpha
channel (slides/_01-epoch.qmd, #s01-ink). That works for the SVG logos as-is,
but three PNGs carry opaque white or tinted fills that would turn into solid
blobs. This script rewrites the PNG logos as black-on-transparent alpha masks,
trimmed to their ink, into images/logos/s01-mono-*.png.

GAR is already tightly trimmed, but its ink is lopsided: the heavy square mark
sits on the left and the light "agribusiness and food" line trails off to the
right (ink centroid at 33% of the width vs about 45-50% for the other logos), so
centring its bounding box makes it read as sitting left of its column. OPTICAL
pads the left edge with transparency so the logo shifts part of the way towards
its ink centroid (k = 0.35 of the gap), which lines its left edge up with Altana
and Assent above and below it.

    uv run --project scripts python scripts/gen_s01_logos.py
"""

from pathlib import Path

import numpy as np
from PIL import Image

LOGOS = Path(__file__).resolve().parent.parent / "images" / "logos"


def lum(rgb: np.ndarray) -> np.ndarray:
    return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]) / 255


def ink_from_dark(a: np.ndarray, hi: float = 0.88, soft: float = 0.12) -> np.ndarray:
    """Anything darker than near-white becomes ink; white fills drop out."""
    rgb = a[..., :3].astype(float)
    alpha = a[..., 3].astype(float) / 255
    return alpha * np.clip((hi - lum(rgb)) / soft, 0, 1)


def ink_lujeri(a: np.ndarray) -> np.ndarray:
    """Lujeri: white letters + green leaves become ink, dark outline/shadow drops out,
    so the letters read as solid shapes knocked out from the leaves."""
    rgb = a[..., :3].astype(float)
    alpha = a[..., 3].astype(float) / 255
    L = lum(rgb)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    neutral = np.clip((30 - np.abs(g - r)) / 15, 0, 1)
    white = neutral * np.clip((L - 0.3) / 0.12, 0, 1)
    green = np.clip((g - np.maximum(r, b) - 30) / 20, 0, 1) * np.clip((g - 72) / 16, 0, 1)
    return alpha * np.maximum(white, green)


OPTICAL = {"gar": 0.35}  # share of the (bbox centre - ink centroid) gap to correct


def optical_pad(im: Image.Image, k: float) -> Image.Image:
    a = np.asarray(im)[..., 3].astype(float)
    cols = a.sum(0)
    centroid = (cols * np.arange(len(cols))).sum() / cols.sum()
    pad = round(2 * k * (len(cols) / 2 - centroid))  # padding p shifts the content by p/2
    if pad <= 0:
        return im
    out = Image.new("RGBA", (im.width + pad, im.height), (0, 0, 0, 0))
    out.paste(im, (pad, 0))
    return out


def write(name: str, mask: np.ndarray) -> None:
    out = np.zeros(mask.shape + (4,), np.uint8)
    out[..., 3] = np.round(mask * 255).astype(np.uint8)
    im = Image.fromarray(out, "RGBA")
    im = im.crop(im.getbbox())
    if name in OPTICAL:
        im = optical_pad(im, OPTICAL[name])
    path = LOGOS / f"s01-mono-{name}.png"
    im.save(path, optimize=True)
    print(path.name, im.size)


def main() -> None:
    sources = {
        "wwf": ("WWF_logo.png", ink_from_dark),
        "altana": ("Altana_logo.png", ink_from_dark),
        "sphera": ("Sphera-logo.png", ink_from_dark),
        "gar": ("GAR_logo.png", ink_from_dark),
        "lujeri": ("Lujeri_logo.png", ink_lujeri),
        "infor": ("Infor_logo.png", lambda a: a[..., 3].astype(float) / 255),
    }
    for name, (src, fn) in sources.items():
        a = np.array(Image.open(LOGOS / src).convert("RGBA"))
        write(name, fn(a))


if __name__ == "__main__":
    main()
