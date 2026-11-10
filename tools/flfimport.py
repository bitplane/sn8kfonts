#!/usr/bin/env python3
"""Import glyphs from a FIGlet font as text-encoded glyph grids.

Takes the first --rows rows of each glyph (hardblanks become spaces, blank
columns either side trimmed) for every
glyph LIKE_DIR has, so a plain-text variant covers what the block font draws.
Existing files are kept unless --force: hand edits survive a re-import.

Usage: flfimport.py SOURCE.flf FONT_DIR LIKE_DIR [--rows N] [--force]
"""
import sys
from pathlib import Path

from genfiglet import flag, glyph_codepoint
from render import glyph_stem, grid_files

DEUTSCH = [196, 214, 220, 228, 246, 252, 223]


def read_flf(path):
    lines = Path(path).read_text(encoding="latin-1").splitlines()
    header = lines[0].split()
    hardblank = header[0][-1]
    height, comments = int(header[1]), int(header[5])
    body = lines[1 + comments :]
    glyphs = {}

    def take(at):
        rows = []
        for line in body[at : at + height]:
            end = line[-1] if line else ""
            rows.append(line.rstrip(end).replace(hardblank, " "))
        return rows

    at = 0
    for cp in list(range(32, 127)) + DEUTSCH:
        glyphs[cp] = take(at)
        at += height
    while at < len(body):
        tag = body[at].split()[0] if body[at].strip() else ""
        try:
            cp = int(tag, 0)
        except ValueError:
            break
        glyphs[cp] = take(at + 1)
        at += 1 + height
    return glyphs


def trim(rows):
    """Drop the blank columns either side: FIGlet fonts pad glyphs for
    smushing, and sn8kfonts bakes spacing in with --gap instead."""
    width = max((len(r) for r in rows), default=0)
    rows = [r.ljust(width) for r in rows]
    inked = [x for x in range(width) if any(r[x] != " " for r in rows)]
    if not inked:
        return rows
    return [r[inked[0] : inked[-1] + 1] for r in rows]


def main(argv):
    args = list(argv)
    rows = flag(args, "--rows", None, int)
    force = "--force" in args
    if force:
        args.remove("--force")
    if len(args) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    source, out, like = args
    glyphs = read_flf(source)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for f in grid_files(like):
        cp = glyph_codepoint(glyph_stem(f))
        target = out / f.name
        if cp not in glyphs:
            print(f"{f.name}: not in {source}", file=sys.stderr)
            continue
        if target.exists() and not force:
            continue
        target.write_text("\n".join(trim(glyphs[cp][:rows])) + "\n")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main(sys.argv[1:]))
