import React, { useState, useCallback } from 'react';
import { Box, Typography } from '@mui/material';
import AddressInput from '../AddressInput';
import MapComponent from '../MapComponent';


function LookupProperty({ onDataChange }) {
  const [location, setLocation] = useState(null);
  const [error, setError] = useState('');

  const handleGeocodeComplete = useCallback((fullAddress, geocodedLocation) => {
    setLocation(geocodedLocation);
    onDataChange({ address: fullAddress, location: geocodedLocation });
  }, [onDataChange]);


  return (
    <Box sx={{ maxWidth: 600, margin: 'auto', mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Look up property
      </Typography>
      <AddressInput 
        onGeocodeComplete={handleGeocodeComplete}
      />
      <MapComponent center={location} />
    </Box>
  );
}

export default LookupProperty;
