import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLoadScript } from '@react-google-maps/api';
import { TextField, Box, Typography } from '@mui/material';
import './AddressInput.css';

const libraries = ['places'];

function AddressInput({ onGeocodeComplete }) {
  const [address, setAddress] = useState('');
  const [geocodedAddress, setGeocodedAddress] = useState('');
  const inputRef = useRef(null);
  const autocompleteRef = useRef(null);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
    libraries,
  });

  const handlePlaceSelect = useCallback(() => {
    const place = autocompleteRef.current.getPlace();
    if (place.formatted_address) {
      setAddress(place.formatted_address);
      setGeocodedAddress(place.formatted_address);
      if (place.geometry && place.geometry.location) {
        const newLocation = {
          lat: place.geometry.location.lat(),
          lng: place.geometry.location.lng(),
        };
        console.log("Calling onGeocodeComplete with:", place.formatted_address, newLocation);
        onGeocodeComplete(place.formatted_address, newLocation);
      }
    }
  }, [onGeocodeComplete]);

  useEffect(() => {
    if (isLoaded && !loadError && inputRef.current) {
      autocompleteRef.current = new window.google.maps.places.Autocomplete(
        inputRef.current,
        { types: ['address'] }
      );
      autocompleteRef.current.addListener('place_changed', handlePlaceSelect);

      return () => {
        if (autocompleteRef.current) {
          window.google.maps.event.clearInstanceListeners(autocompleteRef.current);
        }
      };
    }
  }, [isLoaded, loadError, handlePlaceSelect]);

  const handleChange = (e) => {
    setAddress(e.target.value);
    setGeocodedAddress('');
  };

  if (loadError) return <div>Error loading Google Maps</div>;
  if (!isLoaded) return <div>Loading...</div>;

  return (
    <Box sx={{ width: '100%', maxWidth: '600px', margin: '0 auto' }}>
      <TextField
        inputRef={inputRef}
        fullWidth
        variant="outlined"
        label="Enter address"
        value={address}
        onChange={handleChange}
        margin="normal"
      />
      {geocodedAddress && (
        <Typography 
          variant="body2" 
          sx={{ mt: 1, color: 'text.secondary', fontStyle: 'italic' }}
        >
          Resolved address: {geocodedAddress}
        </Typography>
      )}
    </Box>
  );
}

export default AddressInput;
