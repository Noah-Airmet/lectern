#!/usr/bin/env python3
"""Harvest Dialogue: A Journal of Mormon Thought from dialoguejournal.com (link-only tier).

Lists every article through the site's WordPress REST API (dj_articles), reads each
article's page for its PDF link, issue and authors, and fetches the per-article PDF.
An article with no PDF of its own falls back to its issue's whole-issue PDF (one row
per issue, the pieces listed in "contents"); with neither, the article page's HTML is
kept. DOIs and printed page ranges come from Crossref (ISSN 0012-2157), matched by
volume, issue and title. label_offset is read from the running heads with pdftotext
when it's installed; failing that, when Crossref's page range matches the PDF's page
count, offset = start - 1; otherwise null. The number in a PDF's filename is not its
start page, so it is never used.

The Element archive pages (slug element-volume-*) are left to element.py.

    python3 harvest/dialogue.py --out /data/lectern/links/dialogue [--limit N] [--issues winter-1988,fall-2026]

Re-runnable: page reads are cached in <out>/pages/, a row whose record and file are on
disk is skipped, and the manifest is rewritten from the records in <out>/meta/.
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

SITE = "https://www.dialoguejournal.com"
UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
DELAY = 1.5  # seconds between requests to one host
NS = "dialogue"
COLLECTION = "Dialogue: A Journal of Mormon Thought"
ISSN = "0012-2157"
LICENCE = {
    "id": "unknown",
    "evidence_url": f"{SITE}/submissions/publication-policy/",
    "quote": "Creative Commons License CC BY-NC-ND",
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


def abs_url(href):
    return urllib.parse.urljoin(SITE + "/", html.unescape(href))


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

def all_pages(url, fields):
    """Every record of a WP REST collection."""
    rows, page = [], 1
    while True:
        sep = "&" if "?" in url else "?"
        batch = fetch_json(f"{url}{sep}per_page=100&page={page}&_fields={fields}")
        rows += batch
        if len(batch) < 100:
            return rows
        page += 1


def crossref(out):
    """{(volume, issue): [(normalised title, page, doi)]} for the journal, cached."""
    cache = os.path.join(out, "pages", "crossref.json")
    items = read_json(cache)
    if items is None:
        items, cursor = [], "*"
        while True:
            q = urllib.parse.urlencode({"rows": 1000, "cursor": cursor, "select": "DOI,volume,issue,page,title"})
            msg = fetch_json(f"https://api.crossref.org/journals/{ISSN}/works?{q}")["message"]
            items += msg.get("items", [])
            if not msg.get("items") or not msg.get("next-cursor"):
                break
            cursor = msg["next-cursor"]
        write_json(cache, items)
    idx = collections.defaultdict(list)
    for it in items:
        t = norm_title((it.get("title") or [""])[0])
        idx[(str(it.get("volume", "")), str(it.get("issue", "")))].append((t, it.get("page"), it.get("DOI")))
    log(len(items), "Crossref records")
    return idx


def match_doi(idx, vol, iss, title):
    t = norm_title(title)
    if not t or not vol:
        return None, None
    for ct, page, doi in idx.get((str(vol), str(iss)), []):
        if ct == t or (min(len(ct), len(t)) >= 15 and (ct.startswith(t) or t.startswith(ct))):
            return doi, page
    return None, None


def read_article(out, a):
    """What the article page says: PDF, issue, section, authors. Cached per WP id."""
    cache = os.path.join(out, "pages", f"{a['id']}.json")
    info = read_json(cache)
    if info is not None:
        return info
    page = fetch(a["link"]).decode("utf-8", "replace")
    m = re.search(r'<a href="([^"]+?\.pdf)"[^>]*class="dl-pdf"', page) or re.search(
        r'href="((?:https?://(?:www\.)?dialoguejournal\.com)?/wp-content/uploads/(?!sbi/issues/)[^"]+?\.pdf)"', page, re.I
    )
    pdf = abs_url(m.group(1)) if m else None
    vi = re.search(r'<p class="vol-info">(.*?)</p>', page, re.S)
    vol = iss = section = issue_href = None
    if vi:
        v = re.search(r"Volume\s+(\d+),\s*No\.\s*([\w/&-]+)", text(vi.group(1)))
        if v:
            vol, iss = str(int(v.group(1))), v.group(2).lstrip("0") or "0"
        section = text(vi.group(1).split("&ndash;")[0]) if "&ndash;" in vi.group(1) else None
        h = re.search(r'href="([^"]*/issues/[^"]+)"', vi.group(1))
        issue_href = abs_url(h.group(1)) if h else None
    al = re.search(r'class="row author-line">(.*?)</div>\s*</div>', page, re.S)
    authors = [text(x) for x in re.findall(r'class="author url fn"[^>]*>(.*?)</a>', al.group(1) if al else "", re.S)]
    info = {"pdf": pdf, "volume": vol, "issue": iss, "section": section or None, "issue_href": issue_href, "authors": authors}
    if not pdf:
        save(out, f"files/html/{slugify(a['slug'])}.html", page.encode("utf-8"))
    write_json(cache, info)
    return info


def read_issue(out, href):
    """The issue page's whole-issue PDF, cached."""
    key = slugify(urllib.parse.urlsplit(href).path)
    cache = os.path.join(out, "pages", f"issue-{key}.json")
    info = read_json(cache)
    if info is not None:
        return info
    try:
        page = fetch(href).decode("utf-8", "replace")
        m = re.search(r'href="([^"]*/wp-content/uploads/sbi/issues/[^"]+?\.pdf)"', page, re.I)
        info = {"pdf": abs_url(m.group(1)) if m else None}
    except Gone as e:
        log("  issue page missing:", e)
        info = {"pdf": None}
    write_json(cache, info)
    return info


