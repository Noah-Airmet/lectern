"""Build Lectern's working corpus from the shelf list.

    python build/ingest.py --shelf shelf/volumes.jsonl --catalog <catalog.sqlite> --work <dir>

Each row of ``shelf/volumes.jsonl`` names one scan by the SHA-256 of its file. The scan is found
on the machine through the archive catalogue it was selected from (``--catalog``, the research collection's
``catalog.sqlite``), read with the engine's PDF extractor (text and word boxes per page), and
imported as one version of one document with its public-domain licence fact. The PDF goes into
the blob store, so the snapshot can render its pages and serve the file.

Re-runnable: a document already in the corpus is skipped. A row that cannot be read is listed
in ``<work>/set-aside.jsonl`` with the reason, and the run goes on.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import sqlite3
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from safetypage.blobs import BlobStore, sha256_file
from safetypage.bundle import Bundle, BundleLicence, BundleVersion, import_bundle
from safetypage.corpus import Corpus
from safetypage.ingest.pdf import NeedsOcrError, PdfError, pdf_outline, pdf_pages
from safetypage.model import Document, NewPage, Rendition
from safetypage.text import clean_text

SITE = "https://lectern.restorationcommons.org"

# Where each shelf of the research collection is on VM 100, and where its OCR'd copies are kept.
SHELF_ROOTS = {
    "Read": Path("/data/research-corpus/source"),
    "Languages": Path("/data/gsa-mirror/Languages"),
    "Visuals": Path("/data/gsa-mirror/Visuals"),
}
OCR_ROOT = Path("/data/gsa-derived/ocr")
# The collection's text of scans that have no text layer: OCR'd (ocrmypdf), one form feed a page.
TEXT_ROOTS = {"Read": Path("/data/research-corpus/processed/text")}

PD_RULE_URL = "https://guides.library.cornell.edu/copyright/publicdomain"
PRODUCER = "lectern/shelf-v1"


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def text_path(catalog: sqlite3.Connection, sha256: str, prefix: Path) -> Path | None:
    row = catalog.execute(
        "select canonical_path, shelf from volumes where id = ?", (sha256,)
    ).fetchone()
    if row is None or row[1] not in TEXT_ROOTS:
        return None
    rel = Path(row[0].split("/", 1)[1]).with_suffix(".txt")
    path = prefix / TEXT_ROOTS[row[1]].relative_to("/") / rel
    return path if path.is_file() else None


def pages_from_text(data: bytes, text: str) -> list[NewPage]:
    """Pages for a scan with no text layer, from its OCR text (one form feed a page).

    No word boxes, so a quote found on such a page cannot be marked on its image."""
    import pymupdf  # noqa: PLC0415

    chunks = text.split("\f")
    pages: list[NewPage] = []
    with pymupdf.open(stream=data, filetype="pdf") as document:
        if abs(len(chunks) - document.page_count) > 1:
            raise PdfError(f"OCR text has {len(chunks)} pages, the scan {document.page_count}")
        for n, page in enumerate(document):
            body = chunks[n] if n < len(chunks) else ""
            pages.append(
                NewPage(
                    text=clean_text(body.strip("\n")),
                    width=round(page.rect.width, 1),
                    height=round(page.rect.height, 1),
                )
            )
    return pages


# A superscript footnote marker flattened onto its word: "made God347 ; and". Only in books
# where it is common (the Schaff e-texts); in an OCR'd scan a digit after letters is more often
# a misread letter.
_MARKER_RE = re.compile(r"(?<=[^\W\d_]{2})(\d{1,4})(?=[\s.,;:!?)\]’”'\"]|$)")
MARKERS_PER_PAGE = 0.5


def separate_markers(pages: list[NewPage]) -> list[NewPage]:
    """Put a space between a word and a footnote marker stuck to it, so the word can be searched
    and quoted. The marker stays in the text; word boxes are moved with the characters."""
    count = sum(len(_MARKER_RE.findall(p.text)) for p in pages)
    if count < MARKERS_PER_PAGE * len(pages):
        return pages
    out: list[NewPage] = []
    for page in pages:
        cuts = [m.start() for m in _MARKER_RE.finditer(page.text)]
        if not cuts:
            out.append(page)
            continue
        text = "".join(
            page.text[a:b] + (" " if b < len(page.text) else "")
            for a, b in zip([0, *cuts], [*cuts, len(page.text)], strict=True)
        )

        # A space goes in at each cut: a word starting at a cut starts after it, one ending there
        # ends before it.
        def start(offset: int, cuts: list[int] = cuts) -> int:
            return offset + bisect.bisect_right(cuts, offset)

        def end(offset: int, cuts: list[int] = cuts) -> int:
            return offset + bisect.bisect_left(cuts, offset)

        words = (
            [(start(a), end(b), *box) for a, b, *box in page.words]
            if page.words is not None
            else None
        )
        out.append(page.model_copy(update={"text": text, "words": words}))
    return out


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


def bundle_for(
    row: dict, data: bytes, sha: str, observed: str, ocr_text: str | None = None
) -> Bundle:
    if ocr_text is None:
        pages = pdf_pages(data)
        outline = pdf_outline(data, pages)
        pages = separate_markers(pages)
    else:
        pages = pages_from_text(data, ocr_text)
        outline = []
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


def prepare(job: tuple[dict, str, str]) -> tuple[dict, Bundle | None, bytes | None, str | None]:
    """Find, hash and parse one scan (in a worker process). Returns the bundle or the reason."""
    row, catalog_path, prefix = job
    catalog = sqlite3.connect(f"{Path(catalog_path).resolve().as_uri()}?mode=ro", uri=True)
    try:
        path = scan_path(catalog, row["sha256"], Path(prefix))
        sha = sha256_file(path)
        data = path.read_bytes()
        try:
            return row, bundle_for(row, data, sha, now()), data, None
        except NeedsOcrError:
            text = text_path(catalog, row["sha256"], Path(prefix))
            if text is None:
                raise
            ocr = text.read_text(encoding="utf-8", errors="replace")
            return row, bundle_for(row, data, sha, now(), ocr), data, None
    except (LookupError, OSError, PdfError, NeedsOcrError) as exc:
        return row, None, None, f"{type(exc).__name__}: {exc}"
    finally:
        catalog.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shelf", type=Path, required=True)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--prefix", type=Path, default=Path("/"), help="where / of VM 100 is mounted")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    rows = [json.loads(line) for line in args.shelf.read_text().splitlines() if line.strip()]
    if args.limit:
        rows = rows[: args.limit]
    blobs = BlobStore(args.work / "blobs")
    set_aside = (args.work / "set-aside.jsonl").open("a", encoding="utf-8")
    done = 0
    with Corpus.open(args.work / "corpus.sqlite") as corpus:
        todo = [r for r in rows if corpus.document(r["id"]) is None]
        jobs = [(r, str(args.catalog), str(args.prefix)) for r in todo]
        # Parsing runs in worker processes; the corpus has one writer, this one.
        with ProcessPoolExecutor(args.workers) as pool:
            for i, (row, bundle, data, reason) in enumerate(pool.map(prepare, jobs), 1):
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
                blobs.put(data)
                corpus.conn.commit()
                done += 1
                print(f"[{i}/{len(todo)}] {row['id']}: {len(bundle.pages)} pages", file=sys.stderr)
    print(f"imported {done}", file=sys.stderr)


if __name__ == "__main__":
    main()
