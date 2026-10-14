"""
make_icons.py - build the ./icons PNGs used by ui_theme.icon() from Lucide.

One-time setup (dev machine only, not needed in the shipped app):
    npm install lucide-static
    pip install cairosvg

Usage:
    python make_icons.py                      # builds the default set below
    python make_icons.py bell mail trash-2    # adds/updates specific icons

Browse names at https://lucide.dev/icons. PNGs are black on transparent;
ui_theme.icon() tints them for light/dark mode, so the color here is irrelevant.
"""
import sys
from pathlib import Path

import cairosvg

SRC = Path("node_modules/lucide-static/icons")
OUT = Path(__file__).resolve().parent / "icons"

DEFAULT = [
    "clipboard-list", "school", "hospital", "settings", "heart", "refresh-cw",
    "coffee", "message-circle", "info", "play", "square", "folder-open",
    "file-spreadsheet", "copy", "external-link", "send", "download", "rocket",
    "circle-check", "chevron-down", "terminal", "trash-2",
]


def main(names):
    if not SRC.exists():
        sys.exit(f"{SRC} not found. Run `npm install lucide-static` in this folder first.")
    OUT.mkdir(exist_ok=True)
    missing = []
    for name in names:
        svg_file = SRC / f"{name}.svg"
        if not svg_file.exists():
            missing.append(name)
            continue
        svg = svg_file.read_text(encoding="utf-8").replace("currentColor", "#000000")
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(OUT / f"{name}.png"),
                         output_width=96, output_height=96)
    print(f"wrote {len(names) - len(missing)} icons to {OUT}")
    if missing:
        print("not found in Lucide:", ", ".join(missing))


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)
