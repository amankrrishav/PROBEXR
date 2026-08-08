# 🧠 PROBEXR

[![CI](https://github.com/amankrrishav/PROBEXR/actions/workflows/ci.yml/badge.svg)](https://github.com/amankrrishav/PROBEXR/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Extract signal. Ignore noise.**
> 
> PROBEXR is a full-stack article summarizer and learning platform. Paste text or URLs, get a short, human-like summary, chat with the document to interrogate facts, and export flashcards seamlessly.

🌐 **Live App:** [https://probexr.vercel.app](https://probexr.vercel.app)

---

## ✨ Key Features

### 📝 Summarization & Intelligence
- **Human-like Summarization:** Two-stage processing (extract → synthesize) powered by OpenAI-compatible APIs.
- **Contextual Chat:** Interrogate your documents directly.
- **Multi-Document Synthesis:** Combine insights across multiple sources into cohesive summaries.
- **Flashcard Export:** Instantly generate Anki-compatible CSV flashcards from your readings.
- **Real-time Delivery:** SSE streaming for fast, token-by-token feedback.

### 🛡️ Authentication & Security
- **Multi-factor Auth Options:** Social Login (Google, GitHub), Magic Links (Passwordless), and API Keys.
- **Enterprise-Grade Protection:** Account lockout, email enumeration defense, CSRF protection, and HttpOnly JWT cookies.
- **GDPR Compliant:** One-click data exports and account deletions with a 30-day soft-delete grace period.

### 📈 Analytics & Observability
- **Usage Dashboards:** Track your personal document library and processing stats.
- **Prometheus Metrics:** Integrated observability for API performance and LLM cost tracking via Grafana.

---

## 🏗️ Architecture & Tech Stack

PROBEXR is built as a modern, decoupled monorepo.

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, Vite, Tailwind CSS (optional), SWR |
| **Backend** | FastAPI (Async), Python 3.11+ |
| **Database** | PostgreSQL (asyncpg) for Prod / SQLite (aiosqlite) for local |
| **Cache & Rate Limiting** | Redis |
| **LLM Provider** | Provider-agnostic (OpenAI, Groq, OpenRouter) |
| **Deployment** | Vercel (Frontend) + Render (Backend) |

### Monorepo Structure
- [`/frontend`](./frontend/) - React SPA and UI components.
- [`/backend`](./backend/) - FastAPI server, database models, and LLM integrations.
- [`/monitoring`](./monitoring/) - Grafana dashboards and Prometheus configuration.

---

## 🚀 Getting Started

To run PROBEXR locally, follow the instructions in the respective directories:

1. **Backend Setup:** See the [Backend README](./backend/README.md) for database configuration, python environment setup, and running the FastAPI server.
2. **Frontend Setup:** See the [Frontend README](./frontend/README.md) for installing npm dependencies and running the Vite dev server.

---

## ⚖️ Legal & Compliance

- [Privacy Policy](PRIVACY_POLICY.md) — How we handle your data, including third-party LLM processing.
- [Terms of Service](TERMS_OF_SERVICE.md) — Acceptable use, disclaimers, and liability.
- [License](LICENSE) — This project is open source and available under the MIT License.
