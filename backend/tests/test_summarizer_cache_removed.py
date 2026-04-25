"""
tests/test_summarizer_cache_removed.py — A-26: Unused summarizer/cache.py deleted

Verifies that the dead cache.py module has been removed from the summarizer
package so it no longer causes confusion about whether caching is active.
"""

import importlib
import os


def test_cache_module_file_deleted():
    """summarizer/cache.py must not exist on disk."""
    import app.services.summarizer as pkg

    pkg_dir = os.path.dirname(pkg.__file__)
    cache_path = os.path.join(pkg_dir, "cache.py")
    assert not os.path.exists(cache_path), (
        f"summarizer/cache.py is dead code and must be deleted. Found at: {cache_path}"
    )


def test_cache_module_not_importable():
    """app.services.summarizer.cache must not be importable."""
    try:
        importlib.import_module("app.services.summarizer.cache")
        raise AssertionError("summarizer.cache must not be importable — it should be deleted")
    except ModuleNotFoundError:
        pass  # expected


def test_summarizer_package_still_works():
    """Deleting cache.py must not break the summarizer package."""
    from app.services.summarizer import (
        parse_takeaways,
        prepare_summarize_messages,
        process_summarize,
        summarize,
    )

    assert all(callable(f) for f in [summarize, process_summarize, prepare_summarize_messages, parse_takeaways])
