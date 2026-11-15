# Harvest

Fetches the journals and archives in [`shelf/links.md`](../shelf/links.md) to VM 100, one
script per source, each writing a manifest that `build/ingest_links.py` reads into the corpus.

Run on VM 100 from `/opt/lectern` with the system Python (standard library only):

```sh
setsid nohup python3 harvest/<source>.py --out /data/lectern/links/<source> \
  > /data/lectern/links/<source>.log 2>&1 &
```

Each script is re-runnable: it skips files it already has and rewrites the manifest from what
is on disk. It sends `User-Agent: Lectern/0.1 (+https://lectern.restorationcommons.org/about)`,
waits at least a second between requests to one host, and stops at a bot challenge rather
than trying to get past it.

## The manifest

`<out>/manifest.jsonl`, one JSON object per item:

| Field | |
|---|---|
| `id` | `<ns>:<slug>`. `ns` names the journal or collection (`byus`, `dialogue`, `interpreter`); `slug` is stable, from the publisher's own URL or volume and issue. Lowercase, `[a-z0-9-]`. |
| `kind` | `article`, `book`, or `blog` |
| `title`, `authors`, `published` | `published` is `YYYY`, `YYYY-MM` or `YYYY-MM-DD` |
| `collection` | The journal or archive's name, as it should show: `BYU Studies Quarterly` |
| `volume`, `issue`, `pages`, `doi` | When known. `pages` is the printed range, `"123-145"` |
| `label_offset` | For a PDF: printed page number = PDF page index (1-based) + `label_offset`. `null` when unknown or not constant. |
| `landing_url` | The item's page at the publisher |
| `source_url` | What "Read at source" opens: the PDF's URL (so `#page=N` lands on the page), or the HTML page |
| `file`, `media_type`, `sha256`, `bytes`, `fetched_at` | The private copy, relative to `<out>` |
| `licence` | `{"id", "evidence_url", "quote"}`: an SPDX-style id (`CC-BY-4.0`, `CC-BY-NC-ND-4.0`), `public-domain`, `all-rights-reserved`, or `unknown`, with where the statement is and its words. `open_journals.py` adds `url` (the licence deed), `scope: "journal"` when the words are the journal's policy rather than a statement on the item, and `item_statement` (what the item itself carries, e.g. its OAI `dc:rights`) |
| `jstor_url`, `ia_identifier` | Optional, from `ia_fetch.py`: JSTOR's stable URL for Early Journal Content (JSTOR asks to be credited with it), and the Internet Archive item. Its `licence` adds `rule_url` (the public-domain rule) and, for JSTOR, `terms_url` |
| `section` | Optional: the journal's own section for the item (`Articles`, `Reviews`, `Editorial`) |
| `number` | Optional: the publisher's own serial number for the item (`scripturecentral.py`: 20 for "KnoWhy #20") |
| `abstract` | Optional: the publisher's abstract (`scholarsarchive.py`, from OAI; the only text a row has while its `file` is null) |
| `pdf_pages` | Optional: the PDF's page count |

Private copies of link-only items stay on VM 100. They are never published.

`scholarsarchive.py` writes a row for every record even when the PDF is behind its bot challenge: those rows have `file` (and the other file fields) null, and a re-run fills them in once the PDFs come through.

`bhr_archive.py` writes no manifest: it keeps only the metadata of the B. H. Roberts Foundation's
archive records (no transcriptions or scans), one record a line, in `<out>/records.jsonl`. Its docstring
lists the fields.
