import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import App from '../../src/App';
import apiClient from '../../src/apiClient';
import useLayers from '../../src/hooks/useLayers';

const _AUTHENTICATED_USER = {
  id: 'u1', email: 'agent@test.com', role: 'AGENT',
  brokerage_id: 'b1', brokerage: { id: 'b1', name: 'Test Brokerage' },
};

jest.mock('../../src/apiClient', () => ({
  getMe: jest.fn(),
  login: jest.fn(),
  logout: jest.fn(),
  listProperties: jest.fn(),
  addProperty: jest.fn(),
  geocodeAddress: jest.fn(),
  generatePost: jest.fn(),
  uploadDocument: jest.fn(),
  getDefaultTemplate: jest.fn(),
}));

jest.mock('../../src/hooks/useLayers');

jest.mock("react-map-gl/mapbox", () => {
  const React = require("react");
  return {
    Map: React.forwardRef(function MockMap({ children }, ref) {
      React.useImperativeHandle(ref, () => ({ flyTo: jest.fn() }), []);
      return React.createElement(
        "div",
        { "data-testid": "google-map" },
        children,
      );
    }),
    Marker: jest.fn(({ children, onClick, latitude, longitude }) =>
      React.createElement(
        "button",
        { "data-testid": `marker-${latitude}-${longitude}`, onClick },
        children,
      ),
    ),
    Source: jest.fn(({ children }) => children || null),
    Layer: jest.fn(() => null),
  };
});

describe('App E2E', () => {
  beforeEach(() => {
    apiClient.getMe.mockResolvedValue(_AUTHENTICATED_USER);
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
