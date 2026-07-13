#!/bin/sh
# Live-render glyph grids while you edit: watch.sh font/sn8kfax [glyph.txt]
# Uses inotifywait when available, falls back to 1s polling.
target="${1:-.}"
shift 2>/dev/null
while :; do
    clear
    python3 "$(dirname "$0")/render.py" "$target" "$@"
    if command -v inotifywait >/dev/null 2>&1; then
        inotifywait -qq -r -e close_write,create,delete,move "$target" || sleep 1
    else
        sleep 1
    fi
done
