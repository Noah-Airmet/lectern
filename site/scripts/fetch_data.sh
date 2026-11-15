#!/bin/sh
# What the site's build reads from a snapshot, copied from the homelab into .snap/:
# the manifest, every book's card, each book's first page (for its cover), and every page of
# the landing page's example book. The rest of the snapshot is only read by browsers, from the API.
#   scripts/fetch_data.sh <snapshot id>
set -e
cd "$(dirname "$0")/.."
id="${1:?snapshot id}"
src="homelab:/data/lectern/snapshots/$id"
mkdir -p .snap/public
rsync -a "$src/manifest.json" .snap/
rsync -a --delete "$src/public/docs/" .snap/public/docs/
rsync -a -m --include='*/' --include='r1/p1.json' --exclude='*' "$src/public/text/" .snap/public/text/
example=$(grep -o "doc: '[^']*'" src/lib/checks.ts | cut -d"'" -f2 | sed 's|:|/|')
rsync -a "$src/public/text/$example/" ".snap/public/text/$example/"
echo "fetched $(ls .snap/public/docs/* | wc -l | tr -d ' ') cards"
