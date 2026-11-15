#!/usr/bin/env python3
"""Harvest the open-access journals in shelf/sources/open-journals.md.

    python3 harvest/open_journals.py <ns> --out /data/lectern/links/<ns> [--limit N]

<ns> is one of:

  jhs     Journal of Hebrew Scriptures. OJS OAI-PMH; licence per article from dc:rights.
  ote     Old Testament Essays, 2018 onward (vol. 31+). OJS OAI-PMH for the list; the
          licence and pages from each article page.
  hugoye  Hugoye: Journal of Syriac Studies. No OAI: /volumes.html -> /volume/N -> article.
  jjmjs   Journal of the Jesus Movement in its Jewish Setting. No OAI: the PDFs on
          /issues.html, with titles, authors and pages from jjmjs_articles.json.
  tynbul  Tyndale Bulletin, link only. The sitemap's article pages give the metadata,
          pages and licence; vol. 71 (2020) and earlier under the journal's own terms,
          vol. 72 (2021) onward CC BY-NC-ND 4.0.

Only items whose licence is CC BY or CC BY-SA are taken for the four open journals.
Each PDF goes to <out>/files/<slug>.pdf and its record to <out>/meta/<slug>.json;
manifest.jsonl is rewritten from meta/ at the end (and every 50 items). Re-runs skip
items already on disk. Standard library only.

Beyond harvest/README.md's fields, records carry `section` (the journal's own section:
Articles, Reviews...) and `licence.url` (the licence deed), and, when the licence is the
journal's stated policy rather than a statement on the item, `licence.scope: "journal"`.
"""

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

UA = "Lectern/0.1 (+https://lectern.restorationcommons.org/about)"
MIN_GAP = 1.5  # seconds between requests to one host
HERE = Path(__file__).resolve().parent


class BotChallenge(Exception):
    pass


