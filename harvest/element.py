#!/usr/bin/env python3
"""Harvest Element: The Journal of the Society for Mormon Philosophy and Theology
(2005-2019) for the link-only tier.

The 51 per-article PDFs on element.wcu.edu, listed by its WordPress media API; and,
for any issue with no article PDF there (vols 3, 7 and 8 as of 2026-11), the
whole-issue PDF that dialoguejournal.com hosts on its "Element Volume N Issue M"
pages, one row per issue. Dialogue's own harvester (dialogue.py) leaves those pages
out, so nothing is taken twice. The 2024- relaunch (Greg Kofford Books) is not here.

Titles and authors come from each PDF's first page ("Title ... by Author"), volume,
issue and season from the running heads ("Element Vol. 4 Issue 1 (Spring 2008)"),
falling back to the filename and the issue page; label_offset from the running-head
page numbers (pdftotext).

    python3 harvest/element.py --out /data/lectern/links/element [--limit N]

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

WCU = "https://element.wcu.edu"
DIALOGUE = "https://www.dialoguejournal.com"
UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
DELAY = 1.5  # seconds between requests to one host
NS = "element"
COLLECTION = "Element: The Journal of the Society for Mormon Philosophy and Theology"
LICENCE_WCU = {
    "id": "all-rights-reserved",
    "evidence_url": f"{WCU}/",
    "quote": "© 2005-2018 | In association with Western Carolina University",
}
LICENCE_DIALOGUE = {
    "id": "all-rights-reserved",
    "evidence_url": f"{DIALOGUE}/articles/element-volume-1-issue-1/",
    "quote": "Copyright © 2026 The Dialogue Journal. All rights reserved.",
}


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

# --- Element ----------------------------------------------------------------

def despace(s):
    """'E l e m e n t Vo l . 1 I s s . 2 ( Fa l l 2 0 0 5 )' -> 'ElementVol.1Iss.2(Fall2005)'."""
    return re.sub(r"\s+", "", s)


def issue_from_heads(pages):
    """(volume, issue, 'Spring 2008') from the running heads, the most common reading."""
    seen = collections.Counter()
    for pg in pages or []:
        lines = [l for l in pg.splitlines() if l.strip()]
        for l in lines[:2] + lines[-2:]:
            m = re.search(r"Vol\.?(\d+),?Iss(?:ue|\.)?(\d+(?:[&-]\d+)?)\((Spring|Summer|Fall|Winter|Autumn)?(?:&\w+)?,?(\d{4})\)",
                          despace(l), re.I)
            if m:
                seen[(m.group(1), m.group(2), f"{m.group(3) or ''} {m.group(4)}".strip())] += 1
    return seen.most_common(1)[0][0] if seen else (None, None, None)


def split_authors(s):
    s = re.sub(r"\s+", " ", s).strip().rstrip(".,")
    parts = re.split(r",?\s+and\s+|\s*&\s*|,\s+(?!Jr\.?|Sr\.?|I{2,3}\b)", s)
    return [p.strip() for p in parts if p.strip()]


SMALL = {"a", "an", "the", "and", "of", "to", "in", "on", "for", "with", "as", "at", "by", "or", "from"}


def unshout(s):
    """'D EFINING D OCTRINE : A R ESPONSE' (small caps) -> 'Defining Doctrine: A Response'."""
    toks = s.split()
    if toks and sum(len(t) == 1 and t.isupper() for t in toks) >= len(toks) / 3:  # spaced small caps
        s = re.sub(r"\b([A-Z]) (?=[A-Z]{2,})", r"\1", s)
        s = re.sub(r"\s*([’'])\s*S\b", r"\1S", s)
    s = re.sub(r"\s+([:;,?!])", r"\1", s)
    if s.upper() != s:
        return s
    words = s.lower().split(" ")
    return " ".join("LDS" if w == "lds" else w if i and w in SMALL and not words[i - 1].endswith(":")
                    else w[:1].upper() + w[1:] for i, w in enumerate(words))


# PDFs whose text layer is garbled (a shifted font encoding), read by hand from the page.
FIXED = {
    "v5.1-03-Ericson.pdf": ("Is It Mormon Doctrine That Mormon Doctrine Is True? A Rejoinder", ["Loyd Ericson"]),
    "v5.2_04Lane.pdf": ("I Am Among You as One That Serveth", ["Jennifer C. Lane"]),
    "v4.2-01Bradshaw-Head.pdf": ("Mormonism’s Satan and the Tree of Life", ["Jeffrey M. Bradshaw", "Ronan James Head"]),
    "v4.2-02Osler.pdf": ("A God Who Is Morally Praiseworthy: A Response to Carl Mosser", ["Blake T. Ostler"]),
    "v4.2-03Mosser.pdf": ("A Lapsable Deity and Mormonism’s Problem of Evil: A Rejoinder to Blake Ostler", ["Carl Mosser"]),
    "v4.2-04Spencer.pdf": ("Taking Grace for Granted: A Roundabout Review of Adam Miller’s Immanent Grace", ["Joseph M. Spencer"]),
}


def head_author(pages):
    """The author named in the odd-page running heads ('Kate Holbrook  89' or 'Faulconer: Dwelling in Hope 21')."""
    seen = collections.Counter()
    for pg in (pages or [])[1:12]:
        lines = [l.strip() for l in pg.splitlines() if l.strip()]
        for l in lines[:1]:
            l = re.sub(r"\s*\[?\d{1,4}\]?$", "", re.sub(r"^\[?\d{1,4}\]?\s*", "", l)).strip()
            if l and not re.match(r"(?i)e\s*l\s*e\s*m\s*e\s*n\s*t", l) and len(l) < 70:
                seen[l] += 1
    return seen.most_common(1)[0][0] if seen and seen.most_common(1)[0][1] >= 2 else None


def title_and_authors(pages):
    """From page 1: the lines before 'by Author' (or before the author the running heads
    name) are the title."""
    if not pages:
        return None, []
    raw = [re.sub(r"^\s*[A-Za-z]\s{3,}(?=\S)", "", l) for l in pages[0].splitlines()]  # drop-cap letters
    lines = [re.sub(r"\s+", " ", l).strip() for l in raw]
    lines = [l for l in lines if len(l) > 2 and not re.match(r"^[IVX]+\.\s+[A-Z][A-Z ]+$", l)]
    for i, l in enumerate(lines[:20]):
        m = re.match(r"by\s+([A-Z].+)$", l)
        if m and len(l) < 80:
            authors = split_authors(m.group(1))
            title = [t for t in lines[max(0, i - 6):i] if t not in authors and not re.match(r"(?i)element\b", t)]
            return unshout(" ".join(title).strip()) or None, authors
    ha = head_author(pages)
    if ha and ":" not in ha:
        key = despace(ha).upper()
        for i, l in enumerate(lines[:12]):
            if despace(l).upper() == key:
                title = [t for t in lines[max(0, i - 6):i]
                         if not re.match(r"(?i)element\b", t) and despace(t).upper() != key]
                if title:
                    return unshout(" ".join(title).strip()), split_authors(ha)
    return None, []


def harvest_wcu(out, media, issues, posts):
    url = media["source_url"]
    name = os.path.basename(urllib.parse.urlsplit(url).path)
    item = slugify(os.path.splitext(name)[0])
    rel = f"files/wcu/{name}"
    path = os.path.join(out, rel)
    if not os.path.exists(path):
        save(out, rel, fetch(url, want_pdf=True))
    pages = page_texts(path)
    vol, iss, season = issue_from_heads(pages)
    m = re.search(r"v\.?(\d+)\.(\d+)", name)
    if not vol and m:
        vol, iss = m.group(1), m.group(2)
    if not vol and name.startswith("element-") and name.endswith("-sm.pdf"):
        vol, iss = "1", "1"  # the five "-sm" files are the first issue's (their wcu posts sit under v1-1)
    page = issues.get((vol, (iss or "").split("-")[0]))
    if not season and page:
        season = page["season"]
    title, authors = FIXED.get(name) or title_and_authors(pages)
    if title:  # a section heading or footnote mark caught on the end
        title = re.sub(r"(?<=[A-Za-z”’\"])\d{1,2}$", "", re.sub(r"\s+INTRODUCTION$", "", title))
    if not title:
        title = os.path.splitext(name)[0]
        log("  no title on page 1:", name)
    landing = page["link"] if page else f"{WCU}/"
    for t, link in posts.items():
        if norm_title(title).startswith(t[:30]) or t.startswith(norm_title(title)[:30]):
            landing = link
    offset = head_offset(pages)
    n = pdf_pages(path)
    with open(path, "rb") as f:
        body = f.read()
    row = {
        "id": f"{NS}:{item}",
        "kind": "article",
        "title": title,
        "authors": authors,
        "published": (re.search(r"\d{4}", season or "") or [None])[0],
        "collection": COLLECTION,
        "volume": vol,
        "issue": iss,
        "pages": (f"{offset + 1}-{offset + n}" if n > 1 else str(offset + 1)) if offset is not None and n else None,
        "doi": None,
        "section": None,
        "label_offset": offset,
        "landing_url": landing,
        "source_url": url,
        "file": rel,
        "media_type": "application/pdf",
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "fetched_at": now(),
        "licence": LICENCE_WCU,
        "pdf_pages": n,
    }
    write_json(os.path.join(out, "meta", item + ".json"), row)
    return row


def harvest_dialogue_issue(out, slug, link, vol, iss, issues):
    page = fetch(link).decode("utf-8", "replace")
    m = re.search(r'href="([^"]+?\.pdf)"[^>]*class="dl-pdf"', page) or re.search(
        r'href="([^"]*/wp-content/uploads/[^"]+?\.pdf)"', page, re.I)
    if not m:
        raise Gone(f"no PDF on {link}")
    url = abs_url(m.group(1), DIALOGUE + "/")
    name = os.path.basename(urllib.parse.urlsplit(url).path)
    item = slugify(f"v{vol}-{iss}-issue")
    rel = f"files/dialogue/{name}"
    path = os.path.join(out, rel)
    if not os.path.exists(path):
        save(out, rel, fetch(url, want_pdf=True))
    pages = page_texts(path)
    hv, hi, season = issue_from_heads(pages)
    if not season and issues.get((vol, iss.split("-")[0])):
        season = issues[(vol, iss.split("-")[0])]["season"]
    offset = head_offset(pages)
    n = pdf_pages(path)
    with open(path, "rb") as f:
        body = f.read()
    label = f"Issues {iss.replace('-', ' and ')}" if "-" in iss else f"Issue {iss}"
    row = {
        "id": f"{NS}:{item}",
        "kind": "article",
        "title": f"Element, Volume {vol}, {label}" + (f" ({season})" if season else ""),
        "authors": [],
        "published": (re.search(r"\d{4}", season or "") or [None])[0],
        "collection": COLLECTION,
        "volume": vol,
        "issue": iss,
        "pages": None,
        "doi": None,
        "section": None,
        "label_offset": offset,
        "landing_url": link,
        "source_url": url,
        "file": rel,
        "media_type": "application/pdf",
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "fetched_at": now(),
        "licence": LICENCE_DIALOGUE,
        "pdf_pages": n,
        "contents": [],  # a whole issue; its pieces aren't listed separately
    }
    write_json(os.path.join(out, "meta", item + ".json"), row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new rows (testing)")
    args = ap.parse_args()
    out = args.out
    for d in ("files", "meta"):
        os.makedirs(os.path.join(out, d), exist_ok=True)

    fresh = have = failed = 0
    try:
        issues = {}
        for p in fetch_json(f"{WCU}/wp-json/wp/v2/pages?per_page=100&_fields=link,content"):
            h = re.search(r'module_header">\s*Volume\s+(\d+),\s*Issues?\s+(\d+).*?</h1>.*?subhead">(.*?)</span>',
                          p["content"]["rendered"], re.S)
            if h:
                issues[(h.group(1), h.group(2))] = {"link": p["link"], "season": text(h.group(3))}
        posts = {norm_title(p["title"]["rendered"]): p["link"]
                 for p in fetch_json(f"{WCU}/wp-json/wp/v2/posts?per_page=100&_fields=link,title")}
        media = [m for m in fetch_json(f"{WCU}/wp-json/wp/v2/media?per_page=100&_fields=source_url,mime_type")
                 if m["mime_type"] == "application/pdf"]
        log(len(media), "article PDFs on element.wcu.edu;", len(issues), "issue pages;", len(posts), "posts")

        covered = set()
        for i, m in enumerate(media, 1):
            item = slugify(os.path.splitext(os.path.basename(urllib.parse.urlsplit(m["source_url"]).path))[0])
            rec = read_json(os.path.join(out, "meta", item + ".json"))
            if rec and os.path.exists(os.path.join(out, rec["file"])):
                have += 1
                covered.add((rec["volume"], rec["issue"]))
                continue
            try:
                row = harvest_wcu(out, m, issues, posts)
                covered.add((row["volume"], row["issue"]))
                fresh += 1
                log(f"[{i}/{len(media)}] {row['id']} {row['volume']}:{row['issue']} {row['published']} "
                    f"pp.{row['pages']} off={row['label_offset']} | {row['title'][:60]} | {', '.join(row['authors'])}")
            except Gone as e:
                failed += 1
                log(f"[{i}/{len(media)}] SKIP {e}")
            if args.limit and fresh >= args.limit:
                break
        log("issues with article PDFs on wcu:", sorted(covered))

        if not args.limit or fresh < args.limit:
            found = fetch_json(f"{DIALOGUE}/wp-json/wp/v2/dj_articles?search=element&per_page=100&_fields=slug,link")
            for p in sorted(found, key=lambda p: p["slug"]):
                m = re.match(r"element-volume-(\d+)-issue-(\d+(?:-\d+)?)$", p["slug"])
                if not m:
                    continue
                vol, iss = m.group(1), m.group(2)
                if any((vol, x) in covered for x in iss.split("-")):
                    continue
                item = slugify(f"v{vol}-{iss}-issue")
                rec = read_json(os.path.join(out, "meta", item + ".json"))
                if rec and os.path.exists(os.path.join(out, rec["file"])):
                    have += 1
                    continue
                try:
                    row = harvest_dialogue_issue(out, p["slug"], p["link"], vol, iss, issues)
                    fresh += 1
                    log(f"  {row['id']} {row['title']} off={row['label_offset']} {row['pdf_pages']}pp {row['bytes'] // 1024}KB")
                except Gone as e:
                    failed += 1
                    log("  SKIP", e)
    except Challenge as e:
        log("STOP: bot challenge:", e)
        write_manifest(out)
        sys.exit(2)
    n = write_manifest(out)
    log(f"done: {fresh} new, {have} already had, {failed} skipped; manifest {n} rows")


if __name__ == "__main__":
    main()
