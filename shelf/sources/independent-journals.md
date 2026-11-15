# Independent LDS-studies journals: sources for Lectern's link-only tier

Researched 2026-11-15 with curl (generic browser user agent), the WordPress REST APIs, OAI-PMH, Crossref and the Wayback CDX API. Samples downloaded: at most two files per source. Nobody was contacted.

"Verified" means I fetched the page or file this session. "Not verified" means I could not, and I say why.

## Summary table

| Source | Free now | Format | Licence | Harvest route | Recommendation |
|---|---|---|---|---|---|
| Dialogue (+ Element) | Everything, 1966 to the current issue | Per-article PDF, per-issue PDF, HTML | Authors keep copyright; post-2020 © Univ. of Illinois; an unclear "CC BY-NC-ND" label | WP REST + Yoast sitemaps | **Include now, priority 1** |
| Interpreter (Interpreter Foundation) | Everything, 2012 to now | HTML + per-article PDF | **CC BY-NC-ND 4.0** | Sitemap (926 URLs) | **Include now, priority 1** |
| Sunstone | Issues 1–164 (1975–2011) as PDF; 165–191 partly HTML | Per-article PDF + per-issue PDF; WP posts | Authors keep copyright; © Sunstone Education Foundation | Live PDFs + Wayback 2024 copy of the broken index | **Include now, priority 2** |
| Mormon Historical Studies / Nauvoo Journal | 1989–2014 (506 PDFs) | Per-article PDF | © Ensign Peak Foundation, all rights reserved | Crawl 47 issue pages | **Include now, priority 2** |
| Journal of Mormon History, USU back run | 1974–2014 (80 issues, 1987 missing) | Whole-issue PDF only | No licence stated (© MHA) | Digital Commons OAI (`dcs` prefix) | **Include later, priority 2**: Cloudflare blocks scripted PDF downloads, and robots.txt disallows `/do/` |
| JMH 2015–now (UIP, JSTOR, MUSE, SPC) | Paywalled | – | © | – | **Skip** |
| John Whitmer Historical Association Journal | 1981–2024 (newest two years members-only) | Whole-issue PDF on Google Drive | © JWHA | Public Drive folders | **Include later, priority 3** (Drive can't open a PDF at a page) |
| Utah Historical Quarterly | Vols 1–70 (1928–2002) at U of Utah; later issues on Issuu | Per-article PDF + OCR at U of U; Issuu viewer | "© Utah State Historical Society. All Rights Reserved."; 1928–30 public domain | U of U OAI (`dha_hpp` set); **not Issuu** | **Include later, priority 3**; consider 1928–30 for the open tier |
| Square Two | Everything, 2008–2026 (386 pages) | Static HTML | "©2007 All Rights Reserved" (site template) | Crawl one archive page | **Include now, priority 3** (small and easy) |
| Exponent II | 1974–2020 (154 issues) on archive.org | Whole-issue PDF + OCR | Rights reserved; robots says `search=yes, ai-train=no` | archive.org API | **Include later, priority 4** |
| IJMS (2008–13) + JMSSA (2023–) | Everything | Per-volume PDF / HTML | **CC BY-NC-ND 2.5 / 4.0** | 6 PDFs + a few pages | **Include now, priority 3** (small) |
| Mormon Studies Review (UIP, 2014–) | Paywalled | – | © | – | **Skip** (FARMS Review / MSR vols 1–23 are free on BYU ScholarsArchive) |
| Claremont Journal of Mormon Studies | One student issue | PDF | – | – | **Skip** |
| Restoration Studies | No free archive found | – | – | – | **Skip** |

On licences: none of these is CC BY, CC BY-SA or CC0, so no journal qualifies for the open tier as the brief defines it. The exceptions are individual public-domain volumes (UHQ 1928–1930). Interpreter, IJMS and JMSSA are CC BY-NC-ND. That licence does allow verbatim, attributed, non-commercial redistribution, so hosting them is permitted if Lectern is non-commercial. Whether to widen the open tier for them is a decision for us. Link-only is safe for them either way.

---

## 1. Dialogue: A Journal of Mormon Thought

**What it is.** Dialogue is published quarterly by the University of Illinois Press for the Dialogue Foundation, an independent 501(c)(3). It is peer-reviewed: "Articles are reviewed by at least two volunteer experts in the subject area of the paper" ([submissions](https://www.dialoguejournal.com/submissions/)). Founded in 1966, it has 59 volumes and about 231 issues (`dj_issues-sitemap.xml`, from fall-1966 to fall-2026). The REST API reports **5,018 article records** (`X-WP-Total` on `/wp-json/wp/v2/dj_articles`). These include poetry, fiction, reviews and letters. Crossref holds **5,628 DOIs** (10.2307/… for the JSTOR backfile, 10.5406/dialjmormthou… for the UIP era). It is the most important independent journal in Mormon studies: history, theology, scripture, and the Bible in LDS contexts. Very relevant.

**What's free.** Everything, including the current issue. I checked `V59N03.pdf` (Fall 2026, 200 pages, 9.3 MB). It returns 200 with no login, and its text layer has about 60k words. The issue pages say "Purchase an individual issue here", which refers to print only. There is no moving wall on dialoguejournal.com. JSTOR and UIP also carry the journal (not checked; JSTOR's journal page wouldn't render for curl or WebFetch).

**Format** (verified):
- One HTML page per article, with full text. Footer: "The Dialogue Foundation provides the web format of articles as a courtesy. There may be unintentional differences from the printed version. For citational and bibliographical purposes, please use the printed version or the PDFs provided online."
- One per-article PDF, linked from each article page: `/wp-content/uploads/sbi/articles/Dialogue_V21N04_145.pdf` (older) and `/wp-content/uploads/sbi/articles/V59N02_1.pdf` (newer).
- One per-issue PDF: `/wp-content/uploads/sbi/issues/V58N04.pdf` or `Dialogue_V54N04.pdf`. Some issues also have an EPUB (`sbi/issues/5304.epub`).
- **Page numbers.** The PDF page index does not equal the printed page, but the offset is constant within a file. Older articles are 2010-era scans with an OCR text layer. In `Dialogue_V21N04_145.pdf` (8 pages), PDF page 1 = printed p. 143 and PDF page 2 = 144; running heads were checked through p. 150. **The number in the filename is not the start page** (145 ≠ 143), so take the offset from the running heads or from metadata. In issue PDF `V59N03.pdf`, PDF page N = printed N − 4 (pdf 10 → 6, pdf 150 → 146).
- **URL stability.** The `sbi/` paths have been in place since at least 2010 (PDF creation dates) and are widely cited and indexed by Google. Article slugs are WordPress permalinks.
- Example article URLs checked:
  - https://www.dialoguejournal.com/articles/the-case-for-the-new-mormon-history-thomas-g-alexander-and-his-critics/ → PDF https://www.dialoguejournal.com/wp-content/uploads/sbi/articles/Dialogue_V21N04_145.pdf (downloaded, 1.9 MB)
  - https://www.dialoguejournal.com/articles/jacobs-temple-sermon-as-reinterpretation-of-scripture-and-rethinking-of-sexual-ethics/ → PDF https://www.dialoguejournal.com/wp-content/uploads/sbi/articles/V59N02_1.pdf (HEAD 200, 360 KB; not downloaded, so I haven't checked that it holds the whole article)

**Licence and terms.**
- Footer on every page: "Copyright © 2026 The Dialogue Journal. All rights reserved."
- The masthead of the Fall 2026 issue PDF reads: "Contents copyrighted by the Board of Trustees of the University of Illinois… Dialogue is available in full text in electronic form at www.dialoguejournal.com and JSTOR.org and is archived by the University of Utah Marriott Library Special Collections". It also says: "Submissions published in the journal… are covered by our publications policy… under which the author retains the copyright of the work and grants Dialogue permission to publish."
- [Publication policy](https://www.dialoguejournal.com/submissions/publication-policy/) for pre-2020 work: "In all cases, you retain the copyright to your submission, and you grant Dialogue the permissions described below… Non-exclusive permission to republish the Work in digital form through use of electronic storage and search capabilities (such as the Internet…) or on Dialogue's website or the website of an archival service". For 2020 onward: "As of all works published in or after 2020, the University of Illinois Press has a publication policy and agreement letter that all author will need to sign."
- The same policy page ends with a bare label, **"Creative Commons License CC BY-NC-ND"**. It doesn't say what the licence covers, and no article page or PDF I checked carries a CC mark. I treat it as unclear. It would be worth asking Dialogue whether the pre-2020 archive is CC BY-NC-ND; if so, it could be hosted verbatim.
- There is no terms-of-use page in `page-sitemap.xml` and nothing on crawling, text mining or AI.
- **robots.txt**: https://www.dialoguejournal.com/robots.txt is **empty** (200, 0 bytes), so all crawling is allowed. Article pages carry `robots: index, follow, max-snippet:-1`.

**Harvest route.**
- WordPress REST: `https://www.dialoguejournal.com/wp-json/wp/v2/dj_articles?per_page=100` gives full HTML content plus taxonomy IDs (`dj_issues`, `dj_article_categories`) and `coauthors`. The PDF link isn't in REST; take it from the article page's `href="/wp-content/uploads/sbi/articles/…pdf"`.
- Yoast sitemaps: `dj_articles-sitemap.xml` through `-sitemap6.xml` (5,001 URLs) and `dj_issues-sitemap.xml` (231).
- Size estimate: issue PDFs run 9–28 MB (V59N03 9.3 MB, V58N04 13 MB, V56N04 20 MB), so about 231 × 13 MB ≈ **3 GB** per-issue. The per-article set is similar. You only need one of the two.
- University of Utah: the Marriott Library's 2004 scans are what dialoguejournal.com serves under `sbi/`. collections.lib.utah.edu holds no separate Dialogue serial set today; a search found only stray manuscript copies. There is no other public host of the back run besides JSTOR (paywalled).

**Metadata.** Title, authors (co-authors taxonomy), issue (season/year, volume/number on the issue page), category, and HTML footnotes. DOIs come from Crossref (match by title, volume and issue). There are no citation_* meta tags.

**Element (companion).** Element: The Journal of the Society for Mormon Philosophy and Theology (2005–2019) is also hosted on dialoguejournal.com (`sbi/articles/E7.pdf`, HEAD 200, 1.8 MB; `E4_1.pdf`, `E2_2.pdf`). The revived run from 2024 is free from Greg Kofford Books (`cdn.shopify.com/s/files/1/0266/2257/files/element_10.1.pdf`, seen in search results, not fetched). Philosophy and theology, high relevance. Harvest it with Dialogue.

**Recommendation: include now, priority 1.** It is free, complete, stable, born-digital or OCRed, permissively crawlable, highly relevant, and has good metadata. Link to the per-article PDF with `#page=N`, where N = printed page − (start page − 1); compute the offset per file from running heads. Asking first isn't required for link-only. A courtesy note to the Dialogue Foundation would be good relations, and it could settle the CC BY-NC-ND question.

---

## 2. Sunstone

**What it is.** Sunstone is a magazine published by the Sunstone Education Foundation (501(c)(3)) since 1975. "Sunstone is a magazine… that discusses Mormonism through scholarship, art, short fiction, and poetry." It is **not peer-reviewed** (submissions are editor-judged; [ads-and-submissions](https://sunstone.org/magazine/ads-and-submissions/)). Quality is mixed: serious history and theology (Barlow, Bergera, Quinn and others) sits beside essays, humour and news. It is very relevant to LDS studies and moderately relevant to biblical studies.

**What's free.**
- Issues **1–164** (1975 to roughly Oct 2011) are PDFs at `https://sunstone.org/wp-content/uploads/sbi/issues/NNN.pdf`. Issues 001, 103, 150, 160, 161, 163 and 164 return 200; 165 and later return 404.
- Per-article PDFs are at `sbi/articles/{issue}-{startpage}-{endpage}.pdf`.
- Issues **165–191** (2011–Spring 2024) are WordPress posts. Some are free HTML; a "premium" category has 111 posts, and the "Recent Issues" page says "Or subscribe".
- **The site's PDF index is broken.** https://sunstone.org/magazine/pdf-back-issues/ and https://sunstone.org/issue-details/?in=103 render the raw shortcodes `sb_view_issues() ?>` and `[sb_view_issue_contents]`. Commenters since 2012 complain they can't find PDFs. The files themselves are still live.

**Format.** Per-article PDFs are born-digital (Quark/Distiller). Sample: `128-24-39.pdf`, 16 pages, PDF page 1 = printed p. 24, through PDF page 16 = p. 39. **The filename encodes the printed page range**, so `#page = printed − start + 1`. Per-issue PDFs are 8–28 MB, and early issues are scans.

Example URLs checked:
- https://sunstone.org/wp-content/uploads/sbi/articles/128-24-39.pdf (downloaded, 265 KB; Bergera, "History of Sunstone part 2", July 2003)
- https://sunstone.org/wp-content/uploads/sbi/issues/103.pdf (HEAD 200, 28 MB)
- HTML era: https://sunstone.org/linguini-to-spare-2/ (about 2,000 words, full text)

**Licence and terms.**
- Footer: "© 2024 Sunstone Education Foundation".
- [Grant of rights](https://sunstone.org/magazine/ads-and-submissions/): "all literary rights are retained by authors… The Author grants Sunstone… Non-exclusive permission to re publish… 5. Permission to authorize copies of the Work to be made for classroom and other use with appropriate citation… The Magazine recognizes that the Author retains all other rights to the Work".
- There is no CC licence and no terms of use.
- **robots.txt** (https://sunstone.org/robots.txt) has WooCommerce disallows only, then a Yoast block of `User-agent: * / Disallow:` (everything allowed). There is no AI or content-signal language.

**Harvest route.**
- The issue and article metadata now exists only in the **Wayback Machine**. There are 176 archived `issue-details/?in=N` pages; for example http://web.archive.org/web/20240605034717/https://sunstone.org/issue-details/?in=103 lists titles, authors and PDF links (33 PDF links for issue 103).
- The Wayback CDX API shows about 1,970 distinct `sunstone.org/wp-content/uploads/sbi/articles/` URLs and about 3,200 under the old `sunstonemagazine.com` host, which overlap. So expect **~2,000–3,000 article PDFs**.
- Fetch the PDFs from live sunstone.org. Size: 164 issues × ~10–15 MB ≈ **2–2.5 GB**.
- The 165–191 posts are available through WP REST (`/wp-json/wp/v2/posts?categories=…`; 5,600 posts in total, mostly podcasts).

**Metadata.** From Wayback: title, author and issue, plus page range from the filename. No DOIs.

**Recommendation: include now, priority 2.** It is free, stable and deep-linkable with the page offset derivable. Lower quality than Dialogue, but a key primary and secondary source for 1975–2011 Mormon intellectual history. Skip premium posts. No need to ask first. Telling Sunstone their PDF index page is broken would be a kindness.

---

## 3. Journal of Mormon History

**What it is.** The journal of the Mormon History Association, peer-reviewed, published since 1974; it has been published by the University of Illinois Press since about 2016. It is the top journal in Mormon history, with Crossref holding **1,049 DOIs** (10.5406/24736031.*). Highly relevant to LDS studies and less so to biblical studies.

**Free: USU DigitalCommons** (https://digitalcommons.usu.edu/mormonhistory/). The page says: "Access: Journals from 1974-2014 are available on this Digital Commons. For complete access of the Journal, please go to JSTOR". OAI returns **80 records, all `dc:type` "Full Issue"**, covering 1974–2014. **1987 is missing.**
- **Format:** one PDF per issue (not per article). The OAI `dc:description` carries the issue's table of contents with printed start pages, e.g. "Lawrence Foster, 3 … Linda K. Newell and Valeen T. Avery, 23".
- The bepress meta tag `bepress_is_article_cover_page=1` suggests Digital Commons prepends a cover page, so expect a PDF-to-print offset. **Not verified**: every scripted fetch of `viewcontent.cgi` (HEAD and GET) returned a **Cloudflare "Just a moment…" 403 challenge**. A browser will get through, so user links should work, but a harvester will need a real browser.
- Example URLs: https://digitalcommons.usu.edu/mormonhistory/vol6/iss1/1/ (PDF https://digitalcommons.usu.edu/cgi/viewcontent.cgi?article=1005&context=mormonhistory) and https://digitalcommons.usu.edu/mormonhistory/vol40/iss4/2/ (PDF `…article=1082…`). These are bepress URLs and are stable.
- **Licence:** none stated on the journal or record pages, only the Digital Commons footer. Contents are © MHA.
- **robots.txt** (https://digitalcommons.usu.edu/robots.txt): `User-agent: ^Byte Disallow: /`, then for `*` many `/cgi/*.cgi` disallows plus **`Disallow: /do/`**, which covers the OAI endpoint. `/cgi/viewcontent.cgi` is not disallowed.
- **OAI-PMH:** `https://digitalcommons.usu.edu/do/oai/?verb=Identify` works. `ListRecords&metadataPrefix=oai_dc&set=publication:mormonhistory` returned **noRecordsMatch**, but **`metadataPrefix=dcs`** returned all 80 records (315 KB). A second set, `publication:usupress_mormonhist`, exists (not explored).
- Size: not measurable (Cloudflare). Expect about 80 × 15–30 MB ≈ 1.5–2 GB.

**Paywalled: 2015 to now.** Current issues are on Scholarly Publishing Collective (e.g. https://scholarlypublishingcollective.org/jmh/article/52/4/105/412924/…) and Project MUSE (vol. 50 onward). JSTOR covers the back run with a moving wall that I couldn't confirm (JSTOR pages don't render for curl). JSTOR's robots.txt has a block headed "# Disallow crawling for the purposes of training models" that names ClaudeBot, CCBot, GPTBot and Google-Extended.

**Recommendation.** For the USU 1974–2014 run, **include later, priority 2**. The content is excellent, but the tooling has two snags. (a) robots disallows `/do/`, which covers OAI. That is a weak objection, since the OAI endpoint exists to be harvested, but it is still a signal. (b) Cloudflare blocks scripted PDF fetches. Linking is fine (`viewcontent.cgi?...#page=N`), but N needs the cover-page and front-matter offset per issue. A short note to USU Libraries' Digital Commons team or to MHA would clear both snags. For the UIP years, **skip**: they are paywalled, and we would have no lawful private full text.

---

## 4. Mormon Historical Studies (now Latter-day Saint Historical Studies) and Nauvoo Journal

**What it is.** The journal of the Ensign Peak Foundation (formerly the Mormon Historic Sites Foundation). It ran as the *Nauvoo Journal* from 1989 to 1999, then as *Mormon Historical Studies* from 2000, and is now *Latter-day Saint Historical Studies*. It is "an independent periodical that includes essays, biographies, documents, book reviews, historic site descriptions… while striving for high scholarly standards." The current editorial board includes Church History Department historians (Godfrey, MacKay, Reeder, Rogers). Peer review is not stated. This is solid LDS history, and I'd guess it is "Journal of Latter-day Saint History" in your list.

**What's free.** "Downloadable PDF files of each article are available for all issues two years from the publication date" ([publications](https://ensignpeakfoundation.org/publications/)). In practice, crawling the 47 issue pages found **506 PDFs covering 1989 to Spring 2014**. The Spring 2015, Fall 2015 and 2016 issue pages have **0 PDFs**, and nothing after 2016 is listed. So the stated two-year wall isn't being kept up.

**Format.** One PDF per article (and per section such as TOC or reviews), born-digital (QuarkXPress 6). Sample `mhs1.1CharlesSpring2000.pdf`: 33 pages, PDF page 1 = printed p. 93, then 94, 95; offset = start − 1. URLs: `http://ensignpeakfoundation.org/wp-content/uploads/2013/05/…pdf` (301 to https). Stable since 2013.

Example URLs checked:
- https://ensignpeakfoundation.org/mormon-historical-studies-spring-2000-vol-1-no-1/ → https://ensignpeakfoundation.org/wp-content/uploads/2013/05/mhs1.1CharlesSpring2000.pdf (downloaded, 335 KB)
- https://ensignpeakfoundation.org/nauvoo-journal-1989-vol-1/ → https://ensignpeakfoundation.org/wp-content/uploads/2013/05/NJ1_Platt1.pdf (listed, not fetched)

**Licence and terms.** Footer: "Copyright © Ensign Peak Foundation, 2006-2026. All Rights Reserved." There are no terms of use. **robots.txt** (https://ensignpeakfoundation.org/robots.txt): `User-agent: *` with `Disallow: /calendar/action*` and `/events/action*` only.

**Harvest route.** Plain crawl: `/publications/` links the 47 issue pages, each of which links its PDFs. WP REST exposes only 1 post, so it is useless. Size: 506 × ~0.3–1 MB ≈ **0.3–0.5 GB**.

**Metadata.** Issue title and date come from the page slug; article title and author come from link text or the PDF's first page; pages come from the PDF text layer. No DOIs.

**Recommendation: include now, priority 2.** It is small, clean, per-article and born-digital, with an easy page offset. Asking first isn't needed.

---

## 5. John Whitmer Historical Association Journal

**What it is.** The journal of the JWHA, which covers Community of Christ (RLDS) and the wider Latter Day Saint movement. Published annually from 1981 and twice yearly now. *Restoration Studies* has been merged into it. The editorial board has "strong scholarly standards"; formal peer review is not stated on the page. It is the main venue for RLDS history and is high-relevance for the non-Utah branches.

**What's free.** "The archive of past issues of The JWHA Journal are available to all except for the past two years' issues. The most recent issues are available to members only." ([JWHA Journal](https://www.jwha.info/publications/jwha-journal/)). The archive is a **public Google Drive folder** (https://drive.google.com/drive/folders/1OH4zSgjOjYXZloqXznyUiM-5Y8JDD_6x), split into 1980s, 1990s, 2000s, 2010–2020 and 2021-present folders, plus a members-only folder. 2021-present currently runs up to `2024V44N1.pdf`.

**Format.** One PDF per volume or issue. Sample `1981V1.pdf` (68 pages, 7.2 MB, scanned with OCR, about 43k words): PDF page 30 = printed p. 28 (offset 2). The masthead reads "Contents copyright © 1981 by the John Whitmer Historical Association."

Example URLs checked:
- https://drive.google.com/file/d/1Xn1gqhyOyMD9b4Pkh9SF21sFqyWgFwPC/view (1981 V1; downloaded via `drive.usercontent.google.com/download?id=…&export=download`)
- https://drive.google.com/file/d/1qj1CTtMbanlDUcM0Sjyu5MN1rTjpewoG/view (2024 V44 N1; redirect checked, not downloaded)

**Licence and terms.** © JWHA, as stated in the masthead. **robots.txt** for jwha.info has WooCommerce rules only. There are no Drive-specific terms beyond Google's.

**Harvest route.** List the public folders with `https://drive.google.com/embeddedfolderview?id=<folder>` (works without login) and download with `uc?export=download`. Journal index: https://www.jwha.info/publications/jwha-journal/jwha-journal-index/ (an embedded document). Size: about 45 files × ~7–20 MB ≈ **0.5 GB**.

**Metadata.** Index document plus the PDF's table of contents; no DOIs (Crossref has no record of the ISSN 0739-7852). JSTOR also carries the journal according to secondary sources; not verified.

**Recommendation: include later, priority 3.** The content is good, but **deep linking is weak**. As far as I know, Google Drive's `/view` preview ignores `#page=N`, so the button would open the file at page 1 and Lectern would have to print "p. 28". This is untested. Drive file IDs are also only as stable as JWHA's folder management. Worth asking JWHA whether they'd put the PDFs on jwha.info, which would make page links work. The members-only folder is out of scope.

---

## 6. Utah Historical Quarterly

**What it is.** The journal of the Utah State Historical Society (a state division) since 1928, now published by the University of Illinois Press (ISSN 0042-143X, e-ISSN 2642-8652). Peer-reviewed via Scholastica. It covers Utah and Western history, much of it LDS-related, with no biblical content. Moderate relevance.

**What's free.**
- **Vols 1–70 (1928–2002)** are on the University of Utah digital library, set **`dha_hpp`** ("Historic and Prehistoric Publications"). There are about 435 items with UHQ titles, including volume records such as "Utah Historical Quarterly Volume L" (1982). Each article is a child record with a PDF and OCR text shown on the details page. Example: https://collections.lib.utah.edu/details?id=421345 (Vols I–VI; OCR shows printed p. 121).
- Later back issues are on **Issuu** (https://issuu.com/utah10, linked as "Back Log" from https://history.utah.gov/utah-historical-quarterly).
- An article index is a published Google Sheet linked as "Browse Articles".
- Current issues are by subscription (UIP).

**Format.** At U of U: per-article PDFs at `https://collections.lib.utah.edu/file?id=N`, plus HTML details pages with OCR text and ARK links (`ark:/87278/s64q7tb2`). Issuu offers only its own page viewer.

**Licence and terms.**
- U of U records: "Rights Management: Digital Image © Utah State Historical Society. All Rights Reserved." (volume level: "Digital image copyright 2009, University of Utah. All rights reserved.")
- **U of U robots.txt** (https://collections.lib.utah.edu/robots.txt): `User-agent: Twitterbot / Disallow:` then `User-agent: * / Disallow: /file`. **PDF downloads are disallowed for crawlers**; the details pages with OCR are allowed. Search pages also sit behind a JavaScript challenge, though crawl4ai gets through.
- **Issuu terms** (https://issuu.com/legal/terms): users may not "Use any data mining or similar automated or manual data extraction, gathering or scraping methods in connection with the Service". **Do not harvest from Issuu.**
- Public domain: UHQ volumes 1–3 (1928–1930) are public domain in the US, since anything published before 1931 is PD as of 2026. 1931–1963 volumes are PD only if the copyright wasn't renewed; I did not check renewals.

**Harvest route.** U of U OAI-PMH: `https://collections.lib.utah.edu/oai?verb=Identify` works. `ListRecords&metadataPrefix=oai_dc&set=dha_hpp` returns 213 records per page with a resumption token. The set also includes *Utah Archaeology* and other state publications, so filter by title. For text, the OCR on details pages is allowed by robots; PDFs via `/file` are not.

**Recommendation: include later, priority 3.** It is LDS-adjacent rather than core. Use U of U OCR from the details pages for the private index, and link users to the U of U details page or ARK. A details page has no `#page`, but each article is its own record, so links still land on the right article. Ask U of U Marriott Library (or the Utah Historical Society) before fetching `/file` PDFs in bulk. Consider vols 1–3 for the **open tier**.

---

## 7. Square Two (SquareTwo)

**What it is.** An online-only journal (2008 to now), edited by Valerie M. Hudson and colleagues: "Faithful Scholarship by Members of the Restored Church of Jesus Christ of Latter-day Saints on Contemporary Issues." It is editor-reviewed ("the standards for publication on SquareTwo are good writing, good arguments, good referencing, and harmony with… teachings of the Church"; [guidelines](https://squaretwo.org/squaretwoguidelines.html)), not formally peer-reviewed. Its themes are ethics, family, politics and doctrine; there is little scripture scholarship. Moderate relevance.

**What's free.** Everything: 386 article pages listed on https://squaretwo.org/squaretwoarchives.html, across 54 issue labels (Fall 2008–Spring 2026).

**Format.** One static HTML page per article, with a self-cited "Full Citation for this Article: Hudson, Valerie M. (2013) 'A Revolutionary Hire at BYU's College of Religious Education,' SquareTwo, Vol. 6 No. 2 (Summer)". There are no PDFs and no page numbers, so text-fragment links (`#:~:text=`) are the way to cite. The URLs are flat and have been stable since 2008.

Examples checked: https://squaretwo.org/Sq2ArticleHudsonAncientScripture.html (about 2,400 words) and https://squaretwo.org/Sq2ArticleAllenGoodGuys.html (a short piece).

**Licence and terms.** Site footer: "©2007 All Rights Reserved." (from the free CSS template). **robots.txt**: https://squaretwo.org/robots.txt returns **404**, so there are no restrictions.

**Harvest route.** Crawl the archive page, then 386 static pages. Size: under 50 MB.

**Metadata.** Author, title, volume, number and season are all in the citation line. No DOIs.

**Recommendation: include now, priority 3.** It is trivial to harvest, clean, and the text fragments work. No need to ask.

---

## 8. Exponent II

**What it is.** A Mormon feminist quarterly magazine (1974 to now), published by Exponent II, Inc. It carries essays, poetry, art and personal narrative. It is not a scholarly journal, but it is a significant primary source for LDS women's history. Low to moderate relevance for scholarship.

**What's free.** "With help of Brigham Young University and in cooperation with Archive.org, every issue of Exponent II from 1974 through 2020 is available online in full color." ([past issues](https://exponentii.org/magazine-home/past-issues/)). That is archive.org collection **`exponentiibrighamyounguniv`**: 154 items, 1974–2020, **12.9 GB**. Issues from 2021 on are for subscribers.

**Format.** archive.org items with a text PDF, `_djvu.txt`, hOCR and `_page_numbers.json`. Example: https://archive.org/details/exponentii371arli has 36 images and a 10 MB PDF. Deep links use `https://archive.org/details/<id>/page/<printed page>/`, which page_numbers.json supports. These are archive.org identifiers and are stable.

**Licence and terms.** One item's metadata (`possible-copyright-status`) reads: "The Exponent II Board retains ownership, control, and license over all content… The magazine and blog remain the intellectual property of the Exponent II organization, which retains any and all copyrights. The Board does not grant permission for modification, derivation, or commercial use of this content." The **exponentii.org robots.txt** has a Cloudflare content-signal block, `User-agent: * / Content-Signal: search=yes,ai-train=no,use=reference / Allow: /`, defined as "search: building a search index and providing search results (e.g., returning hyperlinks and short excerpts…)". It also has explicit `Disallow: /` for ClaudeBot, anthropic-ai, GPTBot, CCBot and others. The archive.org copy is governed by archive.org's robots.txt (permissive).

**Harvest route.** archive.org advancedsearch (`collection:exponentiibrighamyounguniv`) plus `/metadata/<id>`, downloading `_djvu.txt` only (small).

**Recommendation: include later, priority 4.** Lectern's link-only use (search index, short excerpts, links) matches exactly what their `search=yes` signal permits, and the ban is on AI training, which we don't do. It isn't core scholarship, though. If included, index from the archive.org OCR and never use their own site for bulk fetching.

---

## 9. Other independent journals worth knowing

### Interpreter: A Journal of Latter-day Saint Faith and Scholarship (Interpreter Foundation)
- **What it is.** Peer-reviewed ([peer review](https://interpreterfoundation.org/peer-review): "Articles that appear in Interpreter are required to undergo a peer-review process before they are accepted"). Founded in 2012 by Daniel C. Peterson and others, and now at volume 70 (2026). Apologetic in stance, with heavy Book of Mormon, Bible and ancient Near East content. **Very relevant to biblical scholarship.** `journal-sitemap.xml` lists **926 URLs**.
- **Free.** Everything, as HTML pages plus per-article PDFs on a CDN.
- **Format.** Example https://interpreterfoundation.org/journal/melchizedek-in-extra-biblical-sources-and-in-joseph-smiths-revelations has about 9,500 words of HTML. Its PDF is https://cdn.interpreterfoundation.org/jnlpdf/ahlstrom-v70-2026-1-24-PDF.pdf (downloaded, 28 pages): PDF page 4 = printed p. 2, offset +2. The site was recently rebuilt in Next.js and `journal.interpreterfoundation.org` now redirects to `interpreterfoundation.org/journal`. **Old URLs moved once**, so watch for stability.
- **Licence.** [Copyrights](https://interpreterfoundation.org/foundation/copyrights/): "All content posted on The Interpreter Foundation's websites is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License… you may freely share, copy, and redistribute any and all content… no need to ask permission from us." The PDF says: "© 2026 The Interpreter Foundation… This work is licensed under a Creative Commons Attribution — NonCommercial — NoDerivs".
- **robots.txt** (https://interpreterfoundation.org/robots.txt): `Disallow: /` for AhrefsBot, PetalBot, AwarioSmartBot, **CCBot, ClaudeBot, OAI-SearchBot, PerplexityBot, GPTBot, bingbot**. `User-agent: *` gets `Allow: /` with only `/api`, `/_next` and `/search` disallowed.
- **Harvest.** Sitemaps; the PDF link is on each article page. No DOIs and no citation meta tags.
- **Recommendation: include now, priority 1.** It is a large, free, CC-licensed, scripture-heavy archive. Link-only is plainly fine. Under NC-ND, hosting verbatim copies non-commercially is also permitted, so it could go in the open tier if we widen the open tier to NC-ND. The ClaudeBot and AI-bot blocks show the foundation dislikes AI crawlers. Our harvester isn't one of those bots, but set a clear non-AI user agent and crawl slowly.

### International Journal of Mormon Studies (2008–2013) and Journal of the Mormon Social Science Association (2023–)
- IJMS was European and peer-reviewed. Its 6 volumes are hosted at https://jmssa.org/ijms: "IJMS published six volumes between 2008 and 2013 and generously allowed for free distribution of articles under a CC BY-NC-ND 2.5 license." Whole-volume PDFs: https://jmssa.org/wp-content/uploads/IJMS-VOLUME01.pdf through `VOLUME06.pdf` (HEAD 200, 3.5 MB).
- JMSSA has DOIs under 10.54587 (27 Crossref records, e.g. 10.54587/jmssa.0111 → https://jmssa.org/volume-1/1-jenkins/). Footer: "This work is licensed under CC BY-NC-ND 4.0."
- robots.txt: standard WordPress.
- **Recommendation: include now, priority 3.** It is small and clean, with the same CC BY-NC-ND note as Interpreter.

### Mormon Studies Review
- Published by UIP since 2014 (996 Crossref DOIs across MSR and the older FARMS Review), paywalled, so **skip**.
- The predecessor *FARMS Review* / *Mormon Studies Review* vols 1–23 (1989–2011) is free on BYU ScholarsArchive (https://scholarsarchive.byu.edu/msr/; OAI `set=publication:msr`, `metadataPrefix=dcs` returned 100 records on page 1). It belongs with whoever is covering BYU and Maxwell Institute sources.

### Claremont Journal of Mormon Studies
- A student journal, 2011–2013. Only the inaugural issue is on https://mormonstudies.cgu.edu/students/student-writings/journal/, as a print-edition link with no PDF in the page HTML. **Skip.**

### Restoration Studies
- Community of Christ (Temple School, later Seminary with JWHA), 1980 on, now merged into the JWHA Journal. I found no free archive: the Community of Christ Library catalog lists print volumes only, and the JWHA Drive has only a members-only TOC folder. **Skip**, and revisit if JWHA posts it.

### Journal of Latter-day Saint History
- I found no journal by that exact title. The closest is *Latter-day Saint Historical Studies* (section 4). BYU's *Journal of Book of Mormon Studies*, *BYU Studies Quarterly* and *Religious Educator* are on BYU ScholarsArchive (`/jbms/` and `/byusq/` return 200). They are not independent, so I assume they're covered elsewhere.

---

## Verified vs not verified

**Verified:**
- Robots files for every site.
- REST counts for Dialogue and Sunstone.
- OAI endpoints at USU and U of Utah.
- Licence and copyright text as quoted.
- Sample PDFs and their page offsets: Dialogue (2), Sunstone (1), MHS (1), JWHA (1), Interpreter (1).
- The Drive folder listings.
- The archive.org collection stats.
- The broken Sunstone index and its Wayback copy.

**Not verified:**
- The JMH USU PDF page offsets and file sizes (Cloudflare challenge).
- JSTOR coverage and moving walls for Dialogue, JMH and JWHA (JSTOR pages don't render for curl or WebFetch).
- Whether Google Drive's viewer honours `#page`.
- Whether Dialogue's recent per-article PDFs (e.g. `V59N02_1.pdf`, 360 KB) hold the whole article.
- UHQ copyright renewals for 1931–1963.
- Interpreter's terms of service (no ToS page found in its sitemap).
- Peer-review status for MHS and JWHA (not stated on their sites).
