import React from 'react';
import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import AddressInput from '../../../src/components/AddressInput';
import apiClient from '../../../src/apiClient';

jest.mock('../../../src/apiClient', () => ({
  geocodeAddress: jest.fn(),
}));

describe('AddressInput', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders an address input field', () => {
    render(<AddressInput onGeocodeComplete={jest.fn()} />);
    expect(screen.getByLabelText('Enter address')).toBeInTheDocument();
  });

  it('updates the displayed address as the user types', () => {
    render(<AddressInput onGeocodeComplete={jest.fn()} />);
    const input = screen.getByLabelText('Enter address');
    fireEvent.change(input, { target: { value: '123 Main St' } });
    expect(input.value).toBe('123 Main St');
  });

  it('calls onGeocodeComplete with address and location when address is submitted', async () => {
    apiClient.geocodeAddress.mockResolvedValue({ location: { lat: 38.25, lng: -85.75 } });
    const onGeocodeComplete = jest.fn();
    render(<AddressInput onGeocodeComplete={onGeocodeComplete} />);

    fireEvent.change(screen.getByLabelText('Enter address'), { target: { value: '500 W Main St' } });
    fireEvent.submit(screen.getByRole('form'));

    await waitFor(() => {
      expect(onGeocodeComplete).toHaveBeenCalledWith('500 W Main St', { lat: 38.25, lng: -85.75 });
    });
  });

  it('does not call onGeocodeComplete when address is empty', async () => {
    const onGeocodeComplete = jest.fn();
    render(<AddressInput onGeocodeComplete={onGeocodeComplete} />);

    fireEvent.submit(screen.getByRole('form'));

    await new Promise((r) => setTimeout(r, 50));
    expect(onGeocodeComplete).not.toHaveBeenCalled();
    expect(apiClient.geocodeAddress).not.toHaveBeenCalled();
  });
});
