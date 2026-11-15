# The shelf

`volumes.jsonl` is the list of what Lectern holds: one row per book.

```json
{"id": "npnf2:04-select-works-and-letters", "sha256": "…", "title": "Select Works and Letters",
 "authors": ["Athanasius", "Archibald Robertson (ed.)"], "publisher": "New York, Christian Literature Company",
 "shelf": "church-fathers", "series": "Nicene and Post-Nicene Fathers, Series 2", "volume": "4",
 "pd": {"year": 1892, "imprint": "The title page reads: “…”.", "front_matter": "…"}}
```

- `id` is permanent: `<ns>:<local>`, where `ns` is the series for the five big sets (`anf`,
  `npnf1`, `npnf2`, `icc`, `egt`) and the Journal of Discourses (`jod`), and otherwise the
  principal author's surname (the ancient author for a translation).
- `sha256` names the scan file. The build finds the file through the catalogue of the
  collection the shelf was drawn from; no file paths are kept here.
- `shelf` is one of the ids in `site/src/lib/cite.ts` (`SHELVES`).
- `pd` is the public-domain evidence that goes into each book's licence fact and is shown on
  its record: the year, the imprint words where they could be read verbatim from the scan,
  and what the front-matter check found.

## How the list was made (2026-11-14)

The shelf is drawn from a private research collection of about 8,700 volumes whose catalogue
records author, title, year and publisher for each one.

1. **Candidates.** 461 volumes whose best year (the catalogue's own, else a verified Open
   Library or web-found year) is before 1931.
2. **Front matter, by pattern.** The text of each scan's first twelve pages was searched for
   any year from 1931 on, a copyright notice or an ISBN. 293 had none. 36 had a post-1930
   copyright notice or an ISBN; 132 had a later year of some other kind.
3. **Front matter, read.** Those 168 were read by Claude Haiku against a written rule:
   reprint lines ("First printed 1914, reprinted 1951"), digitisation notices and library
   stamps pass; a copyright notice, ISBN, or revision, new edition, introduction or
   translation dated 1931 or later does not; anything unclear is out. It passed 109, kept out
   56, and could not decide 3 (kept out). A random 20 of its calls were checked by hand and
   agreed.
4. **Files.** 7 files that were not PDFs (Word and spreadsheet transcriptions) were dropped.
5. **Catalogue.** The 395 left were catalogued by Claude Haiku from their title pages: title,
   authors with roles, publisher, place, year, shelf, series, volume, and the imprint words.
   An imprint quote is kept only where it is found word for word in the scan's OCR (81).
6. **Duplicates.** 43 second scans of the same volume were dropped, leaving 352.

What was not done, and could be next:

- Books from 1931 to 1963 are in the public domain if their copyright was not renewed. The
  collection has 507 dated in those years. Each needs a search of the renewal records (the
  Stanford Copyright Renewal Database, or the NYPL's CCE data) before it can be added.
- The 238 books first published before 1931 whose scan is a later edition were left out
  wholesale. Some are unchanged reprints and could come in after a closer look.
- The Latter-day Saint books and manuals inventoried for Refrain
  (`websites/refrain/research/11-inventory.csv`, 158 published before 1931) that the
  collection lacks could come in from the Internet Archive scans listed there.
