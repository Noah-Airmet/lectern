# Primary sources for Lectern: link-only and open-tier candidates

Researched 2026-11-15. Every fact marked **verified** was fetched today with curl (generic UA `Mozilla/5.0 (compatible; research-bot)`) or the site's own public API. Facts marked **unverified** come from search results or the site's own claims and were not checked against the live data. Nothing was downloaded in bulk: at most one or two metadata calls or sample pages per source. No forms, no contact.

Tier vocabulary below: **link only** = private full text for index and quote check, public sees snippets ≤300 chars, quote checks ≤40 words, citation and a deep link to the owner's page. **Open** = Lectern hosts the text and page images (public domain or CC BY only).

## Summary table

| Source | What | Size (verified unless noted) | Licence / terms in one line | Harvest route | Recommendation |
|---|---|---|---|---|---|
| Mormonr Q&As (B. H. Roberts Fdn) | Modern apologetic-historical Q&As with timelines and footnotes | 86 English Q&As (+10 translations each), 46 blog posts | © B. H. Roberts Foundation; robots `Allow: /` | sitemap.xml, server-rendered HTML | **Include now, link only.** Ask first (courtesy). High priority, low effort |
| BHR primary source archive | Excerpt records: bibliography + transcription of the relevant passage + scan of that passage | 12,321 index entries across 408 subjects; ~5,100 dated before 1931 | Fair-use excerpts of others' works; "non-commercial personal research purposes" | Public Algolia index (search-only key in page JS) | **Ask first.** Use as a citation map, not as texts. Not a massive harvest |
| Joseph Smith Papers | Critical edition: transcripts + page images | ~10,000 items in control file (FAQ, unverified count of what is online) | Church Terms of Use: no robots, spiders or automated copying | No robots.txt; private API exists; no sitemap | **Ask first; do not crawl.** Highest value, link only if permitted |
| Church History Library catalog | Archival scans (manuscripts, records) | Very large; not countable without crawling | Church Terms of Use (same) | Client-rendered; internal `/api/` with DeepZoom, not IIIF | **Skip as a text source**; use as link target only |
| CHL uploads on archive.org | Church periodicals and books, OCR'd | 15,539 items; 9,181 dated 1800–1930 | Old items are US public domain (blanket "© IRI" label on items) | archive.org advancedsearch + per-item `_djvu.txt`, page anchors | **Include now, open tier (pre-1931).** Highest effort-to-value ratio of anything here |
| Church History Biographical Database / Saints by Sea | Person records, voyage accounts | 100,000+ people (site claim); Saints by Sea accounts uncounted | Church terms / BYU copyright statement | Crawling only | **Skip** (genealogical, not scholarship) |
| BYU HBLL CONTENTdm | 19th-c. Mormon publications, Millennial Star, Woman's Exponent, BOMP, missionary diaries | 119 collections; NCMP 154 titles, MStar 62 vols, BOMP 582 items, MMD 378 diaries | Items say "Public Domain, Courtesy L. Tom Perry Special Collections" | CONTENTdm API + IIIF manifests; OAI-PMH works but robots disallows `/oai/` | **Include now, open tier** (Times and Seasons, Evening and Morning Star, Messenger and Advocate, BOMP). Re-OCR needed |
| U of Utah Marriott (digital library + Utah Digital Newspapers) | Utah newspapers, Tanner Trust Books, oral histories | 467 OAI sets; UDN millions of pages (unverified) | Item pages now behind a bot challenge (HTTP 418) | OAI-PMH for metadata only | **Later**, link only, selective |
| Scripture Central archive + KnoWhys | Hosted copies of FARMS, JBMS, BYU Studies, Interpreter etc.; own KnoWhys and Evidences | Sitemap: 14,239 archive URLs; 2,447 KnoWhy URLs; 734 Evidence pages | "Non-commercial, private use"; robots allows all | Single sitemap (7 MB), SSR HTML, PDFs on Google Cloud Storage | **KnoWhys: include now, link only. Archive: link to the original publisher where one exists; use SC only for orphaned FARMS material.** Ask first |
| Wilford Woodruff Papers | Transcribed journals, letters, discourses | Thousands of documents (site claims every extant WW document by 2027) | Copyright-and-use page: non-profit educational use; **robots blocks ClaudeBot, GPTBot, CCBot etc.** | Official read-only API (sign up, accept terms, explain use) | **Ask first, via the API sign-up.** Do not crawl |
| Church Historian's Press | Eliza R. Snow, Emmeline B. Wells, George Q. Cannon journals, First Fifty Years of RS, At the Pulpit | 6,599 URLs across 10 sitemaps | Church Terms of Use | Sitemaps | **Ask first** (same owner as JSP) |
| Book of Mormon Critical Text Project | Skousen's Analysis of Textual Variants etc. | 6-part ATV | © Royal Skousen; free to read online at Interpreter (2014) | omner.interpreterfoundation.org did not respond today | **Later**, ask Skousen/Interpreter |
| BOAP (boap.org) | Formerly transcriptions of early LDS sources | — | Domain now redirects to a Vietnamese football-streaming site | — | **Skip**; old links are dead |

