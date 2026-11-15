// Cite strings and reader URLs: docs/ARCHITECTURE.md sections 2 and 3. Works in Node and the browser.
import type { DocumentCard } from './types';

export interface Cite { ns: string; local: string; version?: string; anchor?: string }

/** `jod:06/r1/p6` (or a ref that stops early) into its parts. */
export function parseCite(cite: string): Cite | null {
  const m = /^([a-z0-9-]+):([A-Za-z0-9._-]+)(?:\/([vr]\d+))?(?:\/([pb]\d+(?:-[pb]?\d+)?))?$/.exec(cite.trim());
  return m ? { ns: m[1], local: m[2], version: m[3], anchor: m[4] } : null;
}

/** The reader path for a cite string: `/d/jod/06/r1/p6`, with the quote as `?q=`. */
export function citePath(cite: string, quote?: string | null): string {
  const path = '/d/' + cite.replace(':', '/');
  return quote ? `${path}?q=${encodeURIComponent(quote)}` : path;
}

export const docIdOf = (cite: string) => cite.split('/')[0];
export const anchorOf = (cite: string) => parseCite(cite)?.anchor ?? '';
export const firstAnchor = (anchor: string) => anchor.split('-')[0];
export const anchorNumber = (anchor: string) => Number(firstAnchor(anchor).slice(1));

/** What a person calls the place when no label came with it. */
export function anchorLabel(anchor: string): string {
  const [a, b] = anchor.split('-');
  const n = a.slice(1);
  if (a[0] === 'p') return b ? `pp. ${n}–${b.replace(/^p/, '')}` : `p. ${n}`;
  return b ? `¶${n}–${b.replace(/^b/, '')}` : `¶${n}`;
}

/** The site a link goes to, as a reader would name it. */
export const hostOf = (url: string) => new URL(url).hostname.replace(/^(www(-cdn)?|cdn|assets)\./, '');

/** Opens the source at the place: `#page=N` for PDFs. */
export function sourceLink(sourceUrl: string, anchor: string | undefined, paged: boolean, words?: string): string {
  const base = sourceUrl.split('#')[0];
  if (!anchor) return base;
  if (paged) return `${base}#page=${anchorNumber(anchor)}`;
  return words ? `${base}#:~:text=${encodeURIComponent(words)}` : base;
}

/** `Roberts 1903`, `Plato 1914`; the title when there are no authors (`Journal of Discourses, Volume 1 1854`). Translators and editors are not the author. */
// `Philip Schaff` and `Schaff, Philip` are both Schaff; `Plato` is Plato; `Pliny the Younger` is Pliny.
const last = (name: string) => (name.includes(',') ? name.split(',')[0] : / the /.test(name) ? name.split(' the ')[0] : name.split(' ').pop()!).trim();
export function shortLabel(doc: Pick<DocumentCard, 'authors' | 'org' | 'published' | 'title'>): string {
  const year = doc.published?.slice(0, 4);
  const named = doc.authors.filter((a) => !/\((tr|ed|trans|eds)\.?\)/.test(a));
  if (named.length) {
    const surname = last(named[0]);
    const who = named.length === 1 ? surname : named.length === 2
      ? `${surname} & ${last(named[1])}` : `${surname} et al.`;
    return year ? `${who} ${year}` : `${who}`;
  }
  if (!doc.authors.length) return doc.title;   // Journal of Discourses, Volume 1
  const who = last(doc.authors[0].replace(/\s*\(.*\)$/, ''));
  return year ? `${who} ${year}` : who;
}

const LICENCES: Record<string, string> = {
  'CC-BY-4.0': 'CC BY 4.0', 'CC-BY-SA-4.0': 'CC BY-SA 4.0', 'CC0-1.0': 'CC0 1.0', 'OGL-UK-3.0': 'OGL v3.0',
  'public-domain': 'Public domain', 'public-domain-us-gov': 'Public domain (US government work)',
  'arXiv-nonexclusive-1.0': 'arXiv non-exclusive licence', 'all-rights-reserved': 'All rights reserved',
  unknown: 'No licence statement found',
};
export const licenceName = (id: string) => LICENCES[id] ?? id;

export const KINDS: Record<string, string> = { book: 'Book', article: 'Article' };

export const publisherOf = (doc: Pick<DocumentCard, 'org' | 'doc_id'>) => doc.org ?? 'Unknown';

