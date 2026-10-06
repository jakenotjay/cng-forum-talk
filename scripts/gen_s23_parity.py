"""Slide 23: Earth Engine vs virtual cube vs difference, from real cached data.

    uv run --project scripts python scripts/gen_s23_parity.py

Input: ``images/src/s23-tmf-parity.npz`` (written by ``gen_s23_extract.py`` from
epoch-mono's local parity cache; no Earth Engine call). The band is the JRC TMF
deforestation year in the production ``eudrCompliance`` composite, on the EUDR
golden tile near Novo Progresso, Para (-55.525, -7.225, -55.475, -7.175),
512 x 512 px x 8 annual slices (2019-2026).

Writes images/gen/s23-ee.png, s23-xr.png, s23-diff.png (each year slice
collapsed to one "year of deforestation" map) and asserts the two sides are
identical on every slice.
"""

from pathlib import Path

import numpy as np
from matplotlib import colormaps
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "images" / "src" / "s23-tmf-parity.npz"
OUT = ROOT / "images" / "gen"

YEARS = list(range(2019, 2026))  # 2026 slice is empty on this tile
BG = (236, 231, 220)  # no deforestation
SCALE = 2  # nearest-neighbour upscale so the browser never smooths pixels


def hexrgb(rgb) -> tuple[int, int, int]:
    return tuple(int(round(c * 255)) for c in rgb[:3])


def year_colours() -> dict[int, tuple[int, int, int]]:
    cmap = colormaps["magma"]
    stops = np.linspace(0.86, 0.22, len(YEARS))  # older = lighter, recent = darker
    return {y: hexrgb(cmap(s)) for y, s in zip(YEARS, stops, strict=True)}


def collapse(stack: np.ndarray) -> np.ndarray:
    """(time, y, x) year-or-0 -> (y, x) year of deforestation, 0 where none."""
    return stack.max(axis=0)


def render(year_map: np.ndarray, colours, path: Path) -> None:
    img = np.empty((*year_map.shape, 3), dtype=np.uint8)
    img[:] = BG
    for y, c in colours.items():
        img[year_map == y] = c
    Image.fromarray(img).resize(
        (year_map.shape[1] * SCALE, year_map.shape[0] * SCALE), Image.NEAREST
    ).save(path, optimize=True)


def main() -> None:
    d = np.load(SRC)
    ee, xr = d["ee_tmf"], d["xr_tmf"]
    assert ee.shape == xr.shape == (8, 512, 512)
    n_diff = int((ee != xr).sum())
    print(f"pixels compared: {ee.size:,}  differ: {n_diff}")
    assert n_diff == 0

    colours = year_colours()
    render(collapse(ee), colours, OUT / "s23-ee.png")
    render(collapse(xr), colours, OUT / "s23-xr.png")

    # Difference map: faint where either side has data (what was compared),
    # red where they disagree (none).
    either = (ee > 0).any(axis=0) | (xr > 0).any(axis=0)
    differ = (ee != xr).any(axis=0)
    img = np.empty((512, 512, 3), dtype=np.uint8)
    img[:] = (226, 241, 230)
    img[either] = (196, 222, 203)
    img[differ] = (214, 69, 69)
    Image.fromarray(img).resize((512 * SCALE, 512 * SCALE), Image.NEAREST).save(
        OUT / "s23-diff.png", optimize=True
    )

    for y, c in colours.items():
        print(y, "#%02X%02X%02X" % c, int((collapse(ee) == y).sum()))


if __name__ == "__main__":
    main()