---

## 1. The B. H. Roberts Foundation

### 1a. What it is

The B. H. Roberts Foundation (BHR) is a 501(c)(3) run by Executive Director Josh Coates; it describes itself as having "a bias toward faith" and supporting "an archival database of primary sources related to difficult topics in Mormonism, original research articles, and research grants" (https://bhroberts.org/about, verified). Projects listed at https://bhroberts.org/projects (verified): Mormonr, LDSBot (its own AI chatbot, ldsbot.com), the 2022 and 2023 national surveys, Church History Cards, a "Mormon Gestapo Archive", a golden-plates modelling paper, Missouri 1838.

Two things that matter for us:

**Mormonr (mormonr.org)** is the public face: long Q&As on hard questions (Adam-God, B. H. Roberts's testimony, anachronisms, etc.), each with a timeline, numbered footnotes, bios and a "Primary Sources" tab. Quality is high and careful about hearsay: every source is tagged Direct / Secondary / Late / 2nd Hand / Scribed Verbatim, etc. The sitemap (https://mormonr.org/sitemap.xml, verified) holds 1,051 URLs: **86 English Q&As**, 46 blog posts, and about 91 pages in each of 10 translations.

**The primary source archive** ("Primary Source Database", https://bhroberts.org/archive) is a search UI over an Algolia index named `prod_records`. I read its size from the same public, search-only key the page's own JavaScript uses (one facet query, `hitsPerPage=2`). **Verified figures:**

- **12,321 index entries**, grouped into **408 subjects**. The objectID is `subject-record`, and subject counts sum to 14,666, so some records sit under more than one subject. Unique records are probably somewhat under 12,321.
- By type: Book 4,365; News 1,497; Website 1,420; Speech/Court transcript 1,397; Periodical 1,352; Academic/Technical report 987; Letter 888; Personal journal/diary 816; Manuscript 815; Meeting minutes 337; Government document 325; Affidavit 147; Interview 122; Social media 105; Audio/video 43.
- By date (`ts_start`): 4,432 before 1900; 5,141 before 1931; the rest are modern (2000s–2020s are heavily represented: books and articles by Roper, Hedges, etc.).
- Top people: Joseph Smith (3,778), Brigham Young (1,195), Oliver Cowdery (517), Sidney Rigdon (455).
- Top subjects: Prophetic Fallibility (453), Anachronistic Book of Mormon Language (425), Anachronistic Technology (421), Adam-God (353), Mountain Meadows Massacre (300), Kirtland Bank (201), View of the Hebrews (201).

**What a record is** (verified on a sample record and on the research page): one record = a bibliography string (e.g. *Matthew Roper, "Joseph Smith, Central American Ruins, and the Book of Mormon," in Approaching Antiquity … (2015), 142*), a one-line summary, a transcription **of the relevant excerpt only**, hearsay tags, people, and a scan of the excerpt (PDF or JPG on `/files/...` behind a signed, expiring token). Many records also carry an `external_source` link to where the full original lives: archive.org, newspapers.lib.utah.edu, catalog.churchofjesuschrist.org, contentdm.lib.byu.edu, scholarsarchive.byu.edu, scripturecentral.org, dialoguejournal.com, JSTOR (counted on the B. H. Roberts research page).

**Honest sizing.** It is not a massive *harvest*: 12k short excerpts is tens of megabytes of text and one index. It is a massive *editorial* asset (hand-selected, tagged excerpts), but it is a **finding aid made of quotations**, not a library of documents. It never holds whole works, and much of it is modern copyrighted scholarship quoted under fair use. So it does not fit Lectern's "the whole item, cited to the page" model directly.

### 1b. Format and deep links

- Q&As: server-rendered HTML (Remix). Stable URLs `https://mormonr.org/qnas/{id}/{slug}` with `#footnote-N` and `#bio-…` anchors; text fragments work because the text is in the HTML.
  - https://mormonr.org/qnas/sk58P/b_h_roberts_testimony (verified, 200)
  - https://mormonr.org/qnas/0JPssK/adam_god_theory (verified, 200)
- Records have **no standalone public page**: `bhroberts.org/records/{id}` and `mormonr.org/records/{id}` both 404 (verified), even though the JS references `/records/${id}`. Records are reachable only (a) inside a Q&A's research tab, anchor `#re-{subjectId}-{recordId}`, e.g. https://mormonr.org/qnas/sk58P/b_h_roberts_testimony/research#re-HB4aQb-582xcj (page verified 200, 204 `re-` anchors present), or (b) through the archive search UI with query parameters, e.g. `https://bhroberts.org/archive?prod_records[query]=Nauvoo`. Records under subjects with no published Q&A have no deep-linkable home.

### 1c. Licence and terms

- No terms-of-use page exists on mormonr.org (`/terms`, `/terms_of_use`, `/privacy` all 404, verified). Footer: "Copyright © by B.H. Roberts Foundation."
- https://mormonr.org/fair_use (verified), the operative statement for the archive: "Records in the archival database include a bibliographic reference to the source of the work, a text transcript of the relevant portion and a digital scan of the relevant portion of the original document. Records in the archival database are publicly available for non-commercial personal research purposes. The records in the archival database are created under the terms of fair use (Title 17, Section 107, of the U.S. Code)." Concerns go to archive@bhroberts.org.
- robots.txt, https://mormonr.org/robots.txt (verified): `User-agent: * / Allow: / / Sitemap: https://mormonr.org/sitemap.xml`. Header `x-robots-tag: all`. bhroberts.org has no robots.txt (the path returns the SPA's 404 page).
- Nothing on AI or text mining. The foundation runs its own AI chatbot (LDSBot) over this material, so it is plainly not hostile to AI use, but the archive's excerpts of third-party copyrighted works are BHR's fair-use claim, not ours to extend.

### 1d. Harvest route

- Q&As: sitemap → HTML. 86 pages (about 0.9 MB each with inline data). Trivial.
- Archive: the Algolia index is technically readable in full with the public search key, but that key is meant for the site's own search box. Pulling all 12k records that way is a bulk harvest the foundation did not offer; I did not do it beyond one facet query.

### 1e. Recommendation

- **Mormonr Q&As: include now, link only.** High priority, small effort (a day). It is modern, copyrighted, faithful, well-sourced scholarship; our snippet + deep link model is exactly what a Q&A site benefits from. Robots allows everything. Asking first is a courtesy rather than a requirement, and worth doing because of step 2.
- **Archive: ask first; don't ingest the excerpts as texts.** The best use for Lectern is a **citation map**: for each record, the bibliography + date + hearsay tag + `external_source`. Where the cited work is already in Lectern (for example a pre-1931 Journal of Discourses volume or a Times and Seasons issue), we can show "Mormonr cites this page" and link back to the Q&A. Where it isn't, the list of 5,141 pre-1931 cited sources is a ready-made acquisition list for the open tier.

**Smallest sensible first step for BHR:**
1. Index the 86 English Q&As as link-only items (sitemap → HTML → Lectern text; deep links via text fragment or `#footnote-N`). No permission needed under robots, but tell them.
2. In the same note to archive@bhroberts.org or info@mormonr.org (we send it), ask for a periodic export of record **metadata** (record id, bibliography, date, subject, Q&A slug, external_source), explicitly without transcriptions or scans, so Lectern can link Q&As and cited pages both ways. Mention we would never re-host excerpts.
3. Only if they offer, take the excerpt transcriptions too as link-only quote-check text. That is their call, given the fair-use basis.

---

## 2. The Joseph Smith Papers (josephsmithpapers.org)

### What it is
The Church History Department's documentary edition of everything Joseph Smith created or owned: journals, revelations, histories, letters, legal and financial records, with full transcripts, page images, source notes, bios and annotation. Gold-standard quality; 27 print volumes plus the website. FAQ (https://www.josephsmithpapers.org/articles/faq1, verified): "the Joseph Smith Papers Project control file currently includes about ten thousand items… about twenty-five hundred are original texts." Covers roughly 1820s–1844.

### Format and deep links (verified)
Server-rendered Next.js HTML; each image/page has its own URL, `/paper-summary/{slug}/{n}` where `n` is the image sequence, with the transcript in the HTML (so text fragments work) and a downloadable JPG.
- https://www.josephsmithpapers.org/paper-summary/history-circa-june-1839-circa-1841-draft-2/12 (200; title "…Page 10")
- https://www.josephsmithpapers.org/paper-summary/letter-to-emma-smith-4-june-1834/1 (200; "Page 56")

The page config exposes a private API base, `PUBLIC_API_URL: https://jsp-api.pvu.cf.churchofjesuschrist.org` (verified in page source); I did not call it.

### Licence and terms (verified)
- Footer: "© 2026 by Intellectual Reserve, Inc. All rights reserved." linking to the Church Terms of Use (Updated 2021-04-13), https://www.churchofjesuschrist.org/legal/terms-of-use?lang=eng. Relevant lines:
  - "You further agree not to: (i) use any robot, spider, or other automatic device, process, or means to access this site for any purpose, including, without limitation, for monitoring or copying any of the material on this site; (ii) use any manual process to monitor or copy any material on this site, or for any other purpose not expressly authorized in this Agreement, without our prior written consent".
  - "materials (besides those available in the Gospel Media) may not be posted from this site to another website or computer network without our prior written permission."
  - On linking: "we believe that linking to other websites is legally permissible and consistent with the expectations of those who use the Internet."
- robots.txt: none (404, verified). Sitemap: none (404).
- The 1830s–40s manuscripts themselves are public domain; the JSP transcriptions are probably thin-copyright at most, but the annotation is copyrighted and, more to the point, the terms are a contract that bars automated access regardless.

### Harvest route
None that the terms allow. A private API exists; no OAI, IIIF or sitemap.

### Recommendation
**Ask first, do not crawl.** Highest value of anything here for Lectern users, and link-only (search + 40-word quote checks + deep link to `/paper-summary/…/{n}`) is exactly the kind of use worth requesting written consent for (the Church History Department / JSP). Effort after permission: moderate (about 10k items, page-level). Meanwhile, the PD printings of the same texts (Times and Seasons, Evening and Morning Star, Messenger and Advocate, Millennial Star) can go in the open tier from BYU and archive.org (sections 5 and 3b), and Lectern can **link out** to JSP pages by hand-curated citation without harvesting anything.

---

## 3. Church History Library digital collections, CHBD, Saints by Sea

### 3a. Church History Catalog (catalog.churchofjesuschrist.org)
- **What:** The Church's archive catalog with digitized manuscripts, minute books, diaries (e.g. Wilford Woodruff journals, MS 1352, 7,000+ pages per Church News 2018, unverified), photos.
- **Format:** Client-rendered Next.js viewer; the page HTML carries no item data. Asset URLs `/assets/{uuid}/{part}/{pageIndex}` deep-link to an image page. The JS calls internal endpoints `/api/catalog`, `/api/delivery/dzi` (DeepZoom tiles, not IIIF), `/api/pdf` (verified in bundles). Examples (both 200, taken from Mormonr's citations):
  - https://catalog.churchofjesuschrist.org/assets/468f6660-c4ab-463c-898c-ffd6ca9aa318/0/5?lang=eng
  - https://catalog.churchofjesuschrist.org/assets/48bc6049-d521-4d76-833b-b3d3fd622fa4/0/14?lang=eng
- **Terms:** same Church Terms of Use as JSP (no robots). robots.txt: none (404).
- **Size:** not countable without crawling.
- **Recommendation: skip as a text source.** These are mostly images of handwriting without transcripts, so there is nothing to index without HTR, and the terms forbid automated access. Use catalog URLs only as **outbound citation links** (e.g. from JSP, Woodruff or Mormonr citations).

### 3b. Church History Library on the Internet Archive (the big find)
The Church History Library itself uploads OCR'd scans to archive.org (contributor "Church History Library…", sponsor "Corporation of the Presiding Bishop"). **Verified via archive.org advancedsearch:**
- `collection:churchhistorylibrary`: **15,539 items**, 15,528 texts; **9,181 dated 1800–1930**.
- `churchhistorylibraryperiodicals`: 5,462 items, 3,493 dated before 1931.
- Pre-1931 counts by title: **Juvenile Instructor 1,284** (1866–1929); **Millennial Star 1,609** (of 2,611, 1840–1970); **Improvement Era 398** (of 880, 1897–1970); **The Contributor 204** (1879–1896, all); **Conference Reports** (`conferencereport`, 312 items 1898–2010); Deseret titles 58; plus Scandinavian and German mission periodicals (Skandinaviens Stjerne, Der Stern).
- Each item has `_djvu.txt` (OCR), `_hocr.html`, `_page_numbers.json` and PDF, e.g. `contributor0206eng` (The Contributor, March 1881).
- **Licence:** items carry `possible-copyright-status: "© Copyright by Intellectual Reserve, Inc. All rights reserved."` even on 1881 issues (verified). That is a blanket label: works published in the US before 1931 are public domain, and under US law (Bridgeman v. Corel) a faithful scan of a PD page adds no new copyright. Treat pre-1931 items as PD; leave 1931+ out or link-only.
- archive.org robots.txt only disallows `/control/` and `/report/` (verified).
- Examples: https://archive.org/details/contributor0206eng/page/n5/mode/1up (200), https://archive.org/details/improvementera3803unse (200).
- **Recommendation: include now, open tier for pre-1931; top priority.** It is the same pipeline Lectern presumably already uses for its 352 PD books (archive.org → text + page images, cite to page). Start with Contributor (204 issues), Juvenile Instructor and Improvement Era 1897–1930, Conference Reports 1898–1930, then Millennial Star. Low effort per item; the main work is issue-level metadata and page-number mapping (`_page_numbers.json` helps).

### 3c. Church History Biographical Database and Saints by Sea (brief)
- CHBD (https://history.churchofjesuschrist.org/chd/landing?lang=eng, 200, verified): "information about the lives of over 100,000 members… pioneer immigrants… early missionaries, Mormon Battalion… thousands of source documents." Church terms apply. Search page: https://history.churchofjesuschrist.org/chd/search?lang=eng (200).
- Saints by Sea (now https://saintsbysea.byu.edu, BYU HBLL; old host redirects): passenger lists and transcribed voyage accounts, 1840–1932, e.g. https://saintsbysea.byu.edu/mii/account/2 (200; a Millennial Star 1882 notice). No robots.txt (404 page). BYU copyright statement applies.
- **Recommendation: skip.** Genealogical databases rather than citable scholarship; the voyage accounts are mostly quotations from journals and the Millennial Star, which Lectern gets anyway from 3b.

---

## 4. BYU Harold B. Lee Library digital collections (contentdm.lib.byu.edu)

### What it is
BYU's CONTENTdm with 119 collections (verified via `dmGetCollectionList`). Relevant ones, with top-level item counts (verified via `dmQuery`):

| Alias | Collection | Items | Notes |
|---|---|---|---|
| NCMP1820-1846 | Nineteenth Century Mormon Publications | 154 titles | Includes **Times and Seasons vols 1–5** (1839–45), **Evening and Morning Star** (1832–34 + Kirtland reprint), **Messenger and Advocate** vols 1–3 (1834–37), pamphlets, hymnals, Millennial Star supplements; some later (to 1888) |
| MStar | Millennial Star | 62 volumes | Vol. 1 = 1840–41 |
| BOMP | 19th Century Publications about the Book of Mormon (1829–1844) | 582 items | Newspaper notices with **transcriptions** by the Maxwell Institute plus facsimile PDFs |
| MMD | Mormon Missionary Diaries | 378 | Scans; e.g. James E. Talmage 1924 journal marked PD |
| WomansExp / YWJ | Woman's Exponent / Young Woman's Journal | 769 / 43 objects | Query counted page-level objects |
| JournalOfDiscourses3 | Journal of Discourses | 27 | PD (1854–86) |
| desnews1–10 | Deseret News | 353 in desnews1 | Early Deseret News |
| 19CMNI | 19th-Century Mormon Article Newspaper Index | 5,758 | Non-Mormon press articles about Mormons |
| EoM | Encyclopedia of Mormonism (1992) | 1 compound | Copyrighted; not PD |
| NibleyOC, rsc, RelEd, MormonBib2 | Nibley, RSC books, etc. | 21 / 81 / 5,066 / 14,533 | Modern, copyrighted; MormonBib2 is URL records |

Improvement Era and The Contributor are **not** in BYU's CONTENTdm; they are on archive.org via the Church History Library (3b).

### Format and deep links (verified)
- Compound objects whose children are **per-article PDFs** (Times and Seasons vol. 1 has 171 child articles, e.g. "A History, of the Persecution… in Missouri", pages 17–20). IIIF Presentation 2 manifests work: https://contentdm.lib.byu.edu/iiif/2/NCMP1820-1846:9373/manifest.json (200; 171 canvases, Image API level 1).
- Item pages: https://contentdm.lib.byu.edu/digital/collection/NCMP1820-1846/id/9373 (200), https://contentdm.lib.byu.edu/digital/collection/BOMP/id/201 (200). Deep link per article is `/id/{childPointer}`; `#page=N` works on the child PDFs.
- **OCR quality is poor** in NCMP (2006 OCR; sample text "T IME TI M asf f … TRUM WIjlefbJ8EVAIL1"). The BOMP transcriptions are clean.

### Licence and terms (verified)
- Item rights field: "**Public Domain, Courtesy L. Tom Perry Special Collections, Harold B. Lee Library, Brigham Young University**" (Times and Seasons, Millennial Star, MMD); BOMP: "Public Domain, Courtesy Neal A. Maxwell Institute…"
- Generic statement, https://lib.byu.edu/about/copyright/generic/: "We encourage use of this Material for non-profit and educational purposes, such as personal research, teaching and private study… Except as provided above, or any use beyond what is allowed by fair use… you may not reproduce, republish, post… without the permission of the copyright owner." Since BYU marks these items PD, there is no copyright owner to ask for the old texts.
- robots.txt (https://contentdm.lib.byu.edu/robots.txt): `Disallow: /config/ /error/ /results/ /utils/ /oai/ /ui/` plus every collection's `/search/`; **`Crawl-Delay: 1`**; Sitemap `http://contentdm.lib.byu.edu/sitemap.xml`.
- OAI-PMH Identify works (https://contentdm.lib.byu.edu/oai/oai.php?verb=Identify → "Digital Collections at BYU"), but **robots disallows `/oai/`**, so use the CONTENTdm web-services API (`/digital/bl/dmwebservices/index.php?q=…`) and IIIF instead, at 1 request/second. Late in the session the server stopped answering me (timeouts), so throttle well below that.

### Recommendation
**Include now, open tier**, medium priority, medium effort:
- **Times and Seasons, Evening and Morning Star, Messenger and Advocate** (NCMP): the core 1830s–40s periodicals. Fetch page images via IIIF and **re-OCR** (BYU's OCR is unusable). Check first whether better OCR copies exist on archive.org or HathiTrust.
- **BOMP**: 582 short PD newspaper items with clean transcriptions. Easy and useful.
- Millennial Star: prefer the archive.org CHL copies (better OCR, per-issue).
- Skip EoM, RSC and Nibley here (copyrighted; Nibley belongs to the Maxwell Institute/FARMS track).

---

## 5. University of Utah J. Willard Marriott Library

- **What:** the Marriott Digital Library (collections.lib.utah.edu, 467 OAI sets) and **Utah Digital Newspapers** (newspapers.lib.utah.edu; article-level OCR of Deseret News, Salt Lake Tribune and many small papers; 3.5–8.7 million pages per secondary sources, unverified). LDS-relevant sets include Tanner Trust Books (14 records in the OAI page, modern annotated editions of diaries such as *A Mormon Mother*, *Diary of Brigham Young 1857*; dc:rights "University of Utah, Copyright 2001"), Mormon Settlement in Arizona, Mormon Homelands Oral History, Ellis Reynolds Shipp Papers, Affirmation records.
- **Format:** ARK URLs (e.g. https://collections.lib.utah.edu/ark:/87278/s67943z3) and `details?id=` for newspapers (e.g. https://newspapers.lib.utah.edu/details?id=25250073, cited by Mormonr). **Both sites returned HTTP 418 with a JavaScript proof-of-work bot challenge today** to curl and to WebFetch (verified), so I could not read item pages, rights text or formats.
- **robots.txt** (both hosts, verified): `User-agent: * / Disallow: /file` (and Twitterbot allowed).
- **OAI-PMH:** works for collections.lib.utah.edu (Identify → "J. Willard Marriott Library Digital Repository", verified); newspapers.lib.utah.edu says "OAI not supported".
- A Marriott page reportedly says Newspapers.com digitized Utah newspapers for free in exchange for three years of exclusive use (search result, unverified).
- **Recommendation: later, link only, selective.** The bot challenge is a clear signal against automated harvesting. Newspapers are useful as citation targets (Lectern can link `details?id=` URLs found in other sources' footnotes) rather than as indexed texts. Pre-1931 Deseret News text could be open tier in principle, but BYU's desnews collections or LOC Chronicling America are friendlier routes.

---

## 6. Scripture Central (formerly Book of Mormon Central)

### What it is
A faith-promoting nonprofit ("independent advocate"); it runs:
- **The archive** (formerly archive.bookofmormoncentral.org, now https://scripturecentral.org/archive; old URLs 301 to the new ones, verified). It hosts copies of FARMS Review, JBMS, BYU Studies, Interpreter, Religious Educator, RSC book chapters, Ensign/New Era articles, conference talks, etc. One sitemap, https://admin.scripturecentral.org/api/sitemap/index.xml (7 MB, verified), lists **18,166 URLs, 14,239 under /archive/**: 3,635 book chapters, 2,903 magazine articles, 2,099 journal articles, 1,664 magazine issues, 268 journal issues, 268 encyclopedia entries, 256 books, 138 general conference talks, plus charts, art and media. Journal-issue pages by title: Religious Educator 32, JBMS 32, BYU Studies Quarterly 30, Interpreter 29+28+7, FARMS Review 16 + FARMS Review of Books 12, Journal of Book of Mormon and Restoration Scripture 11.
- **KnoWhys**: 2,447 URLs under `/knowhy/` (verified), plus 734 `/evidence/` pages ("Book of Mormon Evidence") and 69 Q&As. Their own writing, with footnotes and further reading.

### Format and deep links (verified)
- Archive item pages are server-rendered HTML with abstract and metadata and a PDF on Google Cloud Storage. `#page=N` works on the PDF. Example: https://scripturecentral.org/archive/periodicals/journal-article/chiasmus-inthebookofmormon → PDF `https://storage.googleapis.com/scripturecentral-prod-strapi-uploads/n_w_welch_chiasmus_in_the_book_of_mormon_1969_57a627445d/…pdf`. The page also lists the **original publisher URL** (here https://byustudies.byu.edu/article/chiasmus-in-the-book-of-mormon/).
- Second example: https://scripturecentral.org/archive/books/book-chapter/renewal-oftheway (200).
- KnoWhys: SSR HTML, text fragments work. Example: https://scripturecentral.org/knowhy/why-would-nephi-call-the-ocean-irreantum (200, "KnoWhy #20 | August 20, 2020").

### Licence and terms (verified)
- On every archive item: "**Terms of use** Items in the BMC Archive are made publicly available for non-commercial, private use. Inclusion within the BMC Archive does not imply endorsement."
- Footer: "© 2025 Scripture Central Foundation: A Non-Profit Organization. All rights reserved."
- https://scripturecentral.org/policies: "If we use material copyrighted by the Church, it is with explicit authorization from the Intellectual Property Office…"; "Scripture Central retains the complete ownership of all content produced by official Scripture Central content creators." The ScripturePlus app terms on the same page say: "Use any robot, spider, or other automatic device, process, or means to access ScripturePlus for any purpose, including monitoring or copying any of the material on ScripturePlus" (prohibited). That clause names ScripturePlus, not the website.
- robots.txt, https://scripturecentral.org/robots.txt: allows facebookexternalhit/facebookcatalog, then a comment "# Block all other crawlers for the site" followed by `User-agent: *` with **no Disallow line**, then the sitemap. Literally, nothing is disallowed; the comment suggests they meant to block. The old archive host's robots: `Crawl-delay: 10`, standard Drupal disallows only.

### Recommendation
- **KnoWhys (+ Evidence pages): include now, link only, after asking.** About 3,200 short, footnoted, faith-centred pieces; ideal for snippet + deep link. Medium priority, low effort (sitemap → HTML). Ask because of the ambiguous robots comment.
- **Archive: link to the original publisher, not to SC, wherever an original exists** (BYU Studies, Interpreter, RSC, ScholarsArchive host the canonical copies, and our model links to "the owner's own site"). Use SC only for material whose original home is gone, chiefly old **FARMS** preliminary reports, FARMS Review and JBMS issues not on BYU ScholarsArchive. Note: BYU ScholarsArchive has `/jbms/`, `/msr/` (Mormon Studies Review, the FARMS Review line) and `/byusq/` series (200, verified), and a working OAI-PMH endpoint (https://scholarsarchive.byu.edu/do/oai/?verb=Identify, verified), so check those before using SC copies. Ask SC (and, for SC-hosted copies of others' journals, the original publisher) before indexing.

---

## 7. Others a serious researcher would expect (brief)

### Wilford Woodruff Papers (wilfordwoodruffpapers.org)
- Wilford Woodruff Papers Foundation; goal "to locate, transcribe, and publish online every extant document created by Wilford Woodruff" 2020–2027 (FAQ, verified). Journals 1833–1898, letters, discourses, with full transcripts tagged for people, places and topics. High quality.
- Page-level permalinks (verified): https://wilfordwoodruffpapers.org/documents/0c971e56-08d1-4e91-9ade-4fb00f2883f0/page/737cd3fc-e349-49b2-9f4b-a77ea306c5e3 (200), whose "Cite this page" gives the short link https://wilfordwoodruffpapers.org/p/yrPw (200).
- Copyright and Use, https://wilfordwoodruffpapers.org/media/copyright (verified): "We encourage use of the material for non-profit and educational purposes, such as personal research, teaching, and private study… Except as provided above, or any use beyond what is allowed by fair use… you may not reproduce, republish, post, transmit, or distribute any material from this website… without the permission of the copyright owner."
- **robots.txt** (verified): `User-agent: * / Crawl-delay: 20`, but **`Disallow: /` for anthropic-ai, ClaudeBot, Claude-Web, GPTBot, ChatGPT-User, CCBot, Google-Extended, Applebot-Extended, Bytespider, Amazonbot, img2dataset, Omgilibot** and others (from a darkvisitors.com list). An explicit no to AI crawling.
- **Developer API** (https://wilfordwoodruffpapers.org/developers, verified): "a read only API… currently in beta and is available to the public… Export transcripts along with tagged people, places, topics, and dates… Before accessing the API, we ask that you accept the terms of use and provide a brief explanation of why you want to use the API." Dashboard: https://wilfordwoodruffpapers.org/api/dashboard.
- **Recommendation: include later via the API, link only. Ask first** by signing up and describing the use honestly (search index + snippets + deep links, no re-hosting, no model training). Do not crawl; their robots blocks AI agents. High value, low effort once approved.

### Church Historian's Press (churchhistorianspress.org)
- Church History Department imprint with free online editions: Eliza R. Snow (1,149 URLs), Emmeline B. Wells diaries (922), The First Fifty Years of Relief Society (2,571), George Q. Cannon journals (798), George F. Richards (576), At the Pulpit (379), Early Sister Missionaries (95), plus others: **6,599 URLs** across 10 sitemaps (verified). robots.txt only disallows search paths. Footer links to the Church Terms of Use (no robots or automated copying).
- **Recommendation: ask first, together with the JSP request** (same department). Link only.

### Book of Mormon Critical Text Project (Royal Skousen)
- The six-part *Analysis of Textual Variants* was made free to read online by the Interpreter Foundation in 2014 (search results; "© 2014 Royal Skousen. All rights reserved"); the Maxwell Institute/BYU Studies sells print (https://mi.byu.edu/analysis-of-textual-variants-of-the-book-of-mormon-part-two, 200, verified, "Buy Print"). The online edition host omner.interpreterfoundation.org **did not respond** today (unverified whether it still exists). Manuscript transcriptions (original and printer's manuscripts) also appear in JSP's Revelations and Translations series.
- **Recommendation: later; ask Skousen/Interpreter.** Link only if a stable host exists.

### Brigham Young Papers
- There is no published online documentary edition comparable to JSP or WWP (I found none). Brigham Young's office files are images in the Church History Catalog (3a); his PD discourses are in the Journal of Discourses (BYU `JournalOfDiscourses3`, archive.org) and the Deseret News. **Recommendation:** cover Brigham Young through Journal of Discourses (open tier) and CHL archive.org periodicals; nothing separate to add.

### Mormon pamphlets
- The main pamphlet sets are BYU's NCMP (section 4, PD) and the Church History Library uploads on archive.org (3b, 15.5k items include pamphlets and books). I found no separate "Mormon Pamphlets" collection on archive.org (collection search turned up web archives, a Relief Society Magazine and Dialogue `pub_` collections). **Recommendation:** covered by NCMP + CHL archive.org, open tier for pre-1931.

### BOAP (boap.org), Book of Abraham Project
- Long a go-to for transcriptions of early LDS sources. **https://www.boap.org/ now redirects to 90phuttv.center, a Vietnamese football-streaming site** (verified); its robots.txt has Vietnamese SEO comments. The domain has lapsed or been taken over. **Skip**, and treat existing boap.org links in any harvested footnotes as dead (Wayback copies only).

---

## Suggested order of work

1. **CHL periodicals on archive.org, pre-1931 → open tier** (Contributor, Juvenile Instructor, Improvement Era 1897–1930, Conference Reports 1898–1930, Millennial Star). No permission needed; same pipeline as the existing PD books.
2. **Mormonr Q&As → link only** (86 pages), plus the courtesy note to BHR asking for archive metadata.
3. **BYU NCMP periodicals + BOMP → open tier** (IIIF + re-OCR; BOMP has clean transcriptions).
4. **KnoWhys/Evidence → link only**, after a note to Scripture Central.
5. **Permission requests** (we send them): Church History Department for JSP + Church Historian's Press; Wilford Woodruff Papers via its API sign-up; Scripture Central for archive items that have no other home.
6. Later: Marriott/UDN as outbound citation targets; Skousen ATV.

## What I could not verify
- Exact number of JSP documents online today (only the FAQ's ~10,000 control-file figure); I did not touch its API.
- The size of the Church History Catalog, or whether any IIIF exists there (the JS shows DeepZoom only).
- Marriott and UDN item pages, rights text and formats (blocked by the HTTP 418 bot challenge); UDN page counts.
- Unique record count in the BHR archive (only 12,321 entries and 408 subjects; records can repeat across subjects).
- Whether Scripture Central's sitemap is complete (one 7 MB file; journal-article counts look low for FARMS + JBMS + BYU Studies combined).
- The current home of Skousen's online ATV (omner.interpreterfoundation.org timed out).
- Woman's Exponent and YWJ counts at BYU (the query counted page-level objects, not issues). Late in the session BYU's server stopped answering, so the MStar item page could not be re-checked (earlier API calls to it succeeded).

## URLs used
- https://bhroberts.org/, /about, /projects, /archive; JS bundles `/assets/_app.archive-Dq49R7ni.js`, `Record-CyTtbCp3.js`, `RecordsTable-BQ9QjG2n.js`; Algolia `https://VNIJAENPNI-dsn.algolia.net/1/indexes/prod_records/query` (one facet query plus three count queries with the page's public search key)
- https://mormonr.org/robots.txt, /sitemap.xml, /fair_use, /about_us, /qnas/sk58P/b_h_roberts_testimony, /qnas/sk58P/b_h_roberts_testimony/research, /qnas/0JPssK/adam_god_theory
- https://www.josephsmithpapers.org/ (+ /robots.txt 404, /sitemap.xml 404), /articles/faq1, /articles/citing-this-website, /articles/note-on-transcriptions, two /paper-summary/ pages above
- https://www.churchofjesuschrist.org/legal/terms-of-use?lang=eng, https://www.churchofjesuschrist.org/robots.txt
- https://catalog.churchofjesuschrist.org/assets/… (2 above) and its JS chunks
- https://archive.org/advancedsearch.php (counts), https://archive.org/metadata/improvementera3803unse, https://archive.org/metadata/contributor0206eng, https://archive.org/metadata/churchhistorylibrary, https://archive.org/robots.txt
- https://history.churchofjesuschrist.org/chd/landing?lang=eng, /chd/search?lang=eng; https://saintsbysea.byu.edu/, /mii/account/2
- https://contentdm.lib.byu.edu/robots.txt, /oai/oai.php?verb=Identify, /digital/bl/dmwebservices/index.php (dmGetCollectionList, dmQuery, dmGetItemInfo, dmGetCompoundObjectInfo), /iiif/2/NCMP1820-1846:9373/manifest.json, https://lib.byu.edu/about/copyright/generic/
- https://collections.lib.utah.edu/robots.txt, /oai?verb=Identify, /oai?verb=ListSets, /oai?verb=ListRecords&set=uum_ttb; https://newspapers.lib.utah.edu/robots.txt, /oai (not supported), /details?id=25250073 (418)
- https://scripturecentral.org/robots.txt, https://admin.scripturecentral.org/api/sitemap/index.xml, https://scripturecentral.org/policies, the archive and KnoWhy pages above; https://archive.bookofmormoncentral.org/robots.txt
- https://scholarsarchive.byu.edu/robots.txt, /do/oai/?verb=Identify, /jbms/, /msr/, /byusq/
- https://wilfordwoodruffpapers.org/robots.txt, /developers, /media/copyright, /about/frequently-asked-questions, document and /p/ pages above
- https://www.churchhistorianspress.org/robots.txt, /sitemap.xml and its 10 sub-sitemaps
- https://mi.byu.edu/analysis-of-textual-variants-of-the-book-of-mormon-part-two; https://omner.interpreterfoundation.org/books/atv (no response)
- https://www.boap.org/ (redirects to 90phuttv.center)
- Search results used for unverified context: https://churchhistorylibrary.churchofjesuschrist.org/blog/digital-access-to-wilford-woodruffs-journals?lang=eng, https://www.fairlatterdaysaints.org/blog/2014/10/20/analysis-of-textual-variants-now-available-online-free, https://digitalnewspapers.org/about
