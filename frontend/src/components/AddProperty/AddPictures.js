import React from 'react';
import { Box } from '@mui/material';
import MaterialImageUploader from '../MaterialImageUploader';

function AddPictures({ selectedImages, onImagesSelected }) {
  return (
    <Box>
      <MaterialImageUploader
        selectedImages={selectedImages}
        onImagesSelected={onImagesSelected}
      />
    </Box>
  );
}

export default AddPictures;
