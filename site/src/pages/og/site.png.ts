import { png, renderCard } from '../../lib/og';
import { allDocs } from '../../lib/data';

export async function GET() {
  return png(await renderCard({
    rubric: `Lectern · ${allDocs().length.toLocaleString('en')} books and articles`,
    title: 'Out of the best books, cited to the page.',
    state: 'verified',
    line: 'Every quotation checked against the page it names',
  }));
}
