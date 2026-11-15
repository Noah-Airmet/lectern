#!/usr/bin/env python3
"""Harvest Mormon Historical Studies (and the Nauvoo Journal before it), 1989-2014,
from ensignpeakfoundation.org, for the link-only tier.

Reads the /publications/ page for the issue pages, each issue page for its article
PDFs (title from the link text, section from the heading above it), and fetches the
PDFs. A PDF linked from several entries (the book reviews) is one row, its pieces in
"contents". Covers, tables of contents and name indexes are left out.

Authors come from the PDF's first page (the byline under the title, else the
contributor note at the foot, else the running head); label_offset from the
running-head page numbers (pdftotext), printed page = PDF page + (start - 1).

    python3 harvest/mhs.py --out /data/lectern/links/mhs [--limit N] [--issues nauvoo-journal-1989-vol-1]

Re-runnable: a PDF already on disk isn't fetched again, and the manifest is
rewritten from the records in <out>/meta/.
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

SITE = "https://ensignpeakfoundation.org"
UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
DELAY = 1.5  # seconds between requests to one host
NS = "mhs"
LICENCE = {
    "id": "all-rights-reserved",
    "evidence_url": f"{SITE}/publications/",
    "quote": "Copyright © Ensign Peak Foundation, 2006-2026. All Rights Reserved.",
}
SKIP = re.compile(r"(?i)^(cover|(table of )?contents|(name )?index)$")


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

# --- Mormon Historical Studies ---------------------------------------------

def split_authors(s):
    s = re.sub(r"\s+", " ", s or "").strip().rstrip(".,")
    if not s:
        return []
    parts = re.split(r",?\s+and\s+|\s*&\s*|,\s+(?!Jr\.?|Sr\.?|I{2,3}\b)", s)
    return [p.strip() for p in parts if p.strip()]


NAME_LINE = re.compile(r"^[A-Z][\w.'’-]*(?:,?\s+(?:[A-Z][\w.'’-]*|and|&|de|van|von|der|la))+$")


def surnames(names):
    return {w.lower() for n in names for w in re.findall(r"[A-Za-z][A-Za-z'’-]+", n)[-1:]}


def titlecase_name(n):
    return " ".join("-".join(x[:1] + x[1:].lower() for x in w.split("-")) if not re.match(r"^[A-Z]\.$", w) else w
                    for w in n.split())


def authors_from_pdf(pages, title):
    """The byline under the title, checked against the running head ('Radke-Moss: Mormon
    Women ...') or the contributor note ('LYMAN D. PLATT is ...'); failing that the note's
    names, then the running head's."""
    if not pages:
        return []
    first = "\n".join(pages[:2])
    heads = collections.Counter()
    for pg in pages[:9]:
        top = next((l.strip() for l in pg.splitlines() if l.strip()), "")
        m = re.match(r"^(?:\d{1,4}\s+)?([^:\d]{4,60}):", top)
        if m:
            heads[m.group(1).strip()] += 1
    head = split_authors(heads.most_common(1)[0][0]) if heads else []
    notes = re.findall(r"(?m)(?:^|\s{3,})([A-Z][A-Z.'’ -]{3,}?[A-Z]) (?:is|was|has|teaches|received|holds|lives|works|served|earned|retired)\b", first)
    bio = list(dict.fromkeys(titlecase_name(p) for n in notes for p in split_authors(re.sub(r"\bAND\b", "and", n))))
    known = surnames(head) | surnames(bio)
    nt = norm_title(title)
    for l in [re.sub(r"\s+", " ", l).strip() for l in first.splitlines()][:40]:
        if len(l) <= 70 and ":" not in l and not re.search(r"\d", l) and NAME_LINE.match(l):
            if norm_title(l) and norm_title(l) not in nt and surnames(split_authors(l)) & known:
                return split_authors(l)
    return bio or head


def issue_meta(slug, h3):
    """('Mormon Historical Studies', '1', '1', '2000') from the slug and the page's heading."""
    collection = "Nauvoo Journal" if slug.startswith("nauvoo-journal") else "Mormon Historical Studies"
    year = re.search(r"(19|20)\d\d", slug)
    vol = re.search(r"vol-?(\d+)", slug)
    no = re.search(r"(?:no|number)-?(\d+(?:-\d+)?)", slug)
    m = re.search(r"Vol\.?\s*(\d+)\s*\|\s*No\.?\s*([\d\s&-]+)", h3 or "")
    if m:
        return collection, m.group(1), re.sub(r"\s*[&-]\s*", "-", m.group(2).strip()), year and year.group(0)
    return collection, vol and vol.group(1), no and no.group(1), year and year.group(0)


def read_issue_page(link):
    """[(section, title, extra, pdf url)] and the page's issue heading."""
    page = fetch(link).decode("utf-8", "replace")
    body = page.split('class="page-inner"', 1)[-1] if 'class="page-inner"' in page else page
    entries, section, heading = [], None, None
    for m in re.finditer(r'<h3>(.*?)</h3>|<a href="([^"]+?\.pdf)"[^>]*>(.*?)</a>(.*?)(?=</p>|<p>|<h3>|$)', body, re.S | re.I):
        if m.group(1) is not None:
            if heading is None:
                heading = text(m.group(1))
            else:
                section = text(m.group(1))
            continue
        url = urllib.parse.urljoin(SITE + "/", html.unescape(m.group(2))).replace("http://", "https://", 1)
        entries.append((section, text(m.group(3)), text(re.sub(r"<a .*", "", m.group(4), flags=re.S)), url))
    return heading, entries


def build_row(out, slug, link, heading, url, entries):
    name = os.path.basename(urllib.parse.urlsplit(url).path)
    item = slugify(os.path.splitext(name)[0])
    rel = f"files/{name}"
    path = os.path.join(out, rel)
    if not os.path.exists(path):
        save(out, rel, fetch(url, want_pdf=True))
    with open(path, "rb") as f:
        body = f.read()
    pages_text = page_texts(path)
    npages = pdf_pages(path)
    offset = head_offset(pages_text)
    collection, vol, no, year = issue_meta(slug, heading)
    titles = [t + (f" {x}" if x.startswith(",") else "") for _, t, x, _ in entries]
    reviews = [a for _, _, x, _ in entries for a in split_authors((re.search(r"Reviewed(?: by)?\s+(.+)$", x) or [None, ""])[1])]
    if not reviews and re.search(r"(?i)review", " ".join(f"{e[0]} {e[1]}" for e in entries)):
        reviews = list(dict.fromkeys(re.sub(r"\s+", " ", r).strip().rstrip(".,") for r in
                                     re.findall(r"(?m)^\s*Reviewed by\s+([A-Z][^\n]{2,60}?)\s*$", "\n".join(pages_text or []))))
    authors = reviews or authors_from_pdf(pages_text, entries[0][1])
    row = {
        "id": f"{NS}:{item}",
        "kind": "article",
        "title": "; ".join(titles),
        "authors": authors,
        "published": year,
        "collection": collection,
        "volume": vol,
        "issue": no,
        "pages": (f"{offset + 1}-{offset + npages}" if npages > 1 else str(offset + 1)) if offset is not None and npages else None,
        "doi": None,
        "section": entries[0][0],
        "label_offset": offset,
        "landing_url": link,
        "source_url": url,
        "file": rel,
        "media_type": "application/pdf",
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "fetched_at": now(),
        "licence": LICENCE,
        "pdf_pages": npages,
    }
    if len(entries) > 1:
        row["contents"] = [{"title": t + (f" {x}" if x.startswith(",") else ""), "section": s,
                            "authors": split_authors((re.search(r"Reviewed(?: by)?\s+(.+)$", x) or [None, ""])[1])}
                           for s, t, x, _ in entries]
    write_json(os.path.join(out, "meta", item + ".json"), row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new rows (testing)")
    ap.add_argument("--issues", default="", help="comma-separated issue page slugs only (testing)")
    args = ap.parse_args()
    out = args.out
    for d in ("files", "meta"):
        os.makedirs(os.path.join(out, d), exist_ok=True)

    fresh = have = failed = 0
    t0 = time.monotonic()
    try:
        pub = fetch(f"{SITE}/publications/").decode("utf-8", "replace")
        links = []
        for href in re.findall(r'href="(https?://ensignpeakfoundation\.org/[^"]*?(?:nauvoo-journal|mormon-historical-studies)[^"]*)"', pub):
            href = href.replace("http://", "https://", 1)
            if href not in links:
                links.append(href)
        if args.issues:
            want = set(args.issues.split(","))
            links = [l for l in links if l.rstrip("/").rsplit("/", 1)[-1] in want]
        log(len(links), "issue pages")
        for li, link in enumerate(links, 1):
            slug = link.rstrip("/").rsplit("/", 1)[-1]
            try:
                heading, entries = read_issue_page(link)
            except Gone as e:
                failed += 1
                log(f"[{li}/{len(links)}] SKIP issue page:", e)
                continue
            by_pdf = collections.OrderedDict()
            for e in entries:
                if not SKIP.match(e[1]):
                    by_pdf.setdefault(e[3], []).append(e)
            log(f"[{li}/{len(links)}] {slug}: {len(by_pdf)} PDFs")
            for url, ents in by_pdf.items():
                item = slugify(os.path.splitext(os.path.basename(urllib.parse.urlsplit(url).path))[0])
                rec = read_json(os.path.join(out, "meta", item + ".json"))
                if rec and os.path.exists(os.path.join(out, rec["file"])):
                    have += 1
                    continue
                try:
                    row = build_row(out, slug, link, heading, url, ents)
                    fresh += 1
                    log(f"  {row['id']} {row['volume']}:{row['issue']} pp.{row['pages']} off={row['label_offset']} | "
                        f"{row['title'][:60]} | {', '.join(row['authors'])[:50]}")
                except Gone as e:
                    failed += 1
                    log("  SKIP", e)
                if args.limit and fresh >= args.limit:
                    break
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
