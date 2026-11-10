# Build every font/<name>/ into dist/<name>.tlf.
# Per-font export flags are target-specific variables below.

FONTS := $(notdir $(patsubst %/,%,$(wildcard font/*/)))
TLFS := $(FONTS:%=dist/%.tlf)
# Built from another font: see the mini rules below.
VARIANTS := dist/sn8kfax.quadrant.tlf dist/smblock.ascii.tlf dist/future.ascii.tlf

all: $(TLFS) $(VARIANTS)

# linegap 1, not 2: glyph grids are 13 subpixel rows, halfblock cells pad
# them to 14, so one gap row reproduces the original 13+2 line pitch
dist/sn8kblock.tlf: FLAGS := --encoding halfblock --gap 2 --space 3 --kern fixed --shade gradient --linegap 1

# Authentic SAA5050 glyphs reduced to 4×8 pixels: exactly 2×2 octant cells.
dist/sn8k5050.tlf: FLAGS := --encoding octant --gap 0 --space 4 --kern fixed

# sn8k5050 for terminals without octants: two plain characters by two rows,
# by script. sn8ks uses it at the quadrant tier and below.
dist/sn8k5050.quadrant.tlf: FLAGS := --encoding text --gap 0 --space 2 --kern fixed

# FIGlet's Mini in plain text, all four rows (descenders on the last):
# tools/flfimport.py source/mini.flf font/mini --rows 4, plus hand-drawn
# pause and fast-forward glyphs. It stands in where the blocks won't draw:
# smblock (four rows, mixed case) and sn8kfax from quadrant down, and
# TOIlet's future (three rows, capitals, box drawing) in ASCII.
MINI_FLAGS := --encoding text --gap 1 --space 2 --kern fixed
dist/mini.tlf: FLAGS := $(MINI_FLAGS)
dist/sn8kfax.quadrant.tlf dist/smblock.ascii.tlf: dist/mini.tlf
	cp $< $@
dist/future.ascii.tlf: dist/mini.tlf
	python3 tools/genfiglet.py font/mini $(MINI_FLAGS) --rows 3 --caps -o $@

.SECONDEXPANSION:
# the second wildcard catches dot-file glyphs like "..txt" (full stop)
dist/%.tlf: $$(wildcard font/%/*.txt) $$(wildcard font/%/.*.txt) $$(wildcard font/%/CREDITS) tools/genfiglet.py tools/render.py
	@mkdir -p dist
	python3 tools/genfiglet.py font/$* $(FLAGS) -o $@

clean:
	rm -rf dist

test:
	python3 -m unittest discover -s tests

.PHONY: all clean test
