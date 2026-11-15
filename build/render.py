"""Render page images for every PDF in the blob store into the snapshot builder's cache.

    python build/render.py --work /work [--workers 2] [--follow]

The snapshot build renders what is missing anyway; running this first (or alongside the
ingest, with --follow) means the build finds the pages already drawn. Re-runnable: pages that
exist are skipped.
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from safetypage.blobs import BlobStore
from safetypage.build.snapshot import render_pdf_pages


def job(args: tuple[str, str]) -> tuple[str, int]:
    pdf, out = args
    return pdf, render_pdf_pages(Path(pdf), Path(out), 10**6)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--follow", action="store_true", help="keep going while the ingest adds PDFs")
    args = ap.parse_args()
    blobs = BlobStore(args.work / "blobs")
    cache = args.work / "cache" / "pages"
    seen: set[str] = set()
    idle = 0
    while True:
        new = [sha for sha in blobs if sha not in seen]
        if not new:
            if not args.follow or idle >= 15:
                break
            idle += 1
            time.sleep(60)
            continue
        idle = 0
        seen.update(new)
        jobs = [(str(blobs.path(sha)), str(cache / sha)) for sha in new]
        with ProcessPoolExecutor(args.workers) as pool:
            for pdf, n in pool.map(job, jobs):
                print(f"{Path(pdf).name[:12]}: {n} rendered", flush=True)


if __name__ == "__main__":
    main()
