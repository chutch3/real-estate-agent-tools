import React, { useState, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Select, 
  MenuItem, 
  Checkbox, 
  FormControlLabel, 
  Typography, 
  Grid 
} from '@mui/material';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';

function MissingDetails({ propertyData, onDataChange }) {
  const [formData, setFormData] = useState({
    // PropertyInfo
    formatted_address: propertyData.address || '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    zip_code: '',
    county: '',
    latitude: propertyData.location?.lat || '',
    longitude: propertyData.location?.lng || '',
    property_type: '',
    bedrooms: '',
    bathrooms: '',
    square_footage: '',
    lot_size: '',
    year_built: '',
    assessor_id: '',
    legal_description: '',
    subdivision: '',
    zoning: '',
    last_sale_date: null,
    last_sale_price: '',
    owner_occupied: false,
    // PropertyFeatures
    architecture_type: '',
    cooling: false,
    cooling_type: '',
    exterior_type: '',
    floor_count: '',
    foundation_type: '',
    garage: false,
    garage_type: '',
    heating: false,
    heating_type: '',
    pool: false,
    roof_type: '',
    room_count: '',
    unit_count: '',
  });

  useEffect(() => {
    onDataChange(formData);
  }, [formData, onDataChange]);

  const handleInputChange = (event) => {
    const { name, value, type, checked } = event.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleDateChange = (date) => {
    setFormData(prevData => ({
      ...prevData,
      last_sale_date: date
    }));
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>Basic Information</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Formatted Address"
              name="formatted_address"
              value={formData.formatted_address}
              onChange={handleInputChange}
              disabled
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Address Line 1"
              name="address_line1"
              value={formData.address_line1}
              onChange={handleInputChange}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Address Line 2"
              name="address_line2"
              value={formData.address_line2}
              onChange={handleInputChange}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="City"
              name="city"
              value={formData.city}
              onChange={handleInputChange}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="State"
              name="state"
              value={formData.state}
              onChange={handleInputChange}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="Zip Code"
              name="zip_code"
              value={formData.zip_code}
              onChange={handleInputChange}
            />
          </Grid>
        </Grid>

        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Property Details</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Property Type"
              name="property_type"
              select
              value={formData.property_type}
              onChange={handleInputChange}
            >
              <MenuItem value="single_family">Single Family</MenuItem>
              <MenuItem value="multi_family">Multi Family</MenuItem>
              <MenuItem value="condo">Condo</MenuItem>
              <MenuItem value="townhouse">Townhouse</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="Bedrooms"
              name="bedrooms"
              type="number"
              value={formData.bedrooms}
              onChange={handleInputChange}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="Bathrooms"
              name="bathrooms"
              type="number"
              value={formData.bathrooms}
              onChange={handleInputChange}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Square Footage"
              name="square_footage"
              type="number"
              value={formData.square_footage}
              onChange={handleInputChange}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Lot Size"
              name="lot_size"
              type="number"
              value={formData.lot_size}
              onChange={handleInputChange}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Year Built"
              name="year_built"
              type="number"
              value={formData.year_built}
              onChange={handleInputChange}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <DatePicker
              label="Last Sale Date"
              value={formData.last_sale_date}
              onChange={handleDateChange}
              renderInput={(params) => <TextField {...params} fullWidth />}
            />
          </Grid>
        </Grid>

        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Features</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.cooling}
                  onChange={handleInputChange}
                  name="cooling"
                />
              }
              label="Cooling"
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.heating}
                  onChange={handleInputChange}
                  name="heating"
                />
              }
              label="Heating"
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.pool}
                  onChange={handleInputChange}
                  name="pool"
                />
              }
              label="Pool"
            />
          </Grid>
          {/* Add more feature fields as needed */}
        </Grid>
      </Box>
    </LocalizationProvider>
  );
}

export default MissingDetails;
