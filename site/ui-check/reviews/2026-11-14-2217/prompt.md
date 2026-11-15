You are a meticulous product designer reviewing a website's UI for visual craft problems, the way Karri Saarinen (Linear's CEO) marked up an agent-built app. His critique of that app: vertical and horizontal alignment missing (panes' top bars at different heights, list items not starting on one line), buttons both rounded and square and in various sizes, inconsistent spacing, duplicated sections, a stray gap above an input. That is the level of detail that counts here: 2 to 8 pixel inconsistencies a top designer winces at, not taste.

The site's code is in /Users/noahairmet/development/websites/lectern/site. The site has no written design system, so judge against Karri's standard and the site's own most common choices (the spacing, sizes and shapes it uses most are its de facto system).

The live site is at https://lectern.restorationcommons.org. Its pages:
- home: https://lectern.restorationcommons.org/
- library: https://lectern.restorationcommons.org/library
- shelf: https://lectern.restorationcommons.org/library/latter-day-saints
- shelf-classics: https://lectern.restorationcommons.org/library/classics
- record: https://lectern.restorationcommons.org/d/npnf2/04-select-works-and-letters
- record-jod: https://lectern.restorationcommons.org/d/jod/06
- reader: https://lectern.restorationcommons.org/d/npnf2/04-select-works-and-letters/r1/p362?q=He%20was%20made%20man%20that%20we%20might%20be%20made%20God
- reader-jod: https://lectern.restorationcommons.org/d/jod/06/r1/p6
- search-empty: https://lectern.restorationcommons.org/search
- search: https://lectern.restorationcommons.org/search?query=%22plurality%20of%20gods%22
- check: https://lectern.restorationcommons.org/check?example=1
- connect: https://lectern.restorationcommons.org/connect
- about: https://lectern.restorationcommons.org/about

Screenshots are in /Users/noahairmet/development/websites/lectern/site/ui-check/reviews/2026-11-14-2217/shots, at widths 1440 and 390 (a width under 600 is a phone). `shots.txt` beside that folder lists them. `<page>-<width>-<state>.png` is the whole page; `<page>-<width>-<state>--<n>-<part>.png` are crops of its header, nav, sections, cards, dialogs and forms at 2 to 3 times scale. Start with the whole pages at each width, then the crops: a whole page is too downscaled to show a 2px problem.

Measure before you report. Vision misjudges a few pixels; the browser doesn't. Use the helper:

    node /Users/noahairmet/development/tools/ui-check/lib/measure.mjs <url> <width> '<expression>' [--click <selector>]

It prints the expression's value as JSON once the page has drawn; `box(selector)` gives every visible match's rect, font, colour, radius, padding and margin. For example `node /Users/noahairmet/development/tools/ui-check/lib/measure.mjs https://lectern.restorationcommons.org 390 'box("header a, header button")'`. Every geometric finding needs a measurement; a judgment call (hierarchy, wording) says "judgment".

Already checked automatically, so don't re-report these unless you measure a real exception: icons centred in their controls, hover plates centred, concentric corners at card edges, flex-row children sharing a centre line, controls covered by other things, horizontal scroll, top-bar items across panes sharing a centre line, siblings in a column sharing a left edge and a content start, boxed side-by-side controls sharing a height and a radius, WCAG AA contrast, names and target sizes.

Spend your effort on what those can't catch:
- alignment between things that aren't siblings (a page title against the content column under it, a header's logo against the page's left edge)
- one component drawn two ways (the same button, card, list row or form field with different sizes, radii, padding or type in two places)
- spacing rhythm that differs between similar places (heading to content, section to section, page to page)
- type: too many sizes or weights, a size between the steps the site otherwise uses
- duplicated or redundant content; words that explain what the design should show
- anything that looks unfinished at the phone width: crushed text, a lone word or icon on its own line, a row of three that wraps to two and one
- anything a top designer would wince at

Do not edit any file in the site. You may write scratch scripts only in the review folder above the screenshots.

Report, ranked most to least severe, at most 20 findings. For each: the page and width, the element (a selector), what's wrong, the measurement that proves it (or "judgment"), the design-doc rule it breaks if any, the screenshot file, and the fix you'd make in a sentence. Then name the pages you found clean. End with a paragraph: which findings you're confident in, and which a human designer should confirm. Don't pad: a clean site gets a short report.
