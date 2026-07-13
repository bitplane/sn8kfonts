#!/usr/bin/env python3
"""Decode teletext G1 mosaic text (as copied from teletext viewers) into a
glyph grid.

Viewers that copy mosaic cells as raw G1 bytes give you ASCII in the ranges
0x20-0x3F and 0x60-0x7F; each character IS a sextant bitmask:
mask = code - 0x20, plus 0x20 if the code is in the 0x60 range.
Anything outside those ranges decodes as empty.

Reads lines from stdin (or a file argument), writes the #/. grid to stdout
and a sextant preview to stderr, so you can redirect the grid straight into
a glyph file:

    g1import.py < paste.txt > font/sn8kfax/0070_p.txt

Options: --yshift N shifts the decoded bitmap up N subpixel rows (some pages
sit a row lower than others; normalize before saving glyphs).

Caveat: paste through anything HTML-shaped and interior SPACE CELLS collapse
(middle rows of lettering have real 0x20 gaps between letters; top/bottom
rows usually don't, so lines come out different lengths and alignment
scrambles). Save viewer copies straight into a file, and check every line
has the same cell count before trusting an import.
"""
import sys
from pathlib import Path

from render import render


def mask(c):
    v = ord(c)
    if 0x20 <= v < 0x40:
        return v - 0x20
    if 0x60 <= v < 0x80:
        return (v - 0x60) + 0x20
    return 0


def main(argv):
    args = list(argv)
    yshift = 0
    if "--yshift" in args:
        i = args.index("--yshift")
        yshift = int(args[i + 1])
        del args[i : i + 2]
    text = Path(args[0]).read_text() if args else sys.stdin.read()
    lines = [l for l in text.splitlines()]
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    width = max((len(l) for l in lines), default=0)
    grid = []
    for line in lines:
        rows = [[], [], []]
        for c in line.ljust(width):
            m = mask(c)
            for dy, bits in enumerate((1, 4, 16)):
                for dx in range(2):
                    rows[dy].append("#" if m & (bits << dx) else ".")
        grid.extend("".join(r) for r in rows)
    if yshift > 0:
        grid = grid[yshift:] + ["." * width * 2] * yshift
    elif yshift < 0:
        grid = ["." * width * 2] * -yshift + grid[:yshift]
    # Normalize: page position is junk — trim empty edge rows/columns,
    # report what was cut so placement can be reconstructed if it mattered.
    def inked(line):
        return any(c == "#" for c in line)
    top_cut = next((i for i, r in enumerate(grid) if inked(r)), 0)
    bot_cut = next((i for i, r in enumerate(reversed(grid)) if inked(r)), 0)
    grid = grid[top_cut : len(grid) - bot_cut] or [""]
    cols = [i for i, _ in enumerate(grid[0]) if any(r[i] == "#" for r in grid)]
    left_cut = cols[0] if cols else 0
    grid = [r[left_cut : (cols[-1] + 1) if cols else 0] for r in grid]
    if top_cut or bot_cut or left_cut:
        print(
            f"trimmed: {top_cut} rows top, {bot_cut} bottom, {left_cut} cols left",
            file=sys.stderr,
        )
    width = (len(grid[0]) + 1) // 2
    lengths = {len(l) for l in lines if l.strip()}
    if len(lengths) > 1:
        print(
            f"WARNING: uneven line lengths {sorted(lengths)} — "
            "interior spaces were probably collapsed in transit",
            file=sys.stderr,
        )
    for r in grid:
        print(r)
    gw = len(grid[0]) + (len(grid[0]) % 2)
    padded = [r.ljust(gw, ".") for r in grid]
    while len(padded) % 3:
        padded.append("." * gw)
    print(render(padded, gw), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
