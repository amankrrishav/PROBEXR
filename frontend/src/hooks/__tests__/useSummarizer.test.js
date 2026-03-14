/**
 * Tests for useSummarizer hook.
 *
 * Mocks: services/api.js, config.js
 * Tests: initial state, successful summarize (fallback path), error handling,
 *        min-word validation, and reset.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSummarizer } from '../useSummarizer.js';

// ── Mocks ──────────────────────────────────────────────────────
vi.mock('../../services/api.js', () => ({
  summarizeText: vi.fn(),
  summarizeTextStream: vi.fn(),
  ingestUrl: vi.fn(),
  ingestText: vi.fn(),
}));

vi.mock('../../config.js', () => ({
  config: {
    summarizer: { minWords: 30 },
    loadingMessages: ['Analyzing…', 'Ranking…', 'Removing…', 'Finalizing…'],
  },
}));

import { summarizeText, summarizeTextStream, ingestText } from '../../services/api.js';

// ── Helpers ────────────────────────────────────────────────────
beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

// Helper: generate text with N words
const wordsOf = (n) => Array.from({ length: n }, (_, i) => `word${i}`).join(' ');

// ── Tests ──────────────────────────────────────────────────────
describe('useSummarizer', () => {

  it('has correct initial state', () => {
    const { result } = renderHook(() => useSummarizer());

    expect(result.current.loading).toBe(false);
    expect(result.current.summaryText).toBe('');
    expect(result.current.error).toBeNull();
    expect(result.current.hasSummary).toBe(false);
    expect(result.current.streaming).toBe(false);
    expect(result.current.summaryMode).toBe('paragraph');
    expect(result.current.summaryLength).toBe('standard');
  });

  it('rejects summarize when word count is below minimum', async () => {
    const { result } = renderHook(() => useSummarizer());

    // Set text with only 5 words (below 30 min)
    act(() => result.current.setText('one two three four five'));

    await act(async () => {
      result.current.onSummarize();
    });

    expect(result.current.error).toMatch(/minimum.*30.*words/i);
    expect(summarizeText).not.toHaveBeenCalled();
    expect(summarizeTextStream).not.toHaveBeenCalled();
  });

  it('handles a successful summary via non-streaming fallback', async () => {
    const mockResult = {
      summary: 'This is the summary output.',
      quality: 'full',
      compression_ratio: 85,
      original_word_count: 100,
      key_takeaways: ['Point A', 'Point B'],
    };

    // Streaming throws → falls back to summarizeText
    summarizeTextStream.mockRejectedValue(new Error('SSE not available'));
    summarizeText.mockResolvedValue(mockResult);
    ingestText.mockResolvedValue({ id: 42 });

    const { result } = renderHook(() => useSummarizer());

    // Set enough text
    act(() => result.current.setText(wordsOf(50)));

    await act(async () => {
      await result.current.onSummarize();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.summaryText).toBe('This is the summary output.');
    expect(result.current.hasSummary).toBe(true);
    expect(result.current.error).toBeNull();
    expect(summarizeText).toHaveBeenCalledOnce();
  });

  it('handles an error during summarize', async () => {
    summarizeTextStream.mockRejectedValue(new Error('SSE fail'));
    summarizeText.mockRejectedValue(new Error('Backend is down'));
    ingestText.mockResolvedValue({ id: 1 });

    const { result } = renderHook(() => useSummarizer());

    act(() => result.current.setText(wordsOf(50)));

    await act(async () => {
      await result.current.onSummarize();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('Backend is down');
    expect(result.current.hasSummary).toBe(false);
  });

  it('reset clears all state', async () => {
    const mockResult = {
      summary: 'Summary here.',
      quality: 'full',
      key_takeaways: [],
    };

    summarizeTextStream.mockRejectedValue(new Error('no stream'));
    summarizeText.mockResolvedValue(mockResult);
    ingestText.mockResolvedValue({ id: 7 });

    const { result } = renderHook(() => useSummarizer());

    act(() => result.current.setText(wordsOf(50)));

    await act(async () => {
      await result.current.onSummarize();
    });

    expect(result.current.summaryText).toBe('Summary here.');

    act(() => result.current.reset());

    expect(result.current.summaryText).toBe('');
    expect(result.current.text).toBe('');
    expect(result.current.hasSummary).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.summaryMode).toBe('paragraph');
  });
});
