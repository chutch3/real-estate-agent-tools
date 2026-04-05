import React, { useState, useEffect, useRef } from 'react';
import { GoogleMap, Marker, Polygon, useLoadScript } from '@react-google-maps/api';
import useLayers from '../hooks/useLayers';
import MapLayerControls from './MapLayerControls';
import CrimeLayerLegend from './CrimeLayerLegend';

const defaultCenter = { lat: 37.7749, lng: -122.4194 };
const mapContainerStyle = { width: '100%', height: '100%' };
const libraries = ['places'];

function PropertyMap({ properties, onPropertySelect, selectedProperty }) {
  const [center, setCenter] = useState(defaultCenter);
  const [mapInstance, setMapInstance] = useState(null);
  const mapRef = useRef(null);
  const { groups, isActive, toggle } = useLayers(mapInstance, selectedProperty?.county_fips ?? null);

  const hasLayers = groups.flatMap((g) => g.categories).length > 0;

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        const location = { lat: position.coords.latitude, lng: position.coords.longitude };
        setCenter(location);
        mapRef.current?.panTo(location);
      });
    }
  }, []);

  useEffect(() => {
    if (!mapRef.current || !selectedProperty?.latitude || !selectedProperty?.longitude) return;
    mapRef.current.panTo({ lat: selectedProperty.latitude, lng: selectedProperty.longitude });
    mapRef.current.setZoom(14);
  }, [selectedProperty, mapInstance]);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
    libraries,
  });

  if (loadError) return <div>Error loading maps</div>;
  if (!isLoaded) return <div>Loading maps</div>;

  return (
    <div className="relative w-full h-full">
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        center={center}
        zoom={10}
        onLoad={(map) => {
          mapRef.current = map;
          setMapInstance(map);
        }}
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
        {selectedProperty?.county_polygon && (
          <Polygon
            paths={selectedProperty.county_polygon.coordinates[0].map(([lng, lat]) => ({ lat, lng }))}
            options={{ strokeColor: '#92400e', strokeWeight: 2, fillOpacity: 0 }}
          />
        )}
      </GoogleMap>
      {hasLayers && (
        <>
          <MapLayerControls groups={groups} isActive={isActive} onToggle={toggle} />
          <CrimeLayerLegend groups={groups} isActive={isActive} panelOpen={!!selectedProperty} />
        </>
      )}
    </div>
  );
}

export default PropertyMap;
