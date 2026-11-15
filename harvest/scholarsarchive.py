#!/usr/bin/env python3
"""Harvest Maxwell Institute and BYU religion journals from BYU ScholarsArchive (link-only tier).

Journal of Book of Mormon Studies, the Review of Books on the Book of Mormon / FARMS Review
(to 2011) and Mormon Studies Review (2014-2023), Studies in the Bible and Antiquity,
Studia Antiqua and Religion in the Age of Enlightenment. Records come from the site's
OAI-PMH endpoint (/do/oai/), whose Identify says "Metadata can be used by commercial and
non-commercial service providers". Written approval to harvest full content is being
arranged (shelf/links.md).

    python3 harvest/scholarsarchive.py --out /data/lectern/links/scholarsarchive [--sets jbms,rae] [--limit N] [--no-pdf]

PDFs sit behind a Cloudflare bot check. Each run tries them politely and stops trying at
the first challenge, so every record still reaches the manifest, with file null. Once
ScholarsArchive lets the harvester through, a re-run fills the files in.

Every ScholarsArchive PDF starts with its own cover page, and some journals add a title
page of their own after it, so label_offset is read from the running heads with pdftotext
when there's a PDF, and is null when there isn't.

Re-runnable: records are rewritten from OAI each run, a PDF already on disk is kept, and
the manifest is rewritten from the records in <out>/meta/.
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
import xml.etree.ElementTree as ET

SITE = "https://scholarsarchive.byu.edu"
OAI = SITE + "/do/oai/"
UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
DELAY = 2.0  # seconds between requests to one host
OAI_NS = "{http://www.openarchives.org/OAI/2.0/}"
DC = "{http://purl.org/dc/elements/1.1/}"

# ScholarsArchive set -> (Lectern ns, collection name)
SETS = {
    "jbms": ("jbms", "Journal of Book of Mormon Studies"),
    "msr": ("farmsreview", None),  # name by volume, below
    "msr2": ("msr", "Mormon Studies Review"),
    "sba": ("sba", "Studies in the Bible and Antiquity"),
    "studiaantiqua": ("studiaantiqua", "Studia Antiqua"),
    "rae": ("rae", "Religion in the Age of Enlightenment"),
}
# Whole-issue PDFs repeat the articles already harvested one by one.
SKIP_TYPES = {"full issue"}
# Lines Digital Commons stamps on its PDFs, whose numbers aren't the printed pages.
STAMP = re.compile(r"Published by (?:BYU )?ScholarsArchive|Downloaded from |ScholarsArchive\.byu\.edu|, Art\. \d+$", re.I)


def farms_review_name(vol):
    """The old review's title as printed on each volume."""
    if vol is None:
        return "FARMS Review"
    if vol <= 7:
        return "Review of Books on the Book of Mormon"
    if vol <= 14:
        return "FARMS Review of Books"
    if vol <= 22:
        return "FARMS Review"
    return "Mormon Studies Review"


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
            raise Challenge(f"{status} {hdrs.get('cf-mitigated', '')} at {url}")
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


def oai(params):
    root = ET.fromstring(fetch(OAI + "?" + urllib.parse.urlencode(params)))
    err = root.find(OAI_NS + "error")
    return root, (err.get("code") if err is not None else None)


_since = [0]


def since():
    """A new, harmless `from` date (all records are later) for each request that must not hit the cache."""
    _since[0] += 1
    return (datetime.date(1900, 1, 1) + datetime.timedelta(days=_since[0])).isoformat()


def list_records(setspec):
    """Every record in a set.

    About half the time the endpoint answers noRecordsMatch (quickly) for a page that has
    records, and Cloudflare caches that answer for four hours, so asking the same URL again
    gets the same answer. So each request asks from a different `from` date, which is a new
    URL: for a later page, the date inside the resumption token (`<n>/<format>/<cursor>/<from>/`)."""
    for attempt in range(6):
        prefix = ("qdc", "oai_dc", "dcq")[attempt % 3]
        for _ in range(10):
            root, err = oai({"verb": "ListRecords", "metadataPrefix": prefix, "set": f"publication:{setspec}", "from": since()})
            if err != "noRecordsMatch":
                break
            time.sleep(3)
        records = []
        while not err:
            lr = root.find(OAI_NS + "ListRecords")
            records += lr.findall(OAI_NS + "record") if lr is not None else []
            tok = lr.find(OAI_NS + "resumptionToken") if lr is not None else None
            if tok is None or not (tok.text or "").strip():
                total = tok.get("completeListSize") if tok is not None else None
                log(f"  {setspec}: {len(records)} records as {prefix} (list size {total or len(records)})")
                return records
            token = tok.text.strip()
            for _ in range(10):
                root, err = oai({"verb": "ListRecords", "resumptionToken": token})
                m = re.fullmatch(r"(.*/)\d{4}-\d{2}-\d{2}/", token)
                if err != "noRecordsMatch" or not m:
                    break
                token = m.group(1) + since() + "/"
                time.sleep(3)
        log(f"  {setspec}: OAI {err} after {len(records)} records as {prefix}; starting again")
        time.sleep(30)
    raise Gone(f"OAI kept failing for {setspec}")


