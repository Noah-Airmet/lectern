#!/bin/sh
# The home page's wall of covers (WALL in src/lib/wall.ts), from a snapshot's page images:
#   scripts/make_wall.sh <snapshot dir>/public
# Needs ImageMagick. Writes public/wall/<ns>-<id>.webp, 300px wide; the files are checked in.
set -e
cd "$(dirname "$0")/.."
src="${1:?the public directory of a snapshot}"
mkdir -p public/wall
sed -n '/^export const WALL/,/^];/p' src/lib/wall.ts | grep -oE "'[a-z0-9-]+:[^']+'" | tr -d "'" | while read -r id; do
  ns="${id%%:*}"; local_id="${id#*:}"
  page=$(ls "$src/pages/$ns/$local_id"/*/p1.800.webp 2>/dev/null | sort | tail -1)
  [ -n "$page" ] || { echo "no page image: $id" >&2; continue; }
  magick "$page" -resize 300x -quality 78 "public/wall/$ns-$local_id.webp"
done
