// src/components/Reports.tsx
import { useState, useEffect } from 'react';
import jsPDF from 'jspdf';

interface Observation { time: string; what: string; confidence?: number; mgrs?: string; sensor_id?: string; unit?: string | null; observer_signature?: string; }

interface Props { observations: Observation[]; }

const HISTORY_KEY = 'opord_history';
interface SavedReport { id: number; generated_at: string; title: string; summary: string; content: string; }

function loadHistory(): SavedReport[] {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch { return []; }
}
function saveHistory(list: SavedReport[]) { try { localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(-50))); } catch {} }

/* NATO OPORD sections reference (simplified):
1. SITUATION
2. MISSION
3. EXECUTION
4. SUSTAINMENT
5. COMMAND & SIGNAL
*/

export default function Reports({ observations }: Props) {
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: any) => {
      const id = e.detail?.id;
      if (!id) return;
      const hist = loadHistory();
      const item = hist.find(r => r.id === id);
      if (item) setReport(item.content);
    };
    window.addEventListener('opord-load-request', handler as any);
    return () => window.removeEventListener('opord-load-request', handler as any);
  }, []);

  const persistReport = (text: string) => {
    if (!text) return;
    const firstLine = text.split('\n').find(l => l.trim())?.slice(0,120) || 'OPORD';
    const entry: SavedReport = {
      id: Date.now(),
      generated_at: new Date().toISOString(),
      title: firstLine.replace(/^\d+\.\s*/,'').slice(0,60),
      summary: firstLine,
      content: text
    };
    const hist = loadHistory();
    hist.push(entry);
    saveHistory(hist);
    window.dispatchEvent(new CustomEvent('opord-history-updated'));
  };

  const buildStructuredSummary = () => {
    if (!observations?.length) return 'No observations available.';
    const total = observations.length;
    const avgConf = (
      observations.reduce((s, o) => s + (typeof o.confidence === 'number' ? o.confidence : 0), 0) /
      total
    ).toFixed(1);
    const byType: Record<string, number> = {};
    observations.forEach(o => { if (o.what) byType[o.what] = (byType[o.what] || 0) + 1; });
    const topTypes = Object.entries(byType).sort((a,b)=>b[1]-a[1]).slice(0,5)
      .map(([t,c]) => `${t} (${c})`).join(', ') || 'N/A';
    const times = observations.map(o => o.time).sort();
    return `SUMMARY: Total ${total} obs; Avg Confidence ${avgConf}%. Top Types: ${topTypes}. Time span: ${times[0]} to ${times[times.length-1]}.`;
  };

  const openAIKey = (import.meta as any).env?.VITE_OPENAI_KEY;

  const generateOpord = async () => {
    setLoading(true); setError(null); setReport('');
    try {
      const contextSummary = buildStructuredSummary();
      const trimmedObs = observations.slice(0, 60); // limit tokens
      const obsLines = trimmedObs.map(o => `- ${o.time} | ${o.mgrs || 'MGRS?'} | ${o.what} | Conf:${o.confidence ?? '?'} | Sensor:${o.sensor_id || 'n/a'}`).join('\n');
      const prompt = `You are a battle staff assistant. Using the raw observations and summary, draft a concise NATO OPORD (5 paragraph format). Focus on clarity.\n\n${contextSummary}\n\nOBSERVATIONS:\n${obsLines}\n\nReturn only the OPORD text labelled with numbered sections.`;

      if (!openAIKey) {
        // Offline deterministic fallback
        const fallback = `1. SITUATION\n${contextSummary}\n2. MISSION\nProvide placeholder mission until OPENAI key set.\n3. EXECUTION\nNotional tasks based on observed types.\n4. SUSTAINMENT\nStandard supply posture.\n5. COMMAND & SIGNAL\nStandard comms plan.`;
        setReport(fallback);
        persistReport(fallback);
        return;
      }

      const res = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${openAIKey}` },
        body: JSON.stringify({
          model: 'gpt-4o-mini',
            messages: [
              { role: 'system', content: 'You produce concise, professional NATO OPORDs.' },
              { role: 'user', content: prompt }
            ],
            temperature: 0.4,
            max_tokens: 800
        })
      });
      if (!res.ok) throw new Error('OpenAI API error ' + res.status);
      const data = await res.json();
      const text = data.choices?.[0]?.message?.content?.trim() || JSON.stringify(data);
      setReport(text);
      persistReport(text);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally { setLoading(false); }
  };

  const handleDownloadPDF = () => {
    if (!report) return;
    const doc = new jsPDF();
    const lines = doc.splitTextToSize(report, 180);
    doc.text(lines, 10, 10);
    doc.save('opord.pdf');
  };

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex items-center gap-3 mb-3">
        <button className="btn-mil" onClick={generateOpord} disabled={loading || !observations.length}>
          {loading ? 'Generating…' : 'Generate OPORD from Observations'}
        </button>
        <button className="btn-mil" onClick={handleDownloadPDF} disabled={!report}>Download PDF</button>
        <div className="text-xs mil-muted">
          {observations.length ? `${observations.length} observations in scope` : 'No observations loaded'}
        </div>
      </div>
      {error && <div className="mb-2 text-xs text-red-400">{error}</div>}
      <textarea
        className="w-full h-96 p-3 text-sm border bg-black/20 border-black/25 rounded resize"
        rows={28}
        value={report}
        placeholder="OPORD output will appear here"
        readOnly
      />
      {!openAIKey && <div className="mt-2 text-xs mil-muted">Set VITE_OPENAI_KEY for live generation. Currently using fallback template.</div>}
    </div>
  );
}