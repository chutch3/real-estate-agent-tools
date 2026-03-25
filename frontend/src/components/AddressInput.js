import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLoadScript } from '@react-google-maps/api';
import { MapPin } from 'lucide-react';

const libraries = ['places'];

function AddressInput({ onGeocodeComplete }) {
  const [address, setAddress] = useState('');
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
      if (place.geometry && place.geometry.location) {
        const newLocation = {
          lat: place.geometry.location.lat(),
          lng: place.geometry.location.lng(),
        };
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

  if (loadError) return <p className="font-sans text-sm text-red-700">Error loading Google Maps</p>;
  if (!isLoaded) return <p className="font-sans text-sm text-ink-400">Loading…</p>;

  return (
    <div className="relative">
      <label htmlFor="address-input" className="block font-sans text-xs uppercase tracking-widest text-ink-400 mb-1.5">
        Property Address
      </label>
      <div className="relative">
        <MapPin
          size={15}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-bronze-400 pointer-events-none"
          strokeWidth={1.5}
        />
        <input
          id="address-input"
          ref={inputRef}
          type="text"
          placeholder="Enter address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          className="w-full pl-9 pr-4 py-2.5 border border-linen-300 rounded-md bg-white font-sans text-sm text-ink-900 placeholder-ink-300 focus:outline-none focus:border-bronze-400 transition-colors"
          aria-label="Enter address"
          autoComplete="off"
        />
      </div>
      {address && (
        <p className="mt-1.5 font-sans text-xs text-ink-400 italic">
          {address}
        </p>
      )}
    </div>
  );
}

export default AddressInput;
