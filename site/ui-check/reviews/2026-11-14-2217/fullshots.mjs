// Full-page screenshots for the review, into ./shots (the harness left it empty).
import { chromium } from '@playwright/test';
import { open } from '/Users/noahairmet/development/tools/ui-check/lib/site.mjs';
const B = 'https://lectern.restorationcommons.org';
const pages = { home: '/', library: '/library', shelf: '/library/latter-day-saints', 'shelf-classics': '/library/classics',
  record: '/d/npnf2/04-select-works-and-letters', 'record-jod': '/d/jod/06',
  reader: '/d/npnf2/04-select-works-and-letters/r1/p362?q=He%20was%20made%20man%20that%20we%20might%20be%20made%20God', 'reader-jod': '/d/jod/06/r1/p6',
  'search-empty': '/search', search: '/search?query=%22plurality%20of%20gods%22', check: '/check?example=1', connect: '/connect', about: '/about' };
const only = process.argv.slice(2);
const b = await chromium.launch({ channel: 'chrome' });
for (const w of [1440, 390]) {
  const mobile = w < 600;
  const page = await b.newPage({ viewport: { width: w, height: mobile ? 844 : 900 }, isMobile: mobile, hasTouch: mobile });
  for (const [name, path] of Object.entries(pages)) {
    if (only.length && !only.includes(name)) continue;
    await open(page, B + path);
    await page.screenshot({ path: `shots/${name}-${w}-full.png`, fullPage: true });
    console.log(name, w);
  }
  await page.close();
}
await b.close();
