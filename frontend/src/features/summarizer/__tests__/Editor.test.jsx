/**
 * Editor component tests — A-37
 *
 * Covers: rendering, summarize button states, URL mode,
 * word count display, length selector, error display.
 *
 * Editor depends on SummarizerContext and AppContext — both are mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Editor from '../Editor.jsx';

// ── Context mocks ────────────────────────────────────────────────────────

const mockSummarizerContext = {
    text: '',
    setText: vi.fn(),
    loading: false,
    streaming: false,
    cancelStreaming: vi.fn(),
    wordCount: 0,
    hasSummary: false,
    isUrlMode: false,
    setIsUrlMode: vi.fn(),
    url: '',
    setUrl: vi.fn(),
    summaryLength: 'standard',
    setSummaryLength: vi.fn(),
    summaryMode: 'paragraph',
    setSummaryMode: vi.fn(),
    summaryTone: 'neutral',
    setSummaryTone: vi.fn(),
    focusKeywords: [],
    setFocusKeywords: vi.fn(),
    focusArea: '',
    setFocusArea: vi.fn(),
    outputLanguage: 'English',
    setOutputLanguage: vi.fn(),
    customInstructions: '',
    setCustomInstructions: vi.fn(),
    resetAdvanced: vi.fn(),
    summarizeStatus: null,
    textareaRef: { current: null },
    error: null,
};

const mockAppContext = {
    providerStatus: { status: 'online' },
};

vi.mock('../../../contexts/SummarizerContext.jsx', () => ({
    useSummarizerContext: () => mockSummarizerContext,
}));

vi.mock('../../../contexts/AppContext.jsx', () => ({
    useAppContext: () => mockAppContext,
}));

// Sub-component mocks — test Editor in isolation
vi.mock('../components/ComplexityMeter.jsx', () => ({ default: () => null }));
vi.mock('../components/ModeSelector.jsx', () => ({ default: () => null }));
vi.mock('../components/AdvancedPanel.jsx', () => ({ default: () => null }));
vi.mock('../components/InputTabs.jsx', () => ({
    default: ({ text, setText }) => (
        <div data-testid="input-tabs">
            <textarea
                data-testid="mock-textarea"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste your article..."
            />
        </div>
    ),
}));

// ── Helpers ──────────────────────────────────────────────────────────────

function renderEditor(contextOverrides = {}, appOverrides = {}) {
    Object.assign(mockSummarizerContext, contextOverrides);
    Object.assign(mockAppContext, appOverrides);
    return render(
        <Editor
            onSummarize={vi.fn()}
            handleKeyDown={vi.fn()}
            focusMode={false}
        />
    );
}

beforeEach(() => {
    vi.clearAllMocks();
    // Reset context to defaults
    Object.assign(mockSummarizerContext, {
        text: '', loading: false, streaming: false,
        wordCount: 0, hasSummary: false, isUrlMode: false,
        url: '', summaryLength: 'standard', error: null,
        summarizeStatus: null,
    });
    Object.assign(mockAppContext, { providerStatus: { status: 'online' } });
});

// ── Rendering ────────────────────────────────────────────────────────────

describe('Editor rendering', () => {
    it('renders the hero header when no summary exists', () => {
        renderEditor({ hasSummary: false });
        expect(screen.getByText('Distill what matters.')).toBeTruthy();
    });

    it('hides the hero header when a summary already exists', () => {
        renderEditor({ hasSummary: true });
        expect(screen.queryByText('Distill what matters.')).toBeNull();
    });

    it('shows 0 words when text is empty', () => {
        renderEditor({ wordCount: 0 });
        expect(screen.getByText('0 words')).toBeTruthy();
    });

    it('displays the correct word count', () => {
        renderEditor({ wordCount: 342 });
        expect(screen.getByText('342 words')).toBeTruthy();
    });
});

// ── Summarize button states ──────────────────────────────────────────────

describe('Editor summarize button', () => {
    it('shows "Summarize →" by default', () => {
        renderEditor();
        expect(screen.getByText('Summarize →')).toBeTruthy();
    });

    it('shows "Streaming…" when streaming is true', () => {
        renderEditor({ streaming: true });
        expect(screen.getByText('Streaming…')).toBeTruthy();
    });

    it('shows "Regenerate ↺" when hasSummary is true', () => {
        renderEditor({ hasSummary: true });
        expect(screen.getByText('Regenerate ↺')).toBeTruthy();
    });

    it('is disabled when loading', () => {
        renderEditor({ loading: true });
        const btn = screen.getByRole('button', { name: /summarizing/i });
        expect(btn.disabled).toBe(true);
    });

    it('is disabled when provider is offline', () => {
        renderEditor({}, { providerStatus: { status: 'offline' } });
        const btn = screen.getByText('Summarize →').closest('button');
        expect(btn.disabled).toBe(true);
    });

    it('calls onSummarize when clicked', () => {
        const onSummarize = vi.fn();
        render(
            <Editor onSummarize={onSummarize} handleKeyDown={vi.fn()} focusMode={false} />
        );
        fireEvent.click(screen.getByText('Summarize →'));
        expect(onSummarize).toHaveBeenCalledTimes(1);
    });
});

// ── Error display ────────────────────────────────────────────────────────

describe('Editor error display', () => {
    it('shows error message from context', () => {
        renderEditor({ error: 'Text too short. Minimum 30 words.' });
        expect(screen.getByText('Text too short. Minimum 30 words.')).toBeTruthy();
    });

    it('does not show error banner when error is null', () => {
        renderEditor({ error: null });
        expect(screen.queryByText(/⚠/)).toBeNull();
    });
});

// ── Length selector ──────────────────────────────────────────────────────

describe('Editor length selector', () => {
    it('shows length options when no summary exists', () => {
        renderEditor({ hasSummary: false });
        expect(screen.getByText('Short')).toBeTruthy();
        expect(screen.getByText('Medium')).toBeTruthy();
        expect(screen.getByText('Long')).toBeTruthy();
    });

    it('calls setSummaryLength when a length option is clicked', () => {
        renderEditor({ hasSummary: false });
        fireEvent.click(screen.getByText('Short'));
        expect(mockSummarizerContext.setSummaryLength).toHaveBeenCalledWith('brief');
    });

    it('hides length selector when summary already exists', () => {
        renderEditor({ hasSummary: true });
        expect(screen.queryByText('Short')).toBeNull();
    });
});

// ── Streaming cancel ─────────────────────────────────────────────────────

describe('Editor streaming cancel', () => {
    it('shows Stop button when streaming', () => {
        renderEditor({ streaming: true });
        expect(screen.getByText('Stop')).toBeTruthy();
    });

    it('calls cancelStreaming when Stop is clicked', () => {
        renderEditor({ streaming: true });
        fireEvent.click(screen.getByText('Stop'));
        expect(mockSummarizerContext.cancelStreaming).toHaveBeenCalledTimes(1);
    });

    it('hides Stop button when not streaming', () => {
        renderEditor({ streaming: false });
        expect(screen.queryByText('Stop')).toBeNull();
    });
});