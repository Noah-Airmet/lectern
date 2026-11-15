"""Build Lectern's working corpus from the shelf list.

    python build/ingest.py --shelf shelf/volumes.jsonl --catalog <catalog.sqlite> --work <dir>

Each row of ``shelf/volumes.jsonl`` names one scan by the SHA-256 of its file. The scan is found
on the machine through the archive catalogue it was selected from (``--catalog``, the GSA's
``catalog.sqlite``), read with the engine's PDF extractor (text and word boxes per page), and
imported as one version of one document with its public-domain licence fact. The PDF goes into
the blob store, so the snapshot can render its pages and serve the file.

Re-runnable: a document already in the corpus is skipped. A row that cannot be read is listed
in ``<work>/set-aside.jsonl`` with the reason, and the run goes on.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

from safetypage.blobs import BlobStore, sha256_file
from safetypage.bundle import Bundle, BundleLicence, BundleVersion, import_bundle
from safetypage.corpus import Corpus
from safetypage.ingest.pdf import NeedsOcrError, PdfError, pdf_outline, pdf_pages
from safetypage.model import Document, Rendition

SITE = "https://lectern.restorationcommons.org"

# Where each GSA shelf's files are on VM 100, and where its OCR'd copies are kept.
SHELF_ROOTS = {
    "Read": Path("/data/research-corpus/source"),
    "Languages": Path("/data/gsa-mirror/Languages"),
    "Visuals": Path("/data/gsa-mirror/Visuals"),
}
OCR_ROOT = Path("/data/gsa-derived/ocr")

PD_RULE_URL = "https://guides.library.cornell.edu/copyright/publicdomain"
PRODUCER = "lectern/shelf-v1"


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def scan_path(catalog: sqlite3.Connection, sha256: str, prefix: Path) -> Path:
    row = catalog.execute(
        "select canonical_path, shelf from volumes where id = ?", (sha256,)
    ).fetchone()
    if row is None:
        raise LookupError("not in the catalogue")
    path, shelf = row
    rel = path.split("/", 1)[1]
    ocr = prefix / OCR_ROOT.relative_to("/") / shelf / rel
    if ocr.is_file():
        return ocr
    return prefix / SHELF_ROOTS[shelf].relative_to("/") / rel


def licence(row: dict, observed: str) -> BundleLicence:
    pd = row["pd"]
    return BundleLicence(
        licence="public-domain",
        evidence_kind="statute",
        evidence_url=PD_RULE_URL,
        evidence_quote=(
            f"Published {pd['year']}. {pd['imprint']} "
            "Works published before 1931 are in the public domain in the United States "
            "(17 U.S.C. 304: a 95-year term, which ran out for 1930 works on 1 January 2026). "
            f"This scan's front matter was checked for later copyright, revision or new matter: "
            f"{pd['front_matter']}"
        ),
        observed_at=observed,
        producer=PRODUCER,
    )


def is_scan(data: bytes) -> bool:
    """Whether the PDF is page pictures with an OCR layer, judged from a page past the front."""
    import pymupdf  # noqa: PLC0415

    with pymupdf.open(stream=data, filetype="pdf") as document:
        page = document[min(10, document.page_count - 1)]
        area = page.rect.width * page.rect.height
        return any(
            (b[2] - b[0]) * (b[3] - b[1]) >= 0.8 * area
            for b in (i["bbox"] for i in page.get_image_info())
        )


def bundle_for(row: dict, data: bytes, sha: str, observed: str) -> Bundle:
    pages = pdf_pages(data)
    outline = pdf_outline(data, pages)
    doc = Document(
        doc_id=row["id"],
        kind="book",
        title=row["title"],
        authors=row.get("authors", []),
        org=row.get("publisher"),
        collection=row["shelf"],
        published=str(row["pd"]["year"]),
        source_url=row.get("source_url") or f"{SITE}/d/{row['id'].replace(':', '/', 1)}",
        added_at=observed,
    )
    url = f"{SITE}/files/{sha}.pdf"
    return Bundle(
        document=doc,
        version=BundleVersion(
            label="r1",
            anchor_kind="page",
            fidelity="ocr" if is_scan(data) else "text_layer",
            source_url=row.get("source_url") or url,
            content_sha256=sha,
            observed_at=observed,
            published=str(row["pd"]["year"]),
        ),
        licence=licence(row, observed),
        renditions=[
            Rendition(
                kind="pdf",
                sha256=sha,
                bytes=len(data),
                media_type="application/pdf",
                source_url=url,
                fetched_at=observed,
            )
        ],
        pages=pages,
        outline=outline,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shelf", type=Path, required=True)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--prefix", type=Path, default=Path("/"), help="where / of VM 100 is mounted")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = [json.loads(line) for line in args.shelf.read_text().splitlines() if line.strip()]
    if args.limit:
        rows = rows[: args.limit]
    catalog = sqlite3.connect(f"{args.catalog.resolve().as_uri()}?mode=ro", uri=True)
    blobs = BlobStore(args.work / "blobs")
    set_aside = (args.work / "set-aside.jsonl").open("a", encoding="utf-8")
    done = 0
    with Corpus.open(args.work / "corpus.sqlite") as corpus:
        for i, row in enumerate(rows, 1):
            if corpus.document(row["id"]) is not None:
                continue
            observed = now()
            try:
                path = scan_path(catalog, row["sha256"], args.prefix)
                sha = sha256_file(path)
                data = path.read_bytes()
                bundle = bundle_for(row, data, sha, observed)
            except (LookupError, OSError, PdfError, NeedsOcrError) as exc:
                reason = f"{type(exc).__name__}: {exc}"
                set_aside.write(json.dumps({"id": row["id"], "reason": reason}) + "\n")
                set_aside.flush()
                print(f"[{i}/{len(rows)}] {row['id']}: set aside ({reason})", file=sys.stderr)
                continue
            blobs.put(data)
            import_bundle(corpus, bundle)
            corpus.conn.commit()
            done += 1
            print(f"[{i}/{len(rows)}] {row['id']}: {len(bundle.pages)} pages", file=sys.stderr)
    print(f"imported {done}", file=sys.stderr)


if __name__ == "__main__":
    main()
