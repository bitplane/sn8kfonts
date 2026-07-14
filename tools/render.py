#!/usr/bin/env python3
"""Render glyph grid .txt files as block characters.

Format: space or "." = empty, anything else = ink. Rows are right-padded to
the widest row, then padded to the encoding's cell size — sextant = 2x3
subpixels per cell (U+1FB00), halfblock = 1x2 (space/upper/lower/full block).
(Dots let you keep leading/trailing empty rows and columns explicit — pure
whitespace gets eaten by editors and tools.)

Usage: render.py FILE_OR_DIR [...] [--encoding sextant|halfblock|octant]
"""
import sys
from pathlib import Path


def grid_files(font_dir):
    # not glob("*.txt") or .suffix: both treat dot-files specially, hiding
    # glyphs like "..txt" (use glyph_stem too — Path.stem has the same hole)
    files = Path(font_dir).iterdir()
    return sorted(f for f in files if f.name.endswith(".txt") and f.name != ".txt")


def glyph_stem(path):
    return path.name[: -len(".txt")]


def load_grid(path, cell=(2, 3)):
    rows = [line.rstrip("\n") for line in Path(path).read_text().splitlines()]
    width = max((len(r) for r in rows), default=0)
    cw, ch = cell
    width += -width % cw
    while len(rows) % ch:
        rows.append("")
    return [r.ljust(width) for r in rows], width


def sextant(mask):
    if mask == 0:
        return " "
    if mask == 63:
        return "█"  # full block
    if mask == 21:
        return "▌"  # left half
    if mask == 42:
        return "▐"  # right half
    return chr(0x1FB00 + mask - 1 - (mask > 21) - (mask > 42))


def halfblock(mask):
    return " ▀▄█"[mask]


def octant(mask):
    special = {
        0x00: " ", 0x01: "\U0001CEA8", 0x02: "\U0001CEAB",
        0x03: "\U0001FB82", 0x05: "▘", 0x0A: "▝", 0x0F: "▀",
        0x14: "\U0001FBE6", 0x28: "\U0001FBE7", 0x3F: "\U0001FB85",
        0x40: "\U0001CEA3", 0x50: "▖", 0x55: "▌", 0x5A: "▞",
        0x5F: "▛", 0x80: "\U0001CEA0", 0xA0: "▗", 0xA5: "▚",
        0xAA: "▐", 0xAF: "▜", 0xC0: "▂", 0xF0: "▄", 0xF5: "▙",
        0xFA: "▟", 0xFC: "▆", 0xFF: "█",
    }
    if mask in special:
        return special[mask]
    skipped = sum(value < mask for value in special)
    return chr(0x1CD00 + mask - skipped)


# name -> (cell width, cell height, mask -> char); mask bit = 1 << (dy*cw + dx)
ENCODINGS = {
    "sextant": (2, 3, sextant),
    "halfblock": (1, 2, halfblock),
    "octant": (2, 4, octant),
}


def cell_size(encoding):
    cw, ch, _ = ENCODINGS[encoding]
    return cw, ch


def render(rows, width, encoding="sextant"):
    cw, ch, char = ENCODINGS[encoding]
    out = []
    for y in range(0, len(rows), ch):
        line = []
        for x in range(0, width, cw):
            mask = 0
            for dy in range(ch):
                for dx in range(cw):
                    if rows[y + dy][x + dx] not in " .":
                        mask |= 1 << (dy * cw + dx)
            line.append(char(mask))
        out.append("".join(line))
    return "\n".join(out)


def main(args):
    args = list(args)
    encoding = "sextant"
    if "--encoding" in args:
        i = args.index("--encoding")
        encoding = args[i + 1]
        del args[i : i + 2]
    files = []
    for arg in args:
        p = Path(arg)
        files.extend(grid_files(p) if p.is_dir() else [p])
    for f in files:
        rows, width = load_grid(f, cell_size(encoding))
        if len(files) > 1:
            print(f"── {glyph_stem(f) if f.name.endswith('.txt') else f.stem} ──")
        print(render(rows, width, encoding))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["."]))
