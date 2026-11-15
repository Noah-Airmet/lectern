// Many measurements in one browser: node measure-many.mjs <width> <path> '<expr>' [<path> '<expr>' ...]
import { chromium } from '@playwright/test';
import { open } from '/Users/noahairmet/development/tools/ui-check/lib/site.mjs';
const B = 'https://lectern.restorationcommons.org';
const [width, ...rest] = process.argv.slice(2);
const mobile = +width < 600;
const b = await chromium.launch({ channel: 'chrome' });
const page = await b.newPage({ viewport: { width: +width, height: mobile ? 844 : 900 }, isMobile: mobile, hasTouch: mobile });
let last = null;
for (let i = 0; i < rest.length; i += 2) {
  const [path, expr] = [rest[i], rest[i + 1]];
  if (path !== last) { await open(page, B + path); last = path; }
  const v = await page.evaluate(e => {
    const f = x => Math.round(x * 10) / 10;
    window.box = sel => [...document.querySelectorAll(sel)].filter(n => n.getClientRects().length).map(n => {
      const r = n.getBoundingClientRect(), s = getComputedStyle(n);
      return { el: n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') + (n.classList.length ? '.' + [...n.classList].join('.') : ''), text: n.textContent.trim().slice(0, 40),
        x: f(r.left), y: f(r.top + scrollY), w: f(r.width), h: f(r.height), right: f(r.right), bottom: f(r.bottom + scrollY),
        font: `${s.fontWeight} ${s.fontSize}/${s.lineHeight} ${s.fontFamily.split(',')[0]}`, color: s.color, radius: s.borderTopLeftRadius, padding: s.padding, margin: s.margin };
    });
    return (0, eval)(e);
  }, expr);
  console.log(`\n## ${width} ${path}\n   ${expr}`);
  console.log(JSON.stringify(v));
}
await b.close();
