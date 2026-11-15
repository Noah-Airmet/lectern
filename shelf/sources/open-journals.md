# Open journals for Lectern: research notes

Checked 2026-11-15. Everything marked **verified** was fetched today with curl (generic browser user agent), the Crossref, DOAJ or Internet Archive APIs, or the homelab crawl4ai service for pages that block scripts. Anything not verified says so. Nothing was bulk-downloaded: at most one or two sample PDFs per source.

Tiers as defined in the brief:
- **open**: CC BY, CC BY-SA, CC0 or public domain. Host in full with page images.
- **link only**: free to read, any other terms. Private full text for the index and quote checks; the public gets snippets and a link to the publisher's page.

A note on public domain: anything published before 1931 is public domain in the US (the 1930 cohort entered on 1 Jan 2026). For British journals (Expository Times, JTS, PEFQS, the Expositor) that is PD-US only, not necessarily worldwide. Lectern's early Loebs are in the same position, so the same policy applies.

---

## Ranked short list

| # | Source | Tier | Size (approx.) | Harvest route | Call |
|---|---|---|---|---|---|
| 1 | JSTOR Early Journal Content on the Internet Archive: JBL, Biblical World, AJT, HTR, Hebraica/AJSL, JQR, Old (& New) Testament Student, Journal of Religion | open (PD) | ~16,000 article items, 1881–1922 | IA advancedsearch + per-item files | **include now, priority 1** |
| 2 | Pre-1931 issue scans on IA: Bibliotheca Sacra, Expository Times, JTS, PEFQS, Princeton Theological Review, Presbyterian & Reformed Review, plus JBL/HTR/J. Religion 1923–30 | open (PD-US) | ~1,500 issues | IA `pub_*` collections | **include now, priority 2** (needs article segmentation) |
| 3 | Journal of Hebrew Scriptures | open (CC BY) | 1,176 records, 1996– | OJS OAI-PMH | **include now, priority 1** |
| 4 | Hugoye: Journal of Syriac Studies | open (CC BY 4.0) | 681 items, 1998–2025 | static site; PDF + TEI XML per article | **include now, priority 1** |
| 5 | Tyndale Bulletin | link only | 913 DOIs, 1956– | Crossref (PDF links) + sitemap | **include now, priority 1** |
| 6 | JJMJS (becoming *Intersections*) | open (CC BY 4.0) | 78 PDFs, 2014–2024 | issues page | **include now, priority 2** |
| 7 | Old Testament Essays | open (CC BY) | 394 records, 2018– | OJS OAI-PMH | **include now, priority 2** |
| 8 | Religion in the Roman Empire (Mohr Siebeck) | open (CC BY-SA 4.0), only items so labelled | ~50 open items, 2023– | Crossref | **include now, small, priority 3** |
| 9 | HTS Teologiese Studies (and AOSIS siblings Verbum et Ecclesia, In die Skriflig) | open (CC BY), modern items only | HTS 6,219 / VE 2,156 / IdS 2,626 records | OJS OAI-PMH + Crossref | **include selectively, priority 3** |
| 10 | Journal of Religion & Society (Creighton) | open (CC BY 4.0) | ~460 articles, 1999– | DSpace OAI (metadata); PDFs block scripts | **later** |
| 11 | Open Theology (De Gruyter) | open (CC BY 4.0) | 511 DOIs, 2015– | Crossref; site has a bot challenge | **later, selective** |
| 12 | Themelios | link only | 153 issues, 1975– | HTML article pages; crawl-delay 600 | **later** |
| 13 | Andrews University Seminary Studies | link only | 2,866 records, 1963– | Digital Commons OAI | **later** |
| 14 | Religions (MDPI) | open (CC BY) | 10,937 DOIs; ~1,500/yr | Crossref + mdpi-res.com PDFs | **later, strictly selective** |
| 15 | TC: A Journal of Biblical Textual Criticism | link only | ~30 vols, 1996– | Crossref, after its platform move | **later** |

LDS journals (BYU Studies, JBMS, Religious Educator, Interpreter) are noted in their own section below. They fit Lectern well but are link only, and they may be covered by another workstream.

---

## Public-domain back runs (open tier)

### 1. JSTOR Early Journal Content (EJC) on the Internet Archive — include now, priority 1

