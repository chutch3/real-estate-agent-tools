import React, { useCallback } from 'react';
import { GoogleMap, Marker, useLoadScript } from '@react-google-maps/api';

const defaultCenter = {
  lat: 40.7128, // New York City coordinates as default
  lng: -74.0060,
};

const defaultZoom = 15;

const MapComponent = ({ center }) => {
  const mapContainerStyle = {
    width: '100%',
    height: '400px'
  };

  const options = {
    mapTypeId: 'satellite',
    disableDefaultUI: true,
    zoomControl: true,
  };
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
    libraries: ['places'],
  });

  const onMapLoad = useCallback((map) => {
    if (center) {
      map.panTo(center);
      map.setZoom(defaultZoom);
    }
  }, [center]);

  if (loadError) return <div>Error loading maps</div>;
  if (!isLoaded) return <div>Loading maps</div>;

  return (
    <GoogleMap
      mapContainerStyle={mapContainerStyle}
      center={center || defaultCenter}
      zoom={defaultZoom}
      options={options}
      onLoad={onMapLoad}
    >
      {center && <Marker position={center} />}
    </GoogleMap>
  );
};

export default MapComponent;
