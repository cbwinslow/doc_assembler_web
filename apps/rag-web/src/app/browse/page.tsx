'use client';
import { useEffect, useState } from 'react';

interface DocMeta {
  id: string;
  title?: string;
  filename?: string;
  type?: string;
  createdAt?: string;
}

/**
 * Displays a table of documents fetched from an API, allowing users to browse document metadata.
 *
 * Fetches document metadata on mount and renders each document's title (as a link), type, creation date, and an options button in a tabular format.
 */
export default function BrowsePage() {
  const [docs, setDocs] = useState<DocMeta[]>([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/documents`)
      .then(res => res.json())
      .then(data => setDocs(data.documents || []))
      .catch(console.error);
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-4">Data Browser</h1>
      <table className="min-w-full border text-sm">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-2 py-1 text-left">Title</th>
            <th className="px-2 py-1 text-left">Type</th>
            <th className="px-2 py-1 text-left">Created</th>
            <th className="px-2 py-1 text-left">Actions</th>
          </tr>
        </thead>
        <tbody>
          {docs.map(doc => (
            <tr key={doc.id} className="border-b">
              <td className="px-2 py-1">
                <a href={`/docs/${doc.id}`} className="text-blue-600 hover:underline">
                  {doc.title || doc.filename || doc.id}
                </a>
              </td>
              <td className="px-2 py-1">{doc.type}</td>
              <td className="px-2 py-1">{doc.createdAt ? new Date(doc.createdAt).toLocaleString() : ''}</td>
              <td className="px-2 py-1">
                <button className="border px-2 py-1">Options</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
