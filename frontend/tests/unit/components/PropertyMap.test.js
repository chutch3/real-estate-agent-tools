import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PropertyMap from '../../../src/components/PropertyMap';
import useLayers from '../../../src/hooks/useLayers';

const mockFlyTo = jest.fn();

jest.mock('react-map-gl/mapbox', () => {
  const React = require('react');
  return {
    Map: React.forwardRef(function MockMap({ children }, ref) {
      React.useImperativeHandle(ref, () => ({ flyTo: mockFlyTo }), []);
      return React.createElement('div', { 'data-testid': 'mapbox-map' }, children);
    }),
    Marker: jest.fn(({ latitude, longitude, onClick }) =>
      React.createElement('button', {
        'data-testid': `marker-${latitude}-${longitude}`,
        onClick,
      })
    ),
    Source: jest.fn(({ children }) => children || null),
    Layer: jest.fn(() => null),
  };
});

jest.mock('../../../src/hooks/useLayers');

describe('PropertyMap', () => {
  const mockProperties = [
    { id: 'prop-1', latitude: 37.4225, longitude: -122.0847 },
    { id: 'prop-2', latitude: 37.3382, longitude: -121.8863 },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    useLayers.mockReturnValue({
      groups: [],
      isActive: jest.fn().mockReturnValue(false),
      toggle: jest.fn(),
    });
  });

  it('renders the map container', () => {
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    expect(screen.getByTestId('mapbox-map')).toBeInTheDocument();
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

  it('passes correct longitude and latitude to each Marker', () => {
    const { Marker } = require('react-map-gl/mapbox');
    render(<PropertyMap properties={mockProperties} onPropertySelect={jest.fn()} />);

    expect(Marker).toHaveBeenCalledWith(
      expect.objectContaining({ longitude: -122.0847, latitude: 37.4225 }),
      expect.anything(),
    );
    expect(Marker).toHaveBeenCalledWith(
      expect.objectContaining({ longitude: -121.8863, latitude: 37.3382 }),
      expect.anything(),
    );
  });

  it('passes null countyFips to useLayers when no property is selected', () => {
    render(
      <PropertyMap
        properties={mockProperties}
        onPropertySelect={jest.fn()}
        selectedProperty={null}
      />
    );

    expect(useLayers).toHaveBeenCalledWith(null);
  });

  it('passes selectedProperty county_fips to useLayers', () => {
    const selectedProperty = { ...mockProperties[0], county_fips: '21111' };
    render(
      <PropertyMap
        properties={mockProperties}
        onPropertySelect={jest.fn()}
        selectedProperty={selectedProperty}
      />
    );

    expect(useLayers).toHaveBeenCalledWith('21111');
  });

  it('flies to the property location when a property is selected', async () => {
    const selectedProperty = {
      ...mockProperties[0],
      county_fips: '21111',
      county_polygon: null,
    };

    render(
      <PropertyMap
        properties={mockProperties}
        onPropertySelect={jest.fn()}
        selectedProperty={selectedProperty}
      />
    );

    await waitFor(() => {
      expect(mockFlyTo).toHaveBeenCalledWith({
        center: [-122.0847, 37.4225],
        zoom: 14,
      });
    });
  });

  it('renders a segment for each category when groups are present', () => {
    useLayers.mockReturnValue({
      groups: [{
        id: 'crime',
        label: 'Crime',
        categories: [{
          id: 'crime-violent',
          label: 'Violent Crime',
          date_from: '2025-04-01',
          date_to: '2026-04-01',
          record_count: 1234,
          tile_zoom: 12,
          bbox: [-86.035, 37.997, -85.404, 38.375],
        }],
      }],
      isActive: jest.fn().mockReturnValue(false),
      toggle: jest.fn(),
    });
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    expect(screen.getByRole('button', { name: 'Violent Crime' })).toBeInTheDocument();
  });
});
