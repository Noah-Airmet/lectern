# What Lectern links to

The plan for adding scholarship beyond the public-domain books, decided 2026-11-15 from a
research pass over about forty sources. The notes behind it, with every URL, quoted licence,
robots.txt line and example article, are in [`sources/`](sources/):
[LDS journals](sources/lds-journals.md), [independent LDS journals](sources/independent-journals.md),
[primary sources](sources/primary-sources.md), [open religious-studies journals](sources/open-journals.md).

Two tiers, from the engine (Catchword's `docs/ARCHITECTURE.md`, section 6):

- **Open:** public domain, CC BY, CC BY-SA, CC0. Hosted in full with page images, like the books.
- **Link only:** everything else that is free to read. Indexed in full from a private copy;
  the public sees search hits, snippets up to 300 characters, quote checks up to 40 words, the
  record, and "Read at source", which opens the publisher's own page (`#page=N` on a PDF).
  NC and ND licences fall here too, under the engine's rule.

## Permissions

What we've been told, 2026-11-15:

- **Interpreter:** Daniel C. Peterson is happy for Lectern to index and link it.
- **BYU ScholarsArchive:** written approval is being arranged with the people who run it;
  harvesting starts now and is deleted if the answer is no.
- **Scripture Central:** its people are happy to have its work searchable here.
- **Joseph Smith Papers and Church Historian's Press:** not until permission is confirmed.
- **Utah State DigitalCommons:** no contact yet; left for later.

## First: free to read, nothing stops us

| Source | Tier | Size | Notes |
|---|---|---|---|
| BYU Studies Quarterly | link only | ~4,000 articles, 1959– | From byustudies.byu.edu (sitemap → article → PDF), not ScholarsArchive. PDF page 1 is the printed start page. No licence statement; robots.txt allows all. Pre-2000 scans need re-OCR. ~5–6 GB. |
| Dialogue | link only | ~5,000 articles, 1966– | WordPress API lists every article; Crossref DOIs. Printed page = PDF page + an offset read from the running heads. Its policy page carries a bare "CC BY-NC-ND". Brings Element's issues with it. |
| Element (SMPT) | link only | ~65 articles, 2005–2019 | 51 article PDFs at element.wcu.edu, the rest as Dialogue-hosted issues. Society defunct. |
| Mormonr Q&As (B. H. Roberts Foundation) | link only | 86 Q&As | Plain HTML with footnote anchors; robots.txt allows all. |
| Religious Educator and RSC books | link only | ~1,000 articles + books | HTML, no page markers, so citations give the article's page range. Plain crawl, under 1 GB. |
| Sunstone | link only | issues 1–164, 1975–2011 | Article PDFs whose filenames carry the printed pages. The site's index is broken; titles come from a 2024 Wayback copy. |
| Mormon Historical Studies | link only | 506 articles, 1989–2014 | Per-article PDFs on ensignpeakfoundation.org. |
| Tyndale Bulletin | link only | 913 articles, 1956– | Terms for 2020 and earlier allow crawling for non-commercial indexing. |
| Church History Library's uploads to the Internet Archive, pre-1931 | open | ~9,200 items | Millennial Star, Juvenile Instructor, Improvement Era to 1930, The Contributor, Conference Reports. OCR and page numbers included. A blanket "© Intellectual Reserve" label sits on even 1881 issues; the issues themselves are public domain. |
| JSTOR Early Journal Content, religion titles | open | ~16,000 articles, 1881–1922 | JBL, Biblical World, American Journal of Theology, HTR, Hebraica/AJSL, JQR. JSTOR allows non-commercial redistribution with "Courtesy of JSTOR". |
| Journal of Hebrew Scriptures, Hugoye, Journal of the Jesus Movement in its Jewish Setting, Old Testament Essays | open (CC BY) | ~2,300 articles | Working OAI feeds; Hugoye also has clean XML text. |

## Next: one note to the owner first

Each is worth having; each has a sign that the owner should hear from us before we harvest.

| Source | Why ask | What it opens |
|---|---|---|
| Interpreter | CC BY-NC-ND, but robots.txt blocks ClaudeBot, GPTBot, OAI-SearchBot, PerplexityBot and bingbot. Lectern answers AI assistants over MCP, so a heads-up is the honest course. | ~926 articles, 2012–, HTML with `[Page N]` markers |
| BYU ScholarsArchive | Its harvest interface says full content "may not be harvested by robots without prior, written approval". | One approval covers ~5,000 items: Journal of Book of Mormon Studies 1–28, FARMS Review and Mormon Studies Review to 2023, Studies in the Bible and Antiquity, Studia Antiqua, Religion in the Age of Enlightenment, Religious Educator PDFs |
| B. H. Roberts Foundation archive | 12,321 records, but each is an excerpt (often from an in-copyright book) for "non-commercial personal research". | Ask for a metadata export only (bibliography, date, subject, Q&A, link). Lectern shows "Mormonr cites this page"; the ~5,100 pre-1931 sources become a list of books to add. |
| Utah State DigitalCommons | Journal of Mormon History 1974–2014: robots.txt blocks the OAI endpoint and PDFs sit behind a bot challenge. | 80 issues |
| Scripture Central KnoWhys | robots.txt comments "Block all other crawlers" without a rule. | ~2,450 KnoWhys, 734 Evidence pages |
| Joseph Smith Papers, Church Historian's Press | The Church's terms forbid robots. A long shot, but the most valuable primary source there is. | Page-level transcripts |
| Wilford Woodruff Papers | Blocks AI crawlers; offers an API on sign-up. | Journals and letters, page-level |
| BYU Lee Library (Times and Seasons, Evening and Morning Star, Messenger and Advocate) | Public domain, no ask needed, but robots.txt blocks OAI and asks for one request a second, and its OCR is unusable. | Open tier, after re-OCR, at a slow pace |

## Left out

Journal of Mormon History 2015– and Mormon Studies Review 2014– (paywalled). Scripture
Central's archive copies (link the original publisher instead). BiblicalStudies.org.uk
(hosts by permission given to it, blocks AI crawlers). HathiTrust bulk download (its terms
forbid it). Issuu copies (its terms forbid scraping). boap.org (the domain now redirects to
a spam site). Bible and Critical Theory, AABNER (NC/ND, small or unreachable). Religions
(MDPI), HTS and Open Theology wholesale: worth picking from by hand, not taking whole.
