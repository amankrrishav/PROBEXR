"""
tests/test_summarize_prep_result.py — A-22: SummarizePrepResult as @dataclass

Verifies SummarizePrepResult was converted from a manual __init__ class
to a proper @dataclass, consistent with the rest of the codebase.
"""
import dataclasses


class TestSummarizePrepResultDataclass:
    def test_is_dataclass(self):
        """SummarizePrepResult must be a dataclass."""
        from app.services.summarizer import SummarizePrepResult
        assert dataclasses.is_dataclass(SummarizePrepResult), (
            "SummarizePrepResult must be decorated with @dataclass"
        )

    def test_instantiation_with_defaults(self):
        """SummarizePrepResult must be instantiable with no arguments."""
        from app.services.summarizer import SummarizePrepResult
        result = SummarizePrepResult()
        assert result.extractive_result is None
        assert result.messages is None
        assert result.max_tokens == 800
        assert result.temperature == 0.3
        assert result.keywords == []
        assert result.takeaway_count == 5

    def test_is_extractive_property_works(self):
        """is_extractive property must still work correctly after dataclass conversion."""
        from app.services.summarizer import SummarizePrepResult
        extractive = SummarizePrepResult(extractive_result="Some summary.")
        llm = SummarizePrepResult(messages=[{"role": "user", "content": "text"}])
        assert extractive.is_extractive is True
        assert llm.is_extractive is False

    def test_keywords_default_is_list_not_shared(self):
        """Each instance must get its own keywords list (field default_factory=list)."""
        from app.services.summarizer import SummarizePrepResult
        a = SummarizePrepResult()
        b = SummarizePrepResult()
        a.keywords.append("ai")
        assert b.keywords == [], "keywords lists must not be shared between instances"

    def test_keywords_empty_list_accepted(self):
        """Passing keywords=[] must work without error."""
        from app.services.summarizer import SummarizePrepResult
        result = SummarizePrepResult(keywords=[])
        assert result.keywords == []