import React, { useState } from 'react';
import { 
  Modal, 
  Box, 
  Typography, 
  Grid, 
  Paper, 
  List, 
  ListItem, 
  ListItemText,
} from '@mui/material';
import { CheckCircleOutline } from '@mui/icons-material';

const PropertySummary = ({ propertyData, images, mlsSheet, onBack, onFinish }) => {
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const handleFinish = async () => {
    try {
      await onFinish();
      setShowSuccessModal(true);
    } catch (error) {
      // Error handling is now managed in the parent component
      console.error('Error in PropertySummary:', error);
    }
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h4" gutterBottom>Property Summary</Typography>
      
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Basic Information</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Address:</strong> {propertyData.formatted_address}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Property Type:</strong> {propertyData.property_type}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Bedrooms:</strong> {propertyData.bedrooms}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Bathrooms:</strong> {propertyData.bathrooms}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Square Footage:</strong> {propertyData.square_footage}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Year Built:</strong> {propertyData.year_built}</Typography>
          </Grid>
        </Grid>
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Features</Typography>
        <List>
          {propertyData.cooling && <ListItem><ListItemText primary="Cooling" /></ListItem>}
          {propertyData.heating && <ListItem><ListItemText primary="Heating" /></ListItem>}
          {propertyData.pool && <ListItem><ListItemText primary="Pool" /></ListItem>}
          {/* Add more features as needed */}
        </List>
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Attachments</Typography>
        <Typography><strong>Images:</strong> {images.length} uploaded</Typography>
        <Typography><strong>MLS Sheet:</strong> {mlsSheet ? 'Uploaded' : 'Not uploaded'}</Typography>
      </Paper>

      <Modal
        open={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        aria-labelledby="success-modal-title"
        aria-describedby="success-modal-description"
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 400,
          bgcolor: 'background.paper',
          boxShadow: 24,
          p: 4,
          textAlign: 'center',
        }}>
          <CheckCircleOutline sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
          <Typography id="success-modal-title" variant="h5" component="h2">
            Added!
          </Typography>
          <Typography id="success-modal-description" sx={{ mt: 2 }}>
            Property has been successfully added.
          </Typography>
        </Box>
      </Modal>
    </Box>
  );
};

export default PropertySummary;