def section_of(a, info, cats):
    names = [cats[c] for c in a.get("dj_article_categories") or [] if c in cats]
    return names[0] if names else info["section"]


def year_of(name):
    m = re.search(r"(1[89]\d\d|20\d\d)", name or "")
    return m.group(1) if m else None


def build_row(out, item, arts, infos, issue, idx, file_url, whole_issue, cats, shared_dois=()):
    """Fetch file_url (unless it's on disk) and write the record for it."""
    first = arts[0]
    fi = infos[first["id"]]
    vol, iss = fi["volume"], fi["issue"]
    vol = str(int(vol)) if vol and vol.isdigit() else vol
    iss = iss.lstrip("0") or iss if iss else iss
    if file_url:
        sub = "issues" if whole_issue else "articles"
        rel = f"files/{sub}/{os.path.basename(urllib.parse.urlsplit(file_url).path)}"
        path = os.path.join(out, rel)
        if not os.path.exists(path):
            save(out, rel, fetch(file_url, want_pdf=True))
        media, source = "application/pdf", file_url
    else:
        rel = f"files/html/{slugify(first['slug'])}.html"
        path = os.path.join(out, rel)
        media, source = "text/html", first["link"]
    with open(path, "rb") as f:
        body = f.read()

    n_pages = offset = pages = doi = None
    if media == "application/pdf":
        n_pages = pdf_pages(path)
        offset = head_offset(page_texts(path))
    if not whole_issue:
        # A DOI that several of the issue's pages match is a roundtable's, not this piece's.
        dois = [(None, None) if d in shared_dois else (d, p)
                for d, p in (match_doi(idx, vol, iss, a["title"]["rendered"]) for a in arts)]
        doi, crpage = dois[0]
        if len(arts) > 1:
            # One PDF holding several pieces: the range runs from the first to the last.
            starts = [p for _, p in dois if p]
            crpage = None
            if starts:
                lo = min(int(re.match(r"\d+", p).group()) for p in starts if re.match(r"\d+", p))
                hi = max(int(re.findall(r"\d+", p)[-1]) for p in starts if re.findall(r"\d+", p))
                crpage = f"{lo}-{hi}"
        crpage = re.sub(r"\s*[–—-]\s*", "-", crpage) if crpage else None
        nums = [int(x) for x in re.findall(r"\d+", crpage or "")]
        if offset is None and n_pages and len(nums) == 2 and nums[1] - nums[0] + 1 == n_pages:
            offset = nums[0] - 1
        if offset is not None and n_pages:
            # The file's own range, which can run past Crossref's (a review sharing a page).
            pages = f"{offset + 1}-{offset + n_pages}" if n_pages > 1 else str(offset + 1)
            if nums and nums[0] - 1 != offset:
                log(f"  note: {item}: running heads give offset {offset}, Crossref says pp. {crpage}")
        else:
            pages = crpage

    if whole_issue:
        title = f"Dialogue, Volume {vol}, No. {iss} ({issue['name']})" if vol else f"Dialogue, {issue['name']}"
        authors = []
        landing = issue.get("link") or first["link"]
    else:
        title = "; ".join(text(a["title"]["rendered"]) for a in arts)
        authors = list(dict.fromkeys(x for a in arts for x in infos[a["id"]]["authors"]))
        landing = first["link"]
    row = {
        "id": f"{NS}:{item}",
        "kind": "article",
        "title": title,
        "authors": authors,
        "published": year_of(issue.get("name")),
        "collection": COLLECTION,
        "volume": vol,
        "issue": iss,
        "pages": pages,
        "doi": doi,
        "section": None if whole_issue else section_of(arts[0], fi, cats),
        "label_offset": offset,
        "landing_url": landing,
        "source_url": source,
        "file": rel,
        "media_type": media,
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "fetched_at": now(),
        "licence": LICENCE,
        "pdf_pages": n_pages,
    }
    if whole_issue or len(arts) > 1:
        row["contents"] = [
            {"title": text(a["title"]["rendered"]), "authors": infos[a["id"]]["authors"],
             "section": section_of(a, infos[a["id"]], cats), "landing_url": a["link"]}
            for a in arts
        ]
    write_json(os.path.join(out, "meta", item + ".json"), row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new rows (testing)")
    ap.add_argument("--issues", default="", help="comma-separated issue slugs only (testing)")
    args = ap.parse_args()
    out = args.out
    for d in ("files", "meta", "pages"):
        os.makedirs(os.path.join(out, d), exist_ok=True)

    try:
        pol = fetch(LICENCE["evidence_url"]).decode("utf-8", "replace")
        if LICENCE["quote"] not in text(pol):
            log("WARNING: licence quote no longer on", LICENCE["evidence_url"])

        log("issues")
        issues = {i["id"]: i for i in all_pages(f"{SITE}/wp-json/wp/v2/dj_issues", "id,name,slug,link,count")}
        log(len(issues), "issues")
        log("articles")
        cats = {c["id"]: text(c["name"]) for c in all_pages(f"{SITE}/wp-json/wp/v2/dj_article_categories", "id,name")}
        arts = all_pages(f"{SITE}/wp-json/wp/v2/dj_articles?orderby=id&order=asc", "id,slug,link,title,dj_issues,dj_article_categories")
        arts = [a for a in arts if not a["slug"].startswith("element-volume")]
        log(len(arts), "articles (Element archive pages left out)")
        idx = crossref(out)
    except Challenge as e:
        log("STOP: bot challenge:", e)
        sys.exit(2)

    groups = collections.defaultdict(list)
    for a in arts:
        groups[(a.get("dj_issues") or [None])[0]].append(a)
    order = sorted(groups, key=lambda k: (k is None, -(issues.get(k, {}).get("id") or 0)))
    if args.issues:
        want = set(args.issues.split(","))
        order = [k for k in order if issues.get(k, {}).get("slug") in want]

    fresh = have = failed = 0
    t0 = time.monotonic()
    for gi, key in enumerate(order, 1):
        issue = issues.get(key, {"name": None, "slug": None, "link": None})
        log(f"[{gi}/{len(order)}] issue {issue['slug']}: {len(groups[key])} articles")
        try:
            infos = {}
            for a in groups[key]:
                try:
                    infos[a["id"]] = read_article(out, a)
                except Gone as e:
                    failed += 1
                    log("  SKIP article page:", e)
            by_file = collections.OrderedDict()
            loose = []
            for a in groups[key]:
                if a["id"] not in infos:
                    continue
                if infos[a["id"]]["pdf"]:
                    by_file.setdefault(infos[a["id"]]["pdf"], []).append(a)
                else:
                    loose.append(a)
            jobs = [(slugify(arts_[0]["slug"]), arts_, url, False) for url, arts_ in by_file.items()]
            if loose:
                href = infos[loose[0]["id"]]["issue_href"] or issue.get("link")
                ipdf = read_issue(out, href)["pdf"] if href else None
                if ipdf:
                    stem = slugify(os.path.splitext(os.path.basename(ipdf))[0])
                    jobs.append((f"{stem}-issue", loose, ipdf, True))
                else:
                    jobs += [(slugify(a["slug"]), [a], None, False) for a in loose]
            def vi(a):
                v, n = infos[a["id"]]["volume"], infos[a["id"]]["issue"]
                return (str(int(v)) if v and v.isdigit() else v), (n.lstrip("0") or n if n else n)
            hits = collections.Counter(match_doi(idx, *vi(a), a["title"]["rendered"])[0] for a in groups[key] if a["id"] in infos)
            shared = {d for d, c in hits.items() if d and c > 1}
            for item, arts_, url, whole in jobs:
                rec = read_json(os.path.join(out, "meta", item + ".json"))
                if rec and os.path.exists(os.path.join(out, rec["file"])):
                    have += 1
                    continue
                try:
                    row = build_row(out, item, arts_, infos, issue, idx, url, whole, cats, shared)
                    fresh += 1
                    log(f"  {row['id']} {row['volume']}:{row['issue']} pp.{row['pages']} off={row['label_offset']} "
                        f"{row['bytes'] // 1024}KB" + (f" ({len(arts_)} pieces)" if len(arts_) > 1 else ""))
                except Gone as e:
                    failed += 1
                    log("  SKIP", item, e)
                if args.limit and fresh >= args.limit:
                    break
        except Challenge as e:
            log("STOP: bot challenge:", e)
            write_manifest(out)
            sys.exit(2)
        rate = fresh / max(time.monotonic() - t0, 1) * 3600
        log(f"  manifest: {write_manifest(out)} rows; {rate:.0f} new rows/hour")
        if args.limit and fresh >= args.limit:
            break
    n = write_manifest(out)
    log(f"done: {fresh} new, {have} already had, {failed} skipped; manifest {n} rows")


if __name__ == "__main__":
    main()
