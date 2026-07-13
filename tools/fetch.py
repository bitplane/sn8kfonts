#!/usr/bin/env python3
"""Fetch a teletextarchive.com page and emit its mosaic cells as G1 text,
ready to pipe into g1import.py.

Each teletext row div becomes one output line. Mosaic spans keep their
characters (entities decoded, &nbsp; -> space); alphanumeric spans become
spaces so column alignment is preserved. --colour N keeps only mosaics in
that foreground colour (teletext 0-7; the archive uses classes like
teletext-colour-3 = yellow).

Usage:
    fetch.py URL_OR_FILE [--colour N] | tools/g1import.py
"""
import html
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


class TeletextExtract(HTMLParser):
    def __init__(self, colour=None):
        super().__init__(convert_charrefs=True)
        self.colour = colour
        self.rows = []
        self.in_row = False
        self.span = None  # (is_mosaic, colour) while inside a span

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "")
        if tag == "div" and "teletext-default" in cls:
            self.in_row = True
            self.rows.append([])
        elif tag == "span" and self.in_row:
            m = re.search(r"teletext-colour-(\d)", cls)
            self.span = ("teletext-mosaics" in cls, int(m.group(1)) if m else None)

    def handle_endtag(self, tag):
        if tag == "div":
            self.in_row = False
        elif tag == "span":
            self.span = None

    def handle_data(self, data):
        if not (self.in_row and self.span):
            return
        is_mosaic, colour = self.span
        text = data.replace("\xa0", " ")
        keep = is_mosaic and (self.colour is None or colour == self.colour)
        self.rows[-1].append(text if keep else " " * len(text))


def main(argv):
    args = list(argv)
    colour = None
    if "--colour" in args:
        i = args.index("--colour")
        colour = int(args[i + 1])
        del args[i : i + 2]
    if len(args) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    src = args[0]
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "sn8kfonts-import"})
        raw = urllib.request.urlopen(req).read().decode("utf-8", "replace")
    else:
        raw = Path(src).read_text()
    parser = TeletextExtract(colour)
    parser.feed(raw)
    for row in parser.rows:
        print("".join(row).rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
