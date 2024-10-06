import React from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Paper, 
  List, 
  ListItem, 
  ListItemText,
} from '@mui/material';


const PropertySummary = ({ propertyData, images, supportingDocs}) => {
  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h4" gutterBottom>Property Summary</Typography>
      
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Basic Information</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Address:</strong> {propertyData.formattedAddress}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Property Type:</strong> {propertyData.propertyType}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Bedrooms:</strong> {propertyData.bedrooms}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Bathrooms:</strong> {propertyData.bathrooms}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Square Footage:</strong> {propertyData.squareFootage}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography><strong>Year Built:</strong> {propertyData.yearBuilt}</Typography>
          </Grid>
        </Grid>
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Features</Typography>
        <List>
          {Object.entries(propertyData.features || {}).map(([feature, value]) => (
            value && (
              <ListItem key={feature}>
                <ListItemText primary={feature.charAt(0).toUpperCase() + feature.slice(1)} />
              </ListItem>
            )
          ))}
        </List>
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Attachments</Typography>
        <Typography variant="subtitle1" gutterBottom><strong>Images:</strong></Typography>
        <Grid container spacing={2}>
          {images.map((image, index) => (
            <Grid item xs={4} key={index}>
              <img src={URL.createObjectURL(image)} alt={`Property image ${index + 1}`} style={{ width: '100%', height: 'auto' }} />
            </Grid>
          ))}
        </Grid>
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}><strong>Supporting Documents:</strong></Typography>
        <Grid container spacing={2}>
          {supportingDocs.map((doc, index) => (
            <Grid item xs={4} key={index}>
              {doc.type.startsWith('image/') ? (
                <img src={URL.createObjectURL(doc)} alt={`Supporting document ${index + 1}`} style={{ width: '100%', height: 'auto' }} />
              ) : (
                <Box sx={{ p: 2, border: '1px solid #ccc', borderRadius: 2 }}>
                  <Typography>{doc.name}</Typography>
                </Box>
              )}
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
};

export default PropertySummary;
