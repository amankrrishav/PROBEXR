"""
tests/test_import_hygiene.py — A-28: Duplicate timedelta import in auth router

Verifies that auth.py router has a single merged datetime import line
instead of two separate `from datetime import ...` statements.
"""
import inspect


class TestAuthRouterImportHygiene:
    def test_no_duplicate_timedelta_import(self):
        """auth.py router must import timedelta only once."""
        import app.routers.auth as auth_router
        src = inspect.getsource(auth_router)
        import_lines = [l for l in src.split('\n') if l.startswith('from datetime')]
        timedelta_imports = [l for l in import_lines if 'timedelta' in l]
        assert len(timedelta_imports) == 1, (
            f"timedelta should appear in exactly one import line, "
            f"found {len(timedelta_imports)}: {timedelta_imports}"
        )

    def test_all_datetime_symbols_in_one_import(self):
        """datetime, timedelta, and timezone must all be in one import statement."""
        import app.routers.auth as auth_router
        src = inspect.getsource(auth_router)
        import_lines = [l.strip() for l in src.split('\n') if l.startswith('from datetime')]
        assert len(import_lines) == 1, (
            f"Expected single datetime import line, got: {import_lines}"
        )
        single_import = import_lines[0]
        assert 'datetime' in single_import
        assert 'timedelta' in single_import
        assert 'timezone' in single_import