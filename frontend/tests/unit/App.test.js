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

jest.mock('@react-google-maps/api', () => ({
  useLoadScript: () => ({ isLoaded: true, loadError: null }),
  GoogleMap: ({ children }) => <div data-testid="google-map">{children}</div>,
  Marker: ({ position, onClick }) => (
    <button data-testid={`marker-${position.lat}-${position.lng}`} onClick={onClick} />
  ),
}));

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
      expect(screen.getByTestId('google-map')).toBeInTheDocument();
    });
  });

  it('renders the home screen route at /', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByTestId('google-map')).toBeInTheDocument();
    });
  });
});
