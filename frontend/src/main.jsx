import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './index.css'
import App from './App.jsx'
import { ErrorBoundary } from './components/ErrorBoundary.jsx'

import { AppProvider } from "./contexts/AppContext.jsx";
import { SummarizerProvider } from "./contexts/SummarizerContext.jsx";

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <AppProvider>
        <SummarizerProvider>
          <App />
        </SummarizerProvider>
      </AppProvider>
    </ErrorBoundary>
  </StrictMode>
)