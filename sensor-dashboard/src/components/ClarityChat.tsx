import React, { useState } from "react";

/* Central chat UI: placeholder data from your prompt, minimal styling via existing mil-* classes */
export default function ClarityChat() {
  const [messages, setMessages] = useState<any[]>([
    {
      id: 1,
      who: "Sensor",
      time: "12:41Z",
      text: "New sensor report: GRID 12K — 5 units on foot. Confidence 91%",
      refs: ["12K/IMG-34"],
      confidence: 91,
      type: "sensor",
    },
    {
      id: 2,
      who: "Platoon Leader",
      time: "12:43Z",
      text: "Observed movement along AXIS-N, probable recon elements.",
      refs: ["C1/TXT-09"],
      confidence: 76,
      type: "platoon",
    },
    {
      id: 3,
      who: "Assistant",
      time: "12:47Z",
      text:
        "1. SITUATION: Coordinated foot movement detected across 12K–D3.\n2. MISSION: Maintain surveillance; prevent corridor penetration on AXIS-N.\n3. EXECUTION: Task Bravo to screen north ridge; cue UAS.\n4. ASSESSMENT: Enemy advance probability 82%.\nRefs: 12K/IMG-34 • C1/TXT-09",
      refs: ["12K/IMG-34", "C1/TXT-09"],
      confidence: 82,
      type: "assistant",
    },
  ]);
  const [input, setInput] = useState("");

  const send = () => {
    if (!input.trim()) return;
    setMessages((m) => [
      ...m,
      { id: Date.now(), who: "Operator", time: new Date().toISOString().slice(11, 16) + "Z", text: input, refs: [], confidence: 0, type: "operator" },
    ]);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3 mil-panel">
        <div>
          <div className="font-bold">CLARITY • Sector D3</div>
          <div className="text-xs mil-muted">Secure • Encrypted • Last sync 00:00:30</div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm mil-muted">Connection: Encrypted</div>
          <div className="status-dot status-ok blink" title="Live" />
        </div>
      </div>

      <div className="flex-1 p-4 overflow-auto mil-panel scanline" style={{ minHeight: 420 }}>
        <div className="space-y-4">
          {messages.map((m) => (
            <div key={m.id} className={`flex ${m.type === "assistant" ? "justify-start" : m.type === "operator" ? "justify-end" : "justify-start"}`}>
              <div style={{ maxWidth: "78%" }}>
                <div className={`p-3 ${m.type === "assistant" ? "bg-black/30 border border-black/15" : "bg-black/20"} ${m.type === "assistant" ? "mil-panel" : "mil-panel"}`}>
                  <div className="flex items-baseline justify-between gap-3">
                    <div className="text-sm font-bold">{m.who}</div>
                    <div className="text-xs mil-muted">{m.time}</div>
                  </div>
                  <pre className="mt-2 text-sm whitespace-pre-wrap" style={{ fontFamily: "inherit" }}>{m.text}</pre>
                  <div className="flex items-center gap-2 mt-3">
                    {m.refs?.map((r: string) => (
                      <span key={r} className="px-2 py-0.5 text-xs" style={{ background: "rgba(197,154,69,0.06)", borderRadius: 6, color: "var(--mil-sand)" }}>{r}</span>
                    ))}
                    {typeof m.confidence === "number" && (
                      <span className="ml-auto text-xs font-bold" style={{ color: m.confidence >= 80 ? "var(--mil-sand)" : "var(--mil-muted)" }}>{m.confidence}%</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3 mt-3">
        <input
          className="flex-1 p-2 border bg-black/20 border-black/15 mil-muted"
          placeholder="Prompt reports, ask for findings, or request summaries…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button className="btn-mil" onClick={send}>Send</button>
        <div className="ml-2">
          <button className="btn-mil" title="Quick: Summarize last hour">Summarize</button>
        </div>
      </div>
    </div>
  );
}