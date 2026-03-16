/**
 * Auth API — matches backend /auth endpoints.
 */
import { request } from "./client.js";

export async function register({ email, password }) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function login({ email, password }) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getCurrentUser() {
  return request("/auth/me", {
    method: "GET",
  });
}

export async function refreshToken() {
  return request("/auth/refresh", {
    method: "POST",
    _skipAutoRefresh: true, // Prevent infinite loop — this IS the refresh call
  });
}

export async function logout() {
  return request("/auth/logout", {
    method: "POST",
    _skipAutoRefresh: true,
  });
}

export async function logoutAll() {
  return request("/auth/logout-all", {
    method: "POST",
  });
}

export async function updateProfile(data) {
  return request("/auth/me", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function requestMagicLink(email) {
  return request("/auth/magic-link", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function forgotPassword(email) {
  return request("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token, newPassword) {
  return request("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export async function resendVerification(email) {
  return request("/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}