# 🎨 PROBEXR Frontend

The frontend for PROBEXR is a blazingly fast, modern Single Page Application (SPA) built with React 19 and Vite.

## ✨ Highlights

- **Modern UX/UI:** Designed with dark mode, smooth transitions, and premium authentication flows.
- **Real-time Streaming:** Seamless SSE integration for token-by-token LLM responses, complete with automatic fallback and connection robustness.
- **Smart Data Fetching:** Utilizes SWR for caching, background revalidation, and optimistic UI updates.
- **Offline Ready:** Service Worker integration ensures core assets are cached for offline resilience.
- **Performance Optimized:** Code-split lazy loading with minimal skeleton screens.
- **Accessibility (a11y):** Built to WCAG 2.1 AA standards, featuring keyboard navigation, semantic landmarks, and aria-labels.
- **Resilient:** Global React Error Boundaries protect against app-wide crashes.
- **GDPR Compliant:** Configurable cookie consent banner with localStorage persistence.
- **100% Test Coverage:** 108 comprehensive frontend tests ensuring rock-solid stability.

## 🚀 Getting Started

### Prerequisites
- Node.js (v18 or higher)
- npm or pnpm

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment variables:
   Copy `.env.development` to `.env` and fill in your API URLs.
   ```bash
   cp .env.development .env
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## 🧪 Testing

Run the test suite using Vitest:
```bash
npm run test
```

## 🏗️ Build for Production

```bash
npm run build
```
The output will be available in the `/dist` directory.
