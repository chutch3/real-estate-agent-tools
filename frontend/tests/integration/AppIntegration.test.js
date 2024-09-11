import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../../src/App';

describe('App Integration', () => {
  let mockApiClient;

  beforeEach(() => {
    mockApiClient = {
      generatePost: jest.fn(),
      postToInstagram: jest.fn(),
    };
  });

  it('generates a post when address is submitted', async () => {
    mockApiClient.generatePost.mockResolvedValue('Generated post content');
    render(<App apiClient={mockApiClient} />);

    fireEvent.change(screen.getByPlaceholderText('Enter address'), { target: { value: '123 Main St' } });
    fireEvent.click(screen.getByText('Generate Post'));

    await waitFor(() => {
      expect(screen.getByTestId('post-textarea')).toHaveValue('Generated post content');
    });
    expect(mockApiClient.generatePost).toHaveBeenCalledWith('123 Main St');
  });

  it('posts to Instagram when button is clicked', async () => {
    mockApiClient.generatePost.mockResolvedValue('Generated post content');
    mockApiClient.postToInstagram.mockResolvedValue({ message: 'Posted successfully' });
    render(<App apiClient={mockApiClient} />);

    // Generate a post
    fireEvent.change(screen.getByPlaceholderText('Enter address'), { target: { value: '123 Main St' } });
    fireEvent.click(screen.getByText('Generate Post'));

    await waitFor(() => {
      expect(screen.getByTestId('post-textarea')).toBeInTheDocument();
    });

    // Post to Instagram
    fireEvent.click(screen.getByTestId('post-to-instagram-button'));

    await waitFor(() => {
      expect(screen.getByTestId('post-status')).toHaveTextContent('Posted successfully');
    });
    expect(mockApiClient.postToInstagram).toHaveBeenCalledWith('Generated post content');
  });
});
