"""
tests/test_textrank_sentence_limit.py — A-33: TextRank O(N²) sentence cap

Verifies that extractive.py caps sentences at 300 before computing the
TextRank similarity matrix, preventing perceptible lag on long documents.
"""
import inspect
import time


def _make_long_text(sentence_count: int) -> str:
    sentence = (
        "Researchers have found that machine learning models perform better "
        "with more training data and careful hyperparameter tuning. "
    )
    return sentence * sentence_count


class TestTextRankSentenceLimit:
    def test_sentence_cap_constant_defined(self):
        """_SENTENCE_LIMIT constant must exist in extractive.py."""
        import app.services.extractive as ext
        src = inspect.getsource(ext)
        assert '_SENTENCE_LIMIT' in src, (
            "extractive.py must define _SENTENCE_LIMIT for the O(N²) guard"
        )

    def test_short_text_produces_summary(self):
        """Text well under 300 sentences produces a valid summary without truncation."""
        from app.services.extractive import summarize_extractive
        text = _make_long_text(10)
        result = summarize_extractive(text, min_words=30)
        assert "summary" in result
        assert len(result["summary"]) > 0

    def test_long_text_completes_in_reasonable_time(self):
        """Text with 400+ sentences must complete in under 10s (cap is working)."""
        from app.services.extractive import summarize_extractive
        text = _make_long_text(400)
        start = time.time()
        result = summarize_extractive(text, min_words=30)
        elapsed = time.time() - start
        assert "summary" in result
        assert elapsed < 10.0, (
            f"TextRank took {elapsed:.1f}s on 400-sentence text — "
            "sentence cap may not be firing"
        )

    def test_long_text_still_produces_summary(self):
        """Even after capping, a meaningful summary is returned."""
        from app.services.extractive import summarize_extractive
        text = _make_long_text(400)
        result = summarize_extractive(text, min_words=30)
        assert len(result["summary"].split()) >= 10, (
            "Summary should have at least 10 words even after sentence cap"
        )

    def test_cap_preserves_content(self):
        """Capped text still produces a non-empty result."""
        from app.services.extractive import summarize_extractive
        text = _make_long_text(350)
        result = summarize_extractive(text, min_words=30)
        assert result["summary"]
        assert isinstance(result["key_takeaways"], list)