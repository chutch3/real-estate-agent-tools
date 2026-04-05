import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import App from '../../src/App';
import apiClient from '../../src/apiClient';
import useLayers from '../../src/hooks/useLayers';

jest.mock('../../src/apiClient', () => ({
  listProperties: jest.fn(),
  addProperty: jest.fn(),
  geocodeAddress: jest.fn(),
  generatePost: jest.fn(),
  uploadDocument: jest.fn(),
  getDefaultTemplate: jest.fn(),
}));

jest.mock('../../src/hooks/useLayers');

jest.mock('@react-google-maps/api', () => ({
  useLoadScript: () => ({ isLoaded: true, loadError: null }),
  GoogleMap: ({ children }) => <div data-testid="google-map">{children}</div>,
  Marker: ({ position, onClick }) => (
    <button data-testid={`marker-${position.lat}-${position.lng}`} onClick={onClick} />
  ),
}));

describe('App E2E', () => {
  beforeEach(() => {
    useLayers.mockReturnValue({
      groups: [],
      isActive: jest.fn().mockReturnValue(false),
      toggle: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('shows map markers for loaded properties and opens detail panel on click', async () => {
    const properties = [
      {
        id: 'prop-1',
        latitude: 37.4225,
        longitude: -122.0847,
        formatted_address: '1600 Amphitheatre Pkwy, Mountain View, CA 94043',
      },
    ];
    apiClient.listProperties.mockResolvedValue(properties);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('marker-37.4225--122.0847'));

    await waitFor(() => {
      expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument();
    });
    const panel = screen.getByTestId('property-detail-panel');
    expect(within(panel).getByText('1600 Amphitheatre Pkwy, Mountain View, CA 94043')).toBeInTheDocument();
  });
});
