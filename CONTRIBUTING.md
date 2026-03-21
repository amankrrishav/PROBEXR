# Contributing to PROBEXR

Thanks for your interest in PROBEXR. This document covers contribution guidelines.

---

## Getting Started

To contribute, please reach out to the maintainer to discuss the feature or fix before submitting a PR.

---

## Code Style

- **Backend:** Python, FastAPI conventions. Async functions for all DB and LLM operations. Type hints where helpful.
- **Frontend:** React 19, ES modules. Feature-based folder structure.

---

## Pull Request Process

1. Fork the repository.
2. Create a feature branch from `main`.
3. Ensure all tests pass before submitting.
4. Write clear commit messages describing the change.
5. Submit a PR with a description of what was changed and why.

---

## Testing

- Backend tests use `pytest` with async fixtures.
- Frontend tests use `vitest` with `@testing-library/react`.
- All PRs must maintain 100% pass rate (currently 348 backend + 108 frontend tests).

---

## Questions?

Open an issue or reach out to the maintainer.