- **What:** JSTOR's free pre-copyright journal content. In 2013 JSTOR uploaded a copy to the Internet Archive: collection `jstor_ejc`, **452,031 items** (verified). That copy covers works published before 1923 in the US and before 1870 elsewhere. Each item is **one article**.
- **Relevant journals in the IA copy** (verified counts, `journalabbrv` field):

  | Journal | Items | Years |
  |---|---|---|
  | Journal of the Society of Biblical Literature and Exegesis (`jsocibiblliteexe`) | 164 | 1881–1888 |
  | Journal of Biblical Literature (`jbibllite`) | 699 | 1890–1922 |
  | The Old Testament Student (`oldteststud`) | 931 | 1883–1889 |
  | The Old and New Testament Student (`oldnewteststud`) | 943 | 1889–1892 |
  | The Biblical World (`biblicalworld`) | 5,546 | 1893–1920 |
  | The American Journal of Theology (`amerjtheo`) | 3,683 | 1897–1920 |
  | Hebraica (`hebraica`) | 468 | 1884–1895 |
  | American Journal of Semitic Languages and Literatures (`amerjsemilanglit`) | 996 | 1895–1922 |
  | Harvard Theological Review (`harvtheorevi`) | 821 | 1908–1922 |
  | Jewish Quarterly Review (`jewiquarrevi`) | 1,609 | 1888–1922 |
  | Journal of Religion (`jreligion`) | 195 | 1921–1922 |

  Also present: JAOS (1,154), The Monist (2,192), Philosophical Review (3,735), International Journal of Ethics (2,438), Classical Journal / Classical Philology. These are useful for Christian origins and philosophy of religion, but select from them; don't take them wholesale.
  Biblical World and AJT counts include many short notes and book notices, so filter by `article-type` and page count.
- **Licence / terms:** the content is public domain. JSTOR's terms (https://about.jstor.org/terms/, verified) say: *"You are free to copy, use, and redistribute the Early Journal Content in part or in whole for non-commercial purposes. Please acknowledge JSTOR as the source of the Early Journal Content by either linking directly to the JSTOR site using the stable URL for the Content item or, if using the Early Journal Content offline, by stating 'Courtesy of JSTOR.'"* JSTOR's EJC definition is now rolling: *"journal content published prior to the last ninety-five years in the United States or prior to the last one hundred forty-three years if initially published internationally"* (US pre-1931 in 2026). The IA copy stops at 1922.
- **Format (verified):** sample item `jstor-3259399` (JBL 40, 1921, pp. 23–37, "Über das erste Kapitel des Buches Jeremia"): https://archive.org/details/jstor-3259399. Files: text PDF, `_jp2.zip` page images (600 ppi), ABBYY XML, DjVu text and XML, and the JSTOR article XML. Metadata includes `pagerange`, `volume`, `date`, `issn`, `creator` and the JSTOR stable URL (`http://www.jstor.org/stable/10.2307/3259399`). That gives page images with print pagination and a stable canonical link: an ideal fit for the open tier.
- **Harvest:** `https://archive.org/advancedsearch.php?q=collection:jstor_ejc AND journalabbrv:jbibllite&fl[]=identifier...&output=json`, then `https://archive.org/metadata/<id>` and `https://archive.org/download/<id>/<file>`. Rough size for the core list: ~16,000 items, a few GB of PDFs (the full JP2s are much larger; take the PDF and derive images).
- **For 1923–1930:** JSTOR itself now serves these free, but bulk text access goes through JSTOR Text Analysis Support (an application, not done here; Constellate was retired 1 July 2025 per search results). Easier: use the IA issue scans in §2 below.
- **Recommendation:** include now, open tier, priority 1. Credit "Courtesy of JSTOR" and keep the stable URL in each record.

### 2. Pre-1931 issue scans on the Internet Archive (Serials in Microfilm and Google scans) — include now, priority 2

These are **whole-issue** scans, not per-article. Each issue goes in as a volume, the way the books do, with article records layered on top. Article boundaries can come from the scan's table of contents or, for JSTOR-indexed titles, from Crossref `10.2307/*` metadata with page ranges.

Pre-1931 issue counts (verified with `year:[1800 TO 1930]`). Every sample checked had no `access-restricted-item` flag and a downloadable PDF (HEAD 200):

