#!/bin/sh
# The landing page's example page as a static image (public/hero/page.webp), rendered on the
# homelab from the book's PDF the way the snapshot renders pages (1600 px wide, lossy WebP).
#   scripts/hero.sh <doc id> <page>      e.g. scripts/hero.sh npnf2:04-select-works-and-letters 362
set -e
cd "$(dirname "$0")/.."
doc="${1:?doc id}"; page="${2:?page}"
sha=$(grep "\"id\": \"$doc\"" ../shelf/volumes.jsonl | sed 's/.*"sha256": "\([0-9a-f]*\)".*/\1/')
ssh homelab "docker run --rm -v /data/lectern:/work lectern-build python -c \"
import pymupdf
from PIL import Image
from pathlib import Path
from safetypage.blobs import BlobStore
d = pymupdf.open(BlobStore(Path('/work/blobs')).path('$sha'))
p = d[$page - 1]; z = 1600 / p.rect.width
pm = p.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
Image.frombytes('RGB', (pm.width, pm.height), pm.samples).save('/work/hero.webp', 'WEBP', quality=60, method=6)
\"" && mkdir -p public/hero && scp -q homelab:/data/lectern/hero.webp public/hero/page.webp
ls -la public/hero/page.webp
