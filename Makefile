# Build every font/<name>/ into dist/<name>.tlf.
# Per-font export flags are target-specific variables below.

FONTS := $(notdir $(patsubst %/,%,$(wildcard font/*/)))
TLFS := $(FONTS:%=dist/%.tlf)

all: $(TLFS)

# linegap 1, not 2: glyph grids are 13 subpixel rows, halfblock cells pad
# them to 14, so one gap row reproduces the original 13+2 line pitch
dist/sn8kblock.tlf: FLAGS := --encoding halfblock --gap 2 --space 3 --kern fixed --shade gradient --linegap 1

.SECONDEXPANSION:
# the second wildcard catches dot-file glyphs like "..txt" (full stop)
dist/%.tlf: $$(wildcard font/%/*.txt) $$(wildcard font/%/.*.txt) tools/genfiglet.py tools/render.py
	@mkdir -p dist
	python3 tools/genfiglet.py font/$* $(FLAGS) -o $@

clean:
	rm -rf dist

.PHONY: all clean
