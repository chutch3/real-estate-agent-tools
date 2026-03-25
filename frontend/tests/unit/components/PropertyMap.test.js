import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { GoogleMap, Marker } from '@react-google-maps/api';
import PropertyMap from '../../../src/components/PropertyMap';

jest.mock('@react-google-maps/api', () => ({
  useLoadScript: () => ({ isLoaded: true, loadError: null }),
  GoogleMap: jest.fn(({ children }) => <div data-testid="google-map">{children}</div>),
  Marker: jest.fn(({ position, onClick }) => (
    <button
      data-testid={`marker-${position.lat}-${position.lng}`}
      onClick={onClick}
    />
  )),
}));

describe('PropertyMap', () => {
  const mockProperties = [
    { id: 'prop-1', latitude: 37.4225, longitude: -122.0847 },
    { id: 'prop-2', latitude: 37.3382, longitude: -121.8863 },
  ];

  afterEach(() => {
    jest.clearAllMocks();
    delete global.navigator.geolocation;
  });

  it('renders a GoogleMap', () => {
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    expect(screen.getByTestId('google-map')).toBeInTheDocument();
  });

  it('centers the map on the user current location when geolocation is available', async () => {
    global.navigator.geolocation = {
      getCurrentPosition: jest.fn((success) =>
        success({ coords: { latitude: 38.352193, longitude: -85.721456 } })
      ),
    };

    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);

    await waitFor(() => {
      expect(GoogleMap).toHaveBeenLastCalledWith(
        expect.objectContaining({ center: { lat: 38.352193, lng: -85.721456 } }),
        expect.anything()
      );
    });
  });

  it('renders a Marker for each property', () => {
    render(<PropertyMap properties={mockProperties} onPropertySelect={jest.fn()} />);

    expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument();
    expect(screen.getByTestId('marker-37.3382--121.8863')).toBeInTheDocument();
  });

  it('calls onPropertySelect with the property when a marker is clicked', () => {
    const onPropertySelect = jest.fn();
    render(<PropertyMap properties={mockProperties} onPropertySelect={onPropertySelect} />);

    fireEvent.click(screen.getByTestId('marker-37.4225--122.0847'));

    expect(onPropertySelect).toHaveBeenCalledWith(mockProperties[0]);
  });

  it('does not render a marker for properties with zero coordinates', () => {
    const propertiesWithZero = [
      { id: 'prop-1', latitude: 37.4225, longitude: -122.0847 },
      { id: 'prop-invalid', latitude: 0, longitude: 0 },
    ];
    render(<PropertyMap properties={propertiesWithZero} onPropertySelect={jest.fn()} />);

    expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument();
    expect(screen.queryByTestId('marker-0-0')).not.toBeInTheDocument();
  });

  it('passes correct position to each Marker', () => {
    render(<PropertyMap properties={mockProperties} onPropertySelect={jest.fn()} />);

    expect(Marker).toHaveBeenCalledWith(
      expect.objectContaining({ position: { lat: 37.4225, lng: -122.0847 } }),
      expect.anything()
    );
    expect(Marker).toHaveBeenCalledWith(
      expect.objectContaining({ position: { lat: 37.3382, lng: -121.8863 } }),
      expect.anything()
    );
  });
});
