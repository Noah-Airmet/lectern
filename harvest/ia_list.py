#!/usr/bin/env python3
"""List the public-domain Internet Archive sets for the open tier and size their files.
Downloads nothing but search results and item metadata.

    python3 harvest/ia_list.py --out /data/lectern/links/ia [--sets chl,ejc,...]

For each set it lists every item with advancedsearch, then reads /metadata/<id> and
writes one line per item to <out>/<set>.jsonl: identifier, title, date, volume, issue
(and journal and page range for JSTOR items), page count, the collections, whether IA
marks it restricted, and the name and size of the files Lectern would want:

  pdf           the item's PDF (Text PDF first)
  djvu_xml      OCR with word positions (DjVu XML)
  hocr          OCR with word positions (hOCR), and chocr, its gzipped form
  djvu_txt      plain OCR text
  page_numbers  printed page number per leaf (_page_numbers.json)

Small sets run first. CHL and EJC then run interleaved in a shuffled order, so the
running totals in the log extrapolate fairly before they finish. Re-runs skip items
already listed. At the end <out>/totals.json has the sums per set.
"""

import argparse
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
GAP = 1.05
_last = [0.0]

EJC_TITLES = ["jbibllite", "jsocibiblliteexe", "oldteststud", "oldnewteststud", "biblicalworld",
              "amerjtheo", "hebraica", "amerjsemilanglit", "harvtheorevi", "jewiquarrevi",
              "jreligion"]

SETS = {
    # pre-1931 issue runs
    "bibsac": "collection:pub_the-bibliotheca-sacra AND year:[1800 TO 1930]",
    "exptimes": "collection:pub_expository-times AND year:[1800 TO 1930]",
    "jts": "collection:pub_journal-of-theological-studies AND year:[1800 TO 1930]",
    "pefqs": "collection:pub_palestine-exploration-quarterly AND year:[1800 TO 1930]",
    # Princeton Seminary's issue scans (the Google scans of the same run are left out);
    # every item is dated 1903, the first year, so the real year comes from `volume`.
    "ptr": 'title:("princeton theological review") AND collection:Princeton',
    # JBL, HTR and Journal of Religion issues after the EJC cut-off of 1922
    "ejc-1923-1930": ("collection:(pub_journal-of-biblical-literature OR "
                      "pub_harvard-theological-review OR pub_journal-of-religion) "
                      "AND year:[1923 TO 1930]"),
    # one item per article; one query per journal, as advancedsearch pages stop at 10,000
    "ejc": [f"collection:jstor_ejc AND journalabbrv:{j}" for j in EJC_TITLES],
    # every Church History Library upload dated before 1931
    "chl": "collection:churchhistorylibrary AND year:[1800 TO 1930]",
}
BIG = ("chl", "ejc")

FIELDS = ["identifier", "title", "date", "volume", "issue", "journaltitle", "journalabbrv",
          "pagerange", "collection", "item_size", "imagecount"]


def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def get_json(url, tries=5):
    for attempt in range(tries):
        wait = _last[0] + GAP - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
            _last[0] = time.monotonic()
            return json.loads(body)
        except urllib.error.HTTPError as e:
            _last[0] = time.monotonic()
            body = (e.read() or b"")[:20000].lower()
            if e.code in (403, 429, 503) and any(m in body for m in
                                                 (b"captcha", b"challenge", b"just a moment")):
                log(f"STOP: bot challenge ({e.code}) at {url}")
                sys.exit(2)
            log(f"  {e.code} on {url}; retry {attempt + 1}")
            time.sleep(30 * (attempt + 1))
        except Exception as e:
            _last[0] = time.monotonic()
            log(f"  {e} on {url}; retry {attempt + 1}")
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"gave up on {url}")


