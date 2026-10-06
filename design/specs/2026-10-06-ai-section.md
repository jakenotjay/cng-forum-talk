# AI section (positions 18–20): findings and storyboard

Date: 2026-10-06. Files: `slides/_21-ai-metaskill.qmd`, `_22-ai-oneshot.qmd`, `_23-ai-verify.qmd`
(ids `#slide-21/22/23`). Replaces old 18 (results) and 19 (bottleneck); see the deck spec §8.

All paths below are in `~/epoch/epoch-mono` unless stated. Repo state read at `99167164c0` (2026-09-29).

## 1. Findings

### The meta-skill

- `.claude/skills/virtual-icechunk/`: **9 files, 677 lines**.
  - `SKILL.md` (117): one protocol, three families, *Step 0: classify on paper before any code*,
    a 7-step lifecycle, scale discipline, "done when" invariants, and when to give up.
  - `families/family-a.md` (82), `family-b.md` (49), `family-c.md` (79): how to build each family.
  - `reference/cores-and-protocol.md` (70), `hosting-and-auth.md` (69), `consume-and-register.md` (77).
  - `troubleshooting.md` (85): symptom → cause → fix (e.g. `400 UserProjectMissing` → requester-pays
    → Family C; `open()` ~86 s → opened with native chunks).
  - `UPDATE.md` (49): version pins and private-API coupling.
- Step 0 (SKILL.md): (1) bytes anonymously range-readable? no → mirror to Source Coop or materialise;
  (2) requester-pays / per-request auth → C; (3) tiles refresh in place or need a live query → C;
  (4) tiles splice into one uniform global grid → A, else stable per-tile manifests → B, else C.
- Lifecycle (SKILL.md): mirror/publish → probe one tile → write the module → build + `--verify` on a
  small AOI → register in `DATASET_SOURCES` → consume in an `xr_getter` → **parity with the EE store**.
- The skill landed with the EE-free deforestation umbrella PR #2954 (merged 2026-08-03); last
  touched in #3672 (2026-09-10).

### What it produced

- `DATASET_SOURCES` in `py/packages/virtual-icechunk/epoch/virtual_icechunk/virtual_configs.py`:
  **24 registered sources** (about 18 distinct datasets; FDP has 4 commodities, TMF/GLOFAS/GLCLU 2 each),
  all behind `VirtualDatasetSource.open(*, target_geobox, start_date, end_date)` in
  `dataset_source.py` (583 lines).
- Package size: 33 modules, ~17.3k lines; tests ~15.6k lines.
- PR #2954 "Earth-engine free deforestation" (opened 2026-07-31, merged 2026-08-03): +54,721 / −1,823,
  230 files; umbrella of 16 child PRs; ~20 raw sources in 3 families; 9 xarray getters; 71 new test
  files; "each composite has a golden-tile parity test against the EE result"; an `eudr_deforestation`
  export with `skip_ccdc=True` makes **zero Earth Engine calls**; xarray lane runs at concurrency 16
  vs EE's 4.
- PR #2954 commits (via `gh api .../pulls/2954/commits`): 236 commits, **233 by Jake, 3 by Ryan**;
  **219 of 236 (93%) carry a `Co-Authored-By: Claude` trailer**. The squash message's human co-authors
  are only Jake and Ryan.
