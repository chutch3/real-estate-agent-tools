import React from 'react';
import { render } from '@testing-library/react';
import { GoogleMap, Marker } from '@react-google-maps/api';
import MapComponent from '../MapComponent';

jest.mock('@react-google-maps/api', () => ({
  GoogleMap: jest.fn(() => null),
  Marker: jest.fn(() => null),
}));

describe('MapComponent', () => {
  it('renders GoogleMap with correct props', () => {
    const center = { lat: 37.7749, lng: -122.4194 };
    render(<MapComponent center={center} />);

    expect(GoogleMap).toHaveBeenCalledWith(
      expect.objectContaining({
        center: center,
        zoom: 18,
        options: expect.objectContaining({
          mapTypeId: 'satellite',
          disableDefaultUI: true,
          zoomControl: true,
        }),
      }),
      expect.anything()
    );

    expect(Marker).toHaveBeenCalledWith(
      expect.objectContaining({
        position: center,
      }),
      expect.anything()
    );
  });
});
