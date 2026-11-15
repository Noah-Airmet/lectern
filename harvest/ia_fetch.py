#!/usr/bin/env python3
"""Download the PDFs that ia_list.py listed, for the open tier.

    python3 harvest/ia_fetch.py --lists /data/lectern/links/ia --out /data/lectern/links [--sets ...]

Reads <lists>/<set>.jsonl and writes <out>/ia-<set>/files/<slug>.pdf, meta/<slug>.json and
manifest.jsonl in harvest/README.md's format. Takes only items published before 1931 that
archive.org doesn't mark restricted. Re-runs skip what is on disk. Stops when /data has less
than 120 GB free, and at a bot challenge.

A few downloads may be in flight at once, but no two requests start less than a second
apart. Rows add `jstor_url` (Early Journal Content: the stable URL JSTOR asks to be credited)
and `licence.rule_url`. Page images, text and ingest are left to build/.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
GAP = 1.05
WORKERS = 3
MIN_FREE = 120e9
ORDER = ["bibsac", "exptimes", "jts", "pefqs", "ptr", "ejc-1923-1930", "ejc", "chl"]

_last = [0.0]
_lock = threading.Lock()
stop = threading.Event()

# ---------------------------------------------------------------- titles

ISSUE_RUNS = {
    "bibsac": ("bibsac", "Bibliotheca Sacra"),
    "exptimes": ("exptimes", "The Expository Times"),
    "jts": ("jts", "The Journal of Theological Studies"),
    "pefqs": ("pefqs", "Palestine Exploration Fund Quarterly Statement"),
    "ptr": ("ptr", "The Princeton Theological Review"),
}
LATER = {  # ejc-1923-1930: by IA collection
    "pub_journal-of-biblical-literature": ("jbl", "Journal of Biblical Literature"),
    "pub_harvard-theological-review": ("htr", "Harvard Theological Review"),
    "pub_journal-of-religion": ("jr", "The Journal of Religion"),
}
EJC = {  # by journalabbrv
    "jbibllite": ("jbl", "Journal of Biblical Literature"),
    "jsocibiblliteexe": ("jsble", "Journal of the Society of Biblical Literature and Exegesis"),
    "oldteststud": ("ots", "The Old Testament Student"),
    "oldnewteststud": ("onts", "The Old and New Testament Student"),
    "biblicalworld": ("bw", "The Biblical World"),
    "amerjtheo": ("ajt", "The American Journal of Theology"),
    "hebraica": ("hebraica", "Hebraica"),
    "amerjsemilanglit": ("ajsl", "The American Journal of Semitic Languages and Literatures"),
    "harvtheorevi": ("htr", "Harvard Theological Review"),
    "jewiquarrevi": ("jqr", "The Jewish Quarterly Review"),
    "jreligion": ("jr", "The Journal of Religion"),
}
CHL_NS = {  # CHL periodicals by IA sub-collection; others get a ns from their identifier
    "millennialstar": "mstar", "juvenileinstructor": "juvinst", "improvementera": "era",
    "thecontributor": "contributor", "conferencereport": "confrep", "theinstructor": "instructor",
    "skandinaviensstjerne": "stjerne", "derstern": "derstern", "dester": "dester",
}

RULE_URL = "https://guides.library.cornell.edu/copyright/publicdomain"
JSTOR_TERMS = ("You are free to copy, use, and redistribute the Early Journal Content in part or "
               "in whole for non-commercial purposes. Please acknowledge JSTOR as the source of the "
               "Early Journal Content by either linking directly to the JSTOR site using the stable "
               "URL for the Content item or, if using the Early Journal Content offline, by stating "
               "“Courtesy of JSTOR.”")
CHL_LABEL = ("archive.org's Church History Library uploads carry the blanket label "
             "\"© Copyright by Intellectual Reserve, Inc. All rights reserved.\", on issues of "
             "every date. It does not apply here: the issue itself is in the public domain, and a "
             "faithful scan of a public-domain work carries no new copyright (Bridgeman Art Library "
             "v. Corel Corp., 36 F. Supp. 2d 191, S.D.N.Y. 1999).")


def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


MONTHS = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}


def year_of(r):
    if r.get("year"):
        return int(r["year"])
    m = re.match(r"(\d{4})", str(r.get("date") or ""))
    return int(m.group(1)) if m else None


def published(r):
    y = year_of(r)
    if r.get("year"):  # PTR: "v.10, no.1 (Jan. 1912)"
        m = re.search(r"\(([A-Za-z]{3})\w*\.? (\d{4})\)", r.get("volume") or "")
        mo = MONTHS.get(m.group(1).lower()) if m else None
        return f"{y}-{mo:02d}" if mo else str(y)
    d = str(r.get("date") or "")[:10]
    m = re.match(r"(\d{4})-(\d\d)-(\d\d)", d)
    if not m:
        return d[:4] or str(y)
    yy, mo, dd = m.groups()
    if mo == "00":
        return yy
    if (mo, dd) == ("01", "01") and f"{yy}-01" not in r["identifier"]:
        return yy  # IA's stand-in for a year-only date
    if dd == "00" or (dd == "01" and "churchhistorylibrary" not in r["collections"]):
        return f"{yy}-{mo}"  # monthly and quarterly issues: IA gives the 1st
    return f"{yy}-{mo}-{dd}"


def vol_issue(r):
    """(volume, issue) from IA's fields: '75 no. 32', 'v.10, no.1 (Jan. 1912)', '27' + '108'."""
    v, i = r.get("volume"), r.get("issue")
    m = re.match(r"\s*v?\.?\s*0*(\d+)\s*,?\s*no\.?\s*0*(\d+)", str(v or ""))
    if m:
        return m.group(1), m.group(2)
    v = str(v).lstrip("0") if v and str(v).strip("0").isdigit() else (v or None)
    return v, (str(i) if i else None)


