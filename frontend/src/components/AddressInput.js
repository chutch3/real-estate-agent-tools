import React, { useState, useEffect, useRef } from "react";
import { MapPin } from "lucide-react";
import apiClient from "../apiClient";

const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;

function AddressInput({ onGeocodeComplete }) {
  const [address, setAddress] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (!address.trim() || !showSuggestions) {
      setSuggestions([]);
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(async () => {
      try {
        const query = encodeURIComponent(address);
        const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${query}.json?access_token=${MAPBOX_TOKEN}&country=us&types=address`;
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data.features || []);
        }
      } catch (err) {
        console.error("Geocoding failed:", err);
      }
    }, 300);

    return () => clearTimeout(debounceRef.current);
  }, [address, showSuggestions]);

  const handleSuggestionClick = async (feature) => {
    const placeName = feature.place_name;
    setAddress(placeName);
    setShowSuggestions(false);
    setSuggestions([]);

    // Fetch highly accurate rooftop coordinates via backend
    const result = await apiClient.geocodeAddress(placeName);
    onGeocodeComplete(placeName, result.location);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!address.trim()) return;
    setShowSuggestions(false);

    // Fallback if they submit without clicking a suggestion
    const result = await apiClient.geocodeAddress(address);
    onGeocodeComplete(address, result.location);
  };

  return (
    <form onSubmit={handleSubmit} role="form" className="relative">
      <label
        htmlFor="address-input"
        className="block font-sans text-xs uppercase tracking-widest text-ink-400 mb-1.5"
      >
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
          onChange={(e) => {
            setAddress(e.target.value);
            setShowSuggestions(true);
          }}
          onFocus={() => setShowSuggestions(true)}
          className="w-full pl-9 pr-4 py-2.5 border border-linen-300 rounded-md bg-white font-sans text-sm text-ink-900 placeholder-ink-300 focus:outline-none focus:border-bronze-400 transition-colors"
          aria-label="Enter address"
          autoComplete="off"
        />
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-white border border-linen-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
          {suggestions.map((feature) => (
            <li
              key={feature.id}
              onClick={() => handleSuggestionClick(feature)}
              className="px-4 py-2 hover:bg-linen-50 cursor-pointer font-sans text-sm text-ink-900 border-b border-linen-100 last:border-b-0"
            >
              {feature.place_name}
            </li>
          ))}
        </ul>
      )}

      {address && !showSuggestions && suggestions.length === 0 && (
        <p className="mt-1.5 font-sans text-xs text-ink-400 italic">
          {address}
        </p>
      )}
    </form>
  );
}

export default AddressInput;
