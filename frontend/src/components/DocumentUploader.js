import React from 'react';
import './DocumentUploader.css'; // We'll create this CSS file

function DocumentUploader({ onUpload, uploadedDocumentId }) {
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      onUpload(file);
    } else {
      alert('Please select a PDF file.');
    }
  };

  return (
    <div className="document-uploader">
      <input
        type="file"
        accept=".pdf"
        onChange={handleFileChange}
        id="document-upload"
        style={{ display: 'none' }}
      />
      <label htmlFor="document-upload" className="upload-button">
        {uploadedDocumentId ? 'Change Document' : 'Upload PDF'}
      </label>
      {uploadedDocumentId && <p className="upload-success">Document uploaded successfully</p>}
    </div>
  );
}

export default DocumentUploader;
