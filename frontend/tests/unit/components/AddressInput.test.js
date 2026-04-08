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
    global.fetch = jest.fn();
    process.env.REACT_APP_MAPBOX_TOKEN = "test-token";
  });

  it('renders an address input field', () => {
    render(<AddressInput onGeocodeComplete={jest.fn()} />);
    expect(screen.getByLabelText('Enter address')).toBeInTheDocument();
  });

  it('fetches and displays address suggestions from Mapbox as the user types', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        features: [
          { id: "1", place_name: "123 Main St, Louisville, KY", center: [-85.75, 38.25] },
          { id: "2", place_name: "123 Main St, Jeffersonville, IN", center: [-85.73, 38.27] }
        ]
      })
    });

    render(<AddressInput onGeocodeComplete={jest.fn()} />);
    const input = screen.getByLabelText('Enter address');

    fireEvent.change(input, { target: { value: '123 Main St' } });
    expect(input.value).toBe('123 Main St');

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("api.mapbox.com/geocoding/v5/mapbox.places/123%20Main%20St.json")
      );
    });

    const suggestions = await screen.findAllByRole('listitem');
    expect(suggestions).toHaveLength(2);
    expect(suggestions[0]).toHaveTextContent("123 Main St, Louisville, KY");
    expect(suggestions[1]).toHaveTextContent("123 Main St, Jeffersonville, IN");
  });

  it('calls onGeocodeComplete when a suggestion is clicked', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        features: [
          { id: "1", place_name: "123 Main St, Louisville, KY", center: [-85.75, 38.25] }
        ]
      })
    });

    apiClient.geocodeAddress.mockResolvedValueOnce({ location: { lat: 38.251, lng: -85.751 } });

    const onGeocodeComplete = jest.fn();
    render(<AddressInput onGeocodeComplete={onGeocodeComplete} />);
    const input = screen.getByLabelText('Enter address');

    fireEvent.change(input, { target: { value: '123 Main' } });

    const suggestion = await screen.findByText("123 Main St, Louisville, KY");
    fireEvent.click(suggestion);

    expect(input.value).toBe("123 Main St, Louisville, KY");

    await waitFor(() => {
      expect(apiClient.geocodeAddress).toHaveBeenCalledWith("123 Main St, Louisville, KY");
      expect(onGeocodeComplete).toHaveBeenCalledWith("123 Main St, Louisville, KY", { lat: 38.251, lng: -85.751 });
    });
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
