import React, { useState, useCallback } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import AddressInput from '../AddressInput';
import MapComponent from '../MapComponent';
import apiClient from '../../apiClient';

function LookupProperty({ onDataChange }) {
  const [location, setLocation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGeocodeComplete = useCallback(async (fullAddress, geocodedLocation) => {
    setLocation(geocodedLocation);
    setIsLoading(true);
    setError('');

    try {
      const propertyDetails = await apiClient.getPropertyDetails(fullAddress);
      onDataChange({ 
        address: fullAddress, 
        location: geocodedLocation,
        ...propertyDetails 
      });
    } catch (error) {
      setError('Failed to fetch property details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [onDataChange]);

  return (
    <Box sx={{ maxWidth: 600, margin: 'auto', mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Look up property
      </Typography>
      <AddressInput onGeocodeComplete={handleGeocodeComplete} />
      <MapComponent center={location} />
      {isLoading && <CircularProgress sx={{ mt: 2 }} />}
      {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
    </Box>
  );
}

export default LookupProperty;
