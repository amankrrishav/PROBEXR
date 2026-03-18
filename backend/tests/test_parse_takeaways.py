"""
tests/test_parse_takeaways.py — A-07: parse_takeaways public export

Verifies that _parse_takeaways was renamed to parse_takeaways, exported
from the summarizer package __init__.py, and that streaming.py no longer
imports the private function directly from core.
"""
import inspect


class TestParseTakeawaysPublicExport:
    def test_importable_from_package(self):
        """parse_takeaways must be importable from app.services.summarizer."""
        from app.services.summarizer import parse_takeaways
        assert callable(parse_takeaways)

    def test_listed_in_all(self):
        """parse_takeaways must appear in summarizer.__all__."""
        import app.services.summarizer as pkg
        assert 'parse_takeaways' in pkg.__all__

    def test_streaming_router_no_longer_uses_private_import(self):
        """streaming.py must not import _parse_takeaways from core directly."""
        import app.routers.streaming as streaming
        src = inspect.getsource(streaming)
        assert 'from app.services.summarizer.core import _parse_takeaways' not in src, (
            "streaming.py must not import private _parse_takeaways from core"
        )

    def test_streaming_router_uses_public_function(self):
        """streaming.py must use the public parse_takeaways."""
        import app.routers.streaming as streaming
        src = inspect.getsource(streaming)
        assert 'parse_takeaways' in src

    def test_parses_bullet_prefixes(self):
        """parse_takeaways correctly strips •, -, * bullet prefixes."""
        from app.services.summarizer import parse_takeaways
        raw = "• First point here.\n- Second point here.\n* Third point here."
        result = parse_takeaways(raw)
        assert len(result) == 3
        assert result[0] == "First point here."
        assert result[1] == "Second point here."
        assert result[2] == "Third point here."

    def test_parses_numbered_list(self):
        """parse_takeaways strips numbered list prefixes like 1. 2. 3."""
        from app.services.summarizer import parse_takeaways
        raw = "1. First item.\n2. Second item.\n3. Third item."
        result = parse_takeaways(raw)
        assert len(result) == 3
        assert result[0] == "First item."

    def test_skips_blank_lines(self):
        """parse_takeaways ignores blank lines between bullets."""
        from app.services.summarizer import parse_takeaways
        raw = "• First.\n\n\n• Second."
        result = parse_takeaways(raw)
        assert len(result) == 2