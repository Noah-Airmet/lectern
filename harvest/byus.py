#!/usr/bin/env python3
"""Harvest BYU Studies Quarterly from byustudies.byu.edu (link-only tier).

Walks the site's issue index, each issue's table of contents and the sitemap's
/article/ pages; reads each article page for its metadata and PDF link, then
fetches the PDF from BYU Studies' S3 bucket. Never touches ScholarsArchive.

    python3 harvest/byus.py --out /data/lectern/links/byus [--limit N] [--issues 64-1,16-4]

Re-runnable: an article whose record and file are on disk is skipped, and the
manifest is rewritten from the records in <out>/meta/.
"""

import argparse
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

SITE = "https://byustudies.byu.edu"
UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
DELAY = 1.5  # seconds between requests to one host
NS = "byus"
COLLECTION = "BYU Studies Quarterly"
LICENCE_QUOTE = "Brigham Young University Provo, UT 84602, USA | © 2026"

# Years for issues the site gives no date for, by volume. From ScholarsArchive's
# public issue list (scholarsarchive.byu.edu/byusq/all_issues.html, metadata only),
# read once by hand on 2026-11-15; issues the site dates use the site's date.
VOLUME_YEAR = {1: 1959, 2: 1960, 3: 1961, 4: 1962, 6: 1965, 7: 1966, 37: 1997, 38: 1999}


def volume_year(vol, iss):
    if vol in VOLUME_YEAR:
        return VOLUME_YEAR[vol]
    if vol == 5:
        return 1962 if iss == "1" else 1964
    if 8 <= vol <= 36:
        return 1960 + vol
    if vol >= 39:
        return 1961 + vol
    return None


class Challenge(Exception):
    pass


class Gone(Exception):
    pass


def log(*a):
    print(datetime.datetime.now().strftime("%H:%M:%S"), *a, flush=True)


_last = {}


def fetch(url, want_pdf=False):
    """GET url politely. Returns bytes. Raises Challenge on a bot check, Gone on 404/410."""
    host = urllib.parse.urlsplit(url).netloc
    for attempt in range(4):
        wait = _last.get(host, 0) + DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last[host] = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
                hdrs = r.headers
                status = r.status
        except urllib.error.HTTPError as e:
            body = e.read() or b""
            hdrs = e.headers
            status = e.code
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
            if re.search(rb"(?i)just a moment|challenge|captcha", body[:20000]):
                raise Challenge(f"non-PDF challenge page at {url}")
            raise Gone(f"not a PDF ({len(body)} bytes, starts {body[:20]!r}) at {url}")
        return body
    raise Gone(f"gave up after retries: {url}")


def flight(page):
    """The Next.js flight payload of a page, as one decoded string."""
    parts = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', page)
    return "".join(json.loads('"' + p + '"') for p in parts)


def json_at(s, marker):
    """Decode the JSON value that starts at marker's first { or [."""
    i = s.find(marker)
    if i < 0:
        return None
    k = min(j for j in (marker.find("{"), marker.find("[")) if j >= 0)
    obj, _ = json.JSONDecoder().raw_decode(s, i + k)
    return obj


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s


def person(a):
    name = " ".join(x.strip() for x in (a.get("first_name"), a.get("middle_name"), a.get("last_name")) if x and x.strip())
    if a.get("suffix") and a["suffix"].strip():
        name += " " + a["suffix"].strip()
    return name


def full_title(t, sub):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()
    sub = html.unescape(re.sub(r"<[^>]+>", "", sub or "")).strip()
    if not sub:
        return t
    return f"{t} {sub}" if t[-1:] in "?!:." else f"{t}: {sub}"


def split_issue_title(title):
    """'16:4' -> (16, '4'); '03:3-4' -> (3, '3-4'); '59:2 - Supplement' -> (59, '2 Supplement')."""
    m = re.match(r"\s*(\d+)\s*:\s*(.+?)\s*$", title or "")
    if not m:
        return None, None
    iss = re.sub(r"\s*-\s*(?=[A-Za-z])", " ", m.group(2))
    return int(m.group(1)), iss


def pdf_url(href):
    href = html.unescape(href)
    parts = urllib.parse.urlsplit(href)
    path = urllib.parse.quote(urllib.parse.unquote(parts.path), safe="/")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))


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
        if os.path.exists(os.path.join(out, row["file"])):
            rows.append(row)
    tmp = os.path.join(out, "manifest.jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, os.path.join(out, "manifest.jsonl"))
    return len(rows)


def harvest_article(out, slug, toc, next_start):
    landing = f"{SITE}/article/{slug}"
    page = fetch(landing).decode("utf-8", "replace")
    s = flight(page)
    data = json_at(s, '{"article":')
    if not data or "article" not in data:
        raise Gone(f"no article data on {landing}")
    a = data["article"]
    authors = [person(x) for x in (data.get("authors") or [])]
    issue = json_at(s, '"issue":{"id"') or {}
    vol, iss = split_issue_title(issue.get("title"))
    if vol is None and toc:
        vol, iss = toc.get("volume"), toc.get("issue")
    if issue.get("publication_date"):
        published = issue["publication_date"][:10]
    else:
        y = volume_year(vol, iss) if vol else None
        published = str(y) if y else None
    start = a.get("page_number")

    hrefs = [h for h in re.findall(r'href="(https://website-files-bucket[^"]*?\.pdf)"', page, re.I)]
    hrefs = list(dict.fromkeys(hrefs))
    item_slug = slugify(slug)
    row = {
        "id": f"{NS}:{item_slug}",
        "kind": "article",
        "title": full_title(a.get("title"), a.get("subtitle")),
        "authors": authors,
        "published": published,
        "collection": COLLECTION,
        "volume": str(vol) if vol is not None else None,
        "issue": iss,
        "pages": None,
        "doi": None,
        "section": (toc or {}).get("section"),
        "label_offset": None,
        "landing_url": landing,
        "source_url": None,
        "licence": {"id": "all-rights-reserved", "evidence_url": landing, "quote": LICENCE_QUOTE},
    }
    if hrefs:
        src = pdf_url(hrefs[0])
        body = fetch(src, want_pdf=True)
        rel = f"files/{item_slug}.pdf"
        row.update(source_url=src, file=rel, media_type="application/pdf")
        n_pages = None
        path = os.path.join(out, rel)
        with open(path + ".part", "wb") as f:
            f.write(body)
        os.replace(path + ".part", path)
        n_pages = pdf_pages(path)
        if isinstance(start, int) and start > 0:
            row["label_offset"] = start - 1
            if n_pages:
                end = start + n_pages - 1
                row["pages"] = f"{start}-{end}" if end > start else str(start)
                if next_start and end > next_start:
                    log(f"  check offset: {slug} p.{start}+{n_pages}pp runs past next item's p.{next_start}")
            else:
                row["pages"] = str(start)
        row["pdf_pages"] = n_pages
    else:
        # No PDF on the page: keep the HTML page itself, where the text (if any) is.
        log("  no PDF link:", slug)
        body = page.encode("utf-8")
        rel = f"files/{item_slug}.html"
        with open(os.path.join(out, rel), "wb") as f:
            f.write(body)
        row.update(source_url=landing, file=rel, media_type="text/html")
        if isinstance(start, int) and start > 0:
            row["pages"] = str(start)
        row["pdf_pages"] = None
    row.update(
        sha256=hashlib.sha256(body).hexdigest(),
        bytes=len(body),
        fetched_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    write_json(os.path.join(out, "meta", item_slug + ".json"), row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new items (testing)")
    ap.add_argument("--issues", default="", help="comma-separated issue slugs only (testing)")
    args = ap.parse_args()
    out = args.out
    os.makedirs(os.path.join(out, "files"), exist_ok=True)
    os.makedirs(os.path.join(out, "meta"), exist_ok=True)
    have = {n[:-5] for n in os.listdir(os.path.join(out, "meta")) if n.endswith(".json")}

    log("issue index")
    s = flight(fetch(f"{SITE}/issue").decode("utf-8", "replace"))
    issues = [i for i in (json_at(s, '{"initialIssues":') or {}).get("initialIssues", []) if i.get("public")]
    if args.issues:
        want = set(args.issues.split(","))
        issues = [i for i in issues if i["slug"] in want]
    log(len(issues), "public issues")

    # Each issue's table of contents, in printed order.
    order = []  # (slug, toc info, next item's start page)
    seen = set()
    for n, iss in enumerate(issues, 1):
        try:
            s = flight(fetch(f"{SITE}/issue/{iss['slug']}").decode("utf-8", "replace"))
        except Gone as e:
            log("  issue missing:", e)
            continue
        types = {t["id"]: t["type"] for t in json.loads("[" + ",".join(re.findall(r'\{"id":\d+,"type":"[^"]*","type_sort":\d+\}', s)) + "]")}
        arts = (json_at(s, '"articles":[') or [])
        vol, inum = split_issue_title(iss["title"])
        arts = [x for x in arts if x.get("slug")]
        starts = sorted({x["page_number"] for x in arts if isinstance(x.get("page_number"), int)})
        for x in arts:
            if x["slug"] in seen:
                continue
            seen.add(x["slug"])
            p = x.get("page_number")
            nxt = next((q for q in starts if isinstance(p, int) and q > p), None)
            order.append((x["slug"], {"volume": vol, "issue": inum, "section": types.get(x.get("article_type_id"))}, nxt))
        if n % 25 == 0:
            log(f"  {n}/{len(issues)} issues read, {len(order)} articles")
    log(len(order), "articles from issue pages")

    if not args.issues:
        sm = fetch(f"{SITE}/sitemap.xml").decode("utf-8", "replace")
        extra = [u for u in re.findall(r"<loc>https://byustudies\.byu\.edu/article/([^<]+)</loc>", sm) if u not in seen]
        log(len(extra), "more articles in the sitemap but in no issue")
        order += [(u, None, None) for u in extra]

    done = fresh = failed = 0
    t0 = time.monotonic()
    for i, (slug, toc, nxt) in enumerate(order, 1):
        item = slugify(slug)
        if item in have:
            meta = os.path.join(out, "meta", item + ".json")
            with open(meta, encoding="utf-8") as f:
                if os.path.exists(os.path.join(out, json.load(f)["file"])):
                    done += 1
                    continue
        try:
            row = harvest_article(out, slug, toc, nxt)
            fresh += 1
            log(f"[{i}/{len(order)}] {row['id']} {row['volume']}:{row['issue']} {row['pages']} {row['bytes']//1024}KB")
        except Gone as e:
            failed += 1
            log(f"[{i}/{len(order)}] SKIP {slug}: {e}")
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
