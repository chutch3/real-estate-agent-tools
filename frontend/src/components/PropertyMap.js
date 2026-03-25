import React, { useState, useEffect, useRef } from 'react';
import { GoogleMap, Marker, useLoadScript } from '@react-google-maps/api';

const defaultCenter = { lat: 37.7749, lng: -122.4194 };
const mapContainerStyle = { width: '100%', height: '100%' };
const libraries = ['places'];

function PropertyMap({ properties, onPropertySelect }) {
  const [center, setCenter] = useState(defaultCenter);
  const mapRef = useRef(null);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        const location = { lat: position.coords.latitude, lng: position.coords.longitude };
        setCenter(location);
        mapRef.current?.panTo(location);
      });
    }
  }, []);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
    libraries,
  });

  if (loadError) return <div>Error loading maps</div>;
  if (!isLoaded) return <div>Loading maps</div>;

  return (
    <GoogleMap
      mapContainerStyle={mapContainerStyle}
      center={center}
      zoom={10}
      onLoad={(map) => { mapRef.current = map; }}
    >
      {properties
        .filter((property) => property.latitude !== 0 || property.longitude !== 0)
        .map((property) => (
          <Marker
            key={property.id}
            position={{ lat: property.latitude, lng: property.longitude }}
            onClick={() => onPropertySelect(property)}
          />
        ))}
    </GoogleMap>
  );
}

export default PropertyMap;