| Run | IA collection | Pre-1931 items | Sample checked |
|---|---|---|---|
| Bibliotheca Sacra | `pub_the-bibliotheca-sacra` | 518 | `sim_the-bibliotheca-sacra_1885-01_42_165` (199 pp.) |
| Expository Times | `pub_expository-times` | 322 (1889–1930) | `expository-times_1910-04_21_7`; note `expositorytimes0055jame` (1944) **is restricted** |
| Journal of Theological Studies | `pub_journal-of-theological-studies` | 156 (1899–1930) | `sim_journal-of-theological-studies_1929-07_30_120` |
| PEF Quarterly Statement / PEQ | `pub_palestine-exploration-quarterly` + Field Museum / Biodiversity scans (`palestineexplor00palef`, "No known copyright restrictions") | 151 + ~50 | 1869 onward |
| Princeton Theological Review | Princeton Seminary scans (`americana`/`Princeton`), e.g. `princetontheolo11semigoog` (`NOT_IN_COPYRIGHT`) | ~122 (1903–1929) | yes |
| Presbyterian and Reformed Review | `pub_presbyterian-and-reformed-review` | 73 (1890–1902) | not sampled |
| JBL 1923–1930 | `pub_journal-of-biblical-literature` | 23 issues | `sim_journal-of-biblical-literature_1930_49_2` (PDF 200) |
| HTR 1923–1930 | `pub_harvard-theological-review` | 40 issues | `harvard-theological-review_1930-04_23_2` (PDF 200) |
| Journal of Religion 1923–1930 | `pub_journal-of-religion` | 49 issues | `sim_journal-of-religion_1930-01_10_1` (PDF 200) |
| Jewish Quarterly Review (old series reprint + 1910–) | `pub_jewish-quarterly-review` | 101 | `jewishquarterlyr10drop` |
| The Expositor (British, ed. Nicoll, 1875–1925) | Google scans, e.g. `expositor603coxs`, `expositor44unkngoog` | ~199 hits (needs dedup) | not sampled |
| Biblical Review (1916–) | `pub_biblical-review-1916` | 73 | not sampled |

- **Caveats:**
  - `pub_expositor-and-homiletic-review` is an American homiletics magazine, **not** the British *Expositor*. Skip it.
  - IA offers some post-1930 issues too (a JBL 1950 issue was not flagged as restricted). That does not make them public domain. Stay at ≤1930.
  - HathiTrust holds most of these runs as well, but its Acceptable Use Policy forbids automated bulk download outside its approved research datasets, which need an application. Its site also served Cloudflare challenges to curl and crawl4ai. Use HathiTrust only to hand-fill gaps.
- **Recommendation:** include now, open tier. Start with JBL/HTR/JR 1923–30 and JTS, Expository Times and Princeton Theological Review. They continue the EJC runs and carry the most citations. Bibliotheca Sacra and PEFQS come next.

---

## Open-access journals

### 3. Journal of Hebrew Scriptures (JHebS) — include now, open, priority 1
- **What:** peer-reviewed (double-anonymous) Hebrew Bible journal, founded 1996, hosted by the University of Alberta Library. Editors: Angelini (Siena), Nihan (Münster), Wilson (Alberta). Indexed in ATLA, RAMBI and BiBIL. No APC. Strong reputation.
- **Licence (verified):** https://jhsonline.org/index.php/jhs/about/submissions: *"All authors published in JHS retain copyright and grant the journal right of first publication with the work simultaneously licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) License … (Please note: articles published before 2021 are licensed under a CC BY 2.5 License.)"* OAI `dc:rights` per record (e.g. `https://creativecommons.org/licenses/by/2.5/`). robots.txt only blocks `/cache/`.
- **Format:** one PDF per article, paginated from 1 within each article (cite as "JHebS 7, art. 16, p. 4"). DOIs are `10.5508/jhs.<year>.v<vol>.a<n>`. Example: https://jhsonline.org/index.php/jhs/article/view/5642 → PDF https://jhsonline.org/index.php/jhs/article/download/5642/4695 (Guillaume, "A Reconsideration of Manuscripts Classified as Scrolls of the Twelve", 8 pp.; downloaded and checked).
- **Harvest:** OJS OAI-PMH https://jhsonline.org/index.php/jhs/oai?verb=Identify (verified; `completeListSize=1176`). Get the PDF from `citation_pdf_url`.

### 4. Hugoye: Journal of Syriac Studies — include now, open, priority 1
- **What:** Beth Mardutho's peer-reviewed journal of Syriac studies, since 1998, printed by Gorgias Press. The standard venue in its field and highly relevant to early Christianity. 28 volumes (latest 2025); **681 items** on the volume pages, including reviews and bibliographies.
- **Licence (verified):** https://hugoye.bethmardutho.org/open-access.html: *"All articles for Hugoye, including the html and xml data, are copyright to Beth Mardutho: The Syriac Institute and licensed under the Creative Commons Attribution 4.0 International Public License."* (The PDF footer also reads "© 2016 by Beth Mardutho … and Gorgias Press"; the CC BY statement governs.) robots.txt returned AccessDenied (S3), so no rules are published.
- **Format:** HTML, TEI XML and PDF per article, with **print pagination** (sample "Vol. 20.1, 129–229"). Example: https://hugoye.bethmardutho.org/article/hv20n1minov.html, PDF https://hugoye.bethmardutho.org/pdf/vol20/HV20N1Minov.pdf (Minov, "Date and Provenance of the Syriac Cave of Treasures", downloaded).
- **Harvest:** no OAI. Crawl `/volumes.html` → `/volume/N` → `/article/*.html`, which link the PDF and XML. The TEI XML is a bonus for clean text.