def search(queries):
    if isinstance(queries, list):
        return [d for q in queries for d in search(q)]
    q, docs, page = queries, [], 1
    while True:
        params = [("q", q), ("rows", "10000"), ("page", str(page)), ("output", "json"),
                  ("sort[]", "identifier asc")] + [("fl[]", f) for f in FIELDS]
        r = get_json("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params))
        resp = r["response"]
        docs += resp["docs"]
        if len(docs) >= resp["numFound"] or not resp["docs"]:
            return docs
        page += 1


def pick(files, test):
    hits = [f for f in files if test(f)]
    return {"name": hits[0]["name"], "size": int(hits[0].get("size") or 0)} if hits else None


def pdf_of(files):
    pdfs = [f for f in files if f["name"].lower().endswith(".pdf")]
    for fmt in ("Text PDF", "Image Container PDF", "Additional Text PDF"):
        for f in pdfs:
            if f.get("format") == fmt:
                return {"name": f["name"], "size": int(f.get("size") or 0)}
    return {"name": pdfs[0]["name"], "size": int(pdfs[0].get("size") or 0)} if pdfs else None


def year_of(doc):
    for s in (doc.get("volume"), doc.get("date")):
        m = re.search(r"\b(1[6-9]\d\d|20\d\d)\b", str(s or ""))
        if m:
            return int(m.group(1))
    return None


def row(set_name, doc, meta):
    m = meta.get("metadata", {})
    files = meta.get("files", [])
    one = lambda v: v[0] if isinstance(v, list) else v
    r = {
        "identifier": doc["identifier"],
        "title": one(doc.get("title")),
        "date": one(doc.get("date")),
        "volume": one(doc.get("volume")),
        "issue": one(doc.get("issue")),
        "pages": int(m["imagecount"]) if str(m.get("imagecount", "")).isdigit() else None,
        "collections": doc.get("collection") if isinstance(doc.get("collection"), list)
        else [doc.get("collection")],
        "restricted": bool(m.get("access-restricted-item") not in (None, "false", False)),
        "item_size": doc.get("item_size"),
        "pdf": pdf_of(files),
        "djvu_xml": pick(files, lambda f: f["name"].endswith("_djvu.xml")),
        "hocr": pick(files, lambda f: f["name"].endswith("_hocr.html")),
        "chocr": pick(files, lambda f: f["name"].endswith("_chocr.html.gz")),
        "djvu_txt": pick(files, lambda f: f["name"].endswith("_djvu.txt")),
        "page_numbers": pick(files, lambda f: f["name"].endswith("_page_numbers.json")),
    }
    if set_name == "ejc":
        r.update({"journal": one(doc.get("journaltitle")), "journalabbrv": one(doc.get("journalabbrv")),
                  "pagerange": one(doc.get("pagerange")),
                  "jstor_url": one(m.get("jstor-stable-url") or m.get("source"))})
    if set_name == "ptr":
        r["year"] = year_of(doc)
    return r


def size(r, k):
    return (r.get(k) or {}).get("size", 0)


def totals(rows, expected=None):
    t = {"items": len(rows)}
    for k in ("pdf", "djvu_xml", "hocr", "chocr", "djvu_txt", "page_numbers"):
        t[k + "_bytes"] = sum(size(r, k) for r in rows)
        t[k + "_missing"] = sum(1 for r in rows if not r.get(k))
    t["words_bytes"] = sum(size(r, "djvu_xml") or size(r, "hocr") for r in rows)
    t["pages"] = sum(r.get("pages") or 0 for r in rows)
    t["restricted"] = sum(1 for r in rows if r.get("restricted"))
    if expected and rows and len(rows) < expected:
        f = expected / len(rows)
        t["expected_items"] = expected
        t["extrapolated"] = {k: round(v * f) for k, v in t.items()
                             if k.endswith("_bytes") or k == "pages"}
    return t


def gb(n):
    return f"{n / 1e9:.1f} GB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sets", default=",".join(SETS))
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    names = [s for s in args.sets.split(",") if s]

    have, queue, expected = {}, {}, {}
    for s in names:
        path = out / f"{s}.jsonl"
        have[s] = [json.loads(l) for l in path.open()] if path.exists() else []
        seen = {r["identifier"] for r in have[s]}
        docs = search(SETS[s])
        if s == "ptr":
            docs = [d for d in docs if (year_of(d) or 0) <= 1930]
        expected[s] = len(docs)
        queue[s] = [d for d in docs if d["identifier"] not in seen]
        log(f"{s}: {len(docs)} items, {len(seen)} already listed")

    def fetch(s, doc):
        meta = get_json("https://archive.org/metadata/" + urllib.parse.quote(doc["identifier"]))
        r = row(s, doc, meta)
        have[s].append(r)
        with (out / f"{s}.jsonl").open("a") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def report(s):
        t = totals(have[s], expected[s])
        (out / "totals.json").write_text(json.dumps(
            {k: totals(have[k], expected[k]) for k in names}, indent=1))
        e = t.get("extrapolated", t)
        log(f"{s}: {t['items']}/{expected[s]}  PDF {gb(t['pdf_bytes'])}, word-position "
            f"{gb(t['words_bytes'])}, page numbers {gb(t['page_numbers_bytes'])}"
            + (f"  (whole set ~PDF {gb(e['pdf_bytes'])}, words {gb(e['words_bytes'])})"
               if "extrapolated" in t else ""))

    for s in [s for s in names if s not in BIG]:
        for doc in queue[s]:
            fetch(s, doc)
        report(s)

    big = [s for s in names if s in BIG]
    rng = random.Random(1931)
    mixed = [(s, d) for s in big for d in queue[s]]
    rng.shuffle(mixed)
    for i, (s, doc) in enumerate(mixed, 1):
        fetch(s, doc)
        if i % 500 == 0:
            for b in big:
                report(b)
    for s in names:
        rows = sorted(have[s], key=lambda r: (str(r.get("date")), r["identifier"]))
        with (out / f"{s}.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        report(s)
    log("done")


if __name__ == "__main__":
    main()
