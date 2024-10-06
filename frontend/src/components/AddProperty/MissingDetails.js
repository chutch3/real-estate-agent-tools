import React from 'react';
import { TextField, Box, Typography, Checkbox, FormControlLabel, Card, CardContent, Grid } from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';

function MissingDetails({ propertyData, onDataChange }) {
  const handleInputChange = (event) => {
    const { name, value, type, checked } = event.target;
    onDataChange({ [name]: type === 'checkbox' ? checked : value });
  };

  const handleDateChange = (name, value) => {
    onDataChange({ [name]: value });
  };

  const handleFeatureChange = (event) => {
    const { name, value, type, checked } = event.target;
    onDataChange({
      features: {
        ...propertyData.features,
        [name]: type === 'checkbox' ? checked : value
      }
    });
  };

  const renderTextField = (label, name, value, onChange, type = "text", multiline = false, rows = 1) => (
    <TextField
      fullWidth
      label={label}
      name={name}
      value={value || ''}
      onChange={onChange}
      type={type}
      multiline={multiline}
      rows={rows}
      margin="normal"
    />
  );

  const renderCheckbox = (label, name, checked, onChange) => (
    <FormControlLabel
      control={
        <Checkbox
          checked={checked || false}
          onChange={onChange}
          name={name}
        />
      }
      label={label}
    />
  );

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ maxWidth: 800, margin: 'auto', mt: 4 }}>
        <Typography variant="h5" gutterBottom>
          Property Details
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Location Information
                </Typography>
                {renderTextField("Formatted Address", "formattedAddress", propertyData.formattedAddress, handleInputChange, "text", false, 1, true)}
                {renderTextField("Address Line 1", "addressLine1", propertyData.addressLine1, handleInputChange, "text", false, 1, true)}
                {renderTextField("Address Line 2", "addressLine2", propertyData.addressLine2, handleInputChange, "text", false, 1, true)}
                {renderTextField("City", "city", propertyData.city, handleInputChange, "text", false, 1, true)}
                {renderTextField("State", "state", propertyData.state, handleInputChange, "text", false, 1, true)}
                {renderTextField("Zip Code", "zipCode", propertyData.zipCode, handleInputChange, "text", false, 1, true)}
                {renderTextField("County", "county", propertyData.county, handleInputChange)}
                {renderTextField("Latitude", "latitude", propertyData.latitude, handleInputChange, "number")}
                {renderTextField("Longitude", "longitude", propertyData.longitude, handleInputChange, "number")}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Property Characteristics
                </Typography>
                {renderTextField("Property Type", "propertyType", propertyData.propertyType, handleInputChange)}
                {renderTextField("Bedrooms", "bedrooms", propertyData.bedrooms, handleInputChange, "number")}
                {renderTextField("Bathrooms", "bathrooms", propertyData.bathrooms, handleInputChange, "number")}
                {renderTextField("Square Footage", "squareFootage", propertyData.squareFootage, handleInputChange, "number")}
                {renderTextField("Lot Size", "lotSize", propertyData.lotSize, handleInputChange, "number")}
                {renderTextField("Year Built", "yearBuilt", propertyData.yearBuilt, handleInputChange, "number")}
                {renderTextField("Assessor ID", "assessorID", propertyData.assessorID, handleInputChange)}
                {renderTextField("Legal Description", "legalDescription", propertyData.legalDescription, handleInputChange, "text", true, 3)}
                {renderTextField("Subdivision", "subdivision", propertyData.subdivision, handleInputChange)}
                {renderTextField("Zoning", "zoning", propertyData.zoning, handleInputChange)}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Sale Information
                </Typography>
                <DatePicker
                  label="Last Sale Date"
                  value={propertyData.lastSaleDate ? new Date(propertyData.lastSaleDate) : null}
                  onChange={(newValue) => handleDateChange('lastSaleDate', newValue)}
                  renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
                />
                {renderTextField("Last Sale Price", "lastSalePrice", propertyData.lastSalePrice, handleInputChange, "number")}
                {renderCheckbox("Owner Occupied", "ownerOccupied", propertyData.ownerOccupied, handleInputChange)}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Property Features
                </Typography>
                {renderTextField("Architecture Type", "architectureType", propertyData.features?.architectureType, handleFeatureChange)}
                {renderCheckbox("Cooling", "cooling", propertyData.features?.cooling, handleFeatureChange)}
                {renderTextField("Cooling Type", "coolingType", propertyData.features?.coolingType, handleFeatureChange)}
                {renderTextField("Exterior Type", "exteriorType", propertyData.features?.exteriorType, handleFeatureChange)}
                {renderTextField("Floor Count", "floorCount", propertyData.features?.floorCount, handleFeatureChange, "number")}
                {renderTextField("Foundation Type", "foundationType", propertyData.features?.foundationType, handleFeatureChange)}
                {renderCheckbox("Garage", "garage", propertyData.features?.garage, handleFeatureChange)}
                {renderTextField("Garage Type", "garageType", propertyData.features?.garageType, handleFeatureChange)}
                {renderCheckbox("Heating", "heating", propertyData.features?.heating, handleFeatureChange)}
                {renderTextField("Heating Type", "heatingType", propertyData.features?.heatingType, handleFeatureChange)}
                {renderCheckbox("Pool", "pool", propertyData.features?.pool, handleFeatureChange)}
                {renderTextField("Roof Type", "roofType", propertyData.features?.roofType, handleFeatureChange)}
                {renderTextField("Room Count", "roomCount", propertyData.features?.roomCount, handleFeatureChange, "number")}
                {renderTextField("Unit Count", "unitCount", propertyData.features?.unitCount, handleFeatureChange, "number")}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </LocalizationProvider>
  );
}

export default MissingDetails;