### 5. Tyndale Bulletin — include now, link only, priority 1
- **What:** Tyndale House, Cambridge. Peer-reviewed biblical studies and theology since 1956, evangelical but academically strong. Indexed in ATLA, DOAJ and ERIH Plus. **913 Crossref DOIs** (`10.53751/001c.*`) spread across 1956–2026. Runs on the Scholastica platform.
- **Licence (verified), on https://www.tyndalebulletin.org/about and article pages:**
  - Vol. 72 (2021) onward: *"released under a Creative Commons CC BY-NC-ND license"* → link only.
  - Vol. 71 (2020) and earlier: *"For commercial reuse, or distribution of derivative works … please contact the Editor. For non-commercial purposes users may read, download, copy, distribute, print, search, or link to the full texts of articles, **crawl them for indexing, pass them as data to software**, or use them for any other lawful purpose, providing appropriate credit is given."* That expressly covers Lectern's private index use.
  - robots.txt only disallows metadata exports (`*.json`, `*.ris` etc.). Sitemap: https://www.tyndalebulletin.org/sitemap.
- **Format:** per-article PDF. Old ones are retyped or OCR'd and carry the **print page numbers**: sample https://www.tyndalebulletin.org/article/30577.pdf (Harris, "The Translation of Elohim in Psalm 45:7–8", TynBul 35, 1984, pp. 65ff., page numbers 66, 67… in the text layer). Recent: https://www.tyndalebulletin.org/article/169615-the-astronomical-language-of-james-1-17-revisited (vol. 77).
- **Harvest:** Crossref `journals/0082-7118/works` gives a PDF link for every DOI.
- **Recommendation:** include now as link only. Strictly the pre-2021 terms would let us redistribute non-commercially, but that isn't CC BY, so it stays link only under our rules.

### 6. JJMJS: Journal of the Jesus Movement in its Jewish Setting — include now, open, priority 2
- **What:** peer-reviewed, edited by Anders Runesson (Oslo). The best open venue for the "Paul within Judaism" and Jesus-movement-in-Judaism work, with high-quality contributors (Nanos, Fredriksen circle). 11 issues, 2014–2024; 78 PDFs on the issues page.
- **Licence (verified):** homepage https://www.jjmjs.org/: *"This work is licensed under a Creative Commons Attribution 4.0 International License."* The notice says it is relaunching as **"Intersections: Early Jewish and Christian Trajectories"** on a University of Oslo OA platform, with the 2025–26 issue due at year end.
- **Format:** per-article PDF with print pagination ("JJMJS No. 11 (2024): 1–34"). Example: https://www.jjmjs.org/uploads/1/1/9/0/11908749/1_nanos_translating.pdf (downloaded). No DOIs or OAI on the current Weebly site.
- **Harvest:** scrape https://www.jjmjs.org/issues.html (78 PDFs). Watch for the Oslo OJS site (it will have OAI) and re-point the records there once it's live.

### 7. Old Testament Essays — include now, open, priority 2
- **What:** journal of the Old Testament Society of South Africa (OTSSA), since 1983, double-anonymous review. On SciELO SA, with DOIs `10.17159/2312-3621/...`. Solid regional society journal. Quality is uneven but it's a real scholarly venue. Charges an APC (DOAJ).
- **Licence (verified):** DOAJ lists CC BY. Site footer: *"This work is licensed under a Creative Commons Attribution 2.0 Generic License."* Article pages carry CC BY 2.0 / 3.0 links. OAI records have no `dc:rights`, so record the licence at journal level.
- **Format:** per-article PDF, with `citation_firstpage`/`lastpage` (e.g. pp. 1–17 in continuous-publication volumes). Example: https://ote-journal.otwsa-otssa.org.za/index.php/journal/article/view/513 → `.../article/download/513/417`.
- **Harvest:** OJS OAI https://ote-journal.otwsa-otssa.org.za/index.php/journal/oai (verified, 394 records; the archive starts at vol. 31, 2018). Older volumes (2005–2017) are on SciELO SA: not checked.

