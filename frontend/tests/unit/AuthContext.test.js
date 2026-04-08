import React from 'react';
import { renderHook, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../../src/context/AuthContext';
import apiClient from '../../src/apiClient';

jest.mock('../../src/apiClient', () => ({
  getMe: jest.fn(),
  login: jest.fn(),
  logout: jest.fn(),
}));

describe('AuthContext', () => {
  const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('calls getMe on mount to determine auth status', async () => {
    apiClient.getMe.mockRejectedValue(new Error('unauthorized'));

    renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(apiClient.getMe).toHaveBeenCalledTimes(1);
    });
  });

  it('sets user when getMe resolves', async () => {
    const user = { id: 'u1', email: 'agent@acme.com', role: 'AGENT', brokerage: { name: 'Acme' } };
    apiClient.getMe.mockResolvedValue(user);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.user).toEqual(user);
    });
  });

  it('user is null and isLoading is false when getMe rejects', async () => {
    apiClient.getMe.mockRejectedValue(new Error('unauthorized'));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.user).toBeNull();
  });

  it('isLoading is true before getMe settles', () => {
    apiClient.getMe.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isLoading).toBe(true);
  });

  it('login calls apiClient.login then getMe and updates user', async () => {
    const user = { id: 'u1', email: 'agent@acme.com', role: 'AGENT', brokerage: { name: 'Acme' } };
    apiClient.getMe
      .mockRejectedValueOnce(new Error('not yet'))
      .mockResolvedValueOnce(user);
    apiClient.login.mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.login('agent@acme.com', 'password123');
    });

    expect(apiClient.login).toHaveBeenCalledWith('agent@acme.com', 'password123');
    expect(result.current.user).toEqual(user);
  });

  it('login propagates error when apiClient.login rejects', async () => {
    apiClient.getMe.mockRejectedValue(new Error('not auth'));
    apiClient.login.mockRejectedValue(new Error('Invalid credentials'));

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await expect(
      act(async () => {
        await result.current.login('bad@acme.com', 'wrong');
      })
    ).rejects.toThrow('Invalid credentials');

    expect(result.current.user).toBeNull();
  });

  it('logout calls apiClient.logout and clears user', async () => {
    const user = { id: 'u1', email: 'agent@acme.com', role: 'AGENT', brokerage: { name: 'Acme' } };
    apiClient.getMe.mockResolvedValue(user);
    apiClient.logout.mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.user).toEqual(user));

    await act(async () => {
      await result.current.logout();
    });

    expect(apiClient.logout).toHaveBeenCalledTimes(1);
    expect(result.current.user).toBeNull();
  });
});
