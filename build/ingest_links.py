"""Read the harvested journals and archives into Lectern's working corpus.

    python build/ingest_links.py --links /work/links --work /work

Reads every ``<links>/<source>/manifest.jsonl`` written by ``harvest/`` (the format is in
``harvest/README.md``). Each row with a file becomes one document with one version, ``v1``: a
PDF as pages (printed page numbers from ``label_offset``), an HTML page as blocks. The licence
fact comes from the row; the engine decides the tier from it, so CC BY items are served in full
and everything else is link only (search, snippets, and "Read at source" at the publisher).

Re-runnable: a document already in the corpus is skipped. A row that cannot be read (no text
layer, a page with no real text) is listed in ``<work>/set-aside-links.jsonl`` with the reason.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ingest import SITE, is_scan, now, separate_markers
from safetypage.blobs import BlobStore
from safetypage.bundle import Bundle, BundleLicence, BundleVersion, import_bundle
from safetypage.corpus import Corpus
from safetypage.ingest.html import ExtractError, outline_of, page_blocks
from safetypage.ingest.pdf import NeedsOcrError, PdfError, pdf_outline, pdf_pages
from safetypage.licence import is_open_licence
from safetypage.model import Document, Rendition

PRODUCER = "lectern/harvest-v1"

# Each journal or archive is a shelf. Most are named by their namespace; a few namespaces share one.
SHELF = {
    "byus": "byu-studies",
    "jbms": "journal-of-book-of-mormon-studies",
    "farmsreview": "mormon-studies-review",
    "msr": "mormon-studies-review",
    "sba": "studies-in-the-bible-and-antiquity",
    "studiaantiqua": "studia-antiqua",
    "rae": "religion-in-the-age-of-enlightenment",
    "releducator": "religious-educator",
    "rsc": "religious-studies-center",
    "knowhy": "scripture-central",
    "evidence": "scripture-central",
    "mhs": "mormon-historical-studies",
    "jhs": "journal-of-hebrew-scriptures",
    "jjmjs": "jesus-movement-jewish-setting",
    "ote": "old-testament-essays",
    "tynbul": "tyndale-bulletin",
}


def licence(row: dict) -> BundleLicence | None:
    lic = row.get("licence") or {}
    if lic.get("id") in (None, "unknown") or not lic.get("evidence_url"):
        return None
    scope = lic.get("scope")
    return BundleLicence(
        licence=lic["id"],
        evidence_kind="publisher_rule" if scope == "journal" else "page_statement",
        evidence_url=lic["evidence_url"],
        evidence_quote=lic.get("quote") or "",
        observed_at=row.get("fetched_at") or now(),
        producer=PRODUCER,
    )


def bundle_for(row: dict, data: bytes) -> Bundle:
    lic = licence(row)
    open_tier = lic is not None and is_open_licence(lic.licence)
    sha = row["sha256"]
    pages, blocks = [], []
    if row["media_type"] == "application/pdf":
        pages = separate_markers(pdf_pages(data))
        outline = pdf_outline(data, pages)
        offset = row.get("label_offset")
        if offset is not None:
            pages = [
                p.model_copy(update={"label": str(i + offset)}) if i + offset >= 1 else p
                for i, p in enumerate(pages, 1)
            ]
        kind, fidelity = "pdf", "ocr" if is_scan(data) else "text_layer"
    else:
        blocks = page_blocks(data, row["source_url"])
        outline = outline_of(blocks)
        kind, fidelity = "html", "html"
    # An open item is served from Lectern; a link-only one names the publisher's copy.
    file_url = f"{SITE}/files/{sha}.{kind}" if open_tier else row["source_url"]
    observed = row.get("fetched_at") or now()
    return Bundle(
        document=Document(
            doc_id=row["id"],
            # An RSC book is read chapter by chapter: each chapter is an article on the shelf.
            kind="article" if row.get("kind") == "book" else (row.get("kind") or "article"),
            title=row["title"],
            authors=row.get("authors") or [],
            # The shelf; the journal's (or, for an RSC chapter, the book's) own name is the org.
            collection=SHELF.get(row["id"].split(":")[0], row["id"].split(":")[0]),
            org=row.get("collection"),
            published=row.get("published"),
            source_url=row.get("landing_url") or row["source_url"],
            added_at=now(),
        ),
        version=BundleVersion(
            label="v1",
            anchor_kind="page" if pages else "block",
            fidelity=fidelity,
            source_url=row["source_url"],
            content_sha256=sha,
            observed_at=observed,
            published=row.get("published"),
        ),
        licence=lic,
        renditions=[
            Rendition(
                kind=kind,
                sha256=sha,
                bytes=len(data),
                media_type=row["media_type"],
                source_url=file_url,
                fetched_at=observed,
            )
        ],
        pages=pages,
        blocks=blocks,
        outline=outline,
    )


def prepare(job: tuple[dict, str]) -> tuple[dict, Bundle | None, bytes | None, str | None]:
    row, path = job
    try:
        data = Path(path).read_bytes()
        return row, bundle_for(row, data), data, None
    except (OSError, PdfError, NeedsOcrError, ExtractError, ValueError) as exc:
        return row, None, None, f"{type(exc).__name__}: {exc}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--links", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--only", nargs="*", help="source folders to read (default: all)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    jobs: list[tuple[dict, str]] = []
    seen: set[str] = set()
    for manifest in sorted(args.links.glob("*/manifest.jsonl")):
        if args.only and manifest.parent.name not in args.only:
            continue
        for line in manifest.read_text(encoding="utf-8").splitlines():
            row = json.loads(line) if line.strip() else None
            if not row or not row.get("file") or row["id"] in seen:
                continue
            seen.add(row["id"])
            jobs.append((row, str(manifest.parent / row["file"])))
    if args.limit:
        jobs = jobs[: args.limit]

    blobs = BlobStore(args.work / "blobs")
    set_aside = (args.work / "set-aside-links.jsonl").open("a", encoding="utf-8")
    done = 0
    with Corpus.open(args.work / "corpus.sqlite") as corpus:
        todo = [j for j in jobs if corpus.document(j[0]["id"]) is None]
        with ProcessPoolExecutor(args.workers) as pool:
            for i, (row, bundle, data, reason) in enumerate(pool.map(prepare, todo, chunksize=8), 1):
                if bundle is None or data is None:
                    set_aside.write(json.dumps({"id": row["id"], "reason": reason}) + "\n")
                    set_aside.flush()
                    print(f"[{i}/{len(todo)}] {row['id']}: set aside ({reason})", file=sys.stderr)
                    continue
                try:
                    import_bundle(corpus, bundle)
                except Exception as exc:  # noqa: BLE001 - one bad row is set aside, the run goes on
                    corpus.conn.rollback()
                    set_aside.write(json.dumps({"id": row["id"], "reason": repr(exc)}) + "\n")
                    print(f"[{i}/{len(todo)}] {row['id']}: set aside ({exc!r})", file=sys.stderr)
                    continue
                # Only an open item's file is served (and drawn as page images); a link-only
                # item's private copy stays where the harvest put it.
                if bundle.renditions[0].source_url.startswith(SITE):
                    blobs.put(data)
                corpus.conn.commit()
                done += 1
                if i % 100 == 0:
                    print(f"[{i}/{len(todo)}] {row['id']}", file=sys.stderr)
    print(f"imported {done} of {len(todo)}", file=sys.stderr)


if __name__ == "__main__":
    main()
