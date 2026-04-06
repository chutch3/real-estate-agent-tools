import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import App from '../../src/App';
import apiClient from '../../src/apiClient';
import useLayers from '../../src/hooks/useLayers';

jest.mock('../../src/apiClient', () => ({
  listProperties: jest.fn().mockResolvedValue([]),
  generatePost: jest.fn(),
  uploadDocument: jest.fn(),
  addDocumentToProperty: jest.fn(),
  getDefaultTemplate: jest.fn(),
}));

jest.mock('../../src/hooks/useLayers');

jest.mock('react-map-gl/mapbox', () => {
  const React = require('react');
  return {
    Map: React.forwardRef(function MockMap({ children }, ref) {
      return React.createElement('div', { 'data-testid': 'mapbox-map' }, children);
    }),
    Marker: ({ latitude, longitude, onClick }) =>
      React.createElement('button', {
        'data-testid': `marker-${latitude}-${longitude}`,
        onClick,
      }),
    Source: jest.fn(({ children }) => children || null),
    Layer: jest.fn(() => null),
  };
});

describe('App', () => {
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

  it('renders the home screen with a map on startup', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByTestId('mapbox-map')).toBeInTheDocument();
    });
  });

  it('renders the home screen route at /', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByTestId('mapbox-map')).toBeInTheDocument();
    });
  });
});
