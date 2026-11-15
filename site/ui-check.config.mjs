// ui-check (~/development/tools/ui-check): what to check on this site, on the real library.
// Build against a snapshot and serve it first (../README.md, "Serving"):
//   node scripts/serve.mjs dist 4412
// UI_CHECK_SCHEME=dark runs the same pages in the dark theme, with its own screenshots.
const q = encodeURIComponent;
const dark = process.env.UI_CHECK_SCHEME === 'dark';
export default {
  base: process.env.UI_CHECK_BASE ?? 'http://localhost:4412',
  scheme: dark ? 'dark' : 'light',
  dir: dark ? 'ui-check/dark' : 'ui-check',
  pages: [
    { name: 'home', path: '/', states: [{ name: 'rejected', click: ['.claim[data-pick="rejected"]'] }] },
    { name: 'library', path: '/library' },
    { name: 'shelf', path: '/library/latter-day-saints' },
    { name: 'shelf-classics', path: '/library/classics' },
    { name: 'record', path: '/d/npnf2/04-select-works-and-letters' },
    { name: 'record-jod', path: '/d/jod/06' },
    { name: 'reader', path: `/d/npnf2/04-select-works-and-letters/r1/p362?q=${q('He was made man that we might be made God')}` },
    { name: 'reader-jod', path: '/d/jod/06/r1/p6' },
    { name: 'search-empty', path: '/search' },
    { name: 'search', path: `/search?query=${q('"plurality of gods"')}` },
    { name: 'check', path: '/check?example=1', mask: ['.evidence .sheet img'] },
    { name: 'connect', path: '/connect' },
    { name: 'about', path: '/about' },
  ],
  widths: [1440, 390],
};
