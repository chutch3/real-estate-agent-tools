import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '../../../src/components/ProtectedRoute';
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

function renderWithRoute() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <AuthProvider>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div data-testid="protected-content">Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div data-testid="login-page">Login</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('ProtectedRoute', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('shows a loading indicator while auth check is in progress', () => {
    apiClient.getMe.mockReturnValue(new Promise(() => {}));

    renderWithRoute();

    expect(screen.getByTestId('auth-loading')).toBeInTheDocument();
  });

  it('redirects to /login when user is not authenticated', async () => {
    apiClient.getMe.mockRejectedValue(new Error('unauthorized'));

    renderWithRoute();

    await waitFor(() => {
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('renders children when user is authenticated', async () => {
    apiClient.getMe.mockResolvedValue(_AUTHENTICATED_USER);

    renderWithRoute();

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });
});
