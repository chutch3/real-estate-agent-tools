import React, { useState } from 'react';
import { Button, Box, Typography, List, ListItem, ListItemText, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import apiClient from '../../apiClient';

function SupportingDocumentation({ onDataChange }) {
  const [supportingDocs, setSupportingDocs] = useState([]);

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    const pdfFiles = files.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== files.length) {
      alert('Only PDF files are allowed. Non-PDF files were ignored.');
    }
    const docIds = await Promise.all(pdfFiles.map(file => apiClient.uploadDocument(file)));

    setSupportingDocs(prevDocIds => [...prevDocIds, ...docIds]);
    onDataChange({ supportingDocs: supportingDocs });
  };

  const handleRemoveFile = async (index) => {
    const updatedDocs = supportingDocs.filter((_, i) => i !== index);
    
    setSupportingDocs(updatedDocs);
    onDataChange({ supportingDocs: updatedDocs });
  };

  return (
    <Box>
      <input
        accept=".pdf"
        style={{ display: 'none' }}
        id="supporting-doc-upload"
        type="file"
        multiple
        onChange={handleFileUpload}
      />
      <label htmlFor="supporting-doc-upload">
        <Button variant="contained" component="span">
          Upload Supporting Documents
        </Button>
      </label>
      <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
        Upload PDF documents as supporting documentation.
      </Typography>
      {supportingDocs.length > 0 && (
        <List>
          {supportingDocs.map((doc, index) => (
            <ListItem key={index} secondaryAction={
              <IconButton edge="end" aria-label="delete" onClick={() => handleRemoveFile(index)}>
                <DeleteIcon />
              </IconButton>
            }>
              <ListItemText primary={doc.name} />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}

export default SupportingDocumentation;
