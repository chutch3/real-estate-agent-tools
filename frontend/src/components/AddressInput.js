import React, { useState, useEffect, useRef } from 'react';
import { useLoadScript } from '@react-google-maps/api';
import './AddressInput.css';

const libraries = ['places'];

function AddressInput({ onGenerate }) {
  const [address, setAddress] = useState('');
  const autocompleteRef = useRef(null);
  const inputRef = useRef(null);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
    libraries,
  });

  useEffect(() => {
    if (isLoaded && !autocompleteRef.current && inputRef.current) {
      autocompleteRef.current = new window.google.maps.places.Autocomplete(
        inputRef.current,
        { types: ['address'] }
      );
      autocompleteRef.current.addListener('place_changed', handlePlaceSelect);
    }
  }, [isLoaded]);

  const handlePlaceSelect = () => {
    const addressObject = autocompleteRef.current.getPlace();
    if (addressObject.formatted_address) {
      setAddress(addressObject.formatted_address);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onGenerate(address);
  };

  if (loadError) return <div className="error">Error loading Google Maps</div>;
  if (!isLoaded) return <div className="loading">Loading...</div>;

  return (
    <form onSubmit={handleSubmit} className="address-form">
      <input
        ref={inputRef}
        type="text"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        placeholder="Enter address"
        required
        className="address-input"
      />
      <button type="submit" className="generate-button">Generate Post</button>
    </form>
  );
}

export default AddressInput;
