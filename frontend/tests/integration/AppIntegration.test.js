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
  uploadDocument: jest.fn().mockResolvedValue('doc-uuid-1'),
  addDocumentToProperty: jest.fn(),
  getDefaultTemplate: jest.fn(),
  getNetSheet: jest.fn(),
  addScenario: jest.fn(),
  updateScenario: jest.fn(),
  deleteScenario: jest.fn(),
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

describe('App Integration', () => {
  const mockProperties = [
    {
      id: 'prop-1',
      representation_id: 'rep-1',
      rentcast_id: 'rc-1',
      latitude: 37.4225,
      longitude: -122.0847,
      formatted_address: '1600 Amphitheatre Pkwy, Mountain View, CA 94043',
      role: 'listing_agent',
    },
    {
      id: 'prop-2',
      representation_id: 'rep-2',
      rentcast_id: 'rc-2',
      latitude: 37.3382,
      longitude: -121.8863,
      formatted_address: '1 Infinite Loop, Cupertino, CA 95014',
      role: 'buyers_agent',
    },
  ];

  beforeEach(() => {
    window.history.pushState({}, '', '/');
    apiClient.getMe.mockResolvedValue(_AUTHENTICATED_USER);
    apiClient.listProperties.mockResolvedValue(mockProperties);
    apiClient.getNetSheet.mockResolvedValue({ id: 'sheet-1', representation_id: 'rep-1', scenarios: [] });
    useLayers.mockReturnValue({
      groups: [],
      isActive: jest.fn().mockReturnValue(false),
      toggle: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('loads and displays a map with property markers on home screen', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('google-map')).toBeInTheDocument();
      expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument();
      expect(screen.getByTestId('marker-37.3382--121.8863')).toBeInTheDocument();
    });

    expect(apiClient.listProperties).toHaveBeenCalledTimes(1);
  });

  it('opens a detail panel when a property marker is clicked', async () => {
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
    expect(within(panel).getByRole('button', { name: /generate/i })).toBeInTheDocument();
    expect(within(panel).getByRole('button', { name: /upload docs/i })).toBeInTheDocument();
  });

  it('shows an add property button that navigates to /add-property', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('google-map')).toBeInTheDocument();
      expect(screen.getByLabelText('Add new property')).toBeInTheDocument();
    });
  });

  it('uploads a document for a property when a file is selected in the detail panel', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('marker-37.4225--122.0847'));

    await waitFor(() => {
      expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument();
    });

    const file = new File(['content'], 'listing.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(apiClient.uploadDocument).toHaveBeenCalledWith(file);
    });
  });

  it('uploads multiple files when multiple files are selected at once', async () => {
    apiClient.uploadDocument
      .mockResolvedValueOnce('doc-uuid-1')
      .mockResolvedValueOnce('doc-uuid-2');
    const propertyWithBothDocs = {
      ...mockProperties[0],
      documents: [
        { id: 'doc-uuid-1', filename: 'disclosure.pdf' },
        { id: 'doc-uuid-2', filename: 'inspection.pdf' },
      ],
    };
    apiClient.addDocumentToProperty.mockResolvedValue(propertyWithBothDocs);

    render(<App />);
    await waitFor(() => expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument());
    fireEvent.click(screen.getByTestId('marker-37.4225--122.0847'));
    await waitFor(() => expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument());

    const file1 = new File(['content'], 'disclosure.pdf', { type: 'application/pdf' });
    const file2 = new File(['content'], 'inspection.pdf', { type: 'application/pdf' });
    fireEvent.change(document.querySelector('input[type="file"]'), {
      target: { files: [file1, file2] },
    });

    await waitFor(() => expect(apiClient.uploadDocument).toHaveBeenCalledTimes(2));
    expect(apiClient.uploadDocument).toHaveBeenCalledWith(file1);
    expect(apiClient.uploadDocument).toHaveBeenCalledWith(file2);
    expect(screen.getByText('disclosure.pdf')).toBeInTheDocument();
    expect(screen.getByText('inspection.pdf')).toBeInTheDocument();
  });

  it('shows uploaded document in panel after closing and reopening', async () => {
    const propertyWithDoc = { ...mockProperties[0], documents: [{ id: 'doc-uuid-1', filename: 'listing.pdf' }] };
    apiClient.addDocumentToProperty.mockResolvedValue(propertyWithDoc);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument();
    });

    // Open panel and upload a document
    fireEvent.click(screen.getByTestId('marker-37.4225--122.0847'));
    await waitFor(() => expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument());

    const file = new File(['content'], 'listing.pdf', { type: 'application/pdf' });
    fireEvent.change(document.querySelector('input[type="file"]'), { target: { files: [file] } });
    await waitFor(() => expect(apiClient.addDocumentToProperty).toHaveBeenCalled());

    // Close the panel
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    await waitFor(() => expect(screen.queryByTestId('property-detail-panel')).not.toBeInTheDocument());

    // Reopen the same property
    fireEvent.click(screen.getByLabelText('Select 1600 Amphitheatre Pkwy, Mountain View, CA 94043'));
    await waitFor(() => expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument());

    expect(screen.getByText('listing.pdf')).toBeInTheDocument();
  });

  it('navigates to /generate-post when Generate is clicked in the detail panel', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('marker-37.4225--122.0847'));

    await waitFor(() => {
      expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument();
    });

    const panel = screen.getByTestId('property-detail-panel');
    fireEvent.click(within(panel).getByRole('button', { name: /generate/i }));

    await waitFor(() => {
      expect(screen.getByTestId('generate-post-page')).toBeInTheDocument();
    });
    expect(screen.getByText('1600 Amphitheatre Pkwy, Mountain View, CA 94043')).toBeInTheDocument();
  });

  it('does not show Net Sheet button for a buyer-side-only property', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('marker-37.3382--121.8863')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('marker-37.3382--121.8863'));

    await waitFor(() => {
      expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument();
    });

    const panel = screen.getByTestId('property-detail-panel');
    expect(within(panel).queryByRole('button', { name: /net sheet/i })).not.toBeInTheDocument();
  });

  it('navigates to /net-sheet when Net Sheet is clicked for a listing-side property', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('marker-37.4225--122.0847'));

    await waitFor(() => {
      expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument();
    });

    const panel = screen.getByTestId('property-detail-panel');
    fireEvent.click(within(panel).getByRole('button', { name: /net sheet/i }));

    await waitFor(() => {
      expect(screen.getByTestId('net-sheet-page')).toBeInTheDocument();
    });
    expect(screen.getByText('1600 Amphitheatre Pkwy, Mountain View, CA 94043')).toBeInTheDocument();
  });
});
