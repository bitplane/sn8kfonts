#!/usr/bin/env python3
"""Create editable 4×8 glyph grids from the Mullard SAA5050 ROM data.

This is an import/bootstrap tool, not part of `make`: generated grids are the
font source and may be hand-edited afterwards. Existing glyphs are preserved
unless --force is supplied.

Usage: saa5050import.py [--source FILE] [--output DIR] [--force]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
KEEP_AUTO_TOP = set("TEQUCFOPSRZDt f".replace(" ", ""))
NAMES = {
    0x20: "space", 0x21: "bang", 0x22: "quote", 0x23: "pound",
    0x27: "apostrophe", 0x2C: "comma", 0x2D: "dash", 0x2E: "dot",
    0x2F: "slash", 0x3A: "colon", 0x3B: "semicolon", 0x3F: "question",
    0x2190: "left", 0x00BD: "half", 0x2192: "right", 0x2191: "up",
    0x2013: "emdash", 0x00BC: "quarter", 0x2016: "doublepipe",
    0x00BE: "threequarters", 0x00F7: "divide", 0x2588: "block",
}


def option(args, name, default):
    if name not in args:
        return default
    index = args.index(name)
    value = Path(args[index + 1])
    del args[index:index + 2]
    return value


def load(path):
    glyphs = []
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        glyphs.append((int(fields[0], 16), [int(value, 16) for value in fields[1:]]))
    return glyphs


def vertical_window(rows):
    total = sum(row.bit_count() for row in rows)
    candidates = []
    for start in range(3):
        window = rows[start:start + 8]
        candidates.append((total - sum(row.bit_count() for row in window), abs(start - 1), start, window))
    return min(candidates, key=lambda candidate: candidate[:3])[3]


def unpack(row, width):
    return [bool(row & (1 << (width - 1 - index))) for index in range(width)]


def pack(bits):
    value = 0
    for bit in bits:
        value = value << 1 | bit
    return value


def reduce_row(row, operation):
    bits = unpack(row, 5)
    if operation < 5:
        return pack(bits[:operation] + bits[operation + 1:])
    merged = operation - 5
    return pack(bits[:merged] + [bits[merged] or bits[merged + 1]] + bits[merged + 2:])


def reconstruct(row, operation):
    bits = unpack(row, 4)
    if operation < 5:
        return pack(bits[:operation] + [False] + bits[operation:])
    merged = operation - 5
    return pack(bits[:merged] + [bits[merged], bits[merged]] + bits[merged + 1:])


def score(expected, actual):
    return (expected & ~actual).bit_count() * 3 + (actual & ~expected).bit_count()


def tie(operation):
    return (1, operation) if operation < 5 else (0, abs((operation - 5) * 2 - 3))


def choose_row(row):
    return min(
        ((score(row, reconstruct(reduce_row(row, op), op)), tie(op), reduce_row(row, op)) for op in range(9)),
        key=lambda candidate: candidate[:2],
    )[2]


def choose_glyph(rows):
    candidates = []
    for operation in range(9):
        reduced = [reduce_row(row, operation) for row in rows]
        loss = sum(score(row, reconstruct(out, operation)) for row, out in zip(rows, reduced))
        candidates.append((loss, tie(operation), reduced))
    return min(candidates, key=lambda candidate: candidate[:2])[2]


def convert(codepoint, rom):
    if codepoint == ord("0"):
        return [0b0110, 0b1001, 0b1001, 0b1001, 0b1001, 0b1001, 0b0110, 0]
    if codepoint == ord("1"):
        return [0b0100, 0b1100, 0b0100, 0b0100, 0b0100, 0b0100, 0b0100, 0]
    rows = vertical_window(rom)
    baseline = choose_glyph(rows)
    output = [choose_row(row) for row in rows]
    character = chr(codepoint)
    if character in KEEP_AUTO_TOP:
        first_ink = next((index for index, row in enumerate(rows) if row), None)
        if first_ink is not None:
            output[first_ink] = baseline[first_ink]
    return output


def filename(codepoint):
    character = chr(codepoint)
    label = character if character.isascii() and character.isalnum() else NAMES.get(codepoint, "glyph")
    return f"{codepoint:04X}_{label}.txt"


def main(argv):
    args = list(argv)
    force = "--force" in args
    if force:
        args.remove("--force")
    source = option(args, "--source", ROOT / "source/saa5050.txt")
    output = option(args, "--output", ROOT / "font/sn8k5050")
    if args:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)
    written = skipped = 0
    for codepoint, rom in load(source):
        path = output / filename(codepoint)
        if path.exists() and not force:
            skipped += 1
            continue
        rows = convert(codepoint, rom)
        path.write_text("\n".join(format(row, "04b").translate(str.maketrans("01", ".#")) for row in rows) + "\n")
        written += 1
    print(f"{output}: wrote {written} glyphs, preserved {skipped} existing glyphs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
