"""Slide 23 data: extract the EE-vs-virtual TMF band from epoch-mono's parity cache.

Run from epoch-mono (it needs that workspace's sco2api environment), not from here:

    cd ~/epoch/epoch-mono/py && uv run --no-sync --package sco2api python \\
        ~/epoch/cng-forum-talk/scripts/gen_s23_extract.py

It makes no Earth Engine or cloud calls. Both sides come from the local
``epoch-mono/.golden-cache/``:

* Earth Engine: ``eudr_golden.zarr``, the production ``eudrCompliance`` composite
  computed in Earth Engine (skip_ccdc, skip_radd) over the golden tile
  (-55.525, -7.225, -55.475, -7.175), Para, Brazil; 512 x 512 px x 8 years.
* Virtual: the EE-free getter (``parity.run_fusion``) run over the cached raw
  sources in ``sources_zarr/`` (read once from the virtual stores by
  ``tests/tools/parity.py``).

Writes ``images/src/s23-tmf-parity.npz`` (int16, NaN encoded as 0; the band is
NaN wherever there is no deforestation that year, so the encoding is lossless).
"""

from pathlib import Path

import numpy as np
import xarray as xr
from epoch.sco2api.tests.tools import golden_cache, parity

OUT = Path.home() / "epoch" / "cng-forum-talk" / "images" / "src" / "s23-tmf-parity.npz"


def main() -> None:
    grid, region = parity.build_region()
    sources = parity.load_sources(grid, region, refresh=False)
    xr_ds = parity.run_fusion(grid, region, sources)
    ee = xr.open_zarr(golden_cache.golden_zarr()).compute()

    x = xr_ds["tmf"].values.astype("float32")
    e = ee["tmf"].values.astype("float32")
    assert np.array_equal(x, e, equal_nan=True), "TMF band no longer pixel-identical"
    print(f"TMF: 0 of {x.size:,} pixels differ ({x.shape})")

    def enc(a: np.ndarray) -> np.ndarray:
        return np.where(np.isnan(a), 0, a).astype(np.int16)

    times = np.asarray(ee["time"].values).astype("datetime64[D]").astype(str)
    np.savez_compressed(OUT, ee_tmf=enc(e), xr_tmf=enc(x), time=times)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
