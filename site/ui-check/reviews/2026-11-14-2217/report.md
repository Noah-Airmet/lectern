Review complete. Here is the report.

# Lectern UI review, 2026-11-14

Screenshots: the harness left `shots/` empty, so I used the full-page captures and 2x crops I took into `/Users/noahairmet/development/websites/lectern/site/ui-check/reviews/2026-11-14-2217/shots/` (the two reader pages are 1.7 million px tall and crashed full-page capture, so those use `ui-check/snapshots/reader-*.png`). Every geometric number below comes from the live DOM.

## Findings, most severe first

1. **connect, 390. `.anatomy`** The citation diagram runs off the phone screen and makes the page scroll sideways. Measured: `scrollWidth` 463 on a 390 viewport; the `p65` code box spans x 425.8 to 457.3, and its label "page of the scan" is squeezed into a 36.8px column, 3 lines tall (h 52.2). Shot: `connect-390-crop-anatomy.png`, `connect-390-full.png`. Fix: at ≤699px switch the anatomy to row flow (one part and its label per line) and drop the code to 14px.

2. **check, 1440 and 390. `.findings > li`** The findings list is indented 12px from the tally and marked text above it. Measured: `.summary` and `.marked` x 112, `.finding-head` x 124 (phone: 16 vs 28). Every other list on the site (`.rows`, `.outline`, `.search ol`) pulls its plate out with a negative margin so text stays on the column line. Shot: `check-1440-crop-findings.png`, `check-390-crop-findings.png`. Fix: `.findings { margin-inline: -12px }` (−8px at phone), matching `.rows`.

3. **reader, 1440. `.rback` vs `.goto .field`, `.contents summary`, `.rsource`** One bar, two control heights. Measured: back link h 36 (plate), page field h 40, Contents h 40, PDF h 40. Centres match so the auto-check passes, but the hover plates differ by 4px. Shot: `ui-check/snapshots/reader-1440.png`. Fix: set `.rback` height to `var(--control)`, or make the bar's quiet buttons `var(--plate)` like the site nav.

4. **record and record-jod vs shelf, both widths. `.rec-top`** The record page starts 16px higher than every other page. Measured: record breadcrumb y 96, title y 128.3; shelf breadcrumb y 112, title y 144.3. Phone: `.rec-top` padding-top 16 vs `.head` 32. Shot: `record-1440-crop-top.png` against `shelf-1440-crop-top.png`. Fix: `.rec-top { padding-top: var(--s-7) }` (and `--s-6` at phone) to match `.head`.

5. **library, 1440. `.publishers span`** "Printed 1835–1925" sits 8px left of the column. Measured: span x 104; the shelf name and description above x 112. `.publishers` has margin-left −8px to cancel an anchor's 8px padding, but these rows are bare spans with no padding. Shot: `library-1440-crop-printed.png`. Fix: give the span the same `padding-inline: var(--s-2)` as `.publishers a`, or drop the negative margin when there is no link.

6. **about vs connect and home, 1440. `.prose h2` vs `.section .h2`** Same 28px heading, two rhythms. Measured on about: 50.4 above the h2, 14 below (h2 bottom 592.9 → p 606.9). On connect: 64 above, 24 below (h2 bottom 410 → content 434). Shot: `about-1440-crop-h2.png`, `connect-1440-crop-h2.png`. Fix: set `.prose h2` margins to `var(--s-8) 0 var(--s-5)`.

7. **home 1440 and 390, search 390. `.tries`** The examples row is drawn two ways. Measured on home 1440: under the search the first example's text starts at x 122 (row at 112 plus 10px padding), under the Connect codeline the row is pulled to x 102 so text starts at 112. Phone: 26 vs 16; on search 390 the row wraps under the Search/Check segment and starts at 26 against the segment's 16. Shot: `home-1440-crop-tries.png`, `home-1440-crop-agent.png`, `search-390-crop-tries.png`. Fix: remove `.hero-find .tries { margin-left: 0 }` and give `.crow .tries` the −10px margin when it wraps to its own line.

8. **library, 390. `a.shelf`** The hover plate reaches 12px past the text at the gutter; every other row at phone reaches 8, and the stylesheet's own comment says 8. Measured: `.shelf` x 4 (margin −12, padding 12) vs `.cat > a` x 8 and `.search ol > li > a` x 8. Shot: `library-390-crop-plate.png`. Fix: at ≤699px `.shelf { margin-inline: -8px; padding-inline: 8px }`.

9. **check, 1440. `.checker form` vs `.audit`** The form and the results under it don't share a right edge. Measured: textarea 112 to 976 (864 wide); marked text and findings 112 to 784 (672 wide). Judgment on severity, measured on fact. Shot: `check-1440-full.png`. Fix: cap the form at the audit's left column, or let the audit's first column grow to 54rem.

10. **check, 1440. `.evidence .pv-empty`** On load the right column is an empty 480×600 outlined rectangle with nothing in it. Measured: `.pv-empty` w 480 h 600, no text. Judgment. Shot: `check-1440-full.png`. Fix: a one-line placeholder ("Open a finding to see its page") or hide the pane until a finding is open.

11. **record, 1440. `.outline > li:first-child a` vs `.lic`** Under two headings at the same y (366), the first texts don't start on one line. Measured: "Title Page." text y 420.6 (row padding 9), "Public domain" y 411.6, 9px apart. Shot: `record-1440-crop-top.png`. Fix: `.outline { margin-top: -9px }` so the first row's text lands on the sidebar's line.

12. **record-jod, both widths. `.outline`** A Contents section whose only entry is the book's own title at p. 1. Measured: 1 outline link. The reader already hides its Contents button in this case, so the record is the odd one out. Judgment. Shot: `record-jod-1440-full.png`. Fix: hide the outline section when it has a single top-level entry.

13. **connect, 1440. `.clients dt`** "Claude.ai, ChatGPT, others" wraps in the 160px label column, leaving "others" alone on a line. Measured: dt h 40.6 in w 160; the sibling label is one line (h 20.3). Shot: `connect-1440-crop-clients.png`. Fix: widen the dt column to 12rem or shorten the label to "Claude.ai, ChatGPT".

14. **home and search, 390. `.send`** The composer's send button is the only 40px control on the phone; everything else grows to 44 for touch. Measured: `.send` 40×40, `.btn` h 44, `.field` h 44, `.seg` h 44. Shot: `search-390-crop-tries.png`. Fix: size `.send` with `var(--control)` and let the box take 52px at phone.

## Clean

shelf-classics (both), search-empty (both), reader-jod (both), search 1440. Shelf 1440, library 390 (apart from the plate), about 390 and connect 1440 (apart from the label) had nothing else I could measure.

## Confidence

Findings 1 through 8, 11, 13 and 14 are measured and I'm confident in them; 1 and 2 are the ones a user will notice without looking for them. Findings 9, 10 and 12 are measured facts but whether they count as defects is a design call: the narrower results column on Check and the empty evidence pane may be deliberate, and the single-entry Contents may be kept for consistency across records. A designer should also confirm the direction of fix for 3 and 6, since either side's value could become the standard.
