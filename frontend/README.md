# ReadPulse Frontend

React + Vite frontend. Structure matches backend: config, services (API), hooks, features.

## Structure (scalable)

```
src/
├── config.js           # Env and constants (like backend app/config.py)
├── App.jsx             # Thin shell: composes hooks + features
├── main.jsx
├── index.css
├── services/           # API layer (like backend routers)
│   ├── client.js       # Base URL, request(), parseErrorDetail
│   └── api.js          # summarizeText(), ingestText(), ingestUrl(), sendChatMessage(), generateAudioSummary(), generateFlashcards(), synthesizeDocuments()
├── hooks/              # Feature and app state (like backend services)
│   ├── useSummarizer.js
│   └── useTheme.js
└── features/           # Feature modules (like backend routers by domain)
    ├── layout/         # Sidebar, etc.
    │   ├── index.js
    │   └── Sidebar.jsx
    └── summarizer/     # Editor, OutputCard, TypingSummary, ChatView, SynthesisWorkspace
        ├── index.js
        ├── Editor.jsx
        ├── OutputCard.jsx
        ├── ChatView.jsx
        ├── DocumentActions.jsx
        ├── SynthesisWorkspace.jsx
        └── TypingSummary.jsx
```

**Adding a feature:** add config (if needed) → API in `services/api.js` → hook in `hooks/` → feature folder under `features/` → wire in `App.jsx`.

## Run

```bash
npm install
npm run dev
```

Uses `VITE_API_URL` (default `http://localhost:8000`) to talk to the backend.

## Env

| Env | Purpose |
|-----|--------|
| `VITE_API_URL` | Backend base URL (default `http://localhost:8000`) |
| `VITE_APP_NAME` | App name (optional) |
| `VITE_SUMMARIZE_MIN_WORDS` | Min words for summarizer (optional, default 30) |
