import React, { useRef, useState, useEffect } from 'react';
import { X, Home, Upload, Sparkles, FileText, Star, Loader2, Trash2 } from 'lucide-react';

function PropertyDetailPanel({ property, onClose, onChat, onGeneratePost, onUploadDocument, onDeleteDocument, isUploading, uploadError, deleteError }) {
  const fileInputRef = useRef(null);
  const [uploadingFileName, setUploadingFileName] = useState(null);

  useEffect(() => {
    if (!isUploading) setUploadingFileName(null);
  }, [isUploading]);

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
      setUploadingFileName(files[0].name);
      onUploadDocument(property, files);
      event.target.value = '';
    }
  };

  return (
    <>
      {/* Backdrop */}
      {property && (
        <div
          className="absolute inset-0 bg-ink-900/10"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className={`absolute inset-y-0 right-0 w-80 bg-white border-l border-linen-200 shadow-2xl flex flex-col
          transform transition-transform duration-300 ease-in-out
          ${property ? 'translate-x-0' : 'translate-x-full'}`}
      >
        {property && (
          <div
            data-testid="property-detail-panel"
            role="complementary"
            aria-label="Property details"
            className="flex flex-col h-full"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-linen-200">
              <Home size={18} className="text-bronze-500" strokeWidth={1.5} />
              <button
                aria-label="close"
                onClick={onClose}
                className="p-1.5 rounded-md text-ink-400 hover:text-ink-900 hover:bg-linen-100 transition-colors focus:outline-none focus:ring-2 focus:ring-bronze-300"
              >
                <X size={15} />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-6">
              {/* Address */}
              <div className="animate-fade-up" style={{ animationFillMode: 'both' }}>
                <p className="font-sans text-xs uppercase tracking-widest text-ink-400 mb-1.5">Address</p>
                <p className="font-serif text-lg leading-snug text-ink-900">
                  {property.formatted_address}
                </p>
              </div>

              {/* Actions */}
              <div className="flex flex-col gap-2 animate-fade-up" style={{ animationDelay: '40ms', animationFillMode: 'both' }}>
                <button
                  onClick={() => onChat(property)}
                  className="w-full py-2.5 px-4 bg-bronze-500 hover:bg-bronze-600 text-white font-sans text-sm rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-bronze-300"
                >
                  Chat
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="w-full py-2.5 px-4 border border-linen-300 hover:border-bronze-400 text-ink-700 hover:text-bronze-600 disabled:text-ink-300 disabled:border-linen-200 disabled:cursor-not-allowed font-sans text-sm rounded-md transition-colors flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-bronze-300"
                >
                  {isUploading ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} strokeWidth={2} />}
                  {isUploading ? 'Uploading…' : 'Upload Docs'}
                </button>
                <button
                  onClick={() => onGeneratePost(property)}
                  className="w-full py-2.5 px-4 border border-linen-300 hover:border-bronze-400 text-ink-700 hover:text-bronze-600 font-sans text-sm rounded-md transition-colors flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-bronze-300"
                >
                  <Sparkles size={13} strokeWidth={2} />
                  Generate
                </button>
              </div>

              {uploadError && (
                <p role="alert" className="font-sans text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                  {uploadError}
                </p>
              )}

              {deleteError && (
                <p role="alert" className="font-sans text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                  {deleteError}
                </p>
              )}

              {/* Documents */}
              <div className="animate-fade-up" style={{ animationDelay: '80ms', animationFillMode: 'both' }}>
                <p className="font-sans text-xs uppercase tracking-widest text-ink-400 mb-2">Documents</p>
                {(property.documents || []).length === 0 && !uploadingFileName ? (
                  <p className="font-sans text-sm text-ink-300">No documents attached</p>
                ) : (
                  <ul className="space-y-1" role="list">
                    {(property.documents || []).map((doc) => (
                      <li key={doc.id} className="flex items-center gap-2.5 py-1">
                        <FileText size={13} className="text-ink-400 flex-shrink-0" strokeWidth={1.5} />
                        <a
                          href={`${process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000'}/documents/${doc.id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="font-sans text-sm text-bronze-500 hover:text-bronze-700 hover:underline truncate flex-1"
                        >
                          {doc.filename}
                        </a>
                        <button
                          aria-label={`Delete ${doc.filename}`}
                          onClick={() => onDeleteDocument(property, doc.id)}
                          className="p-1 text-ink-300 hover:text-red-500 transition-colors focus:outline-none"
                        >
                          <Trash2 size={12} strokeWidth={1.5} />
                        </button>
                      </li>
                    ))}
                    {uploadingFileName && (
                      <li className="flex items-center gap-2.5 py-1" aria-label={`Uploading ${uploadingFileName}`}>
                        <Loader2 size={13} className="text-bronze-400 animate-spin flex-shrink-0" />
                        <span className="font-sans text-sm text-ink-400 italic">{uploadingFileName}</span>
                      </li>
                    )}
                  </ul>
                )}
              </div>

              {/* Ratings */}
              <div className="animate-fade-up" style={{ animationDelay: '120ms', animationFillMode: 'both' }}>
                <p className="font-sans text-xs uppercase tracking-widest text-ink-400 mb-2">Ratings</p>
                <div className="flex gap-1" role="img" aria-label="No rating">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Star key={s} size={15} className="text-linen-300" strokeWidth={1.5} />
                  ))}
                </div>
              </div>

              {/* Climate */}
              <div className="animate-fade-up" style={{ animationDelay: '160ms', animationFillMode: 'both' }}>
                <p className="font-sans text-xs uppercase tracking-widest text-ink-400 mb-2">Climate</p>
                <div className="flex gap-1" role="img" aria-label="No climate rating">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Star key={s} size={15} className="text-linen-300" strokeWidth={1.5} />
                  ))}
                </div>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              multiple
              className="hidden"
              onChange={handleFileChange}
              aria-hidden="true"
            />
          </div>
        )}
      </div>
    </>
  );
}

export default PropertyDetailPanel;