// The shelves, in the order the library lists them. A collection not named here still gets a shelf.
export const SHELVES: Record<string, { name: string; about: string; cloth: string }> = {
  'latter-day-saints': { name: 'Latter-day Saints', about: 'Sermons, doctrine and history from the first century of the Restoration: the Journal of Discourses, Pratt, Roberts, Widtsoe, the Lectures on Faith.', cloth: 'lds' },
  'church-fathers': { name: 'Church Fathers', about: 'The Nicene and Post-Nicene Fathers in the Schaff edition, the Apostolic Fathers, Augustine, Basil, Bede and Boethius.', cloth: 'fathers' },
  'bible-texts': { name: 'Bible: texts and versions', about: 'The Septuagint, the Greek New Testament, the 1611 King James Bible, Codex Sinaiticus.', cloth: 'bible' },
  'bible-study': { name: 'Bible: commentary and study', about: 'The International Critical Commentary, the Expositor\'s Greek Testament, Clarke, Alford and the reference works.', cloth: 'commentary' },
  'jewish-antiquity': { name: 'Jewish antiquity', about: 'Josephus and Philo, the Targums, Second Temple literature and the dictionaries for reading them.', cloth: 'jewish' },
  classics: { name: 'Greek and Latin classics', about: 'The first Loeb Classical Library volumes: the world the early Church read and wrote in, Greek or Latin on one page and English on the other.', cloth: 'classics' },
  languages: { name: 'Languages', about: 'Lexicons and grammars of Hebrew, Aramaic, Greek and Latin.', cloth: 'languages' },
  'theology-history': { name: 'Theology and history', about: 'Creeds, councils, devotion and poetry: Schaff, Law, Herbert, Traherne, Milton, Aquinas.', cloth: 'theology' },
  shorthand: { name: 'Shorthand', about: 'The Pitman phonography the Church\'s reporters learned, and in which many early sermons were first taken down.', cloth: 'shorthand' },
};
export const shelfName = (id: string) => SHELVES[id]?.name ?? id[0].toUpperCase() + id.slice(1).replace(/[-_]/g, ' ');
// Bookcloth: which shelf a book stands on (never state).
export const clothOf = (shelf: string | null | undefined) => `var(--c-${SHELVES[shelf ?? '']?.cloth ?? 'shorthand'})`;
/** `Title: subtitle`, split on the first colon followed by a space. */
export function titleParts(title: string): { main: string; sub: string } {
  const at = title.indexOf(': ');
  return at > 0 && at < title.length - 2 ? { main: title.slice(0, at), sub: title.slice(at + 2) } : { main: title, sub: '' };
}
export const shelfOrder = (id: string) => { const at = Object.keys(SHELVES).indexOf(id); return at < 0 ? 99 : at; };

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '';
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return m ? `${d ? d + ' ' : ''}${months[m - 1]} ${y}` : String(y);
}

/** A plain-text citation for copying with a quote. */
export function proseCitation(doc: DocumentCard, anchor: string, label?: string): string {
  const who = doc.authors.length ? shortLabel(doc).replace(/ \d{4}$/, '') : doc.org ?? '';
  const year = doc.published?.slice(0, 4);
  return [who, `“${doc.title}”`, year, label ?? anchorLabel(anchor)].filter(Boolean).join(', ');
}

export function bibtex(doc: DocumentCard): string {
  const year = doc.published?.slice(0, 4) ?? '';
  const key = ((doc.authors[0]?.split(' ').pop() ?? doc.org ?? 'doc') + year).toLowerCase().replace(/[^a-z0-9]/g, '');
  const fields = [
    `  title = {${doc.title}}`,
    doc.authors.length ? `  author = {${doc.authors.map((a) => a.replace(/\s*\(.*\)$/, '')).join(' and ')}}` : null,
    doc.org && `  publisher = {${doc.org}}`,
    year && `  year = {${year}}`,
    `  url = {${doc.source_url}}`,
  ].filter(Boolean);
  return `@book{${key},\n${fields.join(',\n')}\n}`;
}

const escHtml = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);
/** A document's outline as nested lists, so a section's subsections sit inside it. The items of one <ol class="outline">. */
export function outlineHtml(outline: { level: number; title: string; anchor: string; cite: string }[]): string {
  interface Node { item: (typeof outline)[number]; children: Node[] }
  const roots: Node[] = [];
  const stack: Node[] = [];
  for (const item of outline) {
    while (stack.length && stack[stack.length - 1].item.level >= item.level) stack.pop();
    const node: Node = { item, children: [] };
    (stack.length ? stack[stack.length - 1].children : roots).push(node);
    stack.push(node);
  }
  const draw = (nodes: Node[]): string => nodes.map(({ item, children }) =>
    `<li><a href="${citePath(item.cite)}" data-jump="${item.anchor}"><span class="o-title">${escHtml(item.title)}</span><span class="o-page">${escHtml(anchorLabel(item.anchor))}</span></a>${children.length ? `<ol>${draw(children)}</ol>` : ''}</li>`).join('');
  return draw(roots);
}
