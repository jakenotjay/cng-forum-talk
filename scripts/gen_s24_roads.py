"""One-off fetch of real Overture roads around Binabaru mill for the supply-shed slide.

Writes images/src/s24-roads.json: {"bbox": [...], "release": ..., "roads": {class: [[[lon, lat], ...], ...]}}
simplified at ~0.002 degrees. gen_s24_shed.py reads only this cache, never the network.

    uv run --project scripts --with duckdb python scripts/gen_s24_roads.py

Source: Overture Maps transportation/segment, release 2026-08-19.0 (the release the
isochrone pipeline pins), public GeoParquet on s3://overturemaps-us-west-2, anonymous.
The bbox struct filter lets DuckDB skip row groups outside the box.
"""

import json
import os
import time
from pathlib import Path

import duckdb
from shapely import wkb
from shapely.geometry import box
from shapely.ops import linemerge, unary_union

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images" / "src" / "s24-roads.json"
FAC = (101.27548, 0.210053)  # Binabaru mill (facility.geojson)
HALF = 0.65  # degrees either side: covers the shed (about +-0.5) plus the overlay's soft edge
RELEASE = "2026-08-19.0"
SRC = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=transportation/type=segment/*"
CLASSES = ["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "unclassified", "track"]
TOL = 0.002
# Raw rows are kept outside the repo so re-processing never re-reads S3.
RAW = Path(os.environ.get("S24_ROADS_RAW", "/tmp/s24-roads-raw.parquet"))


def main() -> None:
    x0, y0, x1, y1 = FAC[0] - HALF, FAC[1] - HALF, FAC[0] + HALF, FAC[1] + HALF
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
    con.execute("SET s3_region='us-west-2'; SET s3_access_key_id=''; SET s3_secret_access_key='';")
    cls = ",".join(f"'{c}'" for c in CLASSES)
    q = f"""
        SELECT class, ST_AsWKB(geometry) AS wkb
        FROM read_parquet('{SRC}', hive_partitioning=1)
        WHERE bbox.xmin <= {x1} AND bbox.xmax >= {x0}
          AND bbox.ymin <= {y1} AND bbox.ymax >= {y0}
          AND subtype = 'road' AND class IN ({cls})
    """
    if not RAW.exists():
        t = time.time()
        con.execute(f"COPY ({q}) TO '{RAW}' (FORMAT parquet)")
        print(f"fetched in {time.time() - t:.0f} s -> {RAW}")
    rows = con.execute(f"SELECT class, wkb FROM read_parquet('{RAW}')").fetchall()
    print(f"{len(rows)} segments")

    clip = box(x0, y0, x1, y1)
    by_class: dict[str, list] = {c: [] for c in CLASSES}
    for c, b in rows:
        by_class[c].append(wkb.loads(bytes(b)))
    roads: dict[str, list] = {c: [] for c in CLASSES}
    nv = 0
    for c, geoms in by_class.items():
        # Overture splits roads at every junction: merge into long lines before simplifying,
        # so short urban segments are not lost.
        g = unary_union(geoms).intersection(clip)
        if g.geom_type == "MultiLineString":
            g = linemerge(g)
        g = g.simplify(TOL)
        for part in getattr(g, "geoms", [g]):
            if part.geom_type != "LineString" or part.length < TOL:
                continue
            coords = [[round(x, 4), round(y, 4)] for x, y in part.coords]
            roads[c].append(coords)
            nv += len(coords)
    print({c: len(v) for c, v in roads.items()}, f"{nv} vertices")
    OUT.write_text(json.dumps({"release": RELEASE, "source": SRC, "bbox": [x0, y0, x1, y1],
                               "tolerance_deg": TOL, "roads": roads}, separators=(",", ":")))
    print(OUT.relative_to(ROOT), f"{OUT.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