- `git log -- py/packages/virtual-icechunk` authors: jnotjay/Jake 13, William Ouellette 7 (mostly the
  CDSE store, since removed, and fixes), Ryan 5 (Hansen, GLAD-L, GLAD-S2 writers in May; also GLCLU
  #2245, Esri io-lulc #2149, GHS_BUILT_C #2313), EnvDroneSense 2, Thomas Struys 1 (GLOFAS, #3508),
  Carl Glaysher 1. So "an engineer and an intern" is fair for the deforestation lane; the package as a
  whole has had small contributions from four others.

### A worked example (slide 19): GPW soil organic carbon, PR #3305

Opened 2026-08-22, merged 2026-08-25, 10 commits, written after the skill existed. From the PR body:

- Family A, 8 rolling 2-year COGs, grid 528,004 × 1,440,004, EPSG:4326, uint16, ~188 GB each
  (**~1.5 TB**).
- `gpw_soc.py` writer (+532 lines), registry entry `"gpw_soc": gpw_soc_source`.
- 1,453,056 references, over the ~1M flat-manifest ceiling, so sharded (52 objects).
- Built and committed in **78.1 s**; the store is **47 MB of references** against ~1.5 TB of COGs.
- EE parity on the area mean of each window: worst relative difference **1.27e-04** (tolerance 1e-3).
  Not pixel-for-pixel: EE `reduceRegion` and the window read use different edge rules.
- Whether this was literally one-shot is not recorded anywhere in git; the speaker's claim is that most
  additions are. Slide wording avoids stating it as a fact about this PR.

### How parity with Earth Engine is checked

Two layers.

1. **Source level, pixel-exact** (opt-in, needs EE auth): read a 100 × 100 block from the persisted
   virtual store, read the same block from the EE asset (`sampleRectangle` / `computePixels`), assert
   `n_diff == 0` / `np.array_equal`.
   - `tests/test_hansen_gfc.py::test_virtual_icechunk_matches_ee_hansen_pixel_for_pixel`
   - `tests/test_jrc_gfc.py::test_virtual_icechunk_matches_ee_jrc_pixel_for_pixel`
   - `tests/test_jrc_gft.py::test_virtual_icechunk_matches_ee_gft_pixel_for_pixel` (Amazon, Kalimantan, Congo)
   - `tests/test_glad_glclu.py::test_virtual_icechunk_matches_ee_glad_pixel_for_pixel`
   - `tests/test_fdp.py::test_virtualised_read_byte_matches_ee_asset` ("byte-identical")
   - `tests/test_glad_landsat.py` (array_equal on conf/date vs EE)
   (all under `py/packages/virtual-icechunk/`)
2. **Composite level, agreement gate** (`py/apps/sco2api/epoch/sco2api/tests/test_*_parity.py`):
   the EE getter and the xarray getter on the same region grid; gate `agreement >= 0.98` (0.99 for
   cattle), plus class-area guards in `parity_asserts.py`. Observed: **1.0000** on cattle, builtupMask
   (three dense cores) and 6 of 7 commodityMask bands. The skill's reason: reproject-then-reduce under
   nearest commutes with EE's reduce-then-reproject, so the result is byte-identical by construction.
3. **EUDR compliance golden tile** (`tests/test_eudr_xr_parity.py`, `tests/tools/parity.py`, cache in
   `.golden-cache/`, 512 × 512 × 8 years at −55.525, −7.225, −55.475, −7.175, Pará, Brazil):
   - **TMF band: 100.000%, xr_only 0, ee_only 0** (`.golden-cache/parity_latest.log`). Re-run locally
     today from the cache with `scripts/gen_s23_extract.py`: `np.array_equal(..., equal_nan=True)` is
     True, **0 of 2,097,152 pixels differ**. No EE call; the EE side is the cached golden.
   - GLAD alerts: 99.6% per-year agreement (target 99.0%), not exact. Cause: alert buckets refresh
     daily, and RADD is EE-only and dropped. Don't call the alerts band pixel-perfect.

### Honest wording

- "Pixel-perfect against Earth Engine" holds for the source-level tests and for the TMF band shown on
  slide 20. Composites are gated at ≥ 98% agreement and measured at 1.0000 on most bands; alerts are
  ~99.6%.
- "Two of us" / "an engineer and an intern": matches PR #2954 (Jake + Ryan). Speaker to confirm Ryan's
  role and how he wants to describe it.
- "Off Earth Engine": CCDC and RADD stay on EE (PR #2954, out of scope). Slide 17 shows spend at ~3%.

## 2. Storyboard (as built)

### 18 · `_21-ai-metaskill` — "A skill, not a script"

- **Visual:** left, a file-tree card of `.claude/skills/virtual-icechunk/` with line counts and a
  one-line purpose per entry (9 files · 677 lines). Centre, an "agent" pill and arrow. Right, the skill's
  own Step 0 as a four-question ladder: range-readable? (no → mirror) · requester-pays or auth? (yes → C)
  · overwritten in place? (yes → C) · splices into one grid? (yes A, no B); footer "then one module,
  one `open()`, one registry entry".
- **Animation:** tree rows rise 0.8–3.6 s, total 4.3 s; agent arrow 5 s; ladder title 5.2 s; questions
  6, 7.5, 9, 10.5 s; A/B/C chips flash solid blue 11.6–12 s; footer 12.2 s.
- **Notes (39 words):** What let so few of us do this is a skill. Everything we learned the hard way
  about families, hosting and failure modes lives in the repo as guidance, so the agent classifies a
  dataset before writing any code.

### 19 · `_22-ai-oneshot` — "One prompt to a registered source"

- **Visual:** terminal prompt bar with the real PR title ("Add a virtual icechunk store for GPW soil
  organic carbon"), typed in. Six numbered step cards (3 × 2), each with one real fact from PR #3305:
  Classify (Family A · 8 global COGs) · Probe one tile (528,004 × 1,440,004 uint16) · Write the source
  (`gpw_soc.py`) · Build & verify (1.45 M refs, sharded · 78 s) · Register (`"gpw_soc": gpw_soc_source,`)
  · Parity with Earth Engine (area means within 0.013%). Strip: 1.5 TB of source COGs → 47 MB of
  references · 0 bytes copied.
- **Animation:** prompt types 0.4–1.9 s; cards rise at 2, 3.5, 5, 6.5, 8, 9.5 s and each turns green
  with a tick 0.7 s later; strip 11 s.
- **Notes (40 words):** Here's a real one, soil organic carbon. The agent classified it, probed a tile,
  wrote the source, registered it and checked it against Earth Engine, turning 1.5 TB of COGs into 47 MB
  of references. Most new datasets go like this.

### 20 · `_23-ai-verify` — "Pixel-perfect against Earth Engine"

- **Visual:** three 432 px panels from real cached data (no EE call): Earth Engine − Virtual cube =
  Difference. JRC TMF deforestation year in the EUDR composite, golden tile in Pará, magma year ramp
  2019–2025. The difference panel is the real comparison map (faint green where either side has data,
  red where they disagree: none) with "0 pixels differ". Caption: 8 years × 512 × 512 px. Then "also
  pixel-exact at source" chips (Hansen, JRC GFC, JRC GFT, GLAD GLCLU, FDP) and the line "How a team of
  two moved our pipeline off Earth Engine".
- **Animation:** EE panel 0.5 s; "−" 2.2 s; virtual 2.5 s; legend/caption 3.5 s; "=" 4.7 s; difference
  panel 5 s; green scan line sweeps 5.6–8 s; "0" lands 8 s; chips 9.5 s; takeaway 11.5 s.
- **Notes (41 words):** And the agent checks its own work: the skill has it test each source against
  the Earth Engine version, and on this tile in Pará not one pixel differs in eight years. That's how two
  of us moved off Earth Engine.

### Generators

- `scripts/gen_s23_extract.py` (run inside epoch-mono's `py/` uv workspace): reads the local
  `.golden-cache/`, asserts equality, writes `images/src/s23-tmf-parity.npz`.
- `scripts/gen_s23_parity.py` (this repo's scripts env): renders `images/gen/s23-{ee,xr,diff}.png`,
  asserting 0 of 2,097,152 pixels differ.