### 8. Religion in the Roman Empire (Mohr Siebeck) — include now (only open items), open, priority 3
- **What:** Rüpke/Aarhus circle, high quality, directly on point for early Christianity in its Roman setting. Subscribe-to-Open model.
- **Licence (verified via Crossref only):** per-DOI `license` = CC BY-SA 4.0 for 14 items in 2023, 26 in 2024 and 9 in 2025. Other 2025–26 items have **no licence** in Crossref. Take only items that carry CC BY-SA. Mohr's own site is a JS shell that defeated curl and crawl4ai, so the publisher's licence text was **not read directly**. Search results describe it as S2O with CC BY-SA 4.0.
- **Harvest:** Crossref `journals/2199-4463/works`. PDF links point to `api.content-select.com` (not tested).

### 9. HTS Teologiese Studies / Theological Studies (+ Verbum et Ecclesia, In die Skriflig) — include selectively, open, priority 3
- **What:** AOSIS-published South African journals. HTS dates from 1943 (Nederduitsch Hervormde Kerk). DHET-accredited, indexed in Scopus, WoS and DOAJ, with double-anonymous review and APCs. **Quality is uneven:** HTS publishes at very high volume (6,322 Crossref DOIs) across practical theology, sociology of religion and much else, and an aggregator lists 5 retractions. It isn't predatory, but there is a lot of filler. The New Testament and early-church content (e.g. the Van Aarde era) can be good.
- **Licence (verified):** HTS OAI for records from 2025 on: `https://creativecommons.org/licenses/by/4.0/` (88+3) or `.../by/2.0/` (9). The PDF footer reads *"Licensee: AOSIS. This work is licensed under the Creative Commons Attribution License."* **Digitized back issues have unclear rights.** OAI rights for 1944–1990s records say *"Copyright Status: Not provided. Contact Holding Institution to verify copyright status. Rights Holder: Nederduitsch Hervormde Kerk van Afrika"*, and the same holds for Verbum et Ecclesia (NG Kerk van Transvaal) and In die Skriflig. Exclude records whose `dc:rights` lacks a CC URL.
- **Format:** per-article PDF, "Page 1 of 9", article number a11593, DOI `10.4102/hts.v82i1.11593`. Example: https://hts.org.za/index.php/hts/article/view/11593 (PDF downloaded). robots.txt: `Disallow: cache/` only.
- **Harvest:** OAI verified:
  - https://hts.org.za/index.php/hts/oai (6,219)
  - https://verbumetecclesia.org.za/index.php/ve/oai (2,156)
  - https://indieskriflig.org.za/index.php/skriflig/oai (2,626)
- **Recommendation:** filter by OAI subject or section (New Testament, Old Testament, Church History) plus a CC licence in `dc:rights`. Don't take the whole journal.
- **Same profile, lower priority:**
  - Acta Theologica (UFS; CC BY; OAI 1,355): https://journals.ufs.ac.za/index.php/at/oai
  - Stellenbosch Theological Journal (CC BY from 2023 per Crossref; 745 DOIs)
  - Integrated Biblical and Theological Studies (new AOSIS title, 2025)

