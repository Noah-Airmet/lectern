#!/usr/bin/env python3
"""Harvest the Religious Studies Center (rsc.byu.edu) for the link-only tier.

Two parts, one manifest:
- Religious Educator (ns `releducator`): /religious-educator -> issue pages -> articles.
- RSC books readable online (ns `rsc`, kind `book`, one item per chapter):
  /books/all -> /book/<slug> -> each chapter in its table of contents.

The site is HTML only (no PDFs, no printed-page markers), so each item's file is the
saved HTML page and source_url is the page itself. Pages come from each page's
"Show Citation" block.

    python3 harvest/rsc.py --out /data/lectern/links/rsc [--limit N] [--only re|books] [--match SUBSTR]

Re-runnable: an item whose record and file are on disk is skipped, and the manifest
is rewritten from the records in <out>/meta/.
"""

import argparse
import datetime
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SITE = "https://rsc.byu.edu"
UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
DELAY = 1.5  # seconds between requests to one host
LICENCE_QUOTE = "© 2022 All rights reserved"


class Challenge(Exception):
    pass


class Gone(Exception):
    pass


def log(*a):
    print(datetime.datetime.now().strftime("%H:%M:%S"), *a, flush=True)


_last = {}


def fetch(url):
    """GET url politely, as text. Raises Challenge on a bot check, Gone on 404/410."""
    host = urllib.parse.urlsplit(url).netloc
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
            body, hdrs, status = (e.read() or b""), e.headers, e.code
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            log("  network error", url, e, "- retrying")
            time.sleep(10 * (attempt + 1))
            continue
        if any(k.lower().endswith("-mitigated") for k in hdrs.keys()) or (
            status in (403, 503) and re.search(rb"(?i)just a moment|challenge|captcha|antibot|are you a robot", body[:20000])
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
        return body
    raise Gone(f"gave up after retries: {url}")


def text(fragment):
    t = re.sub(r"<[^>]+>", " ", fragment or "")
    t = re.sub(r"\s+", " ", html.unescape(t)).strip()
    return re.sub(r"\s+([,.;:])", r"\1", t)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def full_title(t, sub):
    if not sub:
        return t
    return f"{t} {sub}" if t[-1:] in "?!:." else f"{t}: {sub}"


def toc_links(page):
    """(href, names) for each entry of a table of contents, in order, without repeats.
    names are the entry's credited people, used when the item's own page names none."""
    entries = {}
    for li in re.split(r"<li\b", page)[1:]:
        m = re.search(r'<div class="toc-title">\s*<a href="(/[^"]+)"', li)
        if not m or m.group(1) in entries:
            continue
        who = re.search(r'<div class="toc-(?:author|source)">(.*?)</div>', li, re.S)
        names = people(who.group(1)) if who else []
        if who and not names:
            names = [n for n in re.split(r",\s*and\s+|\s+and\s+|,\s*", text(who.group(1))) if n]
        entries[m.group(1)] = names
    return list(entries.items())


def people(fragment):
    return [text(n) for n in re.findall(r"<a [^>]*>(.*?)</a>", fragment or "", re.S) if text(n)]


def expand_range(a, b):
    """'135', '50' -> '135-150' (Chicago-style abbreviated ranges)."""
    if a.isdigit() and b.isdigit() and len(b) < len(a):
        b = a[: len(a) - len(b)] + b
    return f"{a}-{b}"


def citation_bits(cite):
    """Pages and year from a citation string."""
    pages = None
    m = re.search(r"(?:[:,]\s*|\)\s*,?\s*)([0-9ivxlc]+)(?:\s*[–—‒−-]\s*([0-9ivxlc]+))?\.?\s*$", cite, re.I)
    if m:
        pages = expand_range(m.group(1), m.group(2)) if m.group(2) else m.group(1)
    years = re.findall(r"\b(1[89]\d\d|20\d\d)\)", cite)
    return pages, (years[-1] if years else None)


def parse_item(page):
    """Title, authors and citation from an article or chapter page."""
    pane = re.search(r'<div class="content-title-pane">(.*?)</div>', page, re.S)
    pane = pane.group(1) if pane else ""
    title = text((re.search(r"<h3[^>]*>(.*?)</h3>", pane, re.S) or [None, ""])[1])
    sub = text((re.search(r"<h4[^>]*>(.*?)</h4>", pane, re.S) or [None, ""])[1])
    authors = people((re.search(r"<h5[^>]*>(.*?)</h5>", pane, re.S) or [None, ""])[1])
    body = page[page.find('class="content-body-pane'):]
    # The first toggle box is usually the citation; on the newest issues it is the
    # author bio instead, and there is no citation.
    boxes = [text(b) for b in re.findall(r'<div class="toggle-box[^"]*">\s*(.*?)</div>', body, re.S)]
    cite = next((b for b in boxes if re.search(r"\((?:[^()]*\D)?(?:1[89]|20)\d\d\)|[“\"].+[”\"]", b)), "")
    return full_title(title, sub), authors, cite


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
    # A chapter whose page gives no citation (a preface, say) takes its book's year.
    years = {}
    for row in rows:
        if row.get("book_url") and row.get("published"):
            years.setdefault(row["book_url"], []).append(row["published"])
    for row in rows:
        if row.get("book_url") and not row.get("published") and years.get(row["book_url"]):
            ys = years[row["book_url"]]
            row["published"] = max(set(ys), key=ys.count)
    tmp = os.path.join(out, "manifest.jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, os.path.join(out, "manifest.jsonl"))
    return len(rows)


def have_item(out, key):
    meta = os.path.join(out, "meta", key + ".json")
    if not os.path.exists(meta):
        return False
    with open(meta, encoding="utf-8") as f:
        return os.path.exists(os.path.join(out, json.load(f)["file"]))


def save_item(out, ns, path, body, row):
    key = f"{ns}--{slugify(path)}"
    rel = f"files/{ns}/{slugify(path)}.html"
    os.makedirs(os.path.join(out, "files", ns), exist_ok=True)
    with open(os.path.join(out, rel), "wb") as f:
        f.write(body)
    url = SITE + path
    row.update(
        id=f"{ns}:{slugify(path)}",
        landing_url=url,
        source_url=url,
        file=rel,
        media_type="text/html",
        sha256=hashlib.sha256(body).hexdigest(),
        bytes=len(body),
        fetched_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        licence={"id": "all-rights-reserved", "evidence_url": url, "quote": LICENCE_QUOTE},
    )
    write_json(os.path.join(out, "meta", key + ".json"), row)
    return row


def religious_educator(out, todo):
    page = fetch(SITE + "/religious-educator").decode("utf-8", "replace")
    issues = list(dict.fromkeys(re.findall(r'href="(/religious-educator/vol-[^"#?]+)"', page)))
    log(len(issues), "Religious Educator issues")
    for n, ipath in enumerate(issues, 1):
        try:
            ipage = fetch(SITE + ipath).decode("utf-8", "replace")
        except Gone as e:
            log("  issue missing:", e)
            continue
        islug = ipath.rsplit("/", 1)[1]
        m = re.match(r"vol-(\d+)-no-(\d+)-(\d{4})", islug)
        vol, num, year = m.groups() if m else (None, None, None)
        for apath, names in toc_links(ipage):
            todo.append(("re", apath, {"volume": vol, "issue": num, "year": year, "toc_names": names}))
        if n % 20 == 0:
            log(f"  {n}/{len(issues)} issues read")


def books(out, todo, match=""):
    page = fetch(SITE + "/books/all").decode("utf-8", "replace")
    bks = list(dict.fromkeys(re.findall(r'href="(/book/[^"#?]+)"', page)))
    if match:
        bks = [b for b in bks if match in b]
    log(len(bks), "books listed")
    online = 0
    for n, bpath in enumerate(bks, 1):
        try:
            bpage = fetch(SITE + bpath).decode("utf-8", "replace")
        except Gone as e:
            log("  book missing:", e)
            continue
        chapters = toc_links(bpage)
        block = re.search(r'<div class="pub-title-block">(.*?)<div class="pub-back-block">', bpage, re.S)
        block = block.group(1) if block else ""
        btitle = text((re.search(r"<h2[^>]*>(.*?)</h2>", block, re.S) or [None, ""])[1])
        bsub = text((re.search(r"<h4[^>]*>(.*?)</h4>", block, re.S) or [None, ""])[1])
        credit = re.search(r'<div class="in-italic[^"]*">(.*?)</div>', block, re.S)
        credit = credit.group(1) if credit else ""
        names = people(credit)
        is_ed = bool(re.search(r"(?i)\beditors?\b|\beds?\.", text(credit)))
        info = {
            "book": full_title(btitle, bsub),
            "book_path": bpath,
            "editors": names if is_ed else [],
            "book_authors": [] if is_ed else names,
        }
        if not chapters:
            note = "not released for online reading" if "not been released" in bpage else "no table of contents"
            log(f"  {bpath}: {note}")
            continue
        online += 1
        for cpath, names in chapters:
            todo.append(("book", cpath, dict(info, toc_names=names)))
        if n % 25 == 0:
            log(f"  {n}/{len(bks)} books read, {online} online, {len(todo)} items queued")
    log(f"{online} of {len(bks)} books readable online")


def harvest(out, kind, path, info):
    body = fetch(SITE + path)
    page = body.decode("utf-8", "replace")
    title, authors, cite = parse_item(page)
    pages, year = citation_bits(cite)
    if kind == "re":
        row = {
            "kind": "article",
            "title": title,
            "authors": authors or info.get("toc_names", []),
            "published": info["year"] or year,
            "collection": "Religious Educator",
            "volume": info["volume"],
            "issue": info["issue"],
            "pages": pages,
            "doi": None,
            "label_offset": None,
            "citation": cite or None,
        }
        return save_item(out, "releducator", path, body, row)
    row = {
        "kind": "book",
        "title": title,
        "authors": authors or info.get("toc_names") or info["book_authors"],
        "published": year,
        "collection": info["book"],
        "editors": info["editors"],
        "book_url": SITE + info["book_path"],
        "volume": None,
        "issue": None,
        "pages": pages,
        "doi": None,
        "label_offset": None,
        "citation": cite or None,
    }
    return save_item(out, "rsc", path, body, row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new items (testing)")
    ap.add_argument("--only", choices=["re", "books"], default="")
    ap.add_argument("--match", default="", help="only books whose path contains this (testing)")
    args = ap.parse_args()
    out = args.out
    os.makedirs(os.path.join(out, "meta"), exist_ok=True)

    todo = []
    try:
        if args.only != "books":
            religious_educator(out, todo)
        if args.only != "re":
            books(out, todo, args.match)
    except Challenge as e:
        log("STOP: bot challenge:", e)
        sys.exit(2)
    seen = set()
    todo = [t for t in todo if not (t[1] in seen or seen.add(t[1]))]
    log(len(todo), "items to harvest")

    done = fresh = failed = 0
    t0 = time.monotonic()
    for i, (kind, path, info) in enumerate(todo, 1):
        ns = "releducator" if kind == "re" else "rsc"
        if have_item(out, f"{ns}--{slugify(path)}"):
            done += 1
            continue
        try:
            row = harvest(out, kind, path, info)
            fresh += 1
            flag = "" if row["pages"] and row["published"] else "  (no pages/year in citation)"
            log(f"[{i}/{len(todo)}] {row['id']} {row['published']} {row['pages']}{flag}")
        except Gone as e:
            failed += 1
            log(f"[{i}/{len(todo)}] SKIP {path}: {e}")
        except Challenge as e:
            log("STOP: bot challenge:", e)
            write_manifest(out)
            sys.exit(2)
        if fresh and fresh % 100 == 0:
            rate = fresh / (time.monotonic() - t0) * 3600
            log(f"  manifest: {write_manifest(out)} rows; {rate:.0f} items/hour")
        if args.limit and fresh >= args.limit:
            break
    n = write_manifest(out)
    log(f"done: {fresh} new, {done} already had, {failed} skipped; manifest {n} rows")


if __name__ == "__main__":
    main()
