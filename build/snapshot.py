"""Seal a snapshot of the working corpus: keyword index, public files, page images.

    python build/snapshot.py --work /work 2026.11.1

The snapshot lands in ``<work>/snapshots/<id>``. Page images are rendered once per PDF into
``<work>/cache/pages`` and reused by later snapshots. There is no dense (embedding) arm yet.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from safetypage.build.snapshot import build_snapshot

SITE = "https://lectern.restorationcommons.org"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("snapshot_id")
    args = ap.parse_args()
    manifest = build_snapshot(
        args.work / "corpus.sqlite",
        args.work,
        args.snapshot_id,
        images=not args.no_images,
        dense_model=None,
        make_current=True,
        base_url=SITE,
        workers=args.workers,
        log=lambda m: print(m, flush=True),
    )
    print(manifest.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
