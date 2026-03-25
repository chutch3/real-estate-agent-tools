import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import App from '../../src/App';
import apiClient from '../../src/apiClient';

jest.mock('../../src/apiClient', () => ({
  listProperties: jest.fn(),
  addProperty: jest.fn(),
  geocodeAddress: jest.fn(),
  generatePost: jest.fn(),
  uploadDocument: jest.fn().mockResolvedValue('doc-uuid-1'),
  addDocumentToProperty: jest.fn(),
  getDefaultTemplate: jest.fn(),
}));

jest.mock('@react-google-maps/api', () => ({
  useLoadScript: () => ({ isLoaded: true, loadError: null }),
  GoogleMap: ({ children }) => <div data-testid="google-map">{children}</div>,
  Marker: ({ position, onClick }) => (
    <button
      data-testid={`marker-${position.lat}-${position.lng}`}
      onClick={onClick}
    />
  ),
}));

describe('App Integration', () => {
  const mockProperties = [
    {
      id: 'prop-1',
      rentcast_id: 'rc-1',
      latitude: 37.4225,
      longitude: -122.0847,
      formatted_address: '1600 Amphitheatre Pkwy, Mountain View, CA 94043',
    },
    {
      id: 'prop-2',
      rentcast_id: 'rc-2',
      latitude: 37.3382,
      longitude: -121.8863,
      formatted_address: '1 Infinite Loop, Cupertino, CA 95014',
    },
  ];

  beforeEach(() => {
    apiClient.listProperties.mockResolvedValue(mockProperties);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('loads and displays a map with property markers on home screen', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('google-map')).toBeInTheDocument();
    });

    expect(apiClient.listProperties).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('marker-37.4225--122.0847')).toBeInTheDocument();
    expect(screen.getByTestId('marker-37.3382--121.8863')).toBeInTheDocument();
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
    });

    expect(screen.getByLabelText('Add new property')).toBeInTheDocument();
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
});
