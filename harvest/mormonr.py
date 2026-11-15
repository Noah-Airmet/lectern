#!/usr/bin/env python3
"""Mormonr's Q&As and blog posts (B. H. Roberts Foundation; link only).

English pages from the sitemap, saved as HTML with their footnotes. The ten translations are
left out. The archive of primary-source records is bhr_archive.py.

    python3 harvest/mormonr.py --out /data/lectern/links/mormonr [--limit N]
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
SITEMAP = "https://mormonr.org/sitemap.xml"
SECTIONS = {
    # URL section → (directory, kind, collection, slug prefix)
    "qnas": ("qnas", "article", "Mormonr", ""),
    "blog": ("blog", "blog", "Mormonr Blog", "blog-"),
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


def remix_value(text, key):
    """A string value for `key` from the page's Remix stream (turbo-stream: a flat array where
    objects map "_<key index>" to a value index)."""
    for raw in re.findall(r'streamController\.enqueue\(("(?:[^"\\]|\\.)*")\)', text):
        try:
            arr = json.loads(json.loads(raw))
        except ValueError:
            continue
        if key not in arr:
            continue
        k = f"_{arr.index(key)}"
        for v in arr:
            if isinstance(v, dict) and k in v and isinstance(v[k], int) and 0 <= v[k] < len(arr):
                val = arr[v[k]]
                if isinstance(val, str):
                    return val
    return None


def row_for(out, section, pub_id, url_slug):
    directory, kind, collection, prefix = SECTIONS[section]
    slug = prefix + url_slug.lower().replace("_", "-")
    rel = f"{directory}/{slug}.html"
    path = os.path.join(out, rel)
    with open(path, "rb") as f:
        data = f.read()
    text = data.decode("utf-8", "replace")
    m = re.search(r'<meta name="og:title" content="([^"]*)"', text) or re.search(r"<title>(.*?)</title>", text, re.S)
    title = html.unescape(m.group(1)).strip() if m else url_slug
    published = None
    if section == "blog":
        published = (remix_value(text, "original_published_at") or remix_value(text, "published_at") or "")[:10] or None
    url = f"https://mormonr.org/{section}/{pub_id}/{url_slug}"
    return {
        "id": f"mormonr:{slug}",
        "kind": kind,
        "title": title,
        "authors": [],
        "published": published,
        "collection": collection,
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
        "licence": {
            "id": "all-rights-reserved",
            "evidence_url": url,
            "quote": "Copyright © by B.H. Roberts Foundation.",
        },
    }


def file_for(out, section, url_slug):
    directory, _, _, prefix = SECTIONS[section]
    return os.path.join(out, directory, prefix + url_slug.lower().replace("_", "-") + ".html")


def write_manifest(out, items):
    rows = [row_for(out, *it) for it in items if os.path.exists(file_for(out, it[0], it[2]))]
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
    items, slugs = [], set()
    for loc in re.findall(r"<loc>([^<]+)</loc>", sitemap):
        m = re.fullmatch(r"https://mormonr\.org/(qnas|blog)/([A-Za-z0-9]+)/([A-Za-z0-9_-]+)", html.unescape(loc).strip())
        if not m:
            continue
        key = file_for(args.out, m.group(1), m.group(3))
        if key in slugs:
            print(f"skip duplicate slug: {loc}", flush=True)
            continue
        slugs.add(key)
        items.append(m.groups())
    print(f"sitemap: {sum(s == 'qnas' for s, *_ in items)} Q&As, "
          f"{sum(s == 'blog' for s, *_ in items)} blog posts", flush=True)

    fetched = failed = 0
    try:
        for i, (section, pub_id, url_slug) in enumerate(items, 1):
            path = file_for(args.out, section, url_slug)
            if os.path.exists(path):
                continue
            if args.limit is not None and fetched >= args.limit:
                break
            url = f"https://mormonr.org/{section}/{pub_id}/{url_slug}"
            try:
                body = fx.get(url)
            except urllib.error.HTTPError as e:
                print(f"[{i}/{len(items)}] {e.code} {url}", flush=True)
                failed += 1
                continue
            write_atomic(path, body)
            fetched += 1
            print(f"[{i}/{len(items)}] {len(body):>8} {url}", flush=True)
    except BotChallenge as e:
        print(f"STOP: bot challenge, {e}", flush=True)
        print(f"manifest: {write_manifest(args.out, items)} rows", flush=True)
        sys.exit(2)
    print(f"done: fetched {fetched}, failed {failed}, manifest {write_manifest(args.out, items)} rows", flush=True)


if __name__ == "__main__":
    main()
