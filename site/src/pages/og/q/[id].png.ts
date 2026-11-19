// The preview card for a quote check: the quote, and whether it is on the page.
import type { APIContext } from 'astro';
import { png, renderCard } from '../../../lib/og';
import { allChecks, type StoredCheck } from '../../../lib/checks';
import { getDoc, getUnit } from '../../../lib/data';
import { anchorOf, docIdOf, placeLabel, shortLabel } from '../../../lib/cite';

export const getStaticPaths = async () => (await allChecks()).map((check) => ({ params: { id: check.id }, props: { check } }));

export async function GET({ props }: APIContext) {
  const check = (props as { check: StoredCheck }).check;
  const doc = getDoc(docIdOf(check.cite))!;
  const here = placeLabel(anchorOf(check.cite), getUnit(check.cite)?.anchor_label);
  const shownAt = placeLabel(anchorOf(check.shown), getUnit(check.shown)?.anchor_label);
  const line = check.passed ? `On ${here}` : check.verdict === 'elsewhere' ? `Not on ${here}. It is on ${shownAt}` : `Not on ${here}`;
  return png(await renderCard({ rubric: `Quote check · ${shortLabel(doc)}`, title: check.quote, quote: true, state: check.passed ? 'verified' : 'rejected', line, detail: doc.title }));
}
