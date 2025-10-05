// src/components/Reports.tsx
import React, { useState } from "react";
import { fetchReport } from "../api";
import jsPDF from "jspdf";

const REPORT_TYPES = [
  { type: "opord", label: "OPORD" },
  { type: "frago", label: "FRAGO" },
  { type: "eoincrep", label: "EOINCREP" },
  { type: "casevac", label: "CASEVAC" },
];

export default function Reports() {
  const [type, setType] = useState("opord");
  const [query, setQuery] = useState("");
  const [report, setReport] = useState("");
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const res = await fetchReport(type, query);
      setReport(res?.body ?? JSON.stringify(res));
    } catch (err) {
      setReport("Error generating report: " + String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = () => {
    const doc = new jsPDF();
    doc.text(report, 10, 10);
    doc.save(`${type}.pdf`);
  };

  return (
    <div className="p-4">
      <div className="flex gap-2 mb-4">
        <select value={type} onChange={(e) => setType(e.target.value)}>
          {REPORT_TYPES.map((r) => (
            <option key={r.type} value={r.type}>{r.label}</option>
          ))}
        </select>
        <input className="p-2 border" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="query" />
        <button className="px-3 py-1 text-white bg-blue-600 rounded" onClick={generate} disabled={loading}>
          {loading ? "Generating..." : "Generate"}
        </button>
      </div>
      <textarea className="w-full h-64 p-2 border" value={report} readOnly />
      <div className="mt-2">
        <button className="btn btn-secondary" onClick={handleDownloadPDF} disabled={!report}>
          Download PDF
        </button>
      </div>
    </div>
  );
}