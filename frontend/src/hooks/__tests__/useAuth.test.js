/**
 * Tests for useAuth hook.
 *
 * Mocks: services/auth.js
 * Tests: unauthenticated init, authenticated init, successful login,
 *        login error, and logout.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth } from '../useAuth.js';

// ── Mocks ──────────────────────────────────────────────────────
vi.mock('../../services/auth.js', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  logoutAll: vi.fn(),
  refreshToken: vi.fn(),
  updateProfile: vi.fn(),
}));

import {
  getCurrentUser,
  login as loginApi,
  register as registerApi,
  logout as logoutApi,
  refreshToken,
} from '../../services/auth.js';

// ── Helpers ────────────────────────────────────────────────────
const mockUser = { id: 1, email: 'test@example.com' };

beforeEach(() => {
  vi.clearAllMocks();
});

// ── Tests ──────────────────────────────────────────────────────
describe('useAuth', () => {

  it('initializes as unauthenticated when no session exists', async () => {
    getCurrentUser.mockRejectedValue(new Error('Unauthorized'));
    refreshToken.mockRejectedValue(new Error('No refresh token'));

    const { result } = renderHook(() => useAuth());

    // Initially loading
    expect(result.current.initializing).toBe(true);

    await waitFor(() => {
      expect(result.current.initializing).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('initializes with existing session', async () => {
    getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.initializing).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('recovers session via refresh token', async () => {
    // First getCurrentUser fails, then refresh succeeds, then second getCurrentUser succeeds
    getCurrentUser
      .mockRejectedValueOnce(new Error('Token expired'))
      .mockResolvedValueOnce(mockUser);
    refreshToken.mockResolvedValue({ access_token: 'new-token' });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.initializing).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(refreshToken).toHaveBeenCalledOnce();
  });

  it('handles successful login', async () => {
    // Init: no session
    getCurrentUser
      .mockRejectedValueOnce(new Error('Unauthorized'))     // init
      .mockResolvedValueOnce(mockUser);                     // after login
    refreshToken.mockRejectedValue(new Error('No token'));
    loginApi.mockResolvedValue({ access_token: 'abc' });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.initializing).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);

    await act(async () => {
      await result.current.login({ email: 'test@example.com', password: 'password123' });
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.error).toBeNull();
    expect(result.current.submitting).toBe(false);
  });

  it('handles login error', async () => {
    // Init: no session
    getCurrentUser.mockRejectedValue(new Error('Unauthorized'));
    refreshToken.mockRejectedValue(new Error('No token'));
    loginApi.mockRejectedValue(new Error('Invalid credentials'));

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.initializing).toBe(false);
    });

    await act(async () => {
      try {
        await result.current.login({ email: 'bad@example.com', password: 'wrong' });
      } catch (e) {
        expect(e.message).toBe('Invalid credentials');
      }
    });

    expect(result.current.user).toBeNull();
    expect(result.current.error).toBe('Invalid credentials');
    expect(result.current.submitting).toBe(false);
  });

  it('logout clears user state', async () => {
    // Init with session
    getCurrentUser
      .mockResolvedValueOnce(mockUser)    // init
      .mockResolvedValueOnce(mockUser);   // after login (not used here)
    logoutApi.mockResolvedValue({});

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.initializing).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(true);

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
