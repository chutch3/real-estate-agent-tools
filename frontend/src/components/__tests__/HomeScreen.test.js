import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import HomeScreen from '../HomeScreen';

// Mock the useNavigate hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

describe('HomeScreen', () => {
  const mockProperties = [
    { id: 1, name: 'Property 1' },
    { id: 2, name: 'Property 2' },
  ];

  it('renders property icons and add property button', () => {
    render(
      <MemoryRouter>
        <HomeScreen properties={mockProperties} />
      </MemoryRouter>
    );

    expect(screen.getByText('My Properties')).toBeInTheDocument();
    expect(screen.getAllByRole('button')).toHaveLength(mockProperties.length + 1);
    expect(screen.getByLabelText('Add New Property')).toBeInTheDocument();
  });

  it('navigates to add property page when add button is clicked', () => {
    const navigateMock = jest.fn();
    jest.spyOn(require('react-router-dom'), 'useNavigate').mockReturnValue(navigateMock);

    render(
      <MemoryRouter>
        <HomeScreen properties={mockProperties} />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByLabelText('Add New Property'));
    expect(navigateMock).toHaveBeenCalledWith('/add-property');
  });
});
