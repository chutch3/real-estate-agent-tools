import React from 'react';
import { render, screen } from '@testing-library/react';
import PropertyMap from '../PropertyMap';
import useLayers from '../../hooks/useLayers';

const mockFlyTo = jest.fn();

jest.mock('react-map-gl/mapbox', () => {
  const React = require('react');
  return {
    Map: React.forwardRef(function MockMap({ children }, ref) {
      React.useImperativeHandle(ref, () => ({ flyTo: mockFlyTo }), []);
      return React.createElement('div', { 'data-testid': 'mapbox-map' }, children);
    }),
    Marker: jest.fn(({ children, onClick, latitude, longitude }) =>
      React.createElement('div', { 'data-testid': `marker-${latitude}-${longitude}`, onClick }, children),
    ),
    Source: jest.fn(({ children }) => children || null),
    Layer: jest.fn(() => null),
  };
});

jest.mock('../../hooks/useLayers');

const GROUPS = [
  {
    id: 'crime',
    label: 'Crime',
    categories: [
      {
        id: 'crime-violent',
        label: 'Violent Crime',
        date_from: '2025-04-01',
        date_to: '2026-04-01',
        record_count: 1234,
        tile_zoom: 12,
        bbox: [-86.035, 37.997, -85.404, 38.375],
      },
      {
        id: 'crime-property',
        label: 'Property Crime',
        date_from: '2025-04-01',
        date_to: '2026-04-01',
        record_count: 4891,
        tile_zoom: 12,
        bbox: [-86.035, 37.997, -85.404, 38.375],
      },
    ],
  },
];

describe('PropertyMap', () => {
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

  it('renders a segment for each category when groups are present', () => {
    useLayers.mockReturnValue({ groups: GROUPS, isActive: jest.fn().mockReturnValue(true), toggle: jest.fn() });
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    expect(screen.getByRole('button', { name: 'Violent Crime' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Property Crime' })).toBeInTheDocument();
  });

  it('shows the legend for active layers', () => {
    useLayers.mockReturnValue({ groups: GROUPS, isActive: (id) => id === 'crime-violent', toggle: jest.fn() });
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    const legend = screen.getByRole('img', { name: 'Crime density scale from low to high' });
    expect(legend).toBeInTheDocument();
  });

  it('does not show the legend when no layers are active', () => {
    useLayers.mockReturnValue({ groups: GROUPS, isActive: jest.fn().mockReturnValue(false), toggle: jest.fn() });
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    expect(screen.queryByRole('img', { name: 'Crime density scale from low to high' })).not.toBeInTheDocument();
  });

  it('passes null countyFips to useLayers when no property is selected', () => {
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={null} />);
    expect(useLayers).toHaveBeenCalledWith(null);
  });

  it('passes selectedProperty county_fips to useLayers', () => {
    const property = { county_fips: '21111', county_polygon: null };
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={property} />);
    expect(useLayers).toHaveBeenCalledWith('21111');
  });

  it('flies to the property location when a property is selected', () => {
    const property = {
      county_fips: '21111',
      latitude: 38.252665,
      longitude: -85.758456,
      county_polygon: null,
    };
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={property} />);
    expect(mockFlyTo).toHaveBeenCalledWith({
      center: [-85.758456, 38.252665],
      zoom: 14,
    });
  });

  it('does not fly to the property again when the parent re-renders with a new object reference for the same property', () => {
    const property = {
      id: 'prop-1',
      county_fips: '21111',
      latitude: 38.252665,
      longitude: -85.758456,
      county_polygon: null,
    };
    const { rerender } = render(
      <PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={property} />,
    );
    expect(mockFlyTo).toHaveBeenCalledTimes(1);

    rerender(
      <PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={{ ...property }} />,
    );
    expect(mockFlyTo).toHaveBeenCalledTimes(1);
  });

  it('renders a GeoJSON Source for the county boundary when selectedProperty has county_polygon', () => {
    const { Source } = require('react-map-gl/mapbox');
    const polygon = {
      type: 'Polygon',
      coordinates: [
        [[-86.035, 37.997], [-85.404, 37.997], [-85.404, 38.375], [-86.035, 38.375], [-86.035, 37.997]],
      ],
    };
    const property = { county_fips: '21111', county_polygon: polygon };
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={property} />);
    expect(Source).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'geojson', data: polygon }),
      {},
    );
  });

  it('does not render county boundary Source when selectedProperty has no county_polygon', () => {
    const { Source } = require('react-map-gl/mapbox');
    const property = { county_fips: '21111', county_polygon: null };
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={property} />);
    const geojsonCall = Source.mock.calls.find(([props]) => props.type === 'geojson');
    expect(geojsonCall).toBeUndefined();
  });

  it('renders a raster Source for the active layer with maxzoom and bounds', () => {
    const { Source } = require('react-map-gl/mapbox');
    useLayers.mockReturnValue({
      groups: GROUPS,
      isActive: (id) => id === 'crime-violent',
      toggle: jest.fn(),
    });
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    expect(Source).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'raster',
        tileSize: 256,
        maxzoom: 12,
        bounds: [-86.035, 37.997, -85.404, 38.375],
      }),
      {},
    );
  });

  it('keeps the raster Source id stable when the active layer changes', () => {
    const { Source } = require('react-map-gl/mapbox');
    useLayers.mockReturnValue({
      groups: GROUPS,
      isActive: (id) => id === 'crime-violent',
      toggle: jest.fn(),
    });
    const { rerender } = render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    const firstId = Source.mock.calls.find(([p]) => p.type === 'raster')[0].id;

    jest.clearAllMocks();
    useLayers.mockReturnValue({
      groups: GROUPS,
      isActive: (id) => id === 'crime-property',
      toggle: jest.fn(),
    });
    rerender(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    const secondId = Source.mock.calls.find(([p]) => p.type === 'raster')[0].id;

    expect(firstId).toBe(secondId);
  });

  it('renders a visible pin for each property marker', () => {
    const properties = [{ id: 'prop-1', latitude: 38.25, longitude: -85.75 }];
    render(<PropertyMap properties={properties} onPropertySelect={jest.fn()} />);
    const marker = screen.getByTestId('marker-38.25--85.75');
    expect(marker.firstChild).not.toBeNull();
  });

  it('renders the selected property marker with an accessible label distinguishing it', () => {
    const properties = [{ id: 'prop-1', latitude: 38.25, longitude: -85.75 }];
    const selectedProperty = { id: 'prop-1', latitude: 38.25, longitude: -85.75, county_fips: '21111' };
    render(
      <PropertyMap properties={properties} onPropertySelect={jest.fn()} selectedProperty={selectedProperty} />,
    );
    const marker = screen.getByTestId('marker-38.25--85.75');
    expect(marker.querySelector('[aria-label="Selected property"]')).not.toBeNull();
  });

  it('does not render a raster Source when no layer is active', () => {
    const { Source } = require('react-map-gl/mapbox');
    useLayers.mockReturnValue({
      groups: GROUPS,
      isActive: jest.fn().mockReturnValue(false),
      toggle: jest.fn(),
    });
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    const rasterCall = Source.mock.calls.find(([props]) => props.type === 'raster');
    expect(rasterCall).toBeUndefined();
  });
});