def log(*a):
    print(dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- HTTP

_last = {}

CHALLENGE_MARKERS = (b"just a moment", b"cf-chl", b"challenge-platform", b"captcha",
                     b"attention required", b"are you a robot", b"ddos-guard",
                     b"sgcaptcha", b"checking your browser")


def looks_like_challenge(status, headers, body):
    if (headers.get("cf-mitigated") or "").lower() == "challenge":
        return True
    head = body[:30000].lower()
    if status in (202, 403, 429, 503):
        return any(m in head for m in CHALLENGE_MARKERS)
    if status == 200 and "html" in (headers.get("content-type") or ""):
        return b"<title>just a moment" in head or b"challenge-platform" in head
    return False


def get(url, tries=4):
    """GET with the Lectern UA and a per-host gap. Returns (status, headers, body, final_url).
    Raises BotChallenge on a challenge page. 404/410 come back as a status, not an error."""
    host = urllib.parse.urlsplit(url).netloc
    for attempt in range(tries):
        wait = _last.get(host, 0) + MIN_GAP - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
                status, headers, final = r.status, {k.lower(): v for k, v in r.headers.items()}, r.url
        except urllib.error.HTTPError as e:
            body = e.read() or b""
            status, headers, final = e.code, {k.lower(): v for k, v in e.headers.items()}, url
        except Exception as e:  # network trouble: back off and retry
            _last[host] = time.monotonic()
            log(f"  retry {attempt + 1}: {url}: {e}")
            time.sleep(10 * (attempt + 1))
            continue
        finally:
            _last[host] = time.monotonic()
        if looks_like_challenge(status, headers, body):
            raise BotChallenge(f"{status} at {url}")
        if status == 429 or status >= 500:
            log(f"  {status} on {url}; waiting")
            time.sleep(60 * (attempt + 1))
            continue
        return status, headers, body, final
    raise RuntimeError(f"gave up on {url}")


def get_text(url):
    status, headers, body, final = get(url)
    if status != 200:
        raise RuntimeError(f"{status} for {url}")
    return body.decode("utf-8", "replace")


# ---------------------------------------------------------------- helpers

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def person(name):
    """'Guillaume, Philippe' -> 'Philippe Guillaume'."""
    name = clean(name)
    if name.count(",") == 1:
        family, given = [p.strip() for p in name.split(",")]
        if given and family:
            return f"{given} {family}"
    return name


def metas(page):
    """citation_* and DC.* meta tags -> {name: [values]}."""
    out = {}
    for m in re.finditer(r"<meta\s+([^>]*)>", page, re.I):
        attrs = dict(re.findall(r'([\w:.-]+)\s*=\s*"([^"]*)"', m.group(1)))
        if "name" in attrs and "content" in attrs:
            out.setdefault(attrs["name"], []).append(html.unescape(attrs["content"]))
    return out


def cc_id(url):
    """https://creativecommons.org/licenses/by/2.5/ -> CC-BY-2.5. None if not a CC licence."""
    m = re.search(r"creativecommons\.org/licenses/([a-z-]+)/(\d\.\d)", url or "")
    if not m:
        return None
    return "CC-" + m.group(1).upper() + "-" + m.group(2)


OPEN_IDS = re.compile(r"^CC-BY(-SA)?-\d\.\d$")


def pages_str(first, last):
    first, last = (first or "").strip(), (last or "").strip()
    if first and last and first != last:
        return f"{first}-{last}"
    return first or None


def offset_from(first):
    """PDF page 1 is the printed first page."""
    return int(first) - 1 if first and str(first).isdigit() else None


# ---------------------------------------------------------------- OAI-PMH

OAI = "{http://www.openarchives.org/OAI/2.0/}"
DC = "{http://purl.org/dc/elements/1.1/}"


def oai_records(base):
    url = f"{base}?verb=ListRecords&metadataPrefix=oai_dc"
    while url:
        root = ET.fromstring(get_text(url))
        lr = root.find(f"{OAI}ListRecords")
        if lr is None:
            err = root.find(f"{OAI}error")
            raise RuntimeError(f"OAI error: {err.text if err is not None else '?'}")
        for rec in lr.findall(f"{OAI}record"):
            head = rec.find(f"{OAI}header")
            if head.get("status") == "deleted":
                continue
            dc = {}
            for el in rec.iter():
                if el.tag.startswith(DC):
                    dc.setdefault(el.tag[len(DC):], []).append((el.text or "").strip())
            yield head.findtext(f"{OAI}identifier"), head.findtext(f"{OAI}setSpec"), dc
        tok = lr.find(f"{OAI}resumptionToken")
        url = (f"{base}?verb=ListRecords&resumptionToken={urllib.parse.quote(tok.text.strip())}"
               if tok is not None and tok.text else None)


def oai_sets(base):
    root = ET.fromstring(get_text(f"{base}?verb=ListSets"))
    return {s.findtext(f"{OAI}setSpec"): s.findtext(f"{OAI}setName")
            for s in root.iter(f"{OAI}set")}


# ---------------------------------------------------------------- sources
# Each source yields records (README fields, minus the file ones) with a private
# "_pdf" key: the list of URLs to try for the PDF.

JHS_BASE = "https://jhsonline.org/index.php/jhs"
JHS_POLICY_URL = f"{JHS_BASE}/about/submissions"
JHS_POLICY = ("All authors published in JHS retain copyright and grant the journal right of "
              "first publication with the work simultaneously licensed under a Creative Commons "
              "Attribution 4.0 International (CC BY 4.0) License that allows others to share the "
              "work, including for commercial purposes, with an acknowledgement of the work's "
              "authorship and initial publication in this journal. ... (Please note: articles "
              "published before 2021 are licensed under a CC BY 2.5 License.)")


def src_jhs(out, done):
    sets = oai_sets(f"{JHS_BASE}/oai")
    for ident, setspec, dc in oai_records(f"{JHS_BASE}/oai"):
        art = ident.rsplit("/", 1)[-1]
        landing = next((i for i in dc.get("identifier", []) if "/article/view/" in i), None)
        doi = next((i for i in dc.get("identifier", []) if i.startswith("10.")), None)
        src = (dc.get("source") or [""])[0]
        m = re.search(r"Vol\. (\d+)(?: No\. (\d+))? \((\d{4})\)", src)
        deed = next((r for r in dc.get("rights", []) if "creativecommons.org" in r), None)
        statement = f"OAI dc:rights: {deed}"
        if not deed and m:
            # Some records carry only "Copyright (c) <year> Author(s)"; the journal's
            # notice licenses every article: CC BY 2.5 before 2021, CC BY 4.0 since.
            deed = ("https://creativecommons.org/licenses/by/2.5/" if int(m.group(3)) < 2021
                    else "https://creativecommons.org/licenses/by/4.0/")
            statement = f"OAI dc:rights: {'; '.join(dc.get('rights', []))} (no licence link)"
        lic = cc_id(deed)
        if not lic or not OPEN_IDS.match(lic):
            log(f"  skip jhs {art}: rights {dc.get('rights')}")
            continue
        galleys = [r for r in dc.get("relation", []) if "/article/view/" in r]
        yield {
            "id": f"jhs:{art}",
            "kind": "article",
            "title": clean((dc.get("title") or [""])[0]),
            "authors": [person(a) for a in dc.get("creator", [])],
            "published": m.group(3) if m else (dc.get("date") or [""])[0][:4],
            "collection": "Journal of Hebrew Scriptures",
            "volume": m.group(1) if m else None,
            "issue": m.group(2) if m else None,
            "pages": None,
            "doi": doi,
            "label_offset": 0,  # each article's PDF is paginated from 1
            "landing_url": landing,
            "section": sets.get(setspec, setspec),
            "licence": {"id": lic, "url": deed, "scope": "journal",
                        "evidence_url": JHS_POLICY_URL, "quote": JHS_POLICY,
                        "item_statement": statement},
            "_pdf": [g.replace("/article/view/", "/article/download/") for g in galleys],
        }


OTE_BASE = "https://ote-journal.otwsa-otssa.org.za/index.php/journal"


def src_ote(out, done):
    sets = oai_sets(f"{OTE_BASE}/oai")
    for ident, setspec, dc in oai_records(f"{OTE_BASE}/oai"):
        art = ident.rsplit("/", 1)[-1]
        src = (dc.get("source") or [""])[0]
        m = re.search(r"Vol\. (\d+)(?: No\. ([\w-]+))? \((\d{4})\)", src)
        if not m or int(m.group(3)) < 2018:
            continue
        if f"ote:{art}" in done:
            continue
        landing = f"{OTE_BASE}/article/view/{art}"
        page = get_text(landing)
        meta = metas(page)
        # The copyright notice on each article page grants the licence; the footer names one too.
        grant = re.search(r"Authors retain copyright[^<]*<a href=\"([^\"]+)\"[^>]*>([^<]+)</a>([^<]*)",
                          page)
        footer = re.search(r"This work is licensed under a\s*<a href=\"([^\"]+)\"[^>]*>([^<]+)</a>",
                           page)
        # Some pages lack the copyright notice; then the footer's statement is the licence.
        stmt = grant or footer
        lic = cc_id(stmt.group(1)) if stmt else None
        if not lic or not OPEN_IDS.match(lic):
            log(f"  skip ote {art}: no CC BY statement on the article page")
            continue
        quote = clean(page[grant.start():grant.end()]) + " " if grant else ""
        if footer:
            quote += f'Page footer: "This work is licensed under a {clean(footer.group(2))}."'
        first = (meta.get("citation_firstpage") or [None])[0]
        last = (meta.get("citation_lastpage") or [None])[0]
        pdf = (meta.get("citation_pdf_url") or [])
        yield {
            "id": f"ote:{art}",
            "kind": "article",
            "title": clean((meta.get("citation_title") or dc.get("title") or [""])[0]),
            "authors": meta.get("citation_author") or [person(a) for a in dc.get("creator", [])],
            "published": ((meta.get("citation_date") or [""])[0].replace("/", "-")
                          or m.group(3)),
            "collection": "Old Testament Essays",
            "volume": m.group(1),
            "issue": m.group(2),
            "pages": pages_str(first, last),
            "doi": (meta.get("citation_doi") or [None])[0],
            "label_offset": offset_from(first),
            "landing_url": landing,
            "section": sets.get(setspec, setspec),
            "licence": {"id": lic, "url": stmt.group(1), "evidence_url": landing,
                        "quote": quote},
            "_pdf": pdf + [r.replace("/article/view/", "/article/download/")
                           for r in dc.get("relation", []) if "/article/view/" in r],
        }


HUGOYE = "https://hugoye.bethmardutho.org"
HUGOYE_POLICY = ("All articles for Hugoye, including the html and xml data, are copyright to "
                 "Beth Mardutho: The Syriac Institute and licensed under the Creative Commons "
                 "Attribution 4.0 International Public License. This means that anyone is free "
                 "to share and adapt material from these articles, as long as the reuse includes "
                 "attribution to the original publication.")


def hugoye_variants(pdfs, vol):
    """Some article pages link a lowercased or misfiled PDF name (hv13n2prkeough.pdf for
    HV13N2PRKeough.pdf, vol1/ for vol2/). Guesses to try after the linked ones fail."""
    out = []
    for url in pdfs:
        name = url.rsplit("/", 1)[-1][:-4]
        names = [name]
        m = re.match(r"(?i)(hv\d+n\d+)(pr|cr|fc|ad|ob|bib)?(.+)$", name)
        if m and name == name.lower():
            names.append(m.group(1).upper() + (m.group(2) or "").upper() + m.group(3)[:1].upper()
                         + m.group(3)[1:])
        for d in dict.fromkeys([f"vol{vol}", url.rsplit("/", 2)[-2]]):
            for n in names:
                out.append(f"{HUGOYE}/pdf/{d}/{n}.pdf")
    return [u for u in dict.fromkeys(out) if u not in pdfs]


def src_hugoye(out, done):
    vols = sorted({int(v) for v in re.findall(r'href="/volume/(\d+)"',
                                              get_text(f"{HUGOYE}/volumes.html"))})
    for vol in vols:
        page = get_text(f"{HUGOYE}/volume/{vol}")
        for m in re.finditer(r'<div[^>]*class="indent"[^>]*date="([^"]*)"[^>]*type="([^"]*)"'
                             r'[^>]*issue="([^"]*)"[^>]*>(.*?)</div>\s*</div>', page, re.S):
            date, section, issue, block = m.groups()
            a = re.search(r'<a href="/article/([^"]+)\.html">(.*?)</a>', block, re.S)
            if not a:
                continue
            slug = a.group(1)
            if f"hugoye:{slugify(slug)}" in done:
                continue
            by = block.split("By", 1)[1] if "By" in block[a.end():] else ""
            by = clean(re.sub(r"<a [^>]*>.*?</a>", "", by, flags=re.S))
            authors = [x.strip() for x in re.split(r",\s*and\s+|\s+and\s+|,\s*", by) if x.strip()]
            landing = f"{HUGOYE}/article/{slug}.html"
            art = get_text(landing)
            pdfs = re.findall(r'href="([^"]+\.pdf)"', art, re.I)
            pdfs = list(dict.fromkeys(urllib.parse.urljoin(landing, p) for p in pdfs))
            pdfs += hugoye_variants(pdfs, vol)
            yield {
                "id": f"hugoye:{slugify(slug)}",
                "kind": "article",
                "title": clean(a.group(2)),
                "authors": authors,
                "published": (re.search(r"\d{4}", date) or [None])[0],
                "collection": "Hugoye: Journal of Syriac Studies",
                "volume": str(vol),
                "issue": issue or None,
                "pages": None,
                "doi": None,
                "label_offset": None,
                "landing_url": landing,
                "section": section or None,
                "licence": {"id": "CC-BY-4.0", "url": "https://creativecommons.org/licenses/by/4.0/",
                            "scope": "journal", "evidence_url": f"{HUGOYE}/open-access.html",
                            "quote": HUGOYE_POLICY},
                "_pdf": pdfs,
            }


JJMJS = "https://www.jjmjs.org"
JJMJS_POLICY = "This work is licensed under a Creative Commons Attribution 4.0 International License."


def src_jjmjs(out, done):
    table = {r["file"]: r for r in json.loads((HERE / "jjmjs_articles.json").read_text())}
    page = get_text(f"{JJMJS}/issues.html")
    seen = set()
    for href in re.findall(r'href="(/uploads/[^"]+\.pdf)"', page):
        href = html.unescape(href)
        name = urllib.parse.unquote(href.rsplit("/", 1)[-1])
        if name in seen:
            continue
        seen.add(name)
        r = table.get(name)
        if not r:
            log(f"  jjmjs: {name} is not in jjmjs_articles.json; add it")
            continue
        rid = f"jjmjs:{r['issue']}-{slugify(name[:-4])}"
        if rid in done:
            continue
        url = JJMJS + urllib.parse.quote(href)
        yield {
            "id": rid,
            "kind": "article",
            "title": r["title"],
            "authors": r["authors"],
            "published": r["year"],
            "collection": "Journal of the Jesus Movement in its Jewish Setting",
            "volume": None,
            "issue": r["issue"],
            "pages": r.get("pages"),
            "doi": None,
            "label_offset": r.get("label_offset"),
            "landing_url": f"{JJMJS}/issues.html",
            "section": r.get("section"),
            "licence": {"id": "CC-BY-4.0", "url": "http://creativecommons.org/licenses/by/4.0/",
                        "scope": "journal", "evidence_url": f"{JJMJS}/", "quote": JJMJS_POLICY},
            "_pdf": [url],
        }


TB = "https://www.tyndalebulletin.org"
TB_TERMS_OLD = ("Articles from volume 71 (2020) and earlier: For commercial reuse, or "
                "distribution of derivative works, of articles from volume 71 and earlier, please "
                "contact the Editor at bulletin@tyndalehouse.com. For non-commercial purposes "
                "users may read, download, copy, distribute, print, search, or link to the full "
                "texts of articles, crawl them for indexing, pass them as data to software, or use "
                "them for any other lawful purpose, providing appropriate credit is given.")
TB_TERMS_NEW = ("Articles from volume 72 (2021) onwards: From volume 72 onwards, articles are "
                "released under a Creative Commons CC BY-NC-ND license. For commercial reuse of "
                "material from these articles, or the distribution of derivative works, please "
                "contact the Editor at bulletin@tyndalehouse.com.")


def src_tynbul(out, done):
    sm = get_text(f"{TB}/sitemap")
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", sm) if "/article/" in u]
    log(f"  sitemap: {len(urls)} articles")
    for landing in urls:
        num = re.search(r"/article/(\d+)", landing).group(1)
        if f"tynbul:{num}" in done:
            continue
        page = get_text(landing)
        meta = metas(page)
        vol = (meta.get("citation_volume") or [None])[0]
        fp = re.search(r'"first_page":"(\d+)","last_page":"(\d+)"', page)
        first, last = (fp.group(1), fp.group(2)) if fp else (None, None)
        cr = (meta.get("citation_copyright") or [""])[0]
        if cr == "ccby-nc-nd-4.0" or (vol and vol.isdigit() and int(vol) >= 72):
            lic = {"id": "CC-BY-NC-ND-4.0", "url": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
                   "evidence_url": landing, "quote": TB_TERMS_NEW,
                   "item_statement": f'citation_copyright "{cr}"'}
        else:
            lic = {"id": "all-rights-reserved", "url": None, "evidence_url": f"{TB}/about",
                   "quote": TB_TERMS_OLD, "scope": "journal",
                   "item_statement": f'citation_copyright "{cr}"'}
        pub = (meta.get("citation_publication_date") or [""])[0]
        try:
            pub = dt.date(*map(int, pub.split("/"))).isoformat()
        except Exception:
            pub = pub[:4] or None
        yield {
            "id": f"tynbul:{num}",
            "kind": "article",
            "title": clean((meta.get("citation_title") or [""])[0]),
            "authors": meta.get("citation_author") or [],
            "published": pub,
            "collection": "Tyndale Bulletin",
            "volume": vol,
            "issue": (meta.get("citation_issue") or [None])[0],
            "pages": pages_str(first, last),
            "doi": (meta.get("citation_doi") or [None])[0],
            "label_offset": offset_from(first),
            "landing_url": landing,
            "section": None,
            "licence": lic,
            "_pdf": meta.get("citation_pdf_url") or [f"{TB}/article/{num}.pdf"],
        }


SOURCES = {"jhs": src_jhs, "ote": src_ote, "hugoye": src_hugoye, "jjmjs": src_jjmjs,
           "tynbul": src_tynbul}


# ---------------------------------------------------------------- main

def write_manifest(out):
    rows = []
    for p in sorted((out / "meta").glob("*.json")):
        rec = json.loads(p.read_text())
        if (out / rec["file"]).exists():
            rows.append(rec)
    tmp = out / "manifest.jsonl.tmp"
    with tmp.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, out / "manifest.jsonl")
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ns", choices=sorted(SOURCES))
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--limit", type=int, help="stop after this many new items (for testing)")
    args = ap.parse_args()
    out = args.out
    (out / "files").mkdir(parents=True, exist_ok=True)
    (out / "meta").mkdir(parents=True, exist_ok=True)

    done = set()
    for p in (out / "meta").glob("*.json"):
        rec = json.loads(p.read_text())
        if (out / rec["file"]).exists():
            done.add(rec["id"])
    log(f"{args.ns}: {len(done)} already on disk")

    src = SOURCES[args.ns]
    gen = src(out, done)
    new = skipped = 0
    try:
        for rec in gen:
            if rec["id"] in done:
                continue
            slug = rec["id"].split(":", 1)[1]
            body = final = None
            for url in rec.pop("_pdf"):
                status, headers, b, f = get(url)
                if status == 200 and b[:5] == b"%PDF-":
                    body, final = b, url
                    break
                log(f"  {rec['id']}: {url} gave {status} {headers.get('content-type')}")
            if body is None:
                log(f"  skip {rec['id']}: no PDF")
                skipped += 1
                continue
            rel = f"files/{slug}.pdf"
            (out / rel).write_bytes(body)
            rec.update({
                "source_url": final,
                "file": rel,
                "media_type": "application/pdf",
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            })
            (out / "meta" / f"{slug}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
            done.add(rec["id"])
            new += 1
            log(f"  {rec['id']}  {rec['published']}  {rec['title'][:70]}  ({len(body) // 1024} KB)")
            if new % 50 == 0:
                write_manifest(out)
            if args.limit and new >= args.limit:
                break
    except BotChallenge as e:
        log(f"STOP: bot challenge: {e}")
        n = write_manifest(out)
        log(f"manifest: {n} rows")
        sys.exit(2)
    n = write_manifest(out)
    log(f"done: {new} new, {skipped} without a PDF, manifest {n} rows")


if __name__ == "__main__":
    main()