### 10. Journal of Religion & Society (Creighton, Kripke Center) — later, open
- **What:** peer-reviewed (single-anonymous) e-journal, 1999–. Covers American religions and Western traditions, with supplements on Jewish–Christian themes. ~460 article PDFs across vols. 1–28 (counted from the `toc/<year>.html` pages). Middling but respectable.
- **Licence (verified):** on every TOC page (https://moses.creighton.edu/JRS/toc/Archive.html): *"freely allows users to read, download, copy, distribute, print, search, or link to the full texts … This work is licensed under a Creative Commons Attribution 4.0 Unported License."* The repository record for a 2005 article (OAI GetRecord `oai:cdr.creighton.edu:10504/64418`) has `dc:rights` = "CC-BY 4.0", https://creativecommons.org/licenses/by/4.0/.
- **Problem:** PDFs live on Creighton's DSpace (`cdr.creighton.edu/bitstream(s)/handle/...`) and returned **403** to curl and WebFetch (bot filtering). OAI-PMH works (https://cdr.creighton.edu/server/oai/request). The PDF format was **not verified**.
- **Recommendation:** later. Needs a browser-based fetch, or try the DSpace REST API.

### 11. Open Theology (De Gruyter Brill) — later, open, selective
- **What:** OA journal, founded 2014 (511 Crossref DOIs). Double-blind review, indexed in ESCI, ERIH+ and DOAJ, APC €1,200, heavy on special issues. Broad religious studies and theology. Quality is acceptable but uneven: better than MDPI's average, not a field-leading venue.
- **Licence (verified via Crossref and the journal page through crawl4ai):** Crossref `license` = `http://creativecommons.org/licenses/by/4.0`. The journal page links an "Open Access License" PDF.
- **Robots (verified):** https://www.degruyterbrill.com/robots.txt blocks `Google-Extended`, `GPTBot`, `CCBot`, `FacebookBot` and `Omgilibot` site-wide. Article and PDF URLs answered curl with an HTTP 202 bot challenge. The CC BY licence permits our use; the robots lines are a signal to crawl slowly and from Crossref links only.
- **Format:** Crossref lists `/document/doi/10.1515/opth-2025-0057/pdf` and `/xml` (JATS XML). PDFs have journal pagination. Not downloaded (challenge).

### 12. Themelios (The Gospel Coalition) — later, link only
- **What:** evangelical peer-reviewed journal, 1975– (RTSF/UCCF, TGC since 2008). Pastoral-academic in level. 153 issues listed at https://www.thegospelcoalition.org/themelios/issues/.
- **Terms (verified), https://www.thegospelcoalition.org/themelios/about/:** *"Readers are free to use it and circulate it in digital form without further permission, but they must acknowledge the source and may not change the content."* That's like ND, not CC → link only.
- **robots.txt (verified):** `Crawl-delay: 600` (one request per 10 minutes) for `*`.
- **Format:** HTML article pages (e.g. https://www.thegospelcoalition.org/themelios/article/retrieving-athanasius-ruled-readings-and-trinitarian-exegesis/) plus one PDF per issue (e.g. https://media.thegospelcoalition.org/wp-content/uploads/2026/09/18124019/Themelios-51.2.pdf). The HTML has no page anchors; page-level links need the issue PDF.

### 13. Andrews University Seminary Studies (AUSS) — later, link only
- **What:** Andrews University (Adventist) seminary journal, 1963–, peer-reviewed. Biblical studies, ANE and church history; respectable. **2,866 records** in Digital Commons OAI (set `publication:auss`, verified, earliest 1963). No CC licence in the records → link only.
- **Example:** https://digitalcommons.andrews.edu/context/auss/article/1004/viewcontent/1.PDF. OAI: https://digitalcommons.andrews.edu/do/oai/.

### 14. Religions (MDPI) — later, open, strictly selective
- **Honest assessment:** not predatory. It's indexed in Scopus (Q1 CiteScore in Religious Studies), AHCI and ATLA, and the licence is clean. But it's a volume operation: Crossref shows 669 articles in 2019, rising to 1,546 in 2023, 1,546 in 2024 and 1,608 in 2025, driven by guest-edited special issues with fast turnaround. Quality ranges from excellent (special issues edited by serious scholars) to thin. Treat it as a pool to pick from, not a journal to ingest.
- **Licence (verified via crawl4ai), https://www.mdpi.com/journal/religions/about:** *"Articles published in Religions will be Open-Access articles distributed under the terms and conditions of the Creative Commons Attribution License (CC BY)."*
- **Access (verified):** www.mdpi.com (Akamai) returns 403 to scripts, including robots.txt and `/oai`. `https://oai.mdpi.com/oai/oai2.php` works, but its sets are by article type, not journal. PDFs download from the CDN (`https://mdpi-res.com/d_attachment/religions/religions-17-01337/article_deploy/religions-17-01337.pdf` → 200 application/pdf).
- **Recommendation:** use Crossref (ISSN 2077-1444) to select by special-issue topic or author, then fetch from mdpi-res.com. Later.

### 15. TC: A Journal of Biblical Textual Criticism — later, link only
- **What:** SBL Press, peer-reviewed, 1996–. The open venue of record for textual criticism (Wasserman et al.). It moved in Nov 2025 to the Scholarly Publishing Collective, https://scholarlypublishingcollective.org/sblpress/tc. The old site jbtc.org returns **522** today. DOIs are `10.15699/tc.<vol>.<year>.<n>`.
- **Terms:** archived jbtc.org home page (Wayback 2025-05-27): *"Users are allowed to read, download, copy, distribute, print, search, or link to the full texts of all TC articles. Articles may not be reproduced without permission."* → link only. Crossref has no licence field. The SPC platform sits behind a Cloudflare JS challenge, so the current terms there were **not verified**.

---

## LDS-specific journals (fit Lectern; all link only)

- **BYU ScholarsArchive** (Digital Commons OAI https://scholarsarchive.byu.edu/do/oai/, verified). Sets and counts:
  - `publication:byusq`: BYU Studies, 4,341
  - `publication:jbms`: Journal of Book of Mormon Studies, 628
  - `publication:re`: Religious Educator, 1,042
  - `publication:sba`: Studies in the Bible and Antiquity, 69
  - also `studiaantiqua`, `msr`, `msr2` and `insights`

  `dc:rights` = http://lib.byu.edu/about/copyright/ → link only. Per-article PDFs, e.g. https://scholarsarchive.byu.edu/context/jbms/article/1008/viewcontent/18234.pdf. Good harvest route; priority depends on whether another workstream already covers LDS periodicals.
- **Interpreter: A Journal of Latter-day Saint Faith and Scholarship** (https://interpreterfoundation.org/journal): peer-reviewed, free PDF and ePub per article with print pagination (e.g. "Interpreter 70 (2027): 1–24"). No CC licence found on the article page. **robots.txt blocks `ClaudeBot`, `GPTBot`, `CCBot`, `OAI-SearchBot`, `PerplexityBot` (and bingbot) with `Disallow: /`.** Link only, and only if Lectern's crawler is honest about what it is. Treat that robots file as a "no" unless the Foundation agrees otherwise.
- **Dialogue** (https://www.dialoguejournal.com): "Copyright © 2026 The Dialogue Journal. All rights reserved." Link only. Not examined further.

---

## Considered and rejected or deferred (one line each)

- **BiblicalStudies.org.uk / Theology on the Web (Rob Bradshaw).** Don't harvest: robots.txt blocks `anthropic-ai`, `GPTBot`, `CCBot`, `Google-Extended` and Applebot; curl got 403. Most items are hosted "by permission of the copyright holder", a permission that is personal to that site, or as orphans ("All reasonable efforts have been made…"). Its "Public Domain" labels are UK life+70 judgements that don't always hold in the US (e.g. JTS 1946 marked PD). Use it as a **discovery index** only and get PD items from IA. ~50,000 articles per its 2023 update (search result, not verified).
- **The Bible and Critical Theory.** DOAJ licence CC BY-NC (site: "open-access (non-commercial)") → link only at best. The site's latest issue is 2022, and articles are embedded PDFs via a plugin. Low fit. Skip.
- **Journal for Interdisciplinary Biblical Studies (JIBS, Sheffield).** CC BY 4.0 from vol. 3 ("Articles published before volume 3 use a different license"; a WRRO record shows CC BY-NC-SA for 2020). Only ~78 WordPress posts, HTML with no print pagination, and a narrow critical-theory focus. Later, low.
- **Journal of Religion & Film (UNO).** CC BY 4.0 (99 of the first 100 OAI records; 1,514 records) but off-topic for Lectern. Skip.
- **Ancient Jew Review.** A good scholarly forum but mostly essays and reviews, not a journal of record. Squarespace HTML, no licence, no pagination. Skip (or link only, low).
- **HathiTrust bulk.** Its AUP bars automated bulk download, the research datasets need an application (not done), and curl and crawl4ai were blocked. Hand-fill gaps only.
- **`pub_expositor-and-homiletic-review` on IA.** An American homiletics magazine, not Nicoll's *Expositor*. Skip.
- **Methodist Review (IA, 795 pre-1931 items).** PD but mostly denominational and popular. Not a priority.
- **AABNER (Advances in Ancient, Biblical, and Near Eastern Research).** Excellent diamond-OA venue but CC BY-NC-ND (DOAJ), and the site timed out today. Later, link only.
- **Scriptura (Stellenbosch), Perichoresis (Sciendo), Biblica et Patristica Thoruniensia, Collectanea Theologica, TheoLogica.** ND or NC-ND licences, mid-to-low fit. Skip for now (link only if ever).
- **The Biblical Annals (KUL).** Mixed licences in OAI (76 CC BY vs "Copyright (c) … The Biblical Annals" statements; 1,334 records). Decent Catholic biblical journal. Later, licence per record.
- **Studies in Christian-Jewish Relations (Boston College).** CC BY 4.0 (OAI 591 records; Crossref CC BY from 2023). Relevant but mostly modern Jewish–Christian dialogue. Later, low.
- **Pharos Journal of Theology; E-Journal of Religious and Theological Studies (Noyam); Indonesian and other high-APC religion titles turned up in DOAJ.** Low reputation or off-scope. Skip. (Not individually investigated beyond DOAJ listings.)
- **Japanese Journal of Religious Studies, Journal of Moral Theology, Jewish Historical Studies (UCL), Entangled Religions.** Clean licences but off the core of Bible, early Christianity and ancient Judaism. Skip for now.
- **JETS, Detroit Baptist Seminary Journal, Southern Baptist Journal of Theology and other free evangelical journals.** Free to read but under copyright. Possible link-only additions later; not checked in detail.

---

## What was verified vs. not

**Verified today (fetched):**
- JHebS: licence, OAI and sample PDF
- Hugoye: licence, volume count and sample PDF
- Tyndale Bulletin: both licence texts, robots, Crossref and sample PDF
- JJMJS: licence, notice of the move and sample PDF
- OTE: footer licence, OAI and article metadata
- HTS/VE/IdS: OAI counts, rights strings and sample PDF
- JRS: licence text and OAI rights
- Themelios: terms and robots
- AUSS and BYU ScholarsArchive: OAI
- Interpreter: robots
- De Gruyter: robots; Open Theology licence (Crossref and journal page)
- MDPI: Religions licence (crawl4ai), oai.mdpi.com and the CDN PDF
- JSTOR EJC: terms, and IA item and file structure
- IA `pub_*`: counts, plus restriction flags on samples
- biblicalstudies.org.uk: robots and permission labels (crawl4ai)
- DOAJ API licence data for all ISSNs listed

**Not verified:**
- TC's current terms on the SPC platform (Cloudflare)
- Religion in the Roman Empire's licence on Mohr's site (relied on Crossref and search)
- JRS PDFs (403)
- Open Theology PDFs (bot challenge)
- AABNER (timeout)
- HathiTrust policy text (relied on search results)
- Religions' APC and impact figures (search results)
- HTS retraction count (aggregator, via search)
- biblicalstudies.org.uk size (search result)
- OTE pre-2018 on SciELO
- Article-type filtering for Biblical World and AJT (not done)

## URLs used

- https://jhsonline.org/index.php/jhs/about/submissions · https://jhsonline.org/index.php/jhs/oai?verb=Identify · https://jhsonline.org/index.php/jhs/article/download/5642/4695
- https://hugoye.bethmardutho.org/open-access.html · https://hugoye.bethmardutho.org/volumes.html · https://hugoye.bethmardutho.org/pdf/vol20/HV20N1Minov.pdf
- https://www.tyndalebulletin.org/about · https://www.tyndalebulletin.org/robots.txt · https://www.tyndalebulletin.org/article/30577.pdf · https://api.crossref.org/journals/0082-7118/works
- https://www.jjmjs.org/ · https://www.jjmjs.org/issues.html
- https://ote-journal.otwsa-otssa.org.za/index.php/journal/about · https://ote-journal.otwsa-otssa.org.za/index.php/journal/oai
- https://www.mohrsiebeck.com/en/journal/religion-in-the-roman-empire-rre/open-access/ (search result) · https://api.crossref.org/journals/2199-4463/works
- https://hts.org.za/index.php/hts/oai · https://verbumetecclesia.org.za/index.php/ve/oai · https://indieskriflig.org.za/index.php/skriflig/oai · https://hts.org.za/index.php/hts/article/view/11593 · https://journals.ufs.ac.za/index.php/at/oai
- https://moses.creighton.edu/JRS/toc/Archive.html · https://moses.creighton.edu/JRS/toc/About.html · https://cdr.creighton.edu/server/oai/request
- https://www.degruyterbrill.com/journal/key/opth/html · https://www.degruyterbrill.com/robots.txt · https://api.crossref.org/journals/2300-6579/works
- https://www.thegospelcoalition.org/themelios/about/ · https://www.thegospelcoalition.org/robots.txt · https://www.thegospelcoalition.org/themelios/issues/
- https://digitalcommons.andrews.edu/do/oai/ (set publication:auss)
- https://www.mdpi.com/journal/religions/about · https://oai.mdpi.com/oai/oai2.php?verb=Identify · https://api.crossref.org/journals/2077-1444/works
- https://evangelicaltextualcriticism.blogspot.com/2025/11/new-issue-30-2025-and-new-home-of-tc.html · https://web.archive.org/web/20250527204922/https://jbtc.org/
- https://scholarsarchive.byu.edu/do/oai/?verb=ListSets · https://interpreterfoundation.org/robots.txt · https://interpreterfoundation.org/journal
- https://about.jstor.org/terms/ · https://archive.org/metadata/jstor_ejc · https://archive.org/details/jstor-3259399 · https://archive.org/advancedsearch.php
- https://biblicalstudies.org.uk/articles.php · https://biblicalstudies.org.uk/robots.txt
- https://bibleandcriticaltheory.com/ · https://jibs.hcommons.org/about-jibs/ · https://digitalcommons.unomaha.edu/do/oai/ (set publication:jrf) · https://www.ancientjewreview.com/robots.txt
- https://doaj.org/api/search/journals/ (ISSN and title queries)
- https://hathitrust.org/acceptable-use and https://hathitrust.org/datasets (via search results; direct fetch blocked)
