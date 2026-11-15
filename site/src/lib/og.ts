// Link preview cards, drawn at build time with Satori and resvg. 1200 x 630: a page on the dark desk.
// The footer is the wordmark and nothing else.
import fs from 'node:fs';
import { createRequire } from 'node:module';
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';

const require = createRequire(import.meta.url);
const font = (pkg: string, file: string) => fs.readFileSync(require.resolve(`@fontsource/${pkg}/files/${file}`));
const fonts = [
  { name: 'Sans', data: font('geist', 'geist-latin-400-normal.woff'), weight: 400 as const, style: 'normal' as const },
  { name: 'Sans', data: font('geist', 'geist-latin-500-normal.woff'), weight: 500 as const, style: 'normal' as const },
  { name: 'Serif', data: font('newsreader', 'newsreader-latin-400-normal.woff'), weight: 400 as const, style: 'normal' as const },
];

const INK = '#17150f', INK2 = '#4f4a40', DESK = '#0d0d0c', PAPER = '#fbfaf6', MARK = '#f2d88a', PENCIL = '#9c2b1e';

type Node = { type: string; props: Record<string, unknown> };
const h = (type: string, style: Record<string, unknown>, ...children: (Node | string | null | false | undefined)[]): Node => ({
  type, props: { style: { display: 'flex', ...style }, children: children.filter((c) => c !== null && c !== false && c !== undefined) },
});
const clip = (text: string, max: number) => (text.length > max ? text.slice(0, text.lastIndexOf(' ', max)) + '…' : text);

export interface Card {
  rubric: string;
  title: string;
  /** A mark before the line under the title: verified, rejected, or none. */
  state?: 'verified' | 'rejected' | 'cited';
  line?: string;
  detail?: string;
  quote?: boolean;
}

// A sheet of paper on the desk. The line under the title carries the mark: highlighted when the
// words are on the page, red and struck when they are not.
export async function renderCard(card: Card): Promise<Uint8Array<ArrayBuffer>> {
  const size = card.title.length > 150 ? 38 : card.title.length > 90 ? 46 : card.title.length > 50 ? 56 : 68;
  const line = card.line
    ? h('div', { alignSelf: 'flex-start', fontFamily: 'Sans', fontWeight: 500, fontSize: 30, padding: '4px 12px', borderRadius: 4, marginLeft: -12,
        color: card.state === 'rejected' ? PENCIL : INK, background: card.state === 'verified' ? MARK : card.state === 'rejected' ? 'rgba(163,32,12,0.1)' : 'rgba(14,22,33,0.09)' }, card.line)
    : null;
  const tree = h('div', { width: 1200, height: 630, background: DESK, color: INK, padding: '44px 56px 0' },
    h('div', { width: 1088, height: 586, background: PAPER, borderRadius: 6, padding: '52px 64px 0', flexDirection: 'column', boxShadow: '0 12px 34px rgba(0,0,0,0.65)' },
      h('div', { fontFamily: 'Sans', fontSize: 26, color: INK2 }, clip(card.rubric, 70)),
      h('div', { fontFamily: 'Serif', fontWeight: 400, fontSize: size * 1.08, lineHeight: 1.12, marginTop: 22, letterSpacing: -size * 0.015, flexGrow: 1, width: 960 }, card.quote ? `“${clip(card.title, 210)}”` : clip(card.title, 210)),
      line,
      card.detail ? h('div', { fontFamily: 'Sans', fontSize: 26, color: INK2, marginTop: 12 }, clip(card.detail, 70)) : null,
      h('div', { alignItems: 'center', gap: 12, fontFamily: 'Sans', fontWeight: 500, fontSize: 28, margin: '20px 0 76px' },
        h('div', { width: 28, height: 6, background: MARK, borderTop: `3px solid ${INK}`, borderBottom: `3px solid ${INK}` }),
        'Lectern'),
    ),
  );
  const svg = await satori(tree as never, { width: 1200, height: 630, fonts });
  return new Uint8Array(new Resvg(svg).render().asPng());
}

export const png = (bytes: Uint8Array<ArrayBuffer>) => new Response(bytes, { headers: { 'Content-Type': 'image/png' } });
