import React, { useState, useEffect } from 'react';
import { TextField, Button, Box, Typography } from '@mui/material';
import apiClient from '../apiClient';

function DefaultPromptEditor({ onCustomTemplateChange }) {
  const [defaultTemplate, setDefaultTemplate] = useState('');
  const [customTemplate, setCustomTemplate] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    const fetchDefaultTemplate = async () => {
      try {
        const response = await apiClient.getDefaultTemplate();
        setDefaultTemplate(response.template);
        setCustomTemplate(response.template);
      } catch (error) {
        console.error('Error fetching default template:', error);
      }
    };
    fetchDefaultTemplate();
  }, []);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSave = () => {
    setIsEditing(false);
    onCustomTemplateChange(customTemplate);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setCustomTemplate(defaultTemplate);
    onCustomTemplateChange(null);
  };

  return (
    <Box sx={{ mt: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>
        Default Prompt
      </Typography>
      {isEditing ? (
        <>
          <TextField
            fullWidth
            multiline
            rows={6}
            value={customTemplate}
            onChange={(e) => setCustomTemplate(e.target.value)}
            variant="outlined"
            margin="normal"
          />
          <Box sx={{ mt: 1 }}>
            <Button variant="contained" color="primary" onClick={handleSave} sx={{ mr: 1 }}>
              Save Changes
            </Button>
            <Button variant="outlined" onClick={handleCancel}>
              Cancel
            </Button>
          </Box>
        </>
      ) : (
        <>
          <Typography variant="body1" gutterBottom>
            {defaultTemplate}
          </Typography>
          <Button variant="outlined" color="primary" onClick={handleEdit}>
            Modify Default Prompt
          </Button>
        </>
      )}
    </Box>
  );
}

export default DefaultPromptEditor;
