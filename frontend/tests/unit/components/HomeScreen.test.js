import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import HomeScreen from '../../../src/components/HomeScreen';
import apiClient from '../../../src/apiClient';

jest.mock('../../../src/apiClient');
jest.mock('../../../src/components/PropertyMap', () => () => <div data-testid="property-map" />);

const mockProperty = {
  id: 'prop-1',
  formatted_address: '1600 Amphitheatre Pkwy, Mountain View, CA 94043',
  latitude: 37.4225,
  longitude: -122.0847,
  documents: [
    { id: 'doc-1', filename: 'listing.pdf' },
  ],
};

describe('HomeScreen', () => {
  beforeEach(() => {
    apiClient.listProperties.mockResolvedValue([mockProperty]);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('shows a delete error message when deleteDocument fails', async () => {
    apiClient.deleteDocument.mockRejectedValue(new Error('Network error'));

    render(<MemoryRouter><HomeScreen /></MemoryRouter>);

    fireEvent.click(await screen.findByLabelText('Select 1600 Amphitheatre Pkwy, Mountain View, CA 94043'));
    fireEvent.click(await screen.findByRole('button', { name: /delete listing\.pdf/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/failed to delete/i);
    });
  });

  it('calls apiClient.deleteDocument and updates the property when a document is deleted', async () => {
    const updatedProperty = { ...mockProperty, documents: [] };
    apiClient.deleteDocument.mockResolvedValue(updatedProperty);

    render(<MemoryRouter><HomeScreen /></MemoryRouter>);

    fireEvent.click(await screen.findByLabelText('Select 1600 Amphitheatre Pkwy, Mountain View, CA 94043'));
    fireEvent.click(await screen.findByRole('button', { name: /delete listing\.pdf/i }));

    await waitFor(() => {
      expect(apiClient.deleteDocument).toHaveBeenCalledWith('prop-1', 'doc-1');
      expect(screen.queryByText('listing.pdf')).not.toBeInTheDocument();
    });
  });
});
