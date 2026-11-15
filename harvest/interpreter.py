#!/usr/bin/env python3
"""Harvest Interpreter: A Journal of Latter-day Saint Faith and Scholarship (link-only tier).

Reads interpreterfoundation.org/journal-sitemap.xml for every article, each article page
for its metadata (the WordPress record inside the page's Next.js payload) and its offprint
PDF link, then fetches the PDF from cdn.interpreterfoundation.org. DOIs (2012-2018) come
from Crossref's list for Interpreter's prefix, 10.67160. Never touches /api, /_next or
/search, which the site's robots.txt disallows.

    python3 harvest/interpreter.py --out /data/lectern/links/interpreter [--limit N] [--slugs a,b]

Each offprint has front pages (cover, licence) before the article, and how many has
changed over the years, so label_offset is read from the PDF's running heads with
pdftotext (poppler) when it's installed, and left null when the heads don't agree.

Re-runnable: an article whose record and file are on disk is skipped, and the manifest
is rewritten from the records in <out>/meta/.
"""

import argparse
import collections
import datetime
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SITE = "https://interpreterfoundation.org"
CDN = "https://cdn.interpreterfoundation.org/jnlpdf/"
UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
DELAY = 1.5  # seconds between requests to one host
NS = "interpreter"
COLLECTION = "Interpreter: A Journal of Latter-day Saint Faith and Scholarship"
LICENCE = {
    "id": "CC-BY-NC-ND-4.0",
    "evidence_url": "https://interpreterfoundation.org/foundation/copyrights/",
    "quote": "All content posted on The Interpreter Foundation’s websites is licensed under a "
    "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License.",
}
DISALLOWED = ("/api", "/_next", "/search", "/es/", "/fr/", "/pt-pt/")


class Challenge(Exception):
    pass


class Gone(Exception):
    pass


def log(*a):
    print(datetime.datetime.now().strftime("%H:%M:%S"), *a, flush=True)


_last = {}


def fetch(url, want_pdf=False):
    """GET url politely. Returns bytes. Raises Challenge on a bot check, Gone on 404/410."""
    parts = urllib.parse.urlsplit(url)
    if parts.netloc == "interpreterfoundation.org" and parts.path.startswith(DISALLOWED):
        raise Gone(f"robots.txt disallows {url}")
    host = parts.netloc
    for attempt in range(4):
        wait = _last.get(host, 0) + DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last[host] = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body, hdrs, status = r.read(), r.headers, r.status
        except urllib.error.HTTPError as e:
            body, hdrs, status = e.read() or b"", e.headers, e.code
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            log("  network error", url, e, "- retrying")
            time.sleep(10 * (attempt + 1))
            continue
        if any(k.lower().endswith("-mitigated") for k in hdrs.keys()) or (
            status in (403, 503) and re.search(rb"(?i)just a moment|challenge|captcha|are you a robot", body[:20000])
        ):
            raise Challenge(f"{status} at {url}")
        if status == 429:
            ra = hdrs.get("Retry-After", "")
            pause = min(int(ra), 600) if ra.isdigit() else 120
            log("  429 rate limited, waiting", pause, "s")
            time.sleep(pause)
            continue
        if status in (404, 410):
            raise Gone(f"{status} {url}")
        if status >= 500:
            log("  server error", status, url, "- retrying")
            time.sleep(15 * (attempt + 1))
            continue
        if status != 200:
            raise Gone(f"{status} {url}")
        if want_pdf and not body.startswith(b"%PDF"):
            raise Gone(f"not a PDF ({len(body)} bytes, starts {body[:20]!r}) at {url}")
        return body
    raise Gone(f"gave up after retries: {url}")


def flight(page):
    """The Next.js flight payload of a page, as one decoded string."""
    parts = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', page)
    return "".join(json.loads('"' + p + '"') for p in parts)


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def page_range(s):
    """'25-55' -> ('25-55', 25); '421–442' -> ('421-442', 421); 'vii-xx' -> ('vii-xx', None)."""
    s = re.sub(r"\s*[–—-]\s*", "-", (s or "").strip())
    if not s:
        return None, None
    m = re.match(r"(\d+)", s)
    return s, (int(m.group(1)) if m else None)


