# ReadPulse Roadmap

ReadPulse is designed as an **open-source app** with a path to **subscription / startup** later. This doc outlines phases and where to plug in new features.

---

## Current (MVP)

- **Backend:** FastAPI, config, routers, services. Summarize (extractive + LLM), health with version/mode/capabilities, basic auth (email + password, JWT), and fake subscription logic (free vs Pro plan flag, daily usage counters, reduced-quality summaries after free limit).
- **Frontend:** React + Vite, config, hooks, features. Summarizer + theme, backend health on load, request timeout, auth modal (sign up / log in), account menu, plan + daily usage display, and Pro Mode demo flow.
- **Subscription-ready:** Config (`SUBSCRIPTION_ENABLED`, `FREE_DAILY_LIMIT`), health `subscription_enabled`, per-user usage tracking, and a demo upgrade endpoint (`POST /auth/upgrade/demo-pro`) instead of real billing.

---

## Phase 2 — More features (still free / open)

- **URL → text:** Backend route `POST /api/url-fetch` (or reuse existing serverless). Frontend: URL input, `useUrlFetch`, feature component.
- **Export:** Download summary as TXT/MD. Backend optional; can be client-only.
- **Reading time / difficulty:** Reintroduce as optional UI (utils + display in OutputCard or sidebar).
- **i18n:** If you want multiple languages, add a small i18n layer and translate config strings + UI.

---

## Phase 3 — Auth (optional accounts)

- **Backend:** (Partially done) `get_current_user` / `get_optional_user`, `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, SQLite `User` model with plan + usage. Future: social login / OAuth and Postgres migration.
- **Frontend:** (Partially done) Auth hook + modal, account dropdown, usage surfaced in UI. Future: full settings page, multi-device sync, and richer account management.

---

## Phase 4 — Subscription / startup

- **Backend:** Integrate real billing (Stripe or similar) on top of existing `plan` + `usage_today` fields. Replace demo endpoint `POST /auth/upgrade/demo-pro` with real plan changes via webhooks. Support multiple tiers (free / pro / team) and enforce limits per plan.
- **Frontend:** Turn Pro Mode demo into a real pricing + checkout flow. Use `config.subscription.enabled` and add a pricing page, stronger upgrade CTAs, and clearer “Lite vs Pro” explanations.
- **Open source:** Keep core summarization and extractive path free and open. Optional: “ReadPulse Cloud” as a hosted subscription; self-host remains free, with maintainers free to customize plans/pricing.

---

## Adding a feature (any phase)

1. **Backend:** Config → schema → service → router → mount in `main.py`. Optional: dependency in `deps.py` (auth, limit).
2. **Frontend:** Config → `services/api.js` → hook → feature folder → wire in `App.jsx`.
3. **Docs:** Update README, ROADMAP, or CONTRIBUTING as needed.

See [CONTRIBUTING.md](CONTRIBUTING.md) for code layout and run instructions.
