// The commons mark: a small copy of the restorationcommons.org window for
// every Restoration Commons site's header. The window links home; the caret
// beside it opens the list of sites.
//
//   <rc-commons site="pulpit"></rc-commons>
//   <script type="module" src="/commons.js"></script>
//
// Attributes: site (the key below; lights the icon in that site's glass),
// label (adds "Restoration Commons" beside the icon), divider (a thin rule
// after it, before the site's own wordmark).
//
// The panel takes the page's font and color-scheme (Canvas / CanvasText);
// a site can set --rc-bg, --rc-ink and --rc-line on rc-commons to match its
// own paper and ink.
//
// The source is restoration-commons/site/commons/commons.js. Every site
// keeps a copy; README "The commons mark" lists them. The names and lines
// match the landing page's list (site/index.html).

const HOME = 'https://restorationcommons.org/';

const SITES = [
  { key: 'pulpit',    glass: '#e2493a', name: 'Pulpit',            kind: 'Every General Conference talk since 1830',   url: 'https://pulpit.restorationcommons.org/' },
  { key: 'lectern',   glass: '#2fb277', name: 'Lectern',           kind: 'A public-domain library your AI can cite',   url: 'https://lectern.restorationcommons.org/' },
  { key: 'telos',     glass: '#4b7df0', name: 'Telos',             kind: 'A journal for emerging writers in Mormon studies', url: 'https://telos.restorationcommons.org/' },
  { key: 'boylan',    glass: '#8f66dc', name: 'Beat the Scholars', kind: 'A timed quiz, hosted by scholars', url: 'https://boylan.restorationcommons.org/' },
  { key: 'refrain',   glass: '#f0a02a', name: 'Refrain',           kind: 'One teaching through every Conference sermon', url: 'https://refrain.restorationcommons.org/' },
  { key: 'crossrefs', glass: '#2bb3c4', name: 'Cross-References',  kind: 'Book of Mormon cross-references, drawn',     url: 'https://crossrefs.restorationcommons.org/' },
];

// Panes in window order: three across, two down, under the arch.
const PANES = SITES.map((s, i) => ({ ...s, x: 3 + (i % 3) * 4.9, y: 11.6 + Math.floor(i / 3) * 6 }));
// A little variation so a one-colour window still reads as glass.
const SHADE = [1, 0.78, 0.9, 0.84, 1, 0.72];

function icon(lit) {
  const panes = PANES.map((p, i) =>
    `<rect x="${p.x}" y="${p.y}" width="4.2" height="5.4" fill="${lit ? lit.glass : p.glass}" opacity="${lit ? SHADE[i] : 1}"/>`).join('');
  const arch = lit ? lit.glass : '#e9c66a';
  return `<svg viewBox="0 0 20 25" aria-hidden="true" focusable="false">
    <path d="M3.4 10.5a6.6 6.6 0 0 1 13.2 0Z" fill="${arch}" opacity="${lit ? 0.6 : 0.7}"/>${panes}
    <path class="lead" d="M1.5 24V10.5a8.5 8.5 0 0 1 17 0V24Z"/></svg>`;
}

