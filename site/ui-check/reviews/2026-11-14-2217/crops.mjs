import { chromium } from '@playwright/test';
import { open } from '/Users/noahairmet/development/tools/ui-check/lib/site.mjs';
const B = 'https://lectern.restorationcommons.org';
const crops = [
  ['library-1440-crop-printed', 1440, '/library', { x: 96, y: 240, width: 760, height: 150 }],
  ['record-1440-crop-top', 1440, '/d/npnf2/04-select-works-and-letters', { x: 96, y: 64, width: 1240, height: 400 }],
  ['shelf-1440-crop-top', 1440, '/library/latter-day-saints', { x: 96, y: 64, width: 1240, height: 220 }],
  ['check-1440-crop-findings', 1440, '/check?example=1', { x: 96, y: 540, width: 1240, height: 640 }],
  ['reader-1440-crop-bar', 1440, '/d/npnf2/04-select-works-and-letters/r1/p362?q=He%20was%20made%20man%20that%20we%20might%20be%20made%20God', { x: 96, y: 0, width: 1250, height: 100 }],
  ['home-1440-crop-tries', 1440, '/', { x: 96, y: 100, width: 520, height: 140 }],
  ['home-1440-crop-agent', 1440, '/', { x: 96, y: 1290, width: 520, height: 170 }],
  ['connect-1440-crop-clients', 1440, '/connect', { x: 96, y: 210, width: 900, height: 120 }],
  ['about-1440-crop-h2', 1440, '/about', { x: 96, y: 480, width: 760, height: 200 }],
  ['connect-1440-crop-h2', 1440, '/connect', { x: 96, y: 340, width: 760, height: 200 }],
  ['connect-390-crop-anatomy', 390, '/connect', { x: 0, y: 1660, width: 390, height: 130 }],
  ['search-390-crop-tries', 390, '/search?query=%22plurality%20of%20gods%22', { x: 0, y: 70, width: 390, height: 190 }],
  ['check-390-crop-findings', 390, '/check?example=1', { x: 0, y: 1190, width: 390, height: 330 }],
  ['library-390-crop-plate', 390, '/library', { x: 0, y: 170, width: 390, height: 200 }],
];
const b = await chromium.launch({ channel: 'chrome' });
for (const [name, w, path, clip] of crops) {
  const mobile = w < 600;
  const page = await b.newPage({ viewport: { width: w, height: mobile ? 844 : 900 }, isMobile: mobile, hasTouch: mobile, deviceScaleFactor: 2 });
  await open(page, B + path);
  if (name === 'library-390-crop-plate') await page.hover('.shelf');
  if (name === 'check-1440-crop-findings') await page.hover('.findings > li:nth-child(3)');
  await page.screenshot({ path: `shots/${name}.png`, clip, fullPage: true });
  await page.close(); console.log(name);
}
await b.close();
