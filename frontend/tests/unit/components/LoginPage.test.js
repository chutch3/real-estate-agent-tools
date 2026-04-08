import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import LoginPage from '../../../src/pages/LoginPage';
import { AuthProvider } from '../../../src/context/AuthContext';
import apiClient from '../../../src/apiClient';

jest.mock('../../../src/apiClient', () => ({
  getMe: jest.fn(),
  login: jest.fn(),
  logout: jest.fn(),
}));

const _AUTHENTICATED_USER = {
  id: 'u1',
  email: 'agent@acme.com',
  role: 'AGENT',
  brokerage_id: 'b1',
  brokerage: { id: 'b1', name: 'Acme Realty' },
};

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<div data-testid="home-page">Home</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('LoginPage', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders email input, password input, and sign-in button', async () => {
    apiClient.getMe.mockRejectedValue(new Error('not authenticated'));

    renderLoginPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });
  });

  it('calls apiClient.login with email and password on submit', async () => {
    apiClient.getMe.mockRejectedValue(new Error('not authenticated'));
    apiClient.login.mockResolvedValue(undefined);

    renderLoginPage();
    await waitFor(() => expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'agent@acme.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(apiClient.login).toHaveBeenCalledWith('agent@acme.com', 'password123');
    });
  });

  it('shows an error message when login fails', async () => {
    apiClient.getMe.mockRejectedValue(new Error('not authenticated'));
    apiClient.login.mockRejectedValue(new Error('Invalid credentials'));

    renderLoginPage();
    await waitFor(() => expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'bad@acme.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument();
    });
  });

  it('redirects to home after a successful login', async () => {
    apiClient.getMe
      .mockRejectedValueOnce(new Error('not authenticated'))
      .mockResolvedValueOnce(_AUTHENTICATED_USER);
    apiClient.login.mockResolvedValue(undefined);

    renderLoginPage();
    await waitFor(() => expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'agent@acme.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });
  });

  it('does not redirect if already on login page and login fails', async () => {
    apiClient.getMe.mockRejectedValue(new Error('not authenticated'));
    apiClient.login.mockRejectedValue(new Error('bad creds'));

    renderLoginPage();
    await waitFor(() => expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'x@x.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument());
    expect(screen.queryByTestId('home-page')).not.toBeInTheDocument();
  });
});
