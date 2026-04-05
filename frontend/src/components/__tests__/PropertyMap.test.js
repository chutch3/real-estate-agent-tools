import React from 'react';
import { render, screen, within } from '@testing-library/react';
import PropertyMap from '../PropertyMap';
import useLayers from '../../hooks/useLayers';

jest.mock('@react-google-maps/api', () => ({
  useLoadScript: () => ({ isLoaded: true, loadError: null }),
  GoogleMap: jest.fn(({ children }) => <div data-testid="google-map">{children}</div>),
  Marker: () => null,
  Polygon: jest.fn(() => null),
}));

jest.mock('../../hooks/useLayers');

const GROUPS = [
  {
    id: 'crime',
    label: 'Crime',
    categories: [
      { id: 'crime-violent', label: 'Violent Crime', date_from: '2025-04-01', date_to: '2026-04-01', record_count: 1234 },
      { id: 'crime-property', label: 'Property Crime', date_from: '2025-04-01', date_to: '2026-04-01', record_count: 4891 },
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
    expect(within(legend).getByText('Violent Crime')).toBeInTheDocument();
    expect(within(legend).queryByText('Property Crime')).not.toBeInTheDocument();
  });

  it('does not show the legend when no layers are active', () => {
    useLayers.mockReturnValue({ groups: GROUPS, isActive: jest.fn().mockReturnValue(false), toggle: jest.fn() });
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    expect(screen.queryByRole('img', { name: 'Crime density scale from low to high' })).not.toBeInTheDocument();
  });

  it('passes null countyFips to useLayers when no property is selected', () => {
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={null} />);
    expect(useLayers).toHaveBeenCalledWith(null, null);
  });

  it('passes selectedProperty county_fips to useLayers', () => {
    const property = { county_fips: '21111', county_polygon: null };
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={property} />);
    expect(useLayers).toHaveBeenCalledWith(null, '21111');
  });

  it('pans to the property location and sets zoom when a property is selected', () => {
    const panTo = jest.fn();
    const setZoom = jest.fn();
    const { GoogleMap } = require('@react-google-maps/api');
    GoogleMap.mockImplementationOnce(({ children, onLoad }) => {
      if (onLoad) onLoad({ panTo, setZoom });
      return <div data-testid="google-map">{children}</div>;
    });

    const property = {
      county_fips: '21111',
      latitude: 38.252665,
      longitude: -85.758456,
      county_polygon: null,
    };
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={property} />);

    expect(panTo).toHaveBeenCalledWith({ lat: 38.252665, lng: -85.758456 });
    expect(setZoom).toHaveBeenCalledWith(14);
  });

  it('renders county boundary polygon when selectedProperty has county_polygon', () => {
    const { Polygon } = require('@react-google-maps/api');
    const property = {
      county_fips: '21111',
      county_polygon: {
        type: 'Polygon',
        coordinates: [
          [[-86.035, 37.997], [-85.404, 37.997], [-85.404, 38.375], [-86.035, 38.375], [-86.035, 37.997]],
        ],
      },
    };
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={property} />);

    expect(Polygon).toHaveBeenCalledWith(
      expect.objectContaining({
        paths: [
          { lat: 37.997, lng: -86.035 },
          { lat: 37.997, lng: -85.404 },
          { lat: 38.375, lng: -85.404 },
          { lat: 38.375, lng: -86.035 },
          { lat: 37.997, lng: -86.035 },
        ],
      }),
      {}
    );
  });

  it('does not render county boundary polygon when selectedProperty has no county_polygon', () => {
    const { Polygon } = require('@react-google-maps/api');
    const property = { county_fips: '21111', county_polygon: null };
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} selectedProperty={property} />);
    expect(Polygon).not.toHaveBeenCalled();
  });
});
