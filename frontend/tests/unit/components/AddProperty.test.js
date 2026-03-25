import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AddProperty from '../../../src/components/AddProperty';
import apiClient from '../../../src/apiClient';

jest.mock('../../../src/apiClient', () => ({
  addProperty: jest.fn(),
  uploadDocument: jest.fn(),
  geocodeAddress: jest.fn(),
  getPropertyDetails: jest.fn(),
}));

jest.mock('@react-google-maps/api', () => ({
  useLoadScript: () => ({ isLoaded: true, loadError: null }),
  GoogleMap: ({ children }) => <div data-testid="google-map">{children}</div>,
  Marker: () => null,
}));

function renderComponent() {
  return render(
    <MemoryRouter>
      <AddProperty />
    </MemoryRouter>
  );
}

describe('AddProperty', () => {
  beforeEach(() => {
    window.google = {
      maps: {
        places: {
          Autocomplete: jest.fn().mockReturnValue({
            addListener: jest.fn(),
            getPlace: jest.fn(),
          }),
        },
        event: { clearInstanceListeners: jest.fn() },
      },
    };
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('calls addProperty with documents_ids from uploaded documents on finish', async () => {
    apiClient.uploadDocument.mockResolvedValue('doc-uuid-1');
    apiClient.addProperty.mockResolvedValue({ id: 'new-prop-id' });
    apiClient.getPropertyDetails.mockResolvedValue({
      rentcast_id: 'rentcast-123',
      latitude: 37.4,
      longitude: -122.1,
    });

    renderComponent();

    // Navigate to SupportingDocumentation step (step 3)
    fireEvent.click(screen.getByText('Next')); // step 0 → 1
    fireEvent.click(screen.getByText('Next')); // step 1 → 2

    const file = new File(['content'], 'doc.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('doc.pdf')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Next')); // step 2 → 3 (Summary)

    fireEvent.click(screen.getByRole('button', { name: 'Add Property' }));

    await waitFor(() => {
      expect(apiClient.addProperty).toHaveBeenCalledWith(
        expect.objectContaining({
          documents: [{ id: 'doc-uuid-1', filename: 'doc.pdf' }],
        })
      );
    });
  });
});
