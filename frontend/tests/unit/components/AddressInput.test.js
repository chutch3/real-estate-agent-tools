import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react';
import AddressInput from '../../../src/components/AddressInput';

describe('AddressInput', () => {
  it('should call onGenerate with the entered address when form is submitted', () => {
    const mockOnGenerate = jest.fn();
    render(<AddressInput onGenerate={mockOnGenerate} />);

    const input = screen.getByPlaceholderText('Enter address');
    fireEvent.change(input, { target: { value: '123 Main St' } });

    const submitButton = screen.getByText('Generate Post');
    fireEvent.click(submitButton);

    expect(mockOnGenerate).toHaveBeenCalledWith('123 Main St');
  });
});
