import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLoadScript, GoogleMap, MarkerF } from '@react-google-maps/api';
import { TextField, Box, Typography } from '@mui/material';
import './AddressInput.css';

const libraries = ['places'];
const mapContainerStyle = {
  width: '100%',
  height: '300px',
  marginTop: '20px',
};

function AddressInput({ onAddressChange }) {
  const [address, setAddress] = useState('');
  const [geocodedAddress, setGeocodedAddress] = useState('');
  const [mapCenter, setMapCenter] = useState(null);
  const autocompleteRef = useRef(null);
  const mapRef = useRef(null);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
    libraries,
  });

  const onMapLoad = useCallback((map) => {
    mapRef.current = map;
  }, []);

  useEffect(() => {
    if (isLoaded && !loadError) {
      const autocomplete = new window.google.maps.places.Autocomplete(
        autocompleteRef.current.querySelector('input'),
        { types: ['address'] }
      );

      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (place.formatted_address) {
          setAddress(place.formatted_address);
          setGeocodedAddress(place.formatted_address);
          onAddressChange(place.formatted_address);
          if (place.geometry && place.geometry.location) {
            const newCenter = {
              lat: place.geometry.location.lat(),
              lng: place.geometry.location.lng(),
            };
            setMapCenter(newCenter);
            if (mapRef.current) {
              mapRef.current.panTo(newCenter);
              mapRef.current.setZoom(15);
            }
          }
        }
      });
    }
  }, [isLoaded, loadError, onAddressChange]);

  const handleChange = (e) => {
    const newAddress = e.target.value;
    setAddress(newAddress);
    onAddressChange(newAddress);
    // Clear geocoded address and map when user starts typing
    setGeocodedAddress('');
    setMapCenter(null);
  };

  if (loadError) return <div>Error loading Google Maps</div>;
  if (!isLoaded) return <div>Loading...</div>;

  return (
    <Box sx={{ width: '100%', maxWidth: '600px', margin: '0 auto' }}>
      <TextField
        ref={autocompleteRef}
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
      {mapCenter && (
        <GoogleMap
          mapContainerStyle={mapContainerStyle}
          zoom={15}
          center={mapCenter}
          onLoad={onMapLoad}
        >
          <MarkerF 
            position={mapCenter}
            icon={{
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 7,
              fillColor: "#F00",
              fillOpacity: 1,
              strokeWeight: 2,
              strokeColor: "#FFF",
            }}
          />
        </GoogleMap>
      )}
    </Box>
  );
}

export default AddressInput;
