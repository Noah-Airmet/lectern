#!/usr/bin/env python3
"""The B. H. Roberts Foundation's primary source archive, as metadata only.

Each archive record is an excerpt: a bibliography line, a transcription of a passage (often
from an in-copyright book) and a scan, offered for non-commercial personal research. This
keeps none of the transcriptions or scans. It writes one line per record to
<out>/records.jsonl (not a manifest): id, bibliography, date, type, author, subjects, which
Mormonr Q&As use it, and the link to the original source where the record gives one. It is
for listing the pre-1931 books the Q&As cite, and perhaps a "Mormonr cites this page" link.

How it reaches the records, the same way the archive page (https://bhroberts.org/archive)
does:
  1. the page's Algolia index, `prod_records`, with the page's public search-only key, one
     query per subject (one index entry per subject a record sits under), asking only for
     metadata fields;
  2. the page's own `/records?ids=` endpoint, for each record's external source link and
     exact dates (the transcriptions it also returns are dropped on read, never written);
  3. each English Mormonr Q&A's research page, for the record anchors it lists
     (`#re-<subject>-<record>`), which say which Q&A uses which record.

    python3 harvest/bhr_archive.py --out /data/lectern/links/bhr-archive [--limit-subjects N --limit-qnas N]
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit

UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
ALGOLIA_APP = "VNIJAENPNI"
ALGOLIA_KEY = "5c55e23c1897a3216beb1ae9e9c5e0e7"  # public search-only key, from the archive page
ALGOLIA_URL = f"https://{ALGOLIA_APP}-dsn.algolia.net/1/indexes/prod_records/query"
RECORDS_URL = "https://bhroberts.org/records?ids="
MORMONR_SITEMAP = "https://mormonr.org/sitemap.xml"
FIELDS = ["objectID", "record_id", "title", "subject", "hearsay_tags", "people", "scribes", "source",
          "source_tags", "bibliography", "type", "tags", "ts_start", "ts_end", "date"]
BATCH = 50


class BotChallenge(Exception):
    pass


class Fetcher:
    """One request at a time, at least `delay` seconds between requests to a host."""

    def __init__(self, delay=1.0):
        self.delay = delay
        self.last = {}

    def get(self, url, data=None, headers=None, tries=3):
        host = urlsplit(url).netloc
        for attempt in range(tries):
            wait = self.last.get(host, 0) + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last[host] = time.monotonic()
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    body = r.read()
                check_challenge(url, 200, body)
                return body
            except urllib.error.HTTPError as e:
                body = e.read()
                check_challenge(url, e.code, body)
                if e.code in (500, 502, 503, 504) and attempt + 1 < tries:
                    time.sleep(10 * (attempt + 1))
                    continue
                raise
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if attempt + 1 < tries:
                    print(f"  retry {url}: {e}", flush=True)
                    time.sleep(10 * (attempt + 1))
                    continue
                raise


def check_challenge(url, status, body):
    head = body[:20000].decode("utf-8", "replace").lower()
    signs = ("cf-chl", "just a moment...", "challenge-platform", "captcha", "attention required")
    if status in (403, 429) or (status == 503 and any(s in head for s in signs)) or (
        status == 200 and "<title>just a moment" in head
    ):
        raise BotChallenge(f"{status} at {url}")


def algolia(fx, **params):
    p = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in params.items()}
    body = json.dumps({"params": urlencode(p)}).encode()
    headers = {"X-Algolia-Application-Id": ALGOLIA_APP, "X-Algolia-API-Key": ALGOLIA_KEY,
               "Content-Type": "application/json"}
    return json.loads(fx.get(ALGOLIA_URL, data=body, headers=headers))


def facet_filter(attr, value):
    if value.startswith("-"):
        value = "\\" + value
    return f"{attr}:{value}"


def slate_text(nodes):
    """Plain text, and the italic runs (titles, mostly), from a Slate document."""
    text, italics = [], []

    def walk(n):
        if isinstance(n, list):
            for c in n:
                walk(c)
        elif isinstance(n, dict):
            if "text" in n:
                text.append(n["text"])
                if n.get("italic") and n["text"].strip():
                    italics.append(n["text"].strip())
            else:
                walk(n.get("children", []))
                if n.get("type") in ("p", "paragraph", "li"):
                    text.append("\n")

    walk(nodes or [])
    return re.sub(r"[ \t]+", " ", "".join(text)).strip(), italics


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def save_jsonl(path, rows):
    tmp = path + ".part"
    with open(tmp, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def year_of(date):
    m = re.match(r"(-?\d{1,4})", date or "")
    return int(m.group(1)) if m else None


def phase_algolia(fx, work, limit):
    path = os.path.join(work, "algolia.jsonl")
    if os.path.exists(path):
        hits = load_jsonl(path)
        print(f"algolia: {len(hits)} entries on disk", flush=True)
        return hits
    facets = algolia(fx, query="", hitsPerPage=0, facets=["subject"], maxValuesPerFacet=1000)
    total, subjects = facets["nbHits"], facets["facets"]["subject"]
    print(f"algolia: {total} entries, {len(subjects)} subjects (summing to {sum(subjects.values())})", flush=True)
    hits, seen = [], set()
    for i, (subject, count) in enumerate(sorted(subjects.items()), 1):
        if limit is not None and i > limit:
            break
        if count > 1000:
            print(f"  WARNING: {subject!r} has {count} entries; Algolia returns only the first 1000", flush=True)
        page = 0
        while True:
            r = algolia(fx, query="", facetFilters=[[facet_filter("subject", subject)]], hitsPerPage=1000,
                        page=page, attributesToRetrieve=FIELDS, attributesToHighlight=[], attributesToSnippet=[])
            for h in r["hits"]:
                h = {k: v for k, v in h.items() if k in FIELDS}
                if h["objectID"] not in seen:
                    seen.add(h["objectID"])
                    hits.append(h)
            page += 1
            if page >= r.get("nbPages", 0):
                break
        if i % 50 == 0:
            print(f"  [{i}/{len(subjects)}] subjects, {len(hits)} entries", flush=True)
    print(f"algolia: {len(hits)} entries read of {total}", flush=True)
    if limit is None:
        save_jsonl(path, hits)
    return hits


def record_meta(r):
    """The metadata kept from one /records response item. Transcriptions, commentary, scans
    and biographies are not copied."""
    bib, italics = slate_text(r.get("bibliography_slate"))
    ext = (r.get("external_source") or "").strip()
    events = []
    for e in r.get("events") or []:
        ev = e.get("event") or {}
        events.append({
            "id": e.get("event_id") or ev.get("id"),
            "name": ev.get("name"),
            "summary": slate_text(e.get("information_slate"))[0] or None,
            "hearsay": e.get("information_tags") or [],
        })
    return {
        "record_id": r.get("id"),
        "bibliography": bib or None,
        "bibliography_italics": italics,
        "date_start": r.get("source_date_start"),
        "date_end": r.get("source_date_end"),
        "date_precision": r.get("source_date_precision"),
        "type": r.get("type"),
        "source": (r.get("source_person") or {}).get("name"),
        "scribes": [p.get("name") for p in r.get("scribe_people") or [] if p.get("name")],
        "source_tags": r.get("source_tags") or [],
        "external_source": ext if ext.lower().startswith("http") else None,
        "subjects": events,
    }


def phase_records(fx, work, ids):
    path = os.path.join(work, "records_meta.jsonl")
    have = {r["record_id"]: r for r in load_jsonl(path)}
    todo = [i for i in ids if i not in have]
    print(f"records: {len(have)} on disk, {len(todo)} to fetch", flush=True)
    missing = []
    for n in range(0, len(todo), BATCH):
        batch = todo[n:n + BATCH]
        data = json.loads(fx.get(RECORDS_URL + ",".join(batch)))
        got = set()
        for r in data.get("records") or []:
            m = record_meta(r)
            have[m["record_id"]] = m
            got.add(m["record_id"])
        missing += [i for i in batch if i not in got]
        save_jsonl(path, have.values())
        if (n // BATCH + 1) % 20 == 0:
            print(f"  {n + len(batch)}/{len(todo)} records", flush=True)
    if missing:
        print(f"records: {len(missing)} ids not returned by /records, e.g. {missing[:5]}", flush=True)
    return have


def phase_qnas(fx, work, limit=None):
    """Which records each English Q&A lists on its research page."""
    path = os.path.join(work, "qnas.json")
    qnas = json.load(open(path)) if os.path.exists(path) else {}
    sitemap = fx.get(MORMONR_SITEMAP).decode("utf-8")
    urls = [u for u in re.findall(r"<loc>(https://mormonr\.org/qnas/[A-Za-z0-9]+/[A-Za-z0-9_-]+)</loc>", sitemap)]
    print(f"qnas: {len(urls)} English Q&As, {len(qnas)} on disk", flush=True)
    if limit is not None:
        urls = urls[:limit]
    for i, url in enumerate(urls, 1):
        if url in qnas:
            continue
        try:
            page = fx.get(url + "/research").decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            print(f"  [{i}/{len(urls)}] {e.code} {url}/research", flush=True)
            continue
        m = re.search(r"<title>(.*?)</title>", page, re.S)
        anchors = sorted(set(re.findall(r'id="re-([A-Za-z0-9]+)-([A-Za-z0-9]+)"', page)))
        qnas[url] = {"title": html.unescape(m.group(1)).strip() if m else None,
                     "anchors": [f"{e}-{r}" for e, r in anchors]}
        del page
        with open(path + ".part", "w") as f:
            json.dump(qnas, f, ensure_ascii=False)
        os.replace(path + ".part", path)
        if i % 10 == 0:
            print(f"  [{i}/{len(urls)}] Q&As", flush=True)
    return qnas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit-subjects", type=int, help="read only N subjects (for testing)")
    ap.add_argument("--limit-qnas", type=int, help="read only N Q&A research pages (for testing)")
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()
    work = os.path.join(args.out, "work")
    os.makedirs(work, exist_ok=True)
    fx = Fetcher(args.delay)

    try:
        hits = phase_algolia(fx, work, args.limit_subjects)
        ids = sorted({h["record_id"] for h in hits if h.get("record_id")})
        print(f"{len(ids)} unique records", flush=True)
        meta = phase_records(fx, work, ids)
        qnas = phase_qnas(fx, work, args.limit_qnas)
    except BotChallenge as e:
        print(f"STOP: bot challenge, {e}", flush=True)
        sys.exit(2)

    by_anchor = {}
    for url, q in qnas.items():
        for a in q["anchors"]:
            by_anchor.setdefault(a, []).append(url)
    entries = {}
    for h in hits:
        entries.setdefault(h["record_id"], []).append(h)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows, pre1931 = [], 0
    for rid in ids:
        hs = entries[rid]
        m = meta.get(rid) or {}
        subjects = m.get("subjects") or []
        known = {s["id"] for s in subjects}
        for h in hs:  # subjects the record API did not list, from the index
            sid = h["objectID"].split("-")[0]
            if sid not in known:
                known.add(sid)
                subjects.append({"id": sid, "name": h.get("subject"), "summary": h.get("title"),
                                 "hearsay": h.get("hearsay_tags") or []})
        used = []
        for s in subjects:
            for url in by_anchor.get(f"{s['id']}-{rid}", []):
                used.append({"title": qnas[url]["title"], "url": url,
                             "research_url": f"{url}/research#re-{s['id']}-{rid}", "subject_id": s["id"]})
        h0 = hs[0]
        bib = m.get("bibliography") or html.unescape(h0.get("bibliography") or "").strip().strip('"') or None
        date_start = m.get("date_start")
        year = year_of(date_start) if date_start else year_of(h0.get("date"))
        if year is not None and year < 1931:
            pre1931 += 1
        rows.append({
            "record_id": rid,
            "bibliography": bib,
            "bibliography_italics": m.get("bibliography_italics", []),
            "date": h0.get("date"),
            "date_start": date_start,
            "date_end": m.get("date_end"),
            "date_precision": m.get("date_precision"),
            "year": year,
            "type": h0.get("type") or m.get("type"),
            "source": h0.get("source") or m.get("source"),
            "scribes": m.get("scribes") or h0.get("scribes") or [],
            "tags": sorted({t for h in hs for t in h.get("tags") or []}),
            "subjects": subjects,
            "qnas": used,
            "external_source": m.get("external_source"),
            "fetched_at": now,
        })
    save_jsonl(os.path.join(args.out, "records.jsonl"), rows)
    print(f"done: {len(rows)} records ({len(hits)} index entries), {pre1931} dated before 1931, "
          f"{sum(1 for r in rows if r['qnas'])} used by a Q&A, "
          f"{sum(1 for r in rows if r['external_source'])} with an external source link", flush=True)


if __name__ == "__main__":
    main()
