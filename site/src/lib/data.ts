// Build-time reading of a snapshot's public/ tree (docs/ARCHITECTURE.md section 7).
// SAFETYPAGE_PUBLIC_DIR points at it; the default is the fixture tree that `npm run data` writes
// (site/.data). The tree is never copied into the build: the host serves it at /data.
import fs from 'node:fs';
import path from 'node:path';
import type { DocumentCard, UnitText } from './types';
import { publisherOf } from './cite';

export const PUBLIC_DIR = process.env.SAFETYPAGE_PUBLIC_DIR ?? path.resolve('.data');

const readJson = <T>(file: string): T => JSON.parse(fs.readFileSync(file, 'utf8')) as T;

let cards: DocumentCard[] | undefined;
/** Every document card, oldest first: a library of old books reads from the beginning. */
export function allDocs(): DocumentCard[] {
  if (cards) return cards;
  const root = path.join(PUBLIC_DIR, 'docs');
  if (!fs.existsSync(root)) throw new Error(`No library data at ${PUBLIC_DIR}. Run "npm run data" or set SAFETYPAGE_PUBLIC_DIR.`);
  cards = fs.readdirSync(root).flatMap((ns) =>
    fs.readdirSync(path.join(root, ns)).filter((f) => f.endsWith('.json')).map((f) => {
      const card = readJson<DocumentCard>(path.join(root, ns, f));
      card.authors = card.authors.map((a) => a.replace(/\s+/g, ' ').trim());   // some sources wrap a name over two lines
      return card;
    }),
  );
  cards.sort((a, b) => (a.published ?? '').localeCompare(b.published ?? '') || a.doc_id.localeCompare(b.doc_id, 'en', { numeric: true }));
  return cards;
}

let byId: Map<string, DocumentCard> | undefined;
export const getDoc = (docId: string) => (byId ??= new Map(allDocs().map((d) => [d.doc_id, d]))).get(docId);

/** Whether a version's text is published under this anchor (open versions only). */
export const hasUnit = (docId: string, version: string, anchor: string) =>
  fs.existsSync(path.join(PUBLIC_DIR, 'text', ...docId.split(':'), version, `${anchor}.json`));

export interface LibraryCounts { snapshot: string | null; built: string | null; documents: number; units: number; pages: number; paragraphs: number; open: number }
let counts: LibraryCounts | undefined;
/** The library's numbers: from the cards, and the snapshot's id and date from its manifest when there is one. */
export function libraryCounts(): LibraryCounts {
  if (counts) return counts;
  const docs = allDocs();
  const sum = (kind: string) => docs.filter((d) => d.anchor_kind === kind).reduce((n, d) => n + d.unit_count, 0);
  const file = path.join(PUBLIC_DIR, '..', 'manifest.json');
  const manifest = fs.existsSync(file) ? readJson<{ snapshot_id: string; created_at: string }>(file) : null;
  const pages = sum('page'), paragraphs = sum('block');
  counts = {
    snapshot: manifest?.snapshot_id ?? null, built: manifest?.created_at ?? null, documents: docs.length,
    units: pages + paragraphs, pages, paragraphs, open: docs.filter((d) => d.tier === 'open').length,
  };
  return counts;
}

export interface Shelf { id: string; docs: DocumentCard[]; publishers: [string, number][]; kinds: [string, number][]; years: [string, number][] }
const tally = (values: string[]): [string, number][] => {
  const n = new Map<string, number>();
  for (const v of values) n.set(v, (n.get(v) ?? 0) + 1);
  return [...n].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
};
let shelves: Shelf[] | undefined;
/** The documents by shelf (a document's `collection`), each with the counts its filters show. */
export function allShelves(): Shelf[] {
  if (shelves) return shelves;
  const groups = new Map<string, DocumentCard[]>();
  for (const doc of allDocs()) {
    const id = doc.collection ?? 'other';
    if (!groups.has(id)) groups.set(id, []);
    groups.get(id)!.push(doc);
  }
  shelves = [...groups].map(([id, docs]) => [id, [...docs].sort((a, b) => a.doc_id.localeCompare(b.doc_id, 'en', { numeric: true }))] as const).map(([id, docs]) => ({
    id, docs, publishers: tally(docs.map(publisherOf)), kinds: tally(docs.map((d) => d.kind)),
    years: tally(docs.map((d) => d.published?.slice(0, 4) ?? '')).filter(([y]) => y).sort((a, b) => a[0].localeCompare(b[0])),
  }));
  return shelves;
}

const unitCache = new Map<string, UnitText[]>();
/** A version's units in reading order. Empty for a link-only version: its text is not published. */
export function unitsOf(docId: string, version: string): UnitText[] {
  const key = `${docId}/${version}`;
  const hit = unitCache.get(key);
  if (hit) return hit;
  const [ns, local] = docId.split(':');
  const dir = path.join(PUBLIC_DIR, 'text', ns, local, version);
  const units = fs.existsSync(dir)
    ? fs.readdirSync(dir).filter((f) => /^[pb]\d+\.json$/.test(f)).map((f) => readJson<UnitText>(path.join(dir, f)))
    : [];
  units.sort((a, b) => (a.spine_start ?? 0) - (b.spine_start ?? 0));
  unitCache.set(key, units);
  return units;
}

export const getUnit = (cite: string) => {
  const [docId, version, anchor] = cite.split('/');
  return unitsOf(docId, version).find((u) => u.anchor === anchor);
};


// What the shelf list knows that the engine's card does not: the series and volume.
export interface ShelfEntry { id: string; series: string | null; volume: string | null }
let shelfEntries: Map<string, ShelfEntry> | undefined;
export function shelfEntry(docId: string): ShelfEntry | undefined {
  if (!shelfEntries) {
    const file = path.resolve('../shelf/volumes.jsonl');
    const rows = fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l) as ShelfEntry) : [];
    shelfEntries = new Map(rows.map((r) => [r.id, r]));
  }
  return shelfEntries.get(docId);
}
