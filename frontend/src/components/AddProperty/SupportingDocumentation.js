import React, { useState } from 'react';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import apiClient from '../../apiClient';

function SupportingDocumentation({ onDataChange }) {
  const [docs, setDocs] = useState([]);
  const [warning, setWarning] = useState('');

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    const pdfFiles = files.filter((f) => f.type === 'application/pdf');

    if (pdfFiles.length !== files.length) {
      setWarning('Only PDF files are allowed. Non-PDF files were ignored.');
    } else {
      setWarning('');
    }

    const uploaded = await Promise.all(
      pdfFiles.map(async (file) => ({
        id: await apiClient.uploadDocument(file),
        filename: file.name,
      }))
    );

    setDocs((prev) => {
      const next = [...prev, ...uploaded];
      onDataChange({ documents: next.map((d) => ({ id: d.id, filename: d.filename })) });
      return next;
    });
  };

  const handleRemove = (index) => {
    setDocs((prev) => {
      const next = prev.filter((_, i) => i !== index);
      onDataChange({ documents: next.map((d) => ({ id: d.id, filename: d.filename })) });
      return next;
    });
  };

  return (
    <div>
      <h2 className="font-serif text-2xl text-ink-900 mb-2">Supporting Documents</h2>
      <p className="font-sans text-sm text-ink-400 mb-5">
        Upload PDF documents as supporting documentation for this property.
      </p>

      {/* Upload area */}
      <label
        htmlFor="supporting-doc-upload"
        className="flex flex-col items-center justify-center gap-3 w-full py-8 px-4 border-2 border-dashed border-linen-300 rounded-lg cursor-pointer hover:border-bronze-400 hover:bg-linen-50 transition-colors group"
        aria-label="Upload PDF files"
      >
        <Upload
          size={24}
          className="text-ink-300 group-hover:text-bronze-400 transition-colors"
          strokeWidth={1.5}
        />
        <div className="text-center">
          <span className="font-sans text-sm font-medium text-ink-700 group-hover:text-bronze-600 transition-colors">
            Click to upload
          </span>
          <span className="font-sans text-sm text-ink-400"> or drag and drop</span>
          <p className="font-sans text-xs text-ink-300 mt-0.5">PDF files only</p>
        </div>
        <input
          id="supporting-doc-upload"
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={handleFileUpload}
        />
      </label>

      {warning && (
        <div className="flex items-center gap-2 mt-3 p-3 bg-amber-50 border border-amber-200 rounded-md" role="alert">
          <AlertCircle size={14} className="text-amber-600 flex-shrink-0" />
          <p className="font-sans text-sm text-amber-700">{warning}</p>
        </div>
      )}

      {docs.length > 0 && (
        <ul className="mt-4 space-y-2" role="list" aria-label="Uploaded documents">
          {docs.map((doc, index) => (
            <li
              key={doc.id}
              className="flex items-center gap-3 px-3 py-2.5 bg-linen-50 rounded-md border border-linen-200"
            >
              <FileText size={15} className="text-bronze-400 flex-shrink-0" strokeWidth={1.5} />
              <span className="font-sans text-sm text-ink-800 flex-1 truncate">{doc.filename}</span>
              <button
                onClick={() => handleRemove(index)}
                aria-label={`Remove ${doc.name}`}
                className="p-1 text-ink-300 hover:text-red-600 transition-colors rounded focus:outline-none focus:ring-2 focus:ring-red-300"
              >
                <X size={13} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default SupportingDocumentation;
