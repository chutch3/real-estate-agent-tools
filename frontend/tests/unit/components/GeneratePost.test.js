import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import GeneratePost from '../../../src/pages/GeneratePost';
import apiClient from '../../../src/apiClient';

jest.mock('../../../src/apiClient', () => ({
  generatePost: jest.fn(),
}));

const mockProperty = {
  id: 'prop-1',
  formatted_address: '1600 Amphitheatre Pkwy, Mountain View, CA 94043',
  latitude: 37.4225,
  longitude: -122.0847,
};

function renderWithProperty(property) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/generate-post', state: { property } }]}>
      <Routes>
        <Route path="/generate-post" element={<GeneratePost />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('GeneratePost', () => {
  afterEach(() => jest.clearAllMocks());

  it('displays the property address', () => {
    renderWithProperty(mockProperty);
    expect(screen.getByTestId('generate-post-page')).toBeInTheDocument();
    expect(screen.getByText('1600 Amphitheatre Pkwy, Mountain View, CA 94043')).toBeInTheDocument();
  });

  it('calls apiClient.generatePost with the property address and agent info', async () => {
    apiClient.generatePost.mockResolvedValue({ post: 'Great house!' });
    renderWithProperty(mockProperty);

    fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: 'Jane Doe' } });
    fireEvent.change(screen.getByLabelText(/company/i), { target: { value: 'Doe Realty' } });
    fireEvent.change(screen.getByLabelText(/contact/i), { target: { value: 'jane@doe.com' } });
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));

    await waitFor(() => {
      expect(apiClient.generatePost).toHaveBeenCalledWith(
        '1600 Amphitheatre Pkwy, Mountain View, CA 94043',
        { agent_name: 'Jane Doe', agent_company: 'Doe Realty', agent_contact: 'jane@doe.com' },
        null
      );
    });
  });

  it('displays the generated post', async () => {
    apiClient.generatePost.mockResolvedValue({ post: 'Great house!' });
    renderWithProperty(mockProperty);

    fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: 'Jane Doe' } });
    fireEvent.change(screen.getByLabelText(/company/i), { target: { value: 'Doe Realty' } });
    fireEvent.change(screen.getByLabelText(/contact/i), { target: { value: 'jane@doe.com' } });
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));

    await waitFor(() => {
      expect(screen.getByDisplayValue('Great house!')).toBeInTheDocument();
    });
  });
});
