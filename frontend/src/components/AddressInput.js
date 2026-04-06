import React, { useState } from 'react';
import { MapPin } from 'lucide-react';
import apiClient from '../apiClient';

function AddressInput({ onGeocodeComplete }) {
  const [address, setAddress] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!address.trim()) return;
    const result = await apiClient.geocodeAddress(address);
    onGeocodeComplete(address, result.location);
  };

  return (
    <form onSubmit={handleSubmit} role="form">
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
    </form>
  );
}

export default AddressInput;
