import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../../src/App';

describe('App E2E', () => {
  it('should generate a post and post to Instagram', async () => {
    const mockApiClient = {
      generatePost: jest.fn().mockResolvedValue('Generated post for 123 Main St'),
      postToInstagram: jest.fn().mockResolvedValue({ message: 'Posted successfully to Instagram' }),
    };

    render(<App apiClient={mockApiClient} />);

    // Enter address and generate post
    fireEvent.change(screen.getByPlaceholderText('Enter address'), { target: { value: '123 Main St' } });
    fireEvent.click(screen.getByText('Generate Post'));

    await waitFor(() => {
      expect(screen.getByTestId('post-textarea')).toHaveValue('Generated post for 123 Main St');
    });

    // Post to Instagram
    fireEvent.click(screen.getByTestId('post-to-instagram-button'));

    await waitFor(() => {
      expect(screen.getByTestId('post-status')).toHaveTextContent('Posted successfully to Instagram');
    });
  });
});
