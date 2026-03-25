import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react';
import AddressInput from '../../../src/components/AddressInput';

jest.mock('@react-google-maps/api', () => ({
  useLoadScript: () => ({ isLoaded: true, loadError: null }),
}));

describe('AddressInput', () => {
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
});
