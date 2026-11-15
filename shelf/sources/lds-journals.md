# LDS journals for Lectern's link-only tier

Research date: 2026-11-15. All fetches made with curl and a generic desktop-browser user agent, plus a few web searches. No forms, no contact, nothing sent about us. Samples downloaded: 2 PDFs per source at most (listed under each source). "Verified" means I fetched the page or file and saw it myself; anything else is marked as unverified.

## Summary table

| Source | What's free | Licence | Harvest route | Recommendation |
|---|---|---|---|---|
| BYU Studies Quarterly (byustudies.byu.edu) | Everything, vols 1–64 (1959–2025), current issues included | No licence or terms stated; no CC | sitemap.xml + article page → PDF on S3 | **Include now, priority 1**, link-only, harvest from byustudies.byu.edu (not ScholarsArchive) |
| Interpreter (interpreterfoundation.org/journal) | Everything, vols 1–69 (2012–2026) | **CC BY-NC-ND 4.0** site-wide | journal-sitemap.xml; HTML has `[Page N]` markers; Crossref DOIs | **Include now, priority 1.** Could go in the open tier if Lectern is non-commercial, **but robots.txt blocks ClaudeBot/GPTBot/CCBot etc.** Send a heads-up email first |
| Element (SMPT) | Everything: 2005–2019 archive + 2024– relaunch | Authors assigned copyright to SMPT (now defunct); no CC | WordPress REST API on element.wcu.edu; Dialogue issue PDFs; Kofford PDFs | **Include now, priority 2** (small, high value for theology) |
| Maxwell Institute titles on ScholarsArchive (JBMS, FARMS Review/MSR, Insights, SBA, MI books) | Full text free to read on ScholarsArchive | None stated | OAI-PMH works, but **its data policy bans robot harvesting of full content without written approval**, and PDFs sit behind a Cloudflare bot challenge | **Include later. Ask ScholarsArchive (HBLL) first**: that one approval unlocks this row and the next |
| BYU Religious Studies Center (rsc.byu.edu): Religious Educator + RSC books | RE 2000–2026 all free in HTML; most RSC books readable online by chapter | "© 2022 All rights reserved" | Plain crawl (no sitemap); HTML only | **Include now, priority 2**, link-only, but citations only reach the article's page range (no page markers) |
| Studia Antiqua and other BYU religion journals on ScholarsArchive | Free to read | None stated | Same ScholarsArchive constraint | **Include later** with the ScholarsArchive approval; priority 3 |

The main finding: **BYU ScholarsArchive's OAI-PMH Identify response says "Full content may not be harvested by robots without prior, written approval of BYU ScholarsArchive."** Its robots.txt also disallows `/do/` (the OAI path), and every PDF download returned a Cloudflare challenge to curl. So we shouldn't privately index anything from ScholarsArchive until we have written approval. Metadata is fine to use ("Metadata can be used by commercial and non-commercial service providers"). The good news is that BYU Studies, Interpreter and Religious Educator all have their own sites, so we don't need ScholarsArchive for them.

---

## 1. BYU Studies Quarterly

**What it is.** Published by BYU Studies at Brigham Young University since 1959. It's a peer-reviewed, interdisciplinary journal ("publishes scholarship that is informed by the restored gospel of Jesus Christ", from the [about page](https://byustudies.byu.edu/about)). It's the most established LDS academic journal, and very relevant: Church history, scripture, theology and Christian/biblical topics, plus poetry, art and book reviews. It covers vols 1–64 (1959–2025), with issue 64:3 the latest on the main site. Size:
- The main site's [sitemap](https://byustudies.byu.edu/sitemap.xml) lists 8,200 URLs, including 3,861 `/article/` pages and 243 `/issue/` pages.
- ScholarsArchive's OAI set `publication:byusq` reports `completeListSize="4341"`. That count includes front matter, poems and reviews.
- So expect roughly 3,800–4,300 items, of which perhaps 2,000+ are substantive articles.

**Free vs paywalled.** Everything is free, including the current issues. I verified that 64:1, 63:4 and 64:2 article pages serve full HTML text and PDF links with no login. The ScholarsArchive "About" page still says "To read recent content, purchase a subscription", but that's out of date: ScholarsArchive itself holds up to 64:2 and the main site holds 64:3.