def person(s):
    """'Brown, S. Kent' -> 'S. Kent Brown'; 'Hauglid, Brian M., Jr.' -> 'Brian M. Hauglid Jr.'"""
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if len(parts) == 2:
        return f"{parts[1]} {parts[0]}"
    if len(parts) == 3:
        return f"{parts[1]} {parts[0]} {parts[2]}"
    return s.strip()


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def running_head_offset(path, expect=()):
    """printed page - PDF page, from the page numbers in the running heads; None if unsure."""
    try:
        out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    pages = out.decode("utf-8", "replace").split("\f")
    votes = collections.Counter()
    for i, pg in enumerate(pages, 1):
        lines = [l.strip() for l in pg.splitlines() if l.strip() and not STAMP.search(l)]
        found = set()
        for l in lines[:2] + lines[-2:]:
            for m in (re.match(r"(\d{1,4})\b(?![./:])", l), re.search(r"(?<![\d/(.,:-])(\d{1,4})$", l)):
                if m:
                    found.add(int(m.group(1)) - i)
        votes.update(found)
    if not votes:
        return None
    (off, n), *rest = votes.most_common(2) + [(None, 0)]
    if n >= 3 and n >= 0.4 * (len(pages) - 1) and n > 2 * rest[0][1]:
        return off
    if n >= 2 and n > 2 * rest[0][1] and n >= 0.4 * (len(pages) - 1):
        return off
    if off in expect and n >= 1 and rest[0][1] == 0:
        return off
    return None


