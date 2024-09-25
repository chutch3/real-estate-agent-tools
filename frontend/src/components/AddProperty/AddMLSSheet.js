import React from 'react';
import { Button, Box } from '@mui/material';

function AddMLSSheet({ onDataChange }) {
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    onDataChange({ mlsSheet: file });
  };

  return (
    <Box>
      <input
        accept=".pdf,.doc,.docx"
        style={{ display: 'none' }}
        id="mls-sheet-upload"
        type="file"
        onChange={handleFileUpload}
      />
      <label htmlFor="mls-sheet-upload">
        <Button variant="contained" component="span">
          Upload MLS Sheet
        </Button>
      </label>
    </Box>
  );
}

export default AddMLSSheet;
