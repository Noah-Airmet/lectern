#!/usr/bin/env python3
"""Harvest Sunstone magazine, issues 1-164 (1975-2011), for the link-only tier.

The PDFs are still live on sunstone.org, but the site's issue index is broken (it
renders raw shortcodes), so each issue's table of contents (page, author, title, PDF
link) is read from the Wayback Machine's copy of its issue-details page: sunstone.org
captures first (nearest June 2024), then the older sunstonemagazine.com ones. Each
article PDF is fetched from live sunstone.org. A PDF that several contents entries
share is one row, its pieces listed in "contents". An issue whose contents give no
article PDF falls back to the whole-issue PDF.

Article filenames carry the printed range ({issue}-{first}-{last}.pdf), so
label_offset = first - 1 when the page count fits the range, else it's read from the
running heads ("PAGE 28") with pdftotext, else null.

There is no live page for an article or an issue, so landing_url is the PDF itself and
"index_url" (a field the README doesn't have) points at the Wayback copy of the issue's
contents page the metadata came from.

    python3 harvest/sunstone.py --out /data/lectern/links/sunstone [--limit N] [--issues 103,128]

Re-runnable: Wayback pages are cached in <out>/wayback/, a PDF already on disk isn't
fetched again, and the manifest is rewritten from the records in <out>/meta/.
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

SITE = "https://sunstone.org"
WAYBACK = "https://web.archive.org"
UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
DELAY = 1.5  # seconds between requests to one host (the Wayback Machine counts as its own)
NS = "sunstone"
COLLECTION = "Sunstone"
LICENCE = {
    "id": "all-rights-reserved",
    "evidence_url": f"{SITE}/magazine/ads-and-submissions/",
    "quote": "all literary rights are retained by authors",
}
MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october november december".split(), 1)}


class Challenge(Exception):
    pass


class Gone(Exception):
    pass


def log(*a):
    print(datetime.datetime.now().strftime("%H:%M:%S"), *a, flush=True)


_last = {}


def fetch(url, want_pdf=False):
    """GET url politely. Returns bytes. Raises Challenge on a bot check, Gone on 404/410."""
    if not url.isascii():  # curly quotes and the like in WordPress upload names
        url = urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%~")
    host = urllib.parse.urlsplit(url).netloc
    for attempt in range(4):
        wait = _last.get(host, 0) + DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read()
                hdrs = r.headers
                status = r.status
        except urllib.error.HTTPError as e:
            body = e.read() or b""
            hdrs = e.headers
            status = e.code
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            _last[host] = time.monotonic()
            log("  network error", url, e, "- retrying")
            time.sleep(10 * (attempt + 1))
            continue
        _last[host] = time.monotonic()
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


def fetch_json(url):
    return json.loads(fetch(url).decode("utf-8"))


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def slugify(s):
    s = urllib.parse.unquote(s or "").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def norm_title(s):
    return re.sub(r"[^a-z0-9]+", "", text(s).lower())


def abs_url(href, base):
    return urllib.parse.urljoin(base, html.unescape(href))


# --- PDFs -------------------------------------------------------------------

def page_texts(path):
    """Each page's text (pdftotext -layout), or None without poppler."""
    try:
        out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, timeout=600).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    pages = out.decode("utf-8", "replace").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def pdf_pages(path):
    try:
        out = subprocess.run(["pdfinfo", path], capture_output=True, text=True, timeout=60).stdout
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        return int(m.group(1)) if m else None
    except (OSError, subprocess.SubprocessError):
        return None


HEAD_START = re.compile(r"^(?:page\s+)?\[?(\d{1,4})\]?(?=\s|$)(?![./:])", re.I)
HEAD_END = re.compile(r"(?<![\d/(.,:–-])\[?(\d{1,4})\]?$")


def head_offset(pages):
    """printed page - PDF page, voted from the numbers at the ends of each page's first
    and last two lines; None unless one offset clearly wins."""
    if not pages:
        return None
    votes = collections.Counter()
    for i, pg in enumerate(pages, 1):
        lines = [l.strip() for l in pg.splitlines() if l.strip()]
        found = set()
        for l in lines[:2] + lines[-2:]:
            l = re.sub(r"(?<=[A-Za-z])\s*/\s*(?=\d)|(?<=\d)\s*/\s*(?=[A-Za-z])", " ", l)  # "Psychologist/55", "56/DIALOGUE"
            for m in (HEAD_START.match(l), HEAD_END.search(l)):
                if m and int(m.group(1)) - i >= -40:
                    found.add(int(m.group(1)) - i)
        votes.update(found)
    if not votes:
        return None
    ranked = votes.most_common(2) + [(None, 0)]
    (off, n), (_, second) = ranked[0], ranked[1]
    if n >= 3 and n >= 0.4 * len(pages) and n > 2 * second:
        return off
    if len(pages) <= 4 and n >= 2 and second == 0:
        return off
    return None


# --- records ----------------------------------------------------------------

