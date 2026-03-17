/**
 * OutputCard component tests — A-37
 *
 * Covers: loading/streaming/summary states, metadata chips,
 * copy/download actions, takeaways, compression bar visibility.
 *
 * OutputCard reads exclusively from SummarizerContext — mocked here.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import OutputCard from '../OutputCard.jsx';

// ── Sub-component mocks ──────────────────────────────────────────────────
// Isolate OutputCard from its children's own deps

vi.mock('../components/SummaryToolbar.jsx', () => ({
    default: ({ onCopy, onDownload, onReset }) => (
        <div data-testid="summary-toolbar">
            <button onClick={onCopy}>Copy</button>
            <button onClick={onDownload}>Download</button>
            <button onClick={onReset}>Reset</button>
        </div>
    ),
}));

vi.mock('../components/SummaryContent.jsx', () => ({
    default: ({ showLoading, showSummary, summaryText, streaming }) => (
        <div data-testid="summary-content">
            {showLoading && <span data-testid="loading-indicator">Loading…</span>}
            {showSummary && <span data-testid="summary-text">{summaryText}</span>}
            {streaming && <span data-testid="streaming-indicator">Streaming…</span>}
        </div>
    ),
}));

vi.mock('../components/CompressionBar.jsx', () => ({
    default: ({ originalWords, summaryWords }) => (
        <div data-testid="compression-bar">
            {originalWords} → {summaryWords}
        </div>
    ),
}));

vi.mock('../ChatView.jsx', () => ({ default: () => null }));
vi.mock('../DocumentActions.jsx', () => ({ default: () => null }));
vi.mock('../KeyTakeaways.jsx', () => ({
    default: ({ takeaways }) => (
        <ul data-testid="key-takeaways">
            {takeaways.map((t, i) => <li key={i}>{t}</li>)}
        </ul>
    ),
}));
vi.mock('../KeyThemesGraph.jsx', () => ({ default: () => null }));

// ── Context mock ─────────────────────────────────────────────────────────

const mockContext = {
    summaryText: '',
    documentId: null,
    isRestored: false,
    loading: false,
    streaming: false,
    streamingText: '',
    summaryMeta: null,
    keyTakeaways: [],
    reset: vi.fn(),
    summaryMode: 'paragraph',
    hasSummary: false,
    onSummarize: vi.fn(),
};

vi.mock('../../../contexts/SummarizerContext.jsx', () => ({
    useSummarizerContext: () => mockContext,
}));

// ── Helpers ──────────────────────────────────────────────────────────────

function renderCard(overrides = {}) {
    Object.assign(mockContext, overrides);
    return render(<OutputCard />);
}

beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(mockContext, {
        summaryText: '', documentId: null, isRestored: false,
        loading: false, streaming: false, streamingText: '',
        summaryMeta: null, keyTakeaways: [], hasSummary: false,
    });
    // Reset clipboard
    Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: vi.fn().mockResolvedValue(undefined) },
        writable: true,
        configurable: true,
    });
});

// ── States ───────────────────────────────────────────────────────────────

describe('OutputCard states', () => {
    it('renders the Summary header always', () => {
        renderCard();
        expect(screen.getByText('Summary')).toBeTruthy();
    });

    it('shows loading indicator when loading=true and no text', () => {
        renderCard({ loading: true, summaryText: '' });
        expect(screen.getByTestId('loading-indicator')).toBeTruthy();
    });

    it('shows streaming indicator when streaming=true', () => {
        renderCard({ streaming: true, summaryText: 'partial' });
        expect(screen.getByTestId('streaming-indicator')).toBeTruthy();
    });

    it('shows summary text when summary is ready', () => {
        renderCard({
            summaryText: 'This is the final summary.',
            loading: false,
            streaming: false,
        });
        expect(screen.getByTestId('summary-text')).toBeTruthy();
        expect(screen.getByText('This is the final summary.')).toBeTruthy();
    });

    it('shows toolbar only when summary is ready (not loading or streaming)', () => {
        renderCard({
            summaryText: 'Done.',
            loading: false,
            streaming: false,
        });
        expect(screen.getByTestId('summary-toolbar')).toBeTruthy();
    });

    it('hides toolbar when loading', () => {
        renderCard({ loading: true, summaryText: '' });
        expect(screen.queryByTestId('summary-toolbar')).toBeNull();
    });
});

// ── Metadata chips ───────────────────────────────────────────────────────

describe('OutputCard metadata chips', () => {
    const readySummary = {
        summaryText: 'Hello world this is a summary with enough words to count.',
        loading: false,
        streaming: false,
        summaryMode: 'paragraph',
        summaryMeta: { compression_ratio: 75, original_word_count: 400 },
    };

    it('shows mode chip when summary is ready', () => {
        renderCard(readySummary);
        expect(screen.getByText('Paragraph')).toBeTruthy();
    });

    it('shows compression chip when compression_ratio is available', () => {
        renderCard(readySummary);
        expect(screen.getByText(/Compressed to/)).toBeTruthy();
    });

    it('shows reading time stats row', () => {
        renderCard(readySummary);
        expect(screen.getByText(/read/)).toBeTruthy();
    });
});

// ── Takeaways ────────────────────────────────────────────────────────────

describe('OutputCard key takeaways', () => {
    it('renders takeaways when summary is ready and takeaways exist', () => {
        renderCard({
            summaryText: 'A summary.',
            loading: false,
            streaming: false,
            keyTakeaways: ['Point one.', 'Point two.', 'Point three.'],
        });
        expect(screen.getByTestId('key-takeaways')).toBeTruthy();
        expect(screen.getByText('Point one.')).toBeTruthy();
        expect(screen.getByText('Point three.')).toBeTruthy();
    });

    it('does not render takeaways section when list is empty', () => {
        renderCard({
            summaryText: 'A summary.',
            loading: false,
            streaming: false,
            keyTakeaways: [],
        });
        expect(screen.queryByTestId('key-takeaways')).toBeNull();
    });
});

// ── Compression bar ──────────────────────────────────────────────────────

describe('OutputCard compression bar', () => {
    it('shows compression bar when summary and originalWordCount are available', () => {
        renderCard({
            summaryText: 'Short summary here.',
            loading: false,
            streaming: false,
            summaryMeta: { original_word_count: 500, compression_ratio: 80 },
        });
        expect(screen.getByTestId('compression-bar')).toBeTruthy();
    });

    it('hides compression bar when no originalWordCount', () => {
        renderCard({
            summaryText: 'Short summary.',
            loading: false,
            streaming: false,
            summaryMeta: null,
        });
        expect(screen.queryByTestId('compression-bar')).toBeNull();
    });
});

// ── Copy action ──────────────────────────────────────────────────────────

describe('OutputCard copy action', () => {
    it('calls clipboard.writeText with summaryText when Copy is clicked', async () => {
        renderCard({
            summaryText: 'Copy this text please.',
            loading: false,
            streaming: false,
        });

        await act(async () => {
            fireEvent.click(screen.getByText('Copy'));
        });

        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Copy this text please.');
    });
});

// ── Reset action ─────────────────────────────────────────────────────────

describe('OutputCard reset action', () => {
    it('calls reset from context when Reset is clicked', async () => {
        renderCard({
            summaryText: 'Some summary.',
            loading: false,
            streaming: false,
        });

        await act(async () => {
            fireEvent.click(screen.getByText('Reset'));
        });

        expect(mockContext.reset).toHaveBeenCalledTimes(1);
    });
});