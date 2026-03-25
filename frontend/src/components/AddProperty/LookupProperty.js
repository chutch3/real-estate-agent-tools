import React, { useState, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import AddressInput from '../AddressInput';
import MapComponent from '../MapComponent';
import apiClient from '../../apiClient';

function LookupProperty({ onDataChange }) {
  const [location, setLocation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGeocodeComplete = useCallback(
    async (fullAddress, geocodedLocation) => {
      setLocation(geocodedLocation);
      setIsLoading(true);
      setError('');
      try {
        const propertyDetails = await apiClient.getPropertyDetails(fullAddress);
        onDataChange({ address: fullAddress, location: geocodedLocation, ...propertyDetails });
      } catch {
        setError('Failed to fetch property details. Please try again.');
      } finally {
        setIsLoading(false);
      }
    },
    [onDataChange]
  );

  return (
    <div>
      <h2 className="font-serif text-2xl text-ink-900 mb-5">Look up property</h2>
      <AddressInput onGeocodeComplete={handleGeocodeComplete} />
      {isLoading && (
        <div className="flex items-center gap-2 mt-4 text-ink-400">
          <Loader2 size={15} className="animate-spin" />
          <span className="font-sans text-sm">Fetching property details…</span>
        </div>
      )}
      {error && (
        <p className="font-sans text-sm text-red-700 mt-3" role="alert">
          {error}
        </p>
      )}
      {location && (
        <div className="mt-5 rounded-lg overflow-hidden border border-linen-200">
          <MapComponent center={location} />
        </div>
      )}
    </div>
  );
}

export default LookupProperty;