def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_manifest(out):
    meta = os.path.join(out, "meta")
    rows = []
    for name in sorted(os.listdir(meta)):
        if name.endswith(".json"):
            row = read_json(os.path.join(meta, name))
            if row and os.path.exists(os.path.join(out, row["file"])):
                rows.append(row)
    tmp = os.path.join(out, "manifest.jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, os.path.join(out, "manifest.jsonl"))
    return len(rows)


def save(out, rel, body):
    path = os.path.join(out, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".part", "wb") as f:
        f.write(body)
    os.replace(path + ".part", path)
    return path


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- the site ---------------------------------------------------------------

# --- Sunstone ---------------------------------------------------------------

def split_authors(s):
    s = re.sub(r"\s+", " ", s or "").strip().rstrip(".,")
    if not s:
        return []
    parts = re.split(r",?\s+and\s+|\s*&\s*|,\s+(?!Jr\.?|Sr\.?|I{2,3}\b)", s)
    return [p.strip() for p in parts if p.strip()]


def published(date):
    """'September 1996' -> '1996-09'; 'Winter 1976' -> '1976'."""
    m = re.search(r"(1[89]\d\d|20\d\d)", date or "")
    if not m:
        return None
    for w in re.findall(r"[A-Za-z]+", date):
        if w.lower() in MONTHS:
            return f"{m.group(1)}-{MONTHS[w.lower()]:02d}"
    return m.group(1)


def captures(prefix):
    """{issue number: [(timestamp, original url)]} from the Wayback CDX API."""
    q = urllib.parse.urlencode({"url": prefix, "matchType": "prefix", "output": "json",
                                "fl": "timestamp,original", "filter": "statuscode:200"})
    rows = fetch_json(f"{WAYBACK}/cdx/search/cdx?{q}")[1:]
    out = collections.defaultdict(list)
    for ts, orig in rows:
        m = re.search(r"[?&]in=(\d+)\b", orig)
        if m:
            out[int(m.group(1))].append((ts, orig))
    return out


def parse_issue(page):
    """(date, issue PDF url, [(page, author, title, pdf url)]) from an issue-details page."""
    tb = re.search(r'<table id="issueArticles">(.*?)</table>', page, re.S)
    if not tb:
        return None, None, []
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", tb.group(1), re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 4:
            continue
        m = re.search(r'href="([^"]+?\.pdf)"', tds[3], re.I)
        rows.append((text(tds[0]), text(tds[1]), text(tds[2]),
                     f"{SITE}/wp-content/uploads/sbi/articles/{os.path.basename(m.group(1))}" if m else None))
    head = re.search(r'<table id="issueHeader">(.*?)</table>', page, re.S)
    date = re.search(r"<strong>(.*?)</strong>", head.group(1)) if head else None
    ipdf = re.search(r'href="([^"]*/sbi/issues/\d+\.pdf)"', page, re.I)
    return (text(date.group(1)) if date else None,
            f"{SITE}/wp-content/uploads/sbi/issues/{os.path.basename(ipdf.group(1))}" if ipdf else None,
            rows)


def read_issue(out, n, caps):
    """The issue's contents from the first Wayback capture that has them. Cached."""
    cache = os.path.join(out, "wayback", f"{n}.json")
    info = read_json(cache)
    if info is not None:
        return info
    info = {"date": None, "issue_pdf": None, "rows": [], "index_url": None}
    for ts, orig in caps:
        url = f"{WAYBACK}/web/{ts}id_/{orig}"
        try:
            page = fetch(url).decode("utf-8", "replace")
        except Gone as e:
            log("  wayback:", e)
            continue
        date, ipdf, rows = parse_issue(page)
        if rows:
            info = {"date": date, "issue_pdf": ipdf, "rows": rows, "index_url": f"{WAYBACK}/web/{ts}/{orig}"}
            break
        log("  no contents table in", url)
    write_json(cache, info)
    return info


def build_row(out, n, info, url, entries, whole=False):
    name = os.path.basename(urllib.parse.urlsplit(url).path)
    stem = os.path.splitext(name)[0]
    item = slugify(stem) + ("-issue" if whole else "")
    rel = f"files/{'issues' if whole else 'articles'}/{name}"
    path = os.path.join(out, rel)
    if not os.path.exists(path):
        save(out, rel, fetch(url, want_pdf=True))
    with open(path, "rb") as f:
        body = f.read()
    npages = pdf_pages(path)
    offset = pages = None
    m = re.match(r"(\d+)-(\d+)(?:-(\d+))?$", stem)
    heads = head_offset(page_texts(path))
    if m and not whole:
        first, last = int(m.group(2)), int(m.group(3) or m.group(2))
        pages = f"{first}-{last}" if last > first else str(first)
        if npages and npages == last - first + 1:
            offset = first - 1
            if heads is not None and heads != offset:
                log(f"  note: {item}: running heads give offset {heads}, filename {offset}")
        else:
            offset = heads
            if npages:
                log(f"  note: {item}: {npages} pages for printed {pages}; offset from heads: {heads}")
    else:
        offset = heads
    if whole:
        title = f"Sunstone, issue {n}" + (f" ({info['date']})" if info.get("date") else "")
        authors = []
    else:
        title = "; ".join(t for _, _, t, _ in entries if t) or stem
        authors = list(dict.fromkeys(a for _, au, _, _ in entries for a in split_authors(au)))
    row = {
        "id": f"{NS}:{item}",
        "kind": "article",
        "title": title,
        "authors": authors,
        "published": published(info.get("date")),
        "collection": COLLECTION,
        "volume": None,
        "issue": str(n),
        "pages": pages,
        "doi": None,
        "section": None,
        "label_offset": offset,
        "landing_url": url,
        "source_url": url,
        "index_url": info.get("index_url"),
        "file": rel,
        "media_type": "application/pdf",
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "fetched_at": now(),
        "licence": LICENCE,
        "pdf_pages": npages,
    }
    if whole or len(entries) > 1:
        row["contents"] = [{"title": t, "authors": split_authors(au), "page": p} for p, au, t, _ in entries]
    write_json(os.path.join(out, "meta", item + ".json"), row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new rows (testing)")
    ap.add_argument("--issues", default="", help="comma-separated issue numbers only (testing)")
    args = ap.parse_args()
    out = args.out
    for d in ("files", "meta", "wayback"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    numbers = [int(x) for x in args.issues.split(",")] if args.issues else list(range(1, 165))

    try:
        cache = os.path.join(out, "wayback", "cdx.json")
        caps = read_json(cache)
        if caps is None:
            log("Wayback CDX")
            caps = collections.defaultdict(list)
            for prefix in ("sunstone.org/issue-details/", "www.sunstonemagazine.com/issue-details/",
                           "sunstonemagazine.com/issue-details/"):
                for k, v in captures(prefix).items():
                    caps[str(k)] += v
            write_json(cache, caps)
    except Challenge as e:
        log("STOP: bot challenge:", e)
        sys.exit(2)

    def order(c):  # sunstone.org first, nearest the June 2024 copy; then the rest, newest first
        ts, orig = c
        return (0 if "//sunstone.org" in orig else 1, abs(int(ts[:8]) - 20240605) if "//sunstone.org" in orig else -int(ts))
    log(sum(1 for n in numbers if caps.get(str(n))), "of", len(numbers), "issues have Wayback captures")

    fresh = have = failed = 0
    t0 = time.monotonic()
    try:
        for n in numbers:
            info = read_issue(out, n, sorted({tuple(c) for c in caps.get(str(n), [])}, key=order)[:4])
            by_pdf = collections.OrderedDict()
            for e in info["rows"]:
                if e[3]:
                    by_pdf.setdefault(e[3], []).append(e)
            log(f"issue {n} ({info['date']}): {len(info['rows'])} entries, {len(by_pdf)} PDFs")
            got = 0
            for url, entries in by_pdf.items():
                item = slugify(os.path.splitext(os.path.basename(url))[0])
                rec = read_json(os.path.join(out, "meta", item + ".json"))
                if rec and os.path.exists(os.path.join(out, rec["file"])):
                    have += 1
                    got += 1
                    continue
                try:
                    row = build_row(out, n, info, url, entries)
                    fresh += 1
                    got += 1
                    log(f"  {row['id']} pp.{row['pages']} off={row['label_offset']} {row['bytes'] // 1024}KB | "
                        f"{row['title'][:60]} | {', '.join(row['authors'])[:40]}")
                except Gone as e:
                    failed += 1
                    log("  SKIP", e)
                if args.limit and fresh >= args.limit:
                    break
            if not got and not (args.limit and fresh >= args.limit):
                url = info["issue_pdf"] or f"{SITE}/wp-content/uploads/sbi/issues/{n:03d}.pdf"
                item = slugify(os.path.splitext(os.path.basename(url))[0]) + "-issue"
                rec = read_json(os.path.join(out, "meta", item + ".json"))
                if rec and os.path.exists(os.path.join(out, rec["file"])):
                    have += 1
                else:
                    try:
                        row = build_row(out, n, info, url, info["rows"], whole=True)
                        fresh += 1
                        log(f"  {row['id']} whole issue, off={row['label_offset']} {row['pdf_pages']}pp {row['bytes'] // 1024}KB")
                    except Gone as e:
                        failed += 1
                        log("  SKIP whole issue:", e)
            log(f"  manifest: {write_manifest(out)} rows; {fresh / max(time.monotonic() - t0, 1) * 3600:.0f} new rows/hour")
            if args.limit and fresh >= args.limit:
                break
    except Challenge as e:
        log("STOP: bot challenge:", e)
        write_manifest(out)
        sys.exit(2)
    n = write_manifest(out)
    log(f"done: {fresh} new, {have} already had, {failed} skipped; manifest {n} rows")


if __name__ == "__main__":
    main()
