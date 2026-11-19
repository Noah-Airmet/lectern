import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import { citePath, parseCite, anchorLabel, placeLabel, sourceLink, shortLabel } from '../src/lib/cite';
import { findQuote, highlightRects, spanInUnit } from '../src/lib/quote';
import type { UnitText } from '../src/lib/types';

describe('cite', () => {
  it('parses cite strings and makes reader paths', () => {
    expect(parseCite('arxiv:2305.15324/v2/p6')).toEqual({ ns: 'arxiv', local: '2305.15324', version: 'v2', anchor: 'p6' });
    expect(parseCite('arxiv:2305.15324')?.version).toBeUndefined();
    expect(parseCite('not a cite')).toBeNull();
    expect(citePath('arxiv:2305.15324/v2/p6', 'main tools')).toBe('/d/arxiv/2305.15324/v2/p6?q=main%20tools');
    expect(anchorLabel('p6-p8')).toBe('pp. 6–8');
    expect(sourceLink('https://x.org/a.pdf', 'p6', true)).toBe('https://x.org/a.pdf#page=6');
  });

  it('shows the printed page and the scan number when they differ', () => {
    expect(placeLabel('p362', 'p. 332 (PDF p. 362)')).toBe('p. 332 (scan p. 362)');
    expect(placeLabel('p14', 'p. xii (PDF p. 14)')).toBe('p. xii (scan p. 14)');
    expect(placeLabel('p5', 'p. 5')).toBe('scan p. 5');
    expect(placeLabel('p6-p8')).toBe('scan pp. 6–8');
    expect(placeLabel('b2', 'Results ¶2')).toBe('¶2');
  });
});

describe('shortLabel', () => {
  it('names the author, not the translator or editor', () => {
    expect(shortLabel({ authors: ['Plato', 'Harold North Fowler (tr.)'], org: null, published: '1914', title: 'Euthyphro' })).toBe('Plato 1914');
    expect(shortLabel({ authors: ['Philip Schaff (ed.)'], org: null, published: '1892', title: 'Athanasius' })).toBe('Schaff 1892');
    expect(shortLabel({ authors: ['Pliny the Younger', 'William Melmoth (tr.)'], org: null, published: '1915', title: 'Letters' })).toBe('Pliny 1915');
    expect(shortLabel({ authors: [], org: null, published: '1854', title: 'Journal of Discourses, Volume 1' })).toBe('Journal of Discourses, Volume 1');
  });
});

describe('findQuote', () => {
  const page = 'Model evaluation is\nnot the only tool avail-\nable for AI risk assessment. They are unable to refuse 3.5% of cases.';
  it('finds words across line breaks, hyphenation and case', () => {
    const [[s, e]] = findQuote(page, 'NOT the only tool available for AI risk assessment')!;
    expect(page.slice(s, e)).toBe('not the only tool avail-\nable for AI risk assessment');
  });
  it('does not skip words or match inside a word', () => {
    expect(findQuote(page, 'Model evaluation is the only tool')).toBeNull();
    expect(findQuote(page, 'able to refuse')).toBeNull();
  });
  it('finds fragments around an ellipsis, in order', () => {
    expect(findQuote(page, 'Model evaluation is … for AI risk assessment')).toHaveLength(2);
    expect(findQuote(page, 'for AI risk assessment … Model evaluation is')).toBeNull();
  });
});

describe('highlight', () => {
  const unit = { width: 100, height: 100, spine_start: 50, spine_end: 70, text: 'one two three',
    words: [[0, 3, 10, 10, 20, 14], [4, 7, 22, 10, 30, 14], [8, 13, 10, 16, 24, 20]] } as unknown as UnitText;
  it('draws one box per line', () => {
    expect(highlightRects(unit, 0, 13)).toHaveLength(2);
    expect(highlightRects(unit, 4, 7)).toHaveLength(1);
  });
  it('clips a spine span to the unit', () => {
    expect(spanInUnit(unit, [40, 60])).toEqual([0, 10]);
    expect(spanInUnit(unit, [80, 90])).toBeNull();
  });
});
