#!/usr/bin/env python3
"""Typeset a string in a grid font at subpixel resolution, output sextants.

Unlike FIGlet (which composes whole cells, quantizing spacing to 2 subpixels
and one fixed phase), this composes glyph bitmaps directly: letters land at
any subpixel offset, auto-kerned so adjacent ink keeps --gap subpixels of
daylight per row, then the merged bitmap is encoded to sextants at the end.

Usage: typeset.py FONT_DIR TEXT [--gap N] [--space N] [--encoding NAME]
"""
import sys
from pathlib import Path

from render import cell_size, glyph_stem, grid_files, load_grid, render


def ink(rows):
    return [[c not in " ." for c in row] for row in rows]


def edges(grid):
    """Per row: (leftmost ink x, rightmost ink x) or None."""
    out = []
    for row in grid:
        xs = [x for x, on in enumerate(row) if on]
        out.append((xs[0], xs[-1]) if xs else None)
    return out


def kern_offset(left_edges, right_edges, gap):
    """Smallest x-offset for the right glyph keeping >= gap empty columns
    between ink in every shared row (bounding boxes may interlock)."""
    offset = 0
    for le, re in zip(left_edges, right_edges):
        if le is not None and re is not None:
            offset = max(offset, le[1] + 1 + gap - re[0])
    return offset


def main(argv):
    args = [a for a in argv]
    gap, space, encoding = 1, 2, "sextant"
    if "--encoding" in args:
        i = args.index("--encoding")
        encoding = args[i + 1]
        del args[i : i + 2]
    if "--gap" in args:
        i = args.index("--gap")
        gap = int(args[i + 1])
        del args[i : i + 2]
    if "--space" in args:
        i = args.index("--space")
        space = int(args[i + 1])
        del args[i : i + 2]
    if len(args) == 1:  # just text: default to the first font dir in ./font
        fonts = sorted(Path(__file__).parent.parent.glob("font/*/"))
        if not fonts:
            print("no fonts found", file=sys.stderr)
            return 2
        font_dir, text = fonts[0], args[0]
    elif len(args) == 2:
        font_dir, text = Path(args[0]), args[1]
    else:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    glyphs = {}
    for f in grid_files(font_dir):
        stem = glyph_stem(f)
        cp = ord(stem) if len(stem) == 1 else None
        if cp is None:
            head = stem.split("_", 1)[0]
            try:
                cp = int(head, 16)
            except ValueError:
                continue
        rows, _ = load_grid(f, cell_size(encoding))
        glyphs[chr(cp)] = ink(rows)

    height = max((len(g) for g in glyphs.values()), default=0)
    canvas = [[] for _ in range(height)]
    cursor = 0

    def canvas_edges():
        return edges([row for row in canvas])

    for ch in text:
        if ch == " ":
            cursor += space
            continue
        g = glyphs.get(ch)
        if g is None:
            print(f"no glyph for {ch!r}, skipped", file=sys.stderr)
            continue
        g = g + [[False] * len(g[0]) for _ in range(height - len(g))]
        offset = max(cursor, kern_offset(canvas_edges(), edges(g), gap))
        for y in range(height):
            row = canvas[y]
            for x, on in enumerate(g[y]):
                gx = offset + x
                while len(row) <= gx:
                    row.append(False)
                row[gx] = row[gx] or on
        cursor = offset + len(g[0])

    cw, ch = cell_size(encoding)
    width = max((len(r) for r in canvas), default=0)
    rows = ["".join("#" if on else " " for on in row).ljust(width) for row in canvas]
    while len(rows) % ch:
        rows.append(" " * width)
    width += -width % cw
    print(render([r.ljust(width) for r in rows], width, encoding))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
