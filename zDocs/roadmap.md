# PROBEXR Roadmap

This doc outlines completed work and upcoming phases.

---

## v1.1.0 (Current)

- Full-stack article summarizer with two-stage human-like summarization
- URL ingestion, contextual chat, multi-document synthesis, flashcard export
- Enterprise-grade authentication (email/password, Google, GitHub, Magic Links)
- API key authentication for programmatic access
- Real-time SSE streaming for token delivery
- Comprehensive analytics dashboard
- Cross-domain CSRF protection and timing-safe OAuth
- Lazy-initialized async database with composite indexes and soft deletes
- Redis-backed cache-aside layer and non-blocking background emails (dead-lettering)
- Global API error handling and robust observability (Prometheus & Grafana)
- LLM API cost tracking via Prometheus counters
- React Error Boundary, SWR data fetching, and Service Worker offline support
- Code-split lazy loaded pages and skeleton loading screens
- ETag-based conditional responses and robust SSE streaming
- GDPR compliance: data export, account deletion, cookie consent
- WCAG 2.1 AA accessibility improvements
- 450 backend + 108 frontend tests — 100% pass rate, 78% coverage
- CI/CD pipeline (GitHub Actions, strict mypy, ruff, vitest, pytest)
- Bundle size monitoring (600KB limit) and SBOM generation

---

## Phase Next — Growth & Retention

- [ ] **Browser Extension** — one-click "Summarize this page" for Chrome/Firefox
- [ ] **Export & Sharing** — copy as markdown, PDF export, public share links
- [ ] **Highlights & Annotations** — highlight text spans, add notes, export
- [ ] **Real TTS** — browser SpeechSynthesis API, then server-side TTS with better voices

---

## Backlog (Deferred)

See [BACKLOG.md](BACKLOG.md) for infrastructure and ops items deferred from the v1.1.0 audit.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
