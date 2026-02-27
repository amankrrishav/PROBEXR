# ReadPulse Roadmap

ReadPulse is designed as an **open-source app** with a path to **subscription / startup** later. This doc outlines phases and where to plug in new features.

---

## Current (Phase 2 Completed)

- **Backend:** FastAPI, config, routers, services. Includes endpoints for Summarize (extractive + LLM), URL Ingest, Text-to-Speech (TTS), Contextual Chat, Flashcard Export, and Multi-Document Synthesis. Health checks, basic auth (email + password, JWT), and fake subscription logic (free vs Pro plan flag, daily usage counters, reduced-quality summaries after free limit) are active.
- **Frontend:** React + Vite, config, hooks, features. Summarizer + theme, backend health on load, request timeout, auth modal (sign up / log in), account menu, plan + daily usage display, and Pro Mode demo flow. Features include the Synthesis Workspace, Sidebar navigation, and interactive Output Cards for audio, chat, and flashcards.
- **Subscription-ready:** Config (`SUBSCRIPTION_ENABLED`, `FREE_DAILY_LIMIT`), health `subscription_enabled`, per-user usage tracking, and a demo upgrade endpoint (`POST /auth/upgrade/demo-pro`) instead of real billing.

---

## Phase 3 — Auth & Ecosystem Expansion

- **Backend:** (Partially done) `get_current_user` / `get_optional_user`, `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, SQLite `User` model with plan + usage. Future: social login / OAuth and Postgres migration.
- **Frontend:** (Partially done) Auth hook + modal, account dropdown, usage surfaced in UI. Future: full settings page, multi-device sync, and richer account management.
- **Mobile Support:** Expanding the React application into React Native for iOS/Android apps or building a dedicated Progressive Web App (PWA).

---

## Phase 4 — Subscription / Startup

- **Backend:** Integrate real billing (Stripe or similar) on top of existing `plan` + `usage_today` fields. Replace demo endpoint `POST /auth/upgrade/demo-pro` with real plan changes via webhooks. Support multiple tiers (free / pro / team) and enforce limits per plan.
- **Frontend:** Turn Pro Mode demo into a real pricing + checkout flow. Use `config.subscription.enabled` and add a pricing page, stronger upgrade CTAs, and clearer “Lite vs Pro” explanations.
- **Open source:** Keep core summarization and extractive path free and open. Optional: “ReadPulse Cloud” as a hosted subscription; self-host remains free, with maintainers free to customize plans/pricing.

---

## Adding a feature (any phase)

1. **Backend:** Config → schema → service → router → mount in `main.py`. Optional: dependency in `deps.py` (auth, limit).
2. **Frontend:** Config → `services/api.js` → hook → feature folder → wire in `App.jsx`.
3. **Docs:** Update README, ROADMAP, or CONTRIBUTING as needed.

See [CONTRIBUTING.md](CONTRIBUTING.md) for code layout and run instructions.
