# PROBEXR Roadmap

This doc outlines completed work and upcoming phases.

---

## Current (Completed)

- Full-stack article summarizer with two-stage human-like summarization
- URL ingestion, contextual chat, multi-document synthesis, flashcard export
- Enterprise-grade authentication (email/password, Google, GitHub, Magic Links)
- Real-time SSE streaming for token delivery
- Comprehensive analytics dashboard
- Cross-domain CSRF protection and timing-safe OAuth
- Lazy-initialized async database with composite indexes and soft deletes
- Redis-backed cache-aside layer and non-blocking background emails (dead-lettering)
- Global API error handling and robust observability (Prometheus & Grafana)
- React Error Boundary, SWR data fetching, and Service Worker offline support
- Code-split lazy loaded pages and skeleton loading screens
- ETag-based conditional responses and robust SSE streaming
- 349 backend + 108 frontend tests — 100% pass rate
- Comprehensive Load and E2E Testing suites
- CI/CD pipeline (GitHub Actions, strict mypy, ruff, vitest, pytest)
---

## Phase Next — Growth & Retention

- [ ] **Browser Extension** — one-click "Summarize this page" for Chrome/Firefox
- [ ] **Export & Sharing** — copy as markdown, PDF export, public share links
- [ ] **Highlights & Annotations** — highlight text spans, add notes, export
- [ ] **Real TTS** — browser SpeechSynthesis API, then server-side TTS with better voices

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
