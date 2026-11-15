#!/usr/bin/env python3
"""Scripture Central's KnoWhys and Evidence pages (link only).

English pages from the site's sitemap, saved as HTML. The sitemap also lists the archive of
articles copied from other journals; those are left out (we link the original publishers).
Spanish and Portuguese translations (centraldle.es, centraldasescrituras.org) are left out too.

    python3 harvest/scripturecentral.py --out /data/lectern/links/scripturecentral [--limit N]
"""

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlsplit

UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
SITEMAP = "https://admin.scripturecentral.org/api/sitemap/index.xml"
SECTIONS = {
    # sitemap path → (ns, collection)
    "knowhy": ("knowhy", "Scripture Central KnoWhys"),
    "evidence": ("evidence", "Scripture Central Evidence"),
}
LICENCE = {
    "id": "all-rights-reserved",
    "evidence_url": "https://scripturecentral.org/policies",
    "quote": "Scripture Central retains the complete ownership of all content produced by "
    "official Scripture Central content creators.",
}


class BotChallenge(Exception):
    pass


class Fetcher:
    """One request at a time, at least `delay` seconds between requests to a host."""

    def __init__(self, delay=1.0):
        self.delay = delay
        self.last = {}

    def get(self, url, tries=3):
        host = urlsplit(url).netloc
        for attempt in range(tries):
            wait = self.last.get(host, 0) + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last[host] = time.monotonic()
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
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


def write_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def next_data(text):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', text, re.S)
    return json.loads(m.group(1)) if m else None


def row_for(out, section, slug):
    """The manifest row, read from the saved page."""
    ns, collection = SECTIONS[section]
    rel = f"{section}/{slug}.html"
    path = os.path.join(out, rel)
    with open(path, "rb") as f:
        data = f.read()
    text = data.decode("utf-8", "replace")
    attrs = {}
    d = next_data(text)
    if d:
        attrs = ((d.get("props", {}).get("pageProps", {}).get("contentData") or {}).get("attributes")) or {}
    title = attrs.get("title")
    if not title:
        m = re.search(r"<title>(.*?)</title>", text, re.S)
        title = html.unescape(m.group(1)).split(" | ")[0].strip() if m else slug
    author = (((attrs.get("author") or {}).get("data") or {}).get("attributes") or {}).get("title")
    url = f"https://scripturecentral.org/{section}/{slug}"
    return {
        "id": f"{ns}:{slug}",
        "kind": "article",
        "title": title.strip(),
        "authors": [author] if author else [],
        "published": attrs.get("publicationDate") or (attrs.get("publishedAt") or "")[:10] or None,
        "collection": collection,
        "number": attrs.get("number"),
        "volume": None,
        "issue": None,
        "pages": None,
        "doi": None,
        "label_offset": None,
        "landing_url": url,
        "source_url": url,
        "file": rel,
        "media_type": "text/html",
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "fetched_at": datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "licence": LICENCE,
    }


def write_manifest(out, items):
    rows = []
    for section, slug in items:
        if os.path.exists(os.path.join(out, section, slug + ".html")):
            rows.append(row_for(out, section, slug))
    tmp = os.path.join(out, "manifest.jsonl.part")
    with open(tmp, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, os.path.join(out, "manifest.jsonl"))
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, help="fetch at most N new pages (for testing)")
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    fx = Fetcher(args.delay)

    sitemap = fx.get(SITEMAP).decode("utf-8")
    items, seen = [], set()
    for loc in re.findall(r"<loc>([^<]+)</loc>", sitemap):
        m = re.fullmatch(r"https://scripturecentral\.org/(knowhy|evidence)/([^/?#]+)", html.unescape(loc).strip())
        if m and m.group(2) not in seen and re.fullmatch(r"[a-z0-9-]+", m.group(2)):
            seen.add(m.group(2))
            items.append((m.group(1), m.group(2)))
        elif m:
            print(f"skip odd slug: {loc}", flush=True)
    print(f"sitemap: {sum(s == 'knowhy' for s, _ in items)} KnoWhys, "
          f"{sum(s == 'evidence' for s, _ in items)} Evidence pages", flush=True)

    fetched = failed = 0
    try:
        for i, (section, slug) in enumerate(items, 1):
            path = os.path.join(args.out, section, slug + ".html")
            if os.path.exists(path):
                continue
            if args.limit is not None and fetched >= args.limit:
                break
            url = f"https://scripturecentral.org/{section}/{slug}"
            try:
                body = fx.get(url)
            except urllib.error.HTTPError as e:
                print(f"[{i}/{len(items)}] {e.code} {url}", flush=True)
                failed += 1
                continue
            if b"__NEXT_DATA__" not in body:
                print(f"[{i}/{len(items)}] no page data, skipped: {url}", flush=True)
                failed += 1
                continue
            write_atomic(path, body)
            fetched += 1
            if fetched % 50 == 0:
                print(f"[{i}/{len(items)}] fetched {fetched}", flush=True)
    except BotChallenge as e:
        print(f"STOP: bot challenge, {e}", flush=True)
        n = write_manifest(args.out, items)
        print(f"manifest: {n} rows", flush=True)
        sys.exit(2)
    n = write_manifest(args.out, items)
    print(f"done: fetched {fetched}, failed {failed}, manifest {n} rows", flush=True)


if __name__ == "__main__":
    main()
