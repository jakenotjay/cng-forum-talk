"""Give every slide a position-based id, so the URL hash reads #/slide-01 … #/slide-20.

Slide files are named for what they are, not where they sit; the order lives only in
index.qmd. This rewrites the `{#slide-…}` id on each included slide's heading to match
its position (the untimed end slide becomes `slide-end`). Run by scripts/render.sh.
Style and script hooks use classes, never these ids.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    files = re.findall(r"\{\{< include (slides/_[^ ]+\.qmd) >\}\}", (ROOT / "index.qmd").read_text())
    n = 0
    for f in files:
        path = ROOT / f
        text = path.read_text()
        untimed = 'data-autoslide="0"' in text.split("\n", 1)[0]
        if untimed:
            new_id = "slide-end"
        else:
            n += 1
            new_id = f"slide-{n:02d}"
        updated = re.sub(r"^(## .*?\{)#slide-[\w-]+", rf"\1#{new_id}", text, count=1, flags=re.M)
        if updated != text:
            path.write_text(updated)


if __name__ == "__main__":
    main()
