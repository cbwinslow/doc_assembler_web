'use client';
import { useEffect, useState } from 'react';

interface DocMeta {
  id: string;
  title?: string;
  filename?: string;
}

export default function ReportPage() {
  const [docs, setDocs] = useState<DocMeta[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [report, setReport] = useState('');

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/documents`)
      .then(res => res.json())
      .then(data => setDocs(data.documents || []))
      .catch(console.error);
  }, []);

  async function generateReport() {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/rag/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: selected.join(' ') })
    });
    const data = await res.json();
    setReport(data.answer);
  }

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-4">Report Writer</h1>
      <div className="flex gap-4">
        <div className="w-1/3 border divide-y">
          {docs.map(doc => (
            <label key={doc.id} className="flex items-center gap-2 p-1">
              <input
                type="checkbox"
                value={doc.id}
                onChange={e => {
                  if (e.target.checked) setSelected([...selected, doc.id]);
                  else setSelected(selected.filter(id => id !== doc.id));
                }}
              />
              <span>{doc.title || doc.filename || doc.id}</span>
            </label>
          ))}
        </div>
        <div className="flex-1">
          <button className="border px-2 py-1 mb-2" onClick={generateReport}>Generate Report</button>
          <textarea className="w-full h-64 border p-2" value={report} readOnly />
        </div>
      </div>
    </div>
  );
}
