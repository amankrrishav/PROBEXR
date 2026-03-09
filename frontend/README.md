# ReadPulse Frontend

React + Vite frontend. Structure matches backend: config, services (API), hooks, features. Includes premium **Auth UX** (Google, GitHub, Magic Links).

## Features

- **Social Login:** Google and GitHub integration.
- **Magic Links:** Passwordless signup/login via email.
- **Profile Management:** In-app settings for name and avatar.
- **Modern UI:** Vibrant, premium design with dark mode and smooth transitions.

## Structure (scalable)

- **src/services/auth.js** — API client for authentication (JWT based).
- **src/hooks/useAuth.js** — Central state management for user sessions and profile updates.
- **src/features/auth/** — AuthModal, SocialCallback, and AccountSettings components.



## Production Deployment (Netlify)

1. **Connect GitHub:** Deploy the `/frontend` subdirectory.
2. **Build Settings:** Netlify automatically uses `netlify.toml`.
3. **Env Vars:** Set `VITE_API_URL` to your Render backend URL.

## Env

| Env | Purpose |
|-----|--------|
| `VITE_API_URL` | Backend base URL. |
| `VITE_APP_NAME` | Defaults to `ReadPulse`. |
| `VITE_SUMMARIZE_MIN_WORDS` | Min word count to trigger summarization (default 30). |