const css = new CSSStyleSheet();
css.replaceSync(`
  :host { display: inline-flex; align-items: center; flex: none; vertical-align: middle;
    --rc-bg: Canvas; --rc-ink: CanvasText;
    --rc-line: color-mix(in srgb, var(--rc-ink) 14%, transparent); }
  * { box-sizing: border-box; }
  a, button { color: inherit; font: inherit; -webkit-tap-highlight-color: transparent; }
  :focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
  .home { display: inline-flex; align-items: center; gap: 8px; padding: 4px; margin: -4px 0 -4px -4px;
    border-radius: 7px; text-decoration: none; }
  .home:hover { background: color-mix(in srgb, currentColor 12%, transparent); }
  svg { width: 21px; height: 26px; display: block; flex: none; }
  .lead { fill: none; stroke: currentColor; stroke-width: 1.15; opacity: .6; }
  .label { white-space: nowrap; }
  .more { appearance: none; border: 0; background: none; cursor: pointer; padding: 6px 4px; margin: -6px 0;
    border-radius: 6px; display: inline-flex; opacity: .6; }
  .more:hover, .more[aria-expanded="true"] { opacity: 1; background: color-mix(in srgb, currentColor 12%, transparent); }
  .more svg { width: 10px; height: 10px; }
  .more path { fill: none; stroke: currentColor; stroke-width: 1.6; }
  .rule { width: 1px; height: 1.25em; margin-left: 10px; background: currentColor; opacity: .25; }

  [popover] { position: fixed; inset: auto; margin: 0; width: min(330px, calc(100vw - 24px));
    max-height: calc(100dvh - 24px); overflow: auto;
    padding: 6px; border: 1px solid var(--rc-line); border-radius: 12px;
    background: var(--rc-bg); color: var(--rc-ink); text-align: start;
    box-shadow: 0 18px 44px rgb(0 0 0 / .28), 0 2px 8px rgb(0 0 0 / .12);
    font-size: 14px; line-height: 1.35; letter-spacing: normal; text-transform: none; }
  [popover]:popover-open { animation: rc-in .14s ease-out; }
  @keyframes rc-in { from { opacity: 0; transform: translateY(-4px); } }
  @media (prefers-reduced-motion: reduce) { [popover]:popover-open { animation: none; } }
  .top { display: flex; align-items: center; gap: 10px; padding: 9px 10px 11px; margin-bottom: 4px;
    border-bottom: 1px solid var(--rc-line); border-radius: 8px 8px 0 0; text-decoration: none; font-size: 15px; }
  .top:hover { background: color-mix(in srgb, var(--rc-ink) 7%, transparent); }
  .top small { margin-left: auto; font-size: 12px; opacity: .55; }
  ul { list-style: none; margin: 0; padding: 0; }
  li a { display: grid; grid-template-columns: 14px 1fr; column-gap: 10px; padding: 7px 10px;
    border-radius: 8px; text-decoration: none; }
  li a:hover, li a[aria-current] { background: color-mix(in srgb, var(--rc-ink) 7%, transparent); }
  li i { width: 8px; height: 8px; margin: 6px 0 0 3px; transform: rotate(45deg); }
  li span { min-width: 0; }
  li small { grid-column: 2; font-size: 12.5px; opacity: .6; }
  li a[aria-current] span::after { content: " · here"; opacity: .5; font-size: 12px; }
`);

class RcCommons extends HTMLElement {
  connectedCallback() {
    if (this.shadowRoot) return;
    const lit = SITES.find((s) => s.key === this.getAttribute('site'));
    const root = this.attachShadow({ mode: 'open' });
    root.adoptedStyleSheets = [css];
    root.innerHTML = `
      <a class="home" href="${HOME}" title="Restoration Commons"${
        this.hasAttribute('label') ? `>${icon(lit)}<span class="label">Restoration Commons</span>` : ` aria-label="Restoration Commons">${icon(lit)}`}</a>
      <button class="more" type="button" popovertarget="rc-panel" aria-label="All Restoration Commons sites">
        <svg viewBox="0 0 10 10" aria-hidden="true"><path d="M2 3.75 5 6.75 8 3.75"/></svg></button>
      ${this.hasAttribute('divider') ? '<span class="rule" aria-hidden="true"></span>' : ''}
      <div id="rc-panel" popover>
        <a class="top" href="${HOME}">${icon(null)}<span>Restoration Commons</span><small>Home</small></a>
        <ul>${SITES.map((s) => `<li><a href="${s.url}"${s === lit ? ' aria-current="page"' : ''}>
          <i style="background:${s.glass}"></i><span>${s.name}</span><small>${s.kind}</small></a></li>`).join('')}</ul>
      </div>`;

    const button = root.querySelector('.more');
    const panel = root.querySelector('[popover]');
    if (!('popover' in HTMLElement.prototype)) { // very old browsers: the caret just goes home too
      button.addEventListener('click', () => { location.href = HOME; });
      return;
    }
    // Hang the panel under the mark, kept inside the viewport.
    const place = () => {
      const r = this.getBoundingClientRect();
      const w = panel.offsetWidth;
      const left = Math.max(12, Math.min(r.left - 10, innerWidth - w - 12));
      panel.style.left = `${left}px`;
      panel.style.top = `${r.bottom + 10}px`;
    };
    const close = () => panel.hidePopover();
    panel.addEventListener('toggle', (e) => {
      const open = e.newState === 'open';
      if (open) place();
      for (const [t, f] of [['scroll', close], ['resize', close]]) {
        open ? addEventListener(t, f, { passive: true }) : removeEventListener(t, f);
      }
    });
  }
}

if (!customElements.get('rc-commons')) customElements.define('rc-commons', RcCommons);