def running_head_offset(path, expect=()):
    """printed page - PDF page, from the page numbers in the running heads; None if unsure.

    A short article has few heads, so fewer votes do when they give an offset the journal's
    usual layouts predict (expect) and nothing disagrees."""
    try:
        out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    pages = out.decode("utf-8", "replace").split("\f")
    votes = collections.Counter()
    for i, pg in enumerate(pages, 1):
        lines = [l.strip() for l in pg.splitlines() if l.strip()]
        found = set()
        for l in lines[:2] + lines[-2:]:
            for m in (re.match(r"(\d{1,4})\b(?![./:])", l), re.search(r"(?<![\d/(.,:-])(\d{1,4})$", l)):
                if m:
                    found.add(int(m.group(1)) - i)
        votes.update(found)
    if not votes:
        return None
    (off, n), *rest = votes.most_common(2) + [(None, 0)]
    numbered = len(pages) - 1
    if n >= 3 and n >= 0.4 * numbered and n > 2 * rest[0][1]:
        return off
    if off in expect and n >= 1 and rest[0][1] == 0:
        return off
    return None


def pdf_pages(path):
    try:
        out = subprocess.run(["pdfinfo", path], capture_output=True, text=True, timeout=60).stdout
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        return int(m.group(1)) if m else None
    except (OSError, subprocess.SubprocessError):
        return None


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def write_manifest(out):
    meta = os.path.join(out, "meta")
    rows = []
    for name in sorted(os.listdir(meta)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(meta, name), encoding="utf-8") as f:
            row = json.load(f)
        if row.get("file") and os.path.exists(os.path.join(out, row["file"])):
            rows.append(row)
    tmp = os.path.join(out, "manifest.jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, os.path.join(out, "manifest.jsonl"))
    return len(rows)


def crossref_dois():
    """slug -> DOI for every Interpreter DOI Crossref has."""
    dois, offset = {}, 0
    while True:
        q = urllib.parse.urlencode({"rows": 500, "offset": offset, "select": "DOI,resource"})
        try:
            msg = json.loads(fetch(f"https://api.crossref.org/prefixes/10.67160/works?{q}"))["message"]
        except (Gone, Challenge, ValueError) as e:
            log("  Crossref unavailable, going on without DOIs:", e)
            return dois
        items = msg.get("items") or []
        for it in items:
            url = ((it.get("resource") or {}).get("primary") or {}).get("URL", "")
            m = re.search(r"interpreterfoundation\.org/(?:journal/)?([^/?#]+)", url)
            if m:
                dois[m.group(1)] = it["DOI"].lower()
        offset += len(items)
        if not items or offset >= msg.get("total-results", 0):
            return dois


def harvest_article(out, slug, dois):
    landing = f"{SITE}/journal/{slug}"
    page = fetch(landing).decode("utf-8", "replace")
    s = flight(page)
    i = s.find('{"data":{"id":')
    if i < 0:
        raise Gone(f"no article record on {landing}")
    d = json.JSONDecoder().raw_decode(s, i)[0]["data"]
    acf = d.get("acf") or {}
    authors = [text((c.get("data") or {}).get("display_name")) for c in d.get("coauthors") or []]
    authors = [a for a in authors if a]
    if not authors and acf.get("sub_heading"):
        authors = [a.strip() for a in re.split(r",\s*(?:and\s+)?|\s+and\s+", text(acf["sub_heading"])) if a.strip()]
    pages, start = page_range(acf.get("page_range"))
    item = slugify(slug)
    row = {
        "id": f"{NS}:{item}",
        "kind": "article",
        "title": text((d.get("title") or {}).get("rendered")),
        "authors": authors,
        "published": (d.get("date") or "")[:10] or (acf.get("volume_year") or None),
        "collection": COLLECTION,
        "volume": (acf.get("volume_number") or "").strip() or None,
        "issue": None,
        "pages": pages,
        "doi": dois.get(slug),
        "label_offset": None,
        "landing_url": landing,
        "source_url": None,
        "licence": LICENCE,
    }
    pdf = (acf.get("pdf_filename") or "").strip()
    if not pdf:
        m = re.search(r'href="(https://cdn\.interpreterfoundation\.org/jnlpdf/[^"]+\.pdf)"', page)
        pdf = m.group(1).rsplit("/", 1)[1] if m else ""
    body = None
    if pdf:
        src = pdf if pdf.startswith("http") else CDN + urllib.parse.quote(pdf)
        try:
            body = fetch(src, want_pdf=True)
        except Gone as e:
            log("  PDF missing, keeping the HTML page:", e)
    if body is not None:
        rel = f"files/{item}.pdf"
        path = os.path.join(out, rel)
        with open(path + ".part", "wb") as f:
            f.write(body)
        os.replace(path + ".part", path)
        off = running_head_offset(path, () if start is None else (start - 3, start - 2))
        row.update(source_url=src, file=rel, media_type="application/pdf", label_offset=off,
                   pdf_pages=pdf_pages(path))
        if start is not None and off is not None and off != start - 3:
            log(f"  note: running heads give offset {off}, not start-3 = {start - 3}")
    else:
        # No offprint: keep the article page itself, which carries the full text with [Page N] markers.
        log("  no PDF:", slug)
        body = page.encode("utf-8")
        rel = f"files/{item}.html"
        with open(os.path.join(out, rel), "wb") as f:
            f.write(body)
        row.update(source_url=landing, file=rel, media_type="text/html", pdf_pages=None)
    row.update(
        sha256=hashlib.sha256(body).hexdigest(),
        bytes=len(body),
        fetched_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    write_json(os.path.join(out, "meta", item + ".json"), row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new items (testing)")
    ap.add_argument("--slugs", default="", help="comma-separated article slugs only (testing)")
    args = ap.parse_args()
    out = args.out
    os.makedirs(os.path.join(out, "files"), exist_ok=True)
    os.makedirs(os.path.join(out, "meta"), exist_ok=True)

    if args.slugs:
        slugs = args.slugs.split(",")
    else:
        sm = fetch(f"{SITE}/journal-sitemap.xml").decode("utf-8", "replace")
        slugs = list(dict.fromkeys(re.findall(r"<loc>https://interpreterfoundation\.org/journal/([^<]+?)/?</loc>", sm)))
    log(len(slugs), "articles in the sitemap")
    dois = crossref_dois()
    log(len(dois), "DOIs from Crossref")

    done = fresh = failed = 0
    t0 = time.monotonic()
    for i, slug in enumerate(slugs, 1):
        meta = os.path.join(out, "meta", slugify(slug) + ".json")
        if os.path.exists(meta):
            with open(meta, encoding="utf-8") as f:
                if os.path.exists(os.path.join(out, json.load(f)["file"])):
                    done += 1
                    continue
        try:
            row = harvest_article(out, slug, dois)
            fresh += 1
            log(f"[{i}/{len(slugs)}] {row['id']} v{row['volume']} {row['pages']} off={row['label_offset']} {row['bytes']//1024}KB")
        except Gone as e:
            failed += 1
            log(f"[{i}/{len(slugs)}] SKIP {slug}: {e}")
        except Challenge as e:
            log("STOP: bot challenge:", e)
            write_manifest(out)
            sys.exit(2)
        if fresh and fresh % 50 == 0:
            rate = fresh / (time.monotonic() - t0) * 3600
            log(f"  manifest: {write_manifest(out)} rows; {rate:.0f} items/hour")
        if args.limit and fresh >= args.limit:
            break
    n = write_manifest(out)
    log(f"done: {fresh} new, {done} already had, {failed} skipped; manifest {n} rows")


if __name__ == "__main__":
    main()
