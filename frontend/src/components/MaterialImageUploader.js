import React from 'react';
import { Button, Box, Typography, ImageList, ImageListItem, ImageListItemBar } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';

function MaterialImageUploader({ selectedImages, onImagesSelected, onImageRemove }) {
  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);
    onImagesSelected(files);
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 600, margin: '0 auto' }}>
      <input
        accept="image/*"
        style={{ display: 'none' }}
        id="raised-button-file"
        multiple
        type="file"
        onChange={handleFileChange}
      />
      <label htmlFor="raised-button-file">
        <Button
          variant="contained"
          component="span"
          startIcon={<AddPhotoAlternateIcon />}
          sx={{ mb: 2 }}
        >
          Select Images
        </Button>
      </label>
      {selectedImages.length > 0 && (
        <>
          <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
            Selected Images:
          </Typography>
          <ImageList sx={{ width: '100%', height: 450 }} cols={3} rowHeight={164}>
            {selectedImages.map((file, index) => (
              <ImageListItem key={index}>
                <img
                  src={URL.createObjectURL(file)}
                  alt={file.name}
                  loading="lazy"
                  style={{ objectFit: 'cover', width: '100%', height: '100%' }}
                />
                <ImageListItemBar
                  title={file.name}
                  subtitle={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                  actionIcon={
                    <Button
                      sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                      onClick={() => onImageRemove(index)}
                    >
                      <DeleteIcon />
                    </Button>
                  }
                />
              </ImageListItem>
            ))}
          </ImageList>
        </>
      )}
    </Box>
  );
}

export default MaterialImageUploader;
