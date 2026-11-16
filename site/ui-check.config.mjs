// ui-check (~/development/tools/ui-check): what to check on this site, on the real library.
// Build against a snapshot and serve it first (../README.md, "Serving"):
//   node scripts/serve.mjs dist 4412
// The site has one theme, dark. The home page's wall and Field move, so they are masked.
const q = encodeURIComponent;
export default {
  base: process.env.UI_CHECK_BASE ?? 'http://localhost:4412',
  scheme: 'dark',
  dir: 'ui-check',
  pages: [
    { name: 'home', path: '/', mask: ['#wall', '#field'], states: [{ name: 'grammar', click: ['.cbtn'] }] },
    { name: 'library', path: '/library' },
    { name: 'shelf', path: '/library/latter-day-saints' },
    { name: 'shelf-classics', path: '/library/classics' },
    { name: 'record', path: '/d/npnf2/04-select-works-and-letters' },
    { name: 'record-jod', path: '/d/jod/06' },
    { name: 'reader', path: `/d/npnf2/04-select-works-and-letters/r1/p362?q=${q('He was made man that we might be made God')}` },
    { name: 'reader-jod', path: '/d/jod/06/r1/p6' },
    { name: 'shelf-journal', path: '/library/interpreter' },
    { name: 'record-article', path: '/d/interpreter/a-backstory-for-the-brass-plates' },
    { name: 'reader-article', path: '/d/interpreter/a-backstory-for-the-brass-plates/v1/p8' },
    { name: 'reader-open-article', path: '/d/jhs/11257/v1/p2' },
    { name: 'search-empty', path: '/search' },
    { name: 'search', path: `/search?query=${q('"plurality of gods"')}` },
    { name: 'check', path: '/check?example=1', mask: ['.evidence .sheet img'] },
    { name: 'connect', path: '/connect' },
    { name: 'about', path: '/about' },
  ],
  widths: [1440, 390],
};
