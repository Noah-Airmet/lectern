// Paste a passage with citations; each one comes back Verified, Page only or Rejected, with the reason.
import { useEffect, useState } from 'react';
import { anchorOf, citePath, docIdOf, placeLabel } from '../lib/cite';
import { API_BASE } from '../lib/env';
import type { AnswerAudit, CitationAudit, CitationState, QuoteCheck } from '../lib/types';
import { Chip, Icon, PageView, citeLabel, useDocs } from './shared';

/** Whether the window is wide enough for the page to stand beside the findings. */
function useWide() {
  const [wide, setWide] = useState(false);
  useEffect(() => {
    const query = matchMedia('(min-width: 1000px)');
    const read = () => setWide(query.matches);
    read();
    query.addEventListener('change', read);
    return () => query.removeEventListener('change', read);
  }, []);
  return wide;
}

const EXAMPLE = `Athanasius put the exchange in one line: "He was made man that we might be made God" (npnf2:04-select-works-and-letters/r1/p362). It is usually quoted as "God became man so that man might become God" (npnf2:04-select-works-and-letters/r1/p362).

In the King Follett sermon Joseph Smith taught that "the intelligence of spirits had no beginning, neither will it have an end" (jod:06/r1/p6), and Lorenzo Snow's couplet ran "As man now is, God once was; as God now is, man may be" (jenson:biographical-encyclopedia-1/r1/p37). One version of this paragraph cited a page the volume does not have (jod:06/r1/p900).`;

const stateOf = (c: CitationAudit): CitationState =>
  !c.resolves ? 'rejected' : c.quotes.length === 0 ? 'cited' : c.quotes.every((q) => q.check?.passed) ? 'verified' : 'rejected';

function Reason({ check, here }: { check: QuoteCheck; here: string }) {
  const where = check.locations[0];
  if (check.verdict === 'exact') return <span className="state" data-state="verified">On {here}, word for word</span>;
  if (check.verdict === 'normalized') return <span className="state" data-state="verified">On {here}, ignoring case and punctuation</span>;
  if (check.verdict === 'elsewhere' && where) return <><span className="state" data-state="rejected">Not on {here}</span> <a className="link" href={citePath(where.cite, check.quote)}>The words are on {placeLabel(where.anchor, where.anchor_label)}</a></>;
  if (check.verdict === 'near_miss' && where) {
    const diffs = check.segments.flatMap((s) => s.diff);
    // The page's own words, with the ones the quotation dropped marked where they stand.
    const dropped = diffs.filter((d) => d.op === 'insert').map((d) => d.source);
    const others = diffs.filter((d) => d.op !== 'insert');
    return (
      <><span className="state" data-state="rejected">Not on {here}</span>
        <span className="says">{placeLabel(where.anchor, where.anchor_label)}: “{where.text.replace(/\s+/g, ' ').split(' ').map((w, i) => <span key={i}>{i > 0 && ' '}{dropped.includes(w) ? <ins className="diff">{w}</ins> : w}</span>)}”</span>
        {others.length > 0 && <span className="diffs">{others.map((d, i) => (
          <span key={i}>{d.op === 'delete' ? <del className="diff">{d.quote}</del> : <><del className="diff">{d.quote}</del> {d.source}</>}</span>
        ))}</span>}
      </>
    );
  }
  return <span className="state" data-state="rejected">Not in this document</span>;
}

