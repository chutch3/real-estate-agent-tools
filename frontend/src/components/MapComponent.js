import React from 'react';
import { GoogleMap, Marker } from '@react-google-maps/api';

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

  return (
    <GoogleMap
      mapContainerStyle={mapContainerStyle}
      center={center}
      zoom={18}
      options={options}
    >
      <Marker position={center} />
    </GoogleMap>
  );
};

export default MapComponent;