def printed_reference(path):
    """The page range from a Maxwell Institute title page: 'Reference ... 1/1 (1992): 163–80.'"""
    try:
        out = subprocess.run(["pdftotext", "-l", "3", path, "-"], capture_output=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"Reference\s.*?\(\d{4}\):\s*(\d+)(?:\s*[–—-]\s*(\d+))?", out.decode("utf-8", "replace"), re.S)
    if not m:
        return None
    a, b = m.group(1), m.group(2)
    if b and len(b) < len(a):  # 163–80 -> 163-180
        b = a[: len(a) - len(b)] + b
    return f"{a}-{b}" if b else a


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
    """Every record, including those whose PDF we couldn't fetch (file null)."""
    meta = os.path.join(out, "meta")
    rows = []
    for name in sorted(os.listdir(meta)):
        if name.endswith(".json"):
            with open(os.path.join(meta, name), encoding="utf-8") as f:
                rows.append(json.load(f))
    tmp = os.path.join(out, "manifest.jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, os.path.join(out, "manifest.jsonl"))
    return len(rows), sum(1 for r in rows if r.get("file"))


def to_row(setspec, rec):
    """An OAI record as a manifest row (without the file fields), or None to skip it."""
    head = rec.find(OAI_NS + "header")
    if head is None or head.get("status") == "deleted":
        return None
    md = rec.find(OAI_NS + "metadata")
    if md is None:
        return None
    dc = collections.defaultdict(list)
    for el in md.iter():
        if el.tag.startswith(DC) and (el.text or "").strip():
            dc[el.tag[len(DC):]].append(el.text.strip())
    kind_ = (dc.get("type") or [""])[0]
    if kind_.lower() in SKIP_TYPES:
        return None
    oai_id = head.findtext(OAI_NS + "identifier") or ""
    m = re.search(r":([a-z0-9_]+)-(\d+)$", oai_id)
    if not m:
        return None
    context, article = m.group(1), m.group(2)
    landing = next((u for u in dc["identifier"] if u.startswith(f"{SITE}/{context}/")), None)
    has_pdf = any(u.lower().endswith(".pdf") for u in dc["identifier"])
    if not landing:
        return None
    path = landing[len(f"{SITE}/{context}/"):].strip("/")
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    vm = re.search(r"vol(\d+)(?:/iss(\d+))?", path)
    vol = int(vm.group(1)) if vm else None
    iss = vm.group(2) if vm and vm.group(2) else None
    ns, name = SETS[setspec]
    if setspec == "msr":
        name = farms_review_name(vol)
    date = (dc.get("date.created") or dc.get("date") or [""])[0]
    year = re.match(r"\d{4}", date)
    pdf = f"{SITE}/cgi/viewcontent.cgi?article={article}&context={context}" if has_pdf else None
    return {
        "id": f"{ns}:{slug}",
        "kind": "article",
        "title": text((dc.get("title") or [""])[0]),
        "authors": [person(text(a)) for a in dc.get("creator", [])],
        "published": year.group(0) if year else None,
        "collection": name,
        "volume": str(vol) if vol is not None else None,
        "issue": iss,
        "pages": None,
        "doi": None,
        "section": kind_ or None,
        "abstract": text((dc.get("description.abstract") or dc.get("description") or [""])[0]) or None,
        "label_offset": None,
        "landing_url": landing,
        "source_url": pdf or landing,
        "licence": {
            "id": "unknown",
            "evidence_url": landing,
            "quote": None,
        },
        "file": None,
        "media_type": None,
        "sha256": None,
        "bytes": None,
        "fetched_at": None,
        "pdf_pages": None,
    }


def attach_pdf(out, row, body):
    item = row["id"].replace(":", "-")
    rel = f"files/{item}.pdf"
    path = os.path.join(out, rel)
    if body is not None:
        with open(path + ".part", "wb") as f:
            f.write(body)
        os.replace(path + ".part", path)
        fetched = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        with open(path, "rb") as f:
            body = f.read()
        fetched = None
    pages = printed_reference(path)
    start = int(re.match(r"\d+", pages).group(0)) if pages else None
    row.update(
        file=rel,
        media_type="application/pdf",
        sha256=hashlib.sha256(body).hexdigest(),
        bytes=len(body),
        pdf_pages=pdf_pages(path),
        pages=pages,
        label_offset=running_head_offset(path, () if start is None else (start - 3, start - 2)),
    )
    return fetched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sets", default=",".join(SETS), help="comma-separated ScholarsArchive sets")
    ap.add_argument("--limit", type=int, default=0, help="records per set (testing)")
    ap.add_argument("--no-pdf", action="store_true", help="metadata only")
    args = ap.parse_args()
    out = args.out
    os.makedirs(os.path.join(out, "files"), exist_ok=True)
    os.makedirs(os.path.join(out, "meta"), exist_ok=True)

    blocked = args.no_pdf
    got = 0
    for setspec in args.sets.split(","):
        log("set", setspec)
        try:
            records = list_records(setspec)
        except (Gone, ET.ParseError) as e:
            log("  could not list", setspec, e)
            continue
        except Challenge as e:
            log("STOP: bot challenge on OAI:", e)
            break
        rows, skipped = [], 0
        for rec in records:
            row = to_row(setspec, rec)
            if row is None:
                skipped += 1
            else:
                rows.append(row)
        if args.limit:
            rows = rows[: args.limit]
        log(f"  {len(rows)} items, {skipped} skipped (whole issues, deleted, no landing page)")
        for n, row in enumerate(rows, 1):
            meta = os.path.join(out, "meta", row["id"].replace(":", "-") + ".json")
            old = None
            if os.path.exists(meta):
                with open(meta, encoding="utf-8") as f:
                    old = json.load(f)
            if old and old.get("file") and os.path.exists(os.path.join(out, old["file"])):
                attach_pdf(out, row, None)
                row["fetched_at"] = old.get("fetched_at")
            elif not blocked and row["source_url"] != row["landing_url"]:
                try:
                    row["fetched_at"] = attach_pdf(out, row, fetch(row["source_url"], want_pdf=True))
                    got += 1
                    log(f"  [{n}/{len(rows)}] {row['id']} {row['pages']} off={row['label_offset']} {row['bytes']//1024}KB")
                except Challenge as e:
                    blocked = True
                    log("  PDFs are behind a bot challenge; not trying again this run:", e)
                    log("  going on with metadata only (file null)")
                except Gone as e:
                    log(f"  [{n}/{len(rows)}] no PDF for {row['id']}: {e}")
            write_json(meta, row)
        total, with_files = write_manifest(out)
        log(f"  manifest: {total} rows, {with_files} with files")
    total, with_files = write_manifest(out)
    log(f"done: manifest {total} rows, {with_files} with files, {got} PDFs fetched this run"
        + ("; PDFs blocked by a bot challenge" if blocked and not args.no_pdf else ""))


if __name__ == "__main__":
    main()