export default function Checker() {
  const [text, setText] = useState('');
  const [checked, setChecked] = useState('');
  const [audit, setAudit] = useState<AnswerAudit | null>(null);
  const [status, setStatus] = useState<'idle' | 'working' | 'down'>('idle');
  const [open, setOpen] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const docs = useDocs(audit ? audit.citations.filter((c) => c.resolves).map((c) => docIdOf(c.cite)) : []);

  const run = async (input: string) => {
    if (!input.trim()) return;
    setStatus('working');
    try {
      const response = await fetch(`${API_BASE}/api/check`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ text: input }) });
      if (!response.ok) throw new Error();
      const body = (await response.json()) as AnswerAudit;
      setAudit(body);
      setChecked(input);
      const firstBad = body.citations.findIndex((c) => stateOf(c) === 'rejected' && c.resolves);
      setOpen(firstBad >= 0 ? firstBad : null);
      setStatus('idle');
      if (input.length < 1800) history.replaceState(null, '', `/check?text=${encodeURIComponent(input)}`);
    } catch {
      setStatus('down');
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const given = params.get('text') ?? (params.has('example') ? EXAMPLE : '');
    if (given) { setText(given); if (!/""/.test(given)) run(given); }
  }, []);

  const states = audit?.citations.map(stateOf) ?? [];
  const count = (s: CitationState) => states.filter((x) => x === s).length;

  // The checked text again, with each citation replaced by its chip.
  const marked: React.ReactNode[] = [];
  if (audit) {
    let at = 0;
    audit.citations.forEach((c, i) => {
      const found = checked.indexOf(c.raw, at);
      if (found < 0) return;
      const wrapped = checked[found - 1] === '(' && checked[found + c.raw.length] === ')';
      const end = found + c.raw.length + (wrapped ? 1 : 0);
      // Punctuation after a citation stays on its line.
      const tail = /^[.,;:!?]+/.exec(checked.slice(end))?.[0] ?? '';
      marked.push(checked.slice(at, wrapped ? found - 1 : found), <span className="nb" key={i}><Chip state={states[i]} label={c.resolves ? citeLabel(c.cite, docs, c.anchor_label) : c.raw} onClick={() => { setOpen(i); document.getElementById(`c${i}`)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }} current={open === i} />{tail}</span>);
      at = end + tail.length;
    });
    marked.push(checked.slice(at));
  }

  const wide = useWide();
  const shown = open !== null ? audit?.citations[open] : undefined;
  const shownAt = shown?.quotes.find((q) => q.check?.locations[0])?.check;
  const page = (check: QuoteCheck, c: CitationAudit) => (
    <>
      <PageView cite={check.locations[0].cite.replace(/-p\d+$/, '')} span={[check.locations[0].spine_start, check.locations[0].spine_end]} kind={check.passed ? 'found' : 'reject'} doc={docs[docIdOf(c.cite)]} />
      <p className="caption" style={{ marginTop: 0 }}><span>{citeLabel(check.locations[0].cite, docs, check.locations[0].anchor_label)}</span><a className="link" href={citePath(check.locations[0].cite, check.passed ? check.quote : undefined)}>Open the page</a></p>
    </>
  );

  return (
    <div className="checker">
      <form onSubmit={(e) => { e.preventDefault(); run(text); }}>
        <label className="sr" htmlFor="check-text">Text with citations</label>
        <textarea id="check-text" className="field" rows={6} value={text} onChange={(e) => setText(e.target.value)} placeholder={'"the quoted words" (jod:06/r1/p6)'} />
        <div className="actions">
          <button className="btn btn-primary" disabled={status === 'working' || !text.trim()}>Check</button>
          <button type="button" className="btn" onClick={() => { setText(EXAMPLE); run(EXAMPLE); }}>Try an example</button>
          {audit && <button type="button" className="btn" onClick={() => { navigator.clipboard.writeText(location.href); setCopied(true); setTimeout(() => setCopied(false), 1200); }}><Icon name={copied ? 'check' : 'link'} small />Copy link</button>}
        </div>
      </form>
      {status === 'down' && <p className="failed">Checker unavailable <button className="btn" onClick={() => run(text)}>Retry</button></p>}

      {audit && (
        <div className="audit" aria-live="polite">
          <p className="summary tally">
            <span className="state" data-state="verified">{count('verified')} verified</span>
            <span className="state" data-state="cited">{count('cited')} page only</span>
            <span className="state" data-state="rejected">{count('rejected')} rejected</span>
          </p>
          <div className="marked prose">{marked.map((part, i) => (typeof part === 'string' ? part.split('\n\n').map((para, j) => <span key={`${i}-${j}`}>{j > 0 && <><br /><br /></>}{para}</span>) : part))}</div>

          <ol className="findings">
            {audit.citations.map((c, i) => (
              <li key={i} id={`c${i}`} data-open={open === i || undefined} onClick={() => wide && c.quotes.some((q) => q.check?.locations[0]) && setOpen(i)}>
                <div className="finding-head">
                  <Chip state={states[i]} label={c.resolves ? citeLabel(c.cite, docs, c.anchor_label) : c.raw} href={c.resolves ? citePath(c.cite, c.quotes[0]?.quote) : undefined} />
                  {c.resolves && <span className="mono cite">{c.cite}</span>}
                </div>
                {!c.resolves && <p className="why">{c.error}</p>}
                {c.resolves && c.quotes.length === 0 && <p className="why"><span className="state" data-state="cited">The page exists; nothing quoted</span></p>}
                {c.quotes.map((q, j) => (
                  <div className="quote" key={j}>
                    <p className="q">“{q.quote}”</p>
                    <p className="why">{q.check ? <Reason check={q.check} here={placeLabel(anchorOf(c.cite), c.anchor_label)} /> : q.error}</p>
                    {q.check?.locations[0] && (open === i
                      ? !wide && <div className="evidence-in">{page(q.check, c)}</div>
                      : !wide && <button className="btn btn-quiet show" onClick={() => setOpen(i)}>Show the page</button>)}
                  </div>
                ))}
              </li>
            ))}
          </ol>
          {audit.unattached_quotes.length > 0 && <p className="note">{audit.unattached_quotes.length} {audit.unattached_quotes.length > 1 ? 'quotations' : 'quotation'} with no citation, not checked</p>}
          {wide && <div className="evidence">{shown && shownAt ? page(shownAt, shown) : <div className="pv pv-empty">Open a finding to see its page</div>}</div>}
        </div>
      )}
    </div>
  );
}
