import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { GoogleMap, Marker } from '@react-google-maps/api';
import PropertyMap from '../../../src/components/PropertyMap';
import useLayers from '../../../src/hooks/useLayers';

jest.mock('@react-google-maps/api', () => ({
  useLoadScript: () => ({ isLoaded: true, loadError: null }),
  GoogleMap: jest.fn(({ children }) => <div data-testid="google-map">{children}</div>),
  Marker: jest.fn(({ position, onClick }) => (
    <button
      data-testid={`marker-${position.lat}-${position.lng}`}
      onClick={onClick}
    />
  )),
  Polygon: jest.fn(() => null),
}));

jest.mock('../../../src/hooks/useLayers');

describe('PropertyMap', () => {
  const mockProperties = [
    { id: 'prop-1', latitude: 37.4225, longitude: -122.0847 },
    { id: 'prop-2', latitude: 37.3382, longitude: -121.8863 },
  ];

  beforeEach(() => {
    useLayers.mockReturnValue({
      groups: [],
      isActive: jest.fn().mockReturnValue(false),
      toggle: jest.fn(),
    });
  });

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

  it('pans the map to the user location when geolocation resolves after the map is loaded', async () => {
    const mockPanTo = jest.fn();
    GoogleMap.mockImplementationOnce(({ children, onLoad }) => {
      React.useEffect(() => { onLoad?.({ panTo: mockPanTo }); }, []);
      return <div data-testid="google-map">{children}</div>;
    });

    global.navigator.geolocation = {
      getCurrentPosition: jest.fn((success) =>
        success({ coords: { latitude: 38.352193, longitude: -85.721456 } })
      ),
    };

    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);

    await waitFor(() => {
      expect(mockPanTo).toHaveBeenCalledWith({ lat: 38.352193, lng: -85.721456 });
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

  it('passes null countyFips to useLayers when no property is selected', () => {
    render(
      <PropertyMap
        properties={mockProperties}
        onPropertySelect={jest.fn()}
        selectedProperty={null}
      />
    );

    expect(useLayers).toHaveBeenCalledWith(null, null);
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

    expect(useLayers).toHaveBeenCalledWith(null, '21111');
  });

  it('pans to the property location and sets zoom when a property is selected', async () => {
    const mockPanTo = jest.fn();
    const mockSetZoom = jest.fn();
    GoogleMap.mockImplementationOnce(({ children, onLoad }) => {
      React.useEffect(() => {
        onLoad?.({ panTo: mockPanTo, setZoom: mockSetZoom });
      }, []);
      return <div data-testid="google-map">{children}</div>;
    });

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
      expect(mockPanTo).toHaveBeenCalledWith({ lat: 37.4225, lng: -122.0847 });
      expect(mockSetZoom).toHaveBeenCalledWith(14);
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
        }],
      }],
      isActive: jest.fn().mockReturnValue(false),
      toggle: jest.fn(),
    });
    render(<PropertyMap properties={[]} onPropertySelect={jest.fn()} />);
    expect(screen.getByRole('button', { name: 'Violent Crime' })).toBeInTheDocument();
  });
});
