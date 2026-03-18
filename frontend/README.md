# PROBEXR Frontend

React + Vite frontend. Structure matches backend: config, services (API), hooks, features. Includes premium **Auth UX** (Google, GitHub, Magic Links).

## Features

- **Social Login:** Google and GitHub integration.
- **Magic Links:** Passwordless signup/login via email.
- **Profile Management:** In-app settings for name and avatar.
- **Security-First UI:** Visual password strength hints (NIST compliant) and CSRF protection.
- **Modern UI:** Vibrant, premium design with dark mode and smooth transitions.
- **Testing:** Comprehensive React 19 component testing with `vitest` and `@testing-library/react`.

## Structure (scalable)

- **src/services/auth.js** — API client for authentication (JWT based).
- **src/hooks/useAuth.js** — Central state management for user sessions and profile updates.
- **src/features/auth/** — AuthModal, SocialCallback, and AccountSettings components.



## Production Deployment

1. **Connect your repo:** Deploy the `/frontend` subdirectory on your preferred hosting platform.
2. **Build Settings:** Use `netlify.toml` or equivalent config for your platform.
3. **Env Vars:** Set `VITE_API_URL` to your backend URL.

## Env

| Env | Purpose |
|-----|--------|
| `VITE_API_URL` | Backend base URL. |
| `VITE_APP_NAME` | Defaults to `PROBEXR`. |
| `VITE_SUMMARIZE_MIN_WORDS` | Min word count to trigger summarization (default 30). |