def label_offset(r):
    m = re.match(r"(\d+)-(\d+)$", r.get("pagerange") or "")
    if not m or not r.get("pages"):
        return None
    first, last = int(m.group(1)), int(m.group(2))
    span = last - first + 1
    if r["pages"] == span + 1:  # JSTOR's cover page comes first
        return first - 2
    if r["pages"] == span:
        return first - 1
    return None


def describe(set_name, r, authors):
    """The README fields for one listed item, without the file ones; ns and a slug base."""
    y = year_of(r)
    vol, iss = vol_issue(r)
    ident = r["identifier"]
    rec = {"kind": "book", "title": r.get("title"), "authors": [], "published": published(r),
           "volume": vol, "issue": iss, "pages": None, "doi": None, "label_offset": None,
           "landing_url": f"https://archive.org/details/{ident}"}
    rule = (f"Published {y}. Works published before 1931 are in the public domain in the "
            f"United States: their copyright term (at most 95 years from publication) has ended.")
    lic = {"id": "public-domain", "evidence_url": rec["landing_url"], "quote": rule,
           "rule_url": RULE_URL}
    if set_name == "ejc":
        ns, coll = EJC[r["journalabbrv"]]
        rec.update(kind="article", authors=authors.get(ident, []), pages=r.get("pagerange"),
                   label_offset=label_offset(r), jstor_url=r.get("jstor_url"),
                   doi=("10.2307/" + ident.split("-", 1)[1]) if ident.startswith("jstor-") else None)
        lic["quote"] = (rule + " JSTOR's terms for the Early Journal Content "
                        "(https://about.jstor.org/terms/): \"" + JSTOR_TERMS + "\"")
        lic["terms_url"] = "https://about.jstor.org/terms/"
        base = ident
    elif set_name == "ejc-1923-1930":
        ns, coll = next(LATER[c] for c in r["collections"] if c in LATER)
        base = ident.split("_", 2)[-1] if ident.startswith("sim_") else ident.split("_", 1)[-1]
    elif set_name == "chl":
        sub = next((c for c in r["collections"] if c in CHL_NS), None)
        periodical = bool(re.match(r"\s*\d+\s*no\.", str(r.get("volume") or "")))
        if sub:
            ns = CHL_NS[sub]
        elif periodical:
            ns = slugify(re.match(r"[a-z]+", ident.lower()).group(0))[:12]
        else:
            ns = "chl"
        coll = r.get("title") if (sub or periodical) else "Church History Library"
        lic["quote"] = rule + " " + CHL_LABEL
        base = f"{vol}-{iss}" if (sub or periodical) and vol and iss else ident
    else:
        ns, coll = ISSUE_RUNS[set_name]
        # "sim_the-bibliotheca-sacra_1870-10_27_108" -> "1870-10_27_108"
        base = ident.split("_", 2)[-1] if ident.startswith("sim_") else (
            ident.split("_", 1)[1] if "_" in ident else (f"{vol}-{iss}" if vol and iss else ident))
    rec["collection"] = coll
    rec["licence"] = lic
    return ns, slugify(base), rec


# ---------------------------------------------------------------- HTTP

def slot():
    with _lock:
        wait = _last[0] + GAP - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()


def get_json(url):
    for attempt in range(5):
        slot()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}),
                                        timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:
            log(f"  {e} on {url}; retry {attempt + 1}")
            time.sleep(20 * (attempt + 1))
    raise RuntimeError(f"gave up on {url}")


def download(url, dest):
    """Stream url to dest. Returns (sha256, bytes) or None. Sets `stop` at a bot challenge."""
    tmp = dest.with_suffix(".part")
    for attempt in range(4):
        if stop.is_set():
            return None
        slot()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r, tmp.open("wb") as f:
                h, n, first = hashlib.sha256(), 0, b""
                while chunk := r.read(1 << 20):
                    if not first:
                        first = chunk[:5]
                    h.update(chunk)
                    f.write(chunk)
                    n += len(chunk)
            if first != b"%PDF-":
                log(f"  not a PDF: {url}")
                tmp.unlink(missing_ok=True)
                return None
            os.replace(tmp, dest)
            return h.hexdigest(), n
        except urllib.error.HTTPError as e:
            body = (e.read() or b"")[:20000].lower()
            if e.code in (403, 429, 503) and any(m in body for m in
                                                 (b"captcha", b"challenge", b"just a moment")):
                log(f"STOP: bot challenge ({e.code}) at {url}")
                stop.set()
                return None
            if e.code in (403, 404, 410):
                log(f"  {e.code} for {url}")
                return None
            log(f"  {e.code} for {url}; retry {attempt + 1}")
        except Exception as e:
            log(f"  {e} for {url}; retry {attempt + 1}")
        tmp.unlink(missing_ok=True)
        time.sleep(30 * (attempt + 1))
    return None


# ---------------------------------------------------------------- main

def ejc_authors():
    """identifier -> creators, one advancedsearch per journal (the list didn't keep them)."""
    out = {}
    for abbr in EJC:
        params = [("q", f"collection:jstor_ejc AND journalabbrv:{abbr}"), ("fl[]", "identifier"),
                  ("fl[]", "creator"), ("rows", "10000"), ("output", "json")]
        r = get_json("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params))
        for d in r["response"]["docs"]:
            c = d.get("creator") or []
            out[d["identifier"]] = c if isinstance(c, list) else [c]
    return out


def write_manifest(folder):
    rows = []
    for p in sorted((folder / "meta").glob("*.json")):
        rec = json.loads(p.read_text())
        if (folder / rec["file"]).exists():
            rows.append(rec)
    tmp = folder / "manifest.jsonl.tmp"
    with tmp.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, folder / "manifest.jsonl")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lists", type=Path, default=Path("/data/lectern/links/ia"))
    ap.add_argument("--out", type=Path, default=Path("/data/lectern/links"))
    ap.add_argument("--sets", default=",".join(ORDER))
    ap.add_argument("--limit", type=int, help="per set, for testing")
    args = ap.parse_args()
    sets = [s for s in args.sets.split(",") if s]
    authors = ejc_authors() if "ejc" in sets else {}
    pool = ThreadPoolExecutor(WORKERS)

    for s in sets:
        rows = [json.loads(l) for l in (args.lists / f"{s}.jsonl").open()]
        folder = args.out / f"ia-{s}"
        (folder / "files").mkdir(parents=True, exist_ok=True)
        (folder / "meta").mkdir(exist_ok=True)
        keep, used, dropped = [], set(), {"1931+": 0, "restricted": 0, "no pdf": 0}
        for r in rows:
            y = year_of(r)
            if not y or y > 1930:
                dropped["1931+"] += 1
            elif r.get("restricted"):
                dropped["restricted"] += 1
            elif not r.get("pdf"):
                dropped["no pdf"] += 1
            else:
                ns, slug, rec = describe(s, r, authors)
                if f"{ns}:{slug}" in used:  # two scans of one issue: fall back to the identifier
                    slug = slugify(r["identifier"])
                used.add(f"{ns}:{slug}")
                rec["id"] = f"{ns}:{slug}"
                keep.append((r, slug, rec))
        todo = [k for k in keep if not (folder / "meta" / f"{k[1]}.json").exists()
                or not (folder / "files" / f"{k[1]}.pdf").exists()]
        log(f"{s}: {len(keep)} to keep ({sum(k[0]['pdf']['size'] for k in keep) / 1e9:.1f} GB), "
            f"{len(keep) - len(todo)} on disk; dropped {dropped}")
        if args.limit:
            todo = todo[:args.limit]

        def job(item):
            r, slug, rec = item
            if stop.is_set():
                return 0
            if shutil.disk_usage(folder).free < MIN_FREE:
                log(f"STOP: less than {MIN_FREE / 1e9:.0f} GB free on {folder}")
                stop.set()
                return 0
            name = r["pdf"]["name"]
            url = (f"https://archive.org/download/{urllib.parse.quote(r['identifier'])}/"
                   f"{urllib.parse.quote(name)}")
            got = download(url, folder / "files" / f"{slug}.pdf")
            if not got:
                return 0
            sha, n = got
            if n != r["pdf"]["size"]:
                log(f"  {rec['id']}: {n} bytes, listed {r['pdf']['size']}")
            rec.update({"source_url": url, "file": f"files/{slug}.pdf",
                        "media_type": "application/pdf", "sha256": sha, "bytes": n,
                        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                        "ia_identifier": r["identifier"]})
            (folder / "meta" / f"{slug}.json").write_text(
                json.dumps(rec, ensure_ascii=False, indent=1))
            return n

        done = got_bytes = 0
        t0 = time.monotonic()
        for n in pool.map(job, todo):
            done += 1
            got_bytes += n
            if done % 200 == 0:
                write_manifest(folder)
                rate = done / (time.monotonic() - t0)
                log(f"  {s}: {done}/{len(todo)}, {got_bytes / 1e9:.1f} GB, "
                    f"{rate:.2f} items/s, ~{(len(todo) - done) / rate / 3600:.1f} h left in set")
        man = write_manifest(folder)
        log(f"{s}: manifest {len(man)} rows, {sum(m['bytes'] for m in man) / 1e9:.1f} GB")
        if stop.is_set():
            sys.exit(2)
    pool.shutdown()
    log("done")


if __name__ == "__main__":
    main()
