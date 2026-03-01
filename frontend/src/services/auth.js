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

export async function logout() {
  return request("/auth/logout", {
    method: "POST",
  });
}