**Full-text format.**
- The main site is Next.js. Each article page has the full text in HTML for most articles: 11 of 15 sampled pages had it. Older pieces instead say "We're working on digitizing this article's content. Please use the PDF version." The HTML has **no printed-page markers**.
- Each article has one PDF, hosted on BYU Studies' S3 bucket `website-files-bucket.s3.us-west-2.amazonaws.com/articles/article_pdfs/…`.
- **PDF page 1 = the printed start page.** I verified this on Pyper, 64:1, printed pp. 21–44 = 24 PDF pages, and on Riddle, 16:4, which starts at printed p. 485 on PDF p. 1. So `#page=N` maps to printed page = start + N − 1.
- Older PDFs are scans with a poor OCR layer (lower-cased text, "1I wish …"). Plan to re-OCR them before quote-checking.
- PDF filenames are made from titles and contain spaces, apostrophes, curly quotes and HTML entities. Two of 15 sampled links needed entity-decoding to resolve. Article page URLs are clean slugs (`/article/<slug>`) and look stable.
- Example URLs checked:
  - https://byustudies.byu.edu/article/not-only-men-but-women-also-an-argument-for-almas-intentional-inclusion-of-women → https://website-files-bucket.s3.us-west-2.amazonaws.com/articles/article_pdfs/64-1-03Pyper.pdf (downloaded; 24 pp., InDesign, clean text)
  - https://byustudies.byu.edu/article/a-byu-for-zion → https://website-files-bucket.s3.us-west-2.amazonaws.com/articles/article_pdfs/A_BYU_for_Zion.pdf (downloaded; 16 pp., scanned)

**Licence and terms.**
- I found no licence, copyright statement or terms of use on the site. The [about](https://byustudies.byu.edu/about) and [submissions](https://byustudies.byu.edu/submissions) pages say nothing about rights, and `/terms`, `/terms-of-use`, `/copyright` and `/permissions` all 307-redirect to the home page. The footer reads only "© 2026" plus a link to the BYU [privacy notice](https://privacy.byu.edu/privacy-notice). Neither sampled PDF has a copyright line. Nothing is under CC; treat it as all rights reserved by BYU Studies/BYU.
- [robots.txt](https://byustudies.byu.edu/robots.txt) in full:
  ```
  User-agent: *
  Disallow:
  Sitemap: https://byustudies.byu.edu/sitemap.xml
  ```
- No ai.txt or llms.txt; both redirect to home.
- The copy on ScholarsArchive falls under the ScholarsArchive harvesting ban (see section 4).

**Harvest route.**
- Walk the sitemap's `/article/` URLs, take the PDF link from each page, and fetch the PDF from S3.
- There's no public API. The site has no `citation_*` meta tags, but the visible page gives authors, "BYU Studies 64:1", the start page, topics and scripture references.
- For clean metadata, use the ScholarsArchive OAI-PMH feed. Metadata use is explicitly allowed there: `https://scholarsarchive.byu.edu/do/oai/?verb=ListRecords&metadataPrefix=oai_dc&set=publication:byusq`. It gives title, creator, date, type, a peer_reviewed flag, ISSN, and a ScholarsArchive URL that encodes vol/iss. ScholarsArchive landing pages carry `bepress_citation_firstpage`, `_volume` and `_issue`.
- Download size: 13 sampled PDFs ranged from 27 KB to 6.7 MB, mean about 1.4 MB, so roughly **5–6 GB** for about 4,000 PDFs.

**Metadata.** Authors, year, volume:issue and start page are all available. No DOIs: Crossref has no record of ISSN 2167-8472 or 2167-8480.

**Recommendation: include now, priority 1, link-only.**
- Harvest from byustudies.byu.edu and S3, never from ScholarsArchive. Nothing on the site forbids indexing or text mining, and robots.txt allows everything.
- For the button, use the S3 PDF with `#page=N`: it's the publisher's own file, though on an AWS hostname. Fall back to the article page with a text fragment where the HTML exists.
- Optional courtesy: a short note to byustudies@byu.edu describing the link-only model. Not required by anything I found.
- Later, also worth looking at: the 36 free "online books" on the same site, such as the BYU New Testament Commentary volumes, *History of the Church* vols 1–7 and *The Journals of William E. McLellin*. They're listed in the sitemap under `/online-book/`. I didn't research them further.

---

## 2. Interpreter: A Journal of Latter-day Saint Faith and Scholarship

**What it is.** Published by the Interpreter Foundation, an independent 501(c)(3) that is not affiliated with the Church. It describes itself as "the academic, peer-reviewed journal of The Interpreter Foundation" ([ScholarsArchive page](https://scholarsarchive.byu.edu/interpreter/)). It runs from 2012 to now: vols 1–69 (2026), with a vol. 70 (2027) placeholder already in the volume sitemap.
- Its [journal-sitemap.xml](https://interpreterfoundation.org/journal-sitemap.xml) lists **926** article URLs, including book reviews.
- The content is apologetic in orientation, centred on the Book of Mormon, scripture, temple and ancient Near East themes. Quality is uneven, but it's highly relevant and much cited in LDS discussion.
- The old host journal.interpreterfoundation.org now redirects to interpreterfoundation.org/journal. The site moved from WordPress to Next.js.

**Free vs paywalled.** Everything is free. The site footer says "All journal publications and video presentations are available for free by digital download and streaming." I verified vols 1 and 68.

**Full-text format.**
- Each article page has the full text in HTML with **`[Page N]` markers inline**. That's ideal for text-fragment links: for example, 21 markers on a 22-page article.
- One PDF per article, as an offprint. Also EPUB, Kindle and MP3. Files sit on `cdn.interpreterfoundation.org` (S3), and the PDF filenames encode the pages: `grandy-v68-2026-421-442-PDF.pdf`.
- Each offprint PDF has **2 front pages** (cover and licence page), so printed page P sits at PDF page P − start + 3. I verified this: Wright & Gardner, printed p. 25, is on PDF p. 3.
- URLs: `https://interpreterfoundation.org/journal/<slug>`. The old URLs still resolve (`journal.interpreterfoundation.org/<slug>/` → 301 → 308 → 200, verified), so slugs survived the migration.
- Example URLs checked:
  - https://interpreterfoundation.org/journal/the-cultural-context-of-nephite-apostasy → https://cdn.interpreterfoundation.org/jnlpdf/wright-gardner_v1_i1_2012_pg25-55-PDF.pdf (downloaded; 36 pp.)
  - https://interpreterfoundation.org/journal/color-in-the-book-of-mormon → https://cdn.interpreterfoundation.org/jnlpdf/grandy-v68-2026-421-442-PDF.pdf (HEAD only; 2.3 MB)

**Licence and terms.**
- From the [Copyrights page](https://interpreterfoundation.org/foundation/copyrights/), which the footer's "Terms of Service" link also points to: "All content posted on The Interpreter Foundation's websites is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License. … no need to ask permission from us."
- The 2012 PDF itself says: "This work is licensed under the Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported License."
- So **every article is CC BY-NC-ND**. That allows verbatim, attributed, non-commercial redistribution, which makes the open tier possible if Lectern is non-commercial and serves the files unaltered.
- [robots.txt](https://interpreterfoundation.org/robots.txt) blocks named AI and SEO crawlers outright:
  ```
  User-agent: CCBot      Disallow: /
  User-agent: ClaudeBot  Disallow: /
  User-agent: OAI-SearchBot Disallow: /
  User-agent: PerplexityBot Disallow: /
  User-agent: GPTBot     Disallow: /
  User-agent: bingbot    Disallow: /
  (also AhrefsBot, PetalBot, AwarioSmartBot, SemrushBot, YandexBot)
  User-agent: *
  Allow: /
  Disallow: /api  /_next  /search  (and /es, /fr, /pt-pt variants)
  ```
- The licence permits what we'd do. But the robots.txt is a clear signal that they don't want AI-company crawlers. A Lectern crawler is technically "*", but it should identify itself honestly rather than hide behind a browser UA.
- No ai.txt or llms.txt (404). The page's robots meta is `index,follow`.

**Harvest route.**
- Sitemap index at https://interpreterfoundation.org/sitemap.xml → `journal-sitemap.xml` (926) and `volumes-sitemap.xml` (70). Then the article HTML, which includes the PDF link.
- No OAI and no public API; robots.txt disallows `/api`.
- **Crossref**: Interpreter is Crossref member 56888 with prefix 10.67160. It has 388 DOIs so far, all vols from 2012–2018, and each DOI resolves to the article page. The API (`https://api.crossref.org/prefixes/10.67160/works`) gives authors, volume, pages and date.
- Completed volumes 1–65 are also on ScholarsArchive. The OAI set `publication:interpreter` returned 0 records, and ScholarsArchive's harvest ban applies there anyway.
- Size: PDFs are 0.35–2.3 MB, so about **1–1.5 GB** for all of them. The HTML alone is much smaller.

**Metadata.** The page gives authors, volume, year and page range ("68 (2026) : 421-442"). Crossref DOIs cover 2012–2018, with more presumably coming.

**Recommendation: include now, priority 1.**
- The best technical fit of any source here: HTML with page markers, a licence that explicitly permits sharing, stable slugs and a sitemap.
- Before bulk-fetching, **send a short heads-up email** through their contact page. Do this because of the AI-crawler blocks, not because the licence requires it.
- Fetch politely under an honest Lectern user agent.
- The open tier is legally available under CC BY-NC-ND if Lectern is non-commercial. Link-only is the low-friction default.

---

## 3. Element: The Journal of the Society for Mormon Philosophy and Theology

**What it is.**
- **smpt.org is dead.** It's a parked Bluehost page (verified; HTTPS doesn't connect, and HTTP serves a Bluehost "Welcome smpt.org" ad page). The Society is defunct.
- *Element* ran from 2005 to 2019: vols 1–8, about 14 issues and about 60–70 articles. Its editorial statement says submissions were subject to blind review. The editors were Brian D. Birch and Loyd Ericson.
- It was relaunched in 2024 as *Element: A Journal of Mormon Philosophy and Theology*, "a continuation of the journal that was sponsored by the former Society", hosted by Greg Kofford Books. That's vols 9–10 (2024–2025), with two issues in 2025.
- Small, but the main venue for LDS philosophy and theology (Ostler, Faulconer, Paulsen, Millet, Mouw and others).

**Where it lives (all free).**
- **element.wcu.edu** (WordPress, "In association with Western Carolina University"): **51 per-article PDFs** covering vols 1–7, listed by `https://element.wcu.edu/wp-json/wp/v2/media`. Also 8 HTML posts for vols 1–2. The issue pages render as empty shells.
- **dialoguejournal.com**: "The Dialogue Foundation is proud to host the archives of Element … which ran from 2006-2019." 13 whole-issue PDFs at `/wp-content/uploads/sbi/articles/E1_1.pdf` … `E7.pdf`, `E8.pdf` (HEAD-checked, 0.75–5.5 MB each). Pages are listed in Dialogue's WP search, for example https://www.dialoguejournal.com/articles/element-volume-4-issue-1/
- **Greg Kofford Books** (Shopify): the [Element is back](https://gregkofford.com/blogs/news/element-is-back) post says they are "making all issues available for free digital downloads". PDFs sit on `cdn.shopify.com/s/files/1/0266/2257/files/…`, for example element_10.1.pdf, which I downloaded (110 pp.). The `/collections/element` page and Shopify's products.json both returned **HTTP 429** to scripted requests, so I couldn't list every issue.

**Full-text format.**
- Text PDFs. The wcu per-article PDFs start at printed page 1 for the first article: Green, "Got Compassion?", v4.1, is printed p. 1 on PDF p. 1.
- The Dialogue issue PDF E4_1 has **8 front pages**: printed p. 1 = PDF p. 9 (verified). Running heads read "Element Vol. 4 Issue 1 (Spring 2008) N".
- wcu upload URLs (`/wp-content/uploads/2018/10/…`) have been stable since 2018.
- Example URLs checked:
  - https://element.wcu.edu/wp-content/uploads/2018/10/v4.1-01Green.pdf (downloaded; 22 pp.)
  - https://www.dialoguejournal.com/wp-content/uploads/sbi/articles/E4_1.pdf (downloaded; 104 pp.)

**Licence and terms.**
- From E4_1's front matter: "It is a condition of publication in Element that authors assign copyright to the Society for Mormon Philosophy and Theology." That rights holder no longer exists.
- Dialogue's site footer: "Copyright © 2026 The Dialogue Journal. All rights reserved."
- element.wcu.edu footer: "© 2005-2018 | In association with Western Carolina University".
- Kofford calls it "the open-source journal" but names no licence.
- No CC licence anywhere.
- robots.txt:
  - element.wcu.edu: `Disallow: /wp-admin/` only, plus `Sitemap: https://element.wcu.edu/wp-sitemap.xml`.
  - dialoguejournal.com: returns 200 with an empty body.
  - gregkofford.com: `Disallow: /.well-known/shopify/monorail` plus shopping-agent instructions (agents.md). Nothing on text mining, but Shopify rate-limits.

**Harvest route.** The WordPress REST API on element.wcu.edu for the archive PDFs; the Dialogue WP search API for the issue pages; Kofford product pages, fetched slowly by hand, for vols 9–10. Total under **100 MB**.

**Metadata.** Volume, issue and author come from filenames and Dialogue page titles. ISSN 1947-9719. No DOIs.

**Recommendation: include now, priority 2.**
- Small and quick to do, with unique theological content.
- Link to the wcu per-article PDF where one exists (offset 0). Otherwise link to the Dialogue issue PDF with a per-issue page offset, and to Kofford for 2024+.
- Low risk. Optionally ask the current editors (elementjournal@gmail.com, printed in 10.1) whether they'd like the open tier, since Kofford already calls it open.

---

## 4. Maxwell Institute titles on BYU ScholarsArchive

All of these are in ScholarsArchive (Elsevier Digital Commons). OAI record counts are from `ListIdentifiers` `completeListSize`.

| Collection | ScholarsArchive set | Coverage on ScholarsArchive | Records |
|---|---|---|---|
| *Journal of Book of Mormon Studies* (incl. *Journal of the Book of Mormon and Restoration Scripture*) | `jbms` | vols 1–28 (1992–2019), full text including vols 26–28 | 628 |
| *Review of Books on the Book of Mormon* / *FARMS Review* / *Mormon Studies Review* (old series) | `msr` | vols 1–23 (1989–2011) | 788 |
| *Mormon Studies Review* (new series) | `msr2` | vols 1–10 (2014–2023) | 268 |
| *Insights* (Maxwell Institute newsletter) | `insights` | vols 1–32 (1981–2023) | 1,374 |
| *Studies in the Bible and Antiquity* | `sba` | vols 1–8 (2009–2016) | 0 in OAI (the web pages exist) |
| Maxwell Institute Publications (books, e.g. *A Preparatory Redemption*, *Christ and Antichrist*, *To Be Learned is Good*) | `mi` | gallery of books | 0 in OAI |

**Quality and relevance.** JBMS and SBA are peer-reviewed. JBMS is the main Book of Mormon studies journal; SBA covers Bible and antiquity. The old FARMS Review is polemical and apologetic but historically important. MSR (2014–) is a strong academic review journal. *Insights* is a newsletter, so low value.

**Paywalled elsewhere.**
- JBMS vols 27–32 (2018–2023) and MSR from 2018 were published by University of Illinois Press, on Scholarly Publishing Collective and JSTOR. Crossref shows 676 JBMS DOIs (1992–2023) and 996 MSR DOIs (1989–2026), with the backfile carrying JSTOR `10.2307/…` DOIs that resolve to `scholarlypublishingcollective.org`.
- I could not check access there: Cloudflare challenged curl.
- UIP's journal page reportedly says it no longer publishes JBMS (from a web-search summary, not fetched).
- MSR continues at UIP (vol. 13, 2026, per Crossref).
- ScholarsArchive holds free copies through JBMS 2019 and MSR 2023.
- **SBA's DOIs (10.18809) are broken**: they resolve to `publications.mi.byu.edu`, which doesn't connect (verified).

**Format.** One PDF per article via `/cgi/viewcontent.cgi?article=N&context=jbms`. Landing pages carry `bepress_citation_*` meta (author, title, date, volume, issue, firstpage, pdf_url) and `bepress_is_article_cover_page=1`, which means Digital Commons likely **prepends a cover page, so `#page=N+1`**. I couldn't confirm this because PDFs are challenge-blocked. URLs (`/jbms/vol28/iss1/2`) are stable Digital Commons paths.
- Examples checked (landing pages only):
  - https://scholarsarchive.byu.edu/jbms/vol28/iss1/2/
  - https://scholarsarchive.byu.edu/msr/vol23/iss1/3/

**Licence and terms.**
- No licence is shown on any landing page. The OAI qdc records carry no rights field.
- The footer "Copyright" link points to Elsevier's website T&C (https://www.elsevier.com/legal/elsevier-website-terms-and-conditions).
- The `mi` [policies page](https://scholarsarchive.byu.edu/mi/policies.html) is an unfilled Digital Commons template ("[INSERT LOCATION OF AGREEMENT…]").
- **OAI Identify** (https://scholarsarchive.byu.edu/do/oai/?verb=Identify):
  - metadataPolicy: "Metadata can be used by commercial and non-commercial service providers"
  - dataPolicy: **"Full content may not be harvested by robots without prior, written approval of BYU ScholarsArchive."**
- [robots.txt](https://scholarsarchive.byu.edu/robots.txt) disallows a long list of `/cgi/*.cgi` admin scripts, plus `Disallow: /do/` (which includes the OAI endpoint) and `Disallow: /fe-journals/`. It blocks `^Byte` entirely. Sitemaps: `/siteindex.xml` and `/exhibit/sitemap.xml`.
- PDF downloads return `403` with `cf-mitigated: challenge` (Cloudflare) to scripted clients (verified twice). I did not try to get past it.

**Harvest route.** OAI-PMH works: Identify, ListSets (358 sets) and ListIdentifiers all tested. Formats offered: oai_dc, qdc/dcq, oai_etdms, oai_openaire. Metadata is fine to harvest; full text needs approval.

**Recommendation: include later. Ask ScholarsArchive (Harold B. Lee Library) for written approval first. Priority 1 to ask.** One approval would cover JBMS, both MSR series, SBA, MI books, Religious Educator PDFs, Studia Antiqua and the rest, roughly 5,000+ items. Meanwhile we could load metadata-only records from OAI, which is explicitly allowed, but without text there's nothing to index. Tell them plainly: private index, 300-character snippets, link-out only, an identified crawler, and a crawl rate of their choosing. Skip *Insights* or give it low priority.

---

## 5. BYU Religious Studies Center (rsc.byu.edu): *Religious Educator* and RSC books

**What it is.** The RSC is the publishing arm of BYU Religious Education.
- *Religious Educator: Perspectives on the Restored Gospel* (2000–present): the [issue index](https://rsc.byu.edu/religious-educator) lists 77 issues, vol. 1 no. 1 (2000) to vol. 27 no. 2 (2026). ScholarsArchive has 1,042 records. Audience: teachers of religion (BYU, Seminaries and Institutes). The content mixes scripture, Church history, pedagogy, interviews and apostolic addresses. Useful, but lighter than BYU Studies. I didn't find a peer-review statement.
- RSC books: [/books/all](https://rsc.byu.edu/books/all) lists 294 books, including the annual Sidney B. Sperry Symposium volumes and Church-history and scripture volumes. In a sample of 12, **10 were readable online** in HTML by chapter. Newer ones say "This book has not been released for online reading" (e.g. *Genesis: A New English Translation*).

**Free vs paywalled.** All *Religious Educator* articles are free in HTML, including 2026 (verified vol. 27 no. 2). Most books are free; the newest are print-only.

**Full-text format.**
- Drupal HTML pages only. No PDFs on the site, apart from book press releases. **No printed-page markers.**
- Each page has a "Show Citation" block giving the page range: e.g. "*Religious Educator* 26, no. 2 (2025): 75–94"; or for a book chapter, "… ed. Truman G. Madsen (Provo, UT: Religious Studies Center, 1984), 135–50".
- So we can cite to the article or chapter page range, not to the exact page. Text-fragment links work on the HTML.
- Page-accurate PDFs of *Religious Educator* exist only on ScholarsArchive (see section 4).
- Example URLs checked:
  - https://rsc.byu.edu/vol-26-no-2-2025/visions-salvation
  - https://rsc.byu.edu/temple-antiquity/jachin-boaz-religious-political-perspective

**Licence and terms.** The footer on every page reads "© 2022 All rights reserved". There's no terms-of-use page (`/terms-use`, `/terms-of-use`, `/copyright` and `/permissions` all 404) and no CC. [robots.txt](https://rsc.byu.edu/robots.txt) is the stock Drupal file: it disallows `/admin/`, `/search/`, `/user/*`, `/node/add/` and the core/profile directories. Nothing about AI or text mining. No sitemap (`/sitemap.xml` 404s). The site runs Drupal's antibot module on forms.

**Harvest route.** Plain crawl:
- `/religious-educator` → issue pages (`/religious-educator/vol-26-no-2-2025`) → articles (`/vol-26-no-2-2025/<slug>`).
- `/books/all` → `/book/<slug>` → chapters (`/<book-slug>/<chapter-slug>`).

The HTML is light. Estimate about 1,000 RE articles plus about 3,000–4,000 book chapters, **well under 1 GB**.

**Metadata.** The citation string on each page gives authors, volume, number, year and pages, or book, editor and pages for chapters. No `citation_*` meta tags and no DOIs.

**Recommendation: include now, priority 2, link-only**, with citations at the page-range level. If ScholarsArchive approves, swap in the RE PDFs for exact-page citations.

---

## 6. Studia Antiqua and other BYU religion collections on ScholarsArchive

- **Studia Antiqua** (`studiaantiqua`): BYU's student journal of ancient studies, covering the Bible, the ancient Near East, Egypt and early Christianity. Vols 1–24 (2001–2025), 316 records. Good metadata (`bepress_citation_firstpage`, volume, issue, author). Example: https://scholarsarchive.byu.edu/studiaantiqua/vol24/iss1/3/. Student work, so modest quality, but on-topic for Christian and biblical scholarship.
- **Religion in the Age of Enlightenment** (`rae`): peer-reviewed annual, 2009–2015, 126 records. Good for Christian intellectual history.
- **Issues in Religion and Psychotherapy** (`irp`, formerly *AMCAP Journal*): 1975–, 615 records. Peer-reviewed, but mental-health-focused.
- Also present: Religious Education faculty publications (`religion`, 1,500), Ancient Scripture faculty publications (457), Church History and Doctrine faculty publications (215) and Theses on Mormonism (784). These mix in publisher versions whose rights vary item by item.

**Recommendation: include later**, under the same ScholarsArchive approval. Studia Antiqua and RAE are priority 3; the rest are low.

---

## Verified vs not verified

**Verified by fetching:**
- robots.txt for every host.
- BYU Studies: sitemap counts, full text on current issues, PDF page alignment on 2 PDFs, no licence pages, PDF size sample.
- Interpreter: CC BY-NC-ND (page and PDF), AI-bot blocks, `[Page N]` markers, the PDF +2 offset, redirects from old URLs, and Crossref DOIs.
- smpt.org parked; Element hosts and PDF lists; Element offsets and the copyright-assignment line.
- ScholarsArchive: OAI Identify, the data policy, set counts, Cloudflare blocking of PDFs, and bepress meta tags.
- RSC: free HTML, citation blocks, no page markers, the copyright footer, and the sampled book availability.
- The broken SBA DOI host.

**Not verified:**
- The ScholarsArchive cover-page offset, since the PDFs were blocked and I didn't try to get past the challenge.
- Access status on Scholarly Publishing Collective (Cloudflare).
- The full list of Kofford Element issues (HTTP 429).
- Exact article counts for RSC books (only sampled).
- Peer-review status of *Religious Educator*.
- Whether UIP still publishes JBMS (from a search summary only).
