# ReadPulse Roadmap

ReadPulse is designed as an **open-source app** with a path to **subscription / startup** later. This doc outlines phases and where to plug in new features.

---

## Current (MVP)

- **Backend:** FastAPI, config, routers, services. Summarize (extractive + LLM). Health with version, mode, capabilities.
- **Frontend:** React + Vite, config, hooks, features. Summarizer + theme. Backend health on load, request timeout.
- **Subscription-ready:** Config placeholders (`SUBSCRIPTION_ENABLED`, `FREE_DAILY_LIMIT`), health `subscription_enabled`, `deps.get_optional_user()`. No billing yet.

---

## Phase 2 — More features (still free / open)

- **URL → text:** Backend route `POST /api/url-fetch` (or reuse existing serverless). Frontend: URL input, `useUrlFetch`, feature component.
- **Export:** Download summary as TXT/MD. Backend optional; can be client-only.
- **Reading time / difficulty:** Reintroduce as optional UI (utils + display in OutputCard or sidebar).
- **i18n:** If you want multiple languages, add a small i18n layer and translate config strings + UI.

---

## Phase 3 — Auth (optional accounts)

- **Backend:** Implement `app/deps.py` — `get_current_user` (JWT or API key), `get_optional_user`. Add `POST /auth/register`, `POST /auth/login` (or OAuth).
- **Frontend:** Auth context, login/register pages, protect routes or show “Sign in to sync” CTA.
- **DB:** Add a small DB (e.g. SQLite/Postgres) for users and usage. Backend service `auth`, `users`.

---

## Phase 4 — Subscription / startup

- **Backend:** Turn on `SUBSCRIPTION_ENABLED`. Enforce `FREE_DAILY_LIMIT` per user (or per IP for anonymous). Add `GET /me` or `GET /usage` for plan and usage. Integrate Stripe (or similar): webhook, plans (free / pro / team).
- **Frontend:** `config.subscription.enabled`, `showUpgradeCta`. Pricing page, “Upgrade” in sidebar, limit-reached message using backend health/usage.
- **Open source:** Keep core summarization and extractive path free and open. Optional: “ReadPulse Cloud” as a hosted subscription; self-host remains free.

---

## Adding a feature (any phase)

1. **Backend:** Config → schema → service → router → mount in `main.py`. Optional: dependency in `deps.py` (auth, limit).
2. **Frontend:** Config → `services/api.js` → hook → feature folder → wire in `App.jsx`.
3. **Docs:** Update README, ROADMAP, or CONTRIBUTING as needed.

See [CONTRIBUTING.md](CONTRIBUTING.md) for code layout and run instructions.
