// The wall (home): books from the library in columns that drift in alternating directions, as on
// the Gospel Scholar Archives' home. Paused under the pointer, still under reduced motion, and
// running off the bottom of the screen. A book is its scanned cover, or its binding drawn in its
// shelf's cloth with the title in gilt. Covers fade at the top into backings of the page's own
// colour that move with them, so a book is never see-through.
type Book = { href: string; title: string; src?: string; bind?: { title: string; sub: string; cloth: string } };

const wall = document.getElementById('wall');
if (wall) {
  const books = JSON.parse(wall.dataset.wall!) as Book[];
  const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);
  const shuffled = books.map((b) => [Math.random(), b] as const).sort((a, b) => a[0] - b[0]).map(([, b]) => b);
  // Drawn and scanned alternate down the list, so neither bunches up in a column.
  const drawn = shuffled.filter((b) => b.bind), scanned = shuffled.filter((b) => !b.bind);
  const list: Book[] = [];
  for (let i = 0; i < Math.max(drawn.length, scanned.length); i++) {
    if (scanned[i]) list.push(scanned[i]);
    if (drawn[i]) list.push(drawn[i]);
  }
  const book = (b: Book) =>
    b.bind
      ? `<a class="wcover wbind" href="${esc(b.href)}" title="${esc(b.title)}" style="--cloth:${esc(b.bind.cloth)}"><span class="b-rule"></span><span class="b-title">${esc(b.bind.title)}</span>${b.bind.sub ? `<span class="b-who">${esc(b.bind.sub)}</span>` : ''}<span class="b-rule"></span></a>`
      : `<a class="wcover" href="${esc(b.href)}" title="${esc(b.title)}"><img alt="" decoding="async" fetchpriority="low" src="${esc(b.src!)}" onload="this.classList.add('in')" onerror="this.closest('a').classList.add('gone')"></a>`;
  const draw = () => {
    if (!wall.clientWidth) return;
    const phone = innerWidth < 720, colw = phone ? 96 : 150, gap = phone ? 12 : 18, per = 6;
    const cols = Math.ceil(wall.clientWidth / (colw + gap)) + 1;
    if (wall.dataset.cols === String(cols)) return;
    wall.dataset.cols = String(cols);
    wall.style.setProperty('--colw', colw + 'px');
    wall.style.setProperty('--gap', gap + 'px');
    let k = 0, covers = '', backs = '';
    for (let c = 0; c < cols; c++) {
      let once = '';
      for (let i = 0; i < per; i++) once += book(list[k++ % list.length]);
      const dur = (per * (colw * 1.5 + gap)) / (10 + ((c * 5) % 7));   // 10-16 px/s: one loop takes minutes
      const col = `class="wcol${c % 2 ? ' down' : ''}" style="--dur:${dur.toFixed(1)}s;--delay:-${(Math.random() * dur).toFixed(1)}s"`;
      covers += `<div ${col}>${once}${once.replace(/<a /g, '<a tabindex="-1" aria-hidden="true" ')}</div>`;
      backs += `<div ${col}>${'<i></i>'.repeat(per * 2)}</div>`;
    }
    wall.querySelector('.wtrack')!.innerHTML = covers;
    wall.querySelector('.wbacks')!.innerHTML = backs;
  };
  draw();
  let t = 0;
  new ResizeObserver(() => { clearTimeout(t); t = window.setTimeout(draw, 200); }).observe(wall);
}
