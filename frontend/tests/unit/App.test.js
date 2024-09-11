import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../../src/App';

describe('App', () => {
  it('renders without crashing', () => {
    const mockApiClient = {
      generatePost: jest.fn(),
      postToInstagram: jest.fn(),
    };
    render(<App apiClient={mockApiClient} />);
    expect(screen.getByText('Instagram Post Generator')).toBeInTheDocument();
  });
});
