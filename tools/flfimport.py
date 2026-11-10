#!/usr/bin/env python3
"""Import glyphs from a FIGlet font as text-encoded glyph grids.

Takes the first --rows rows of each glyph (hardblanks become spaces, blank
columns either side trimmed): every glyph the source draws, or with --like
only those LIKE_DIR has, named as it names them. Space is left to genfiglet's
--space. Existing files are kept unless --force: hand edits survive a
re-import.

Usage: flfimport.py SOURCE.flf FONT_DIR [--like LIKE_DIR] [--rows N] [--force]
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


def file_name(cp):
    ch = chr(cp)
    return f"{cp:04X}_{ch if ch.isascii() and ch.isalnum() else 'glyph'}.txt"


def main(argv):
    args = list(argv)
    rows = flag(args, "--rows", None, int)
    like = flag(args, "--like", None, Path)
    force = "--force" in args
    if force:
        args.remove("--force")
    if len(args) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    source, out = args
    glyphs = read_flf(source)
    if like:
        wanted = {glyph_codepoint(glyph_stem(f)): f.name for f in grid_files(like)}
    else:
        wanted = {cp: file_name(cp) for cp in glyphs if cp != 32}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for cp, name in sorted(wanted.items()):
        target = out / name
        if cp not in glyphs:
            print(f"{name}: not in {source}", file=sys.stderr)
            continue
        if target.exists() and not force:
            continue
        target.write_text("\n".join(trim(glyphs[cp][:rows])) + "\n")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main(sys.argv[1:]))
