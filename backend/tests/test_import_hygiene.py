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

# ---------------------------------------------------------------------------
# R-01: auth router has no unused imports (Depends, AsyncSession, get_session)
# ---------------------------------------------------------------------------

class TestAuthRouterNoUnusedImports:
    def test_no_unused_depends_import(self):
        """auth router must not import Depends — it uses DbSession/CurrentUser aliases."""
        import inspect, app.routers.auth as r
        src = inspect.getsource(r)
        import_lines = [l for l in src.split('\n') if l.startswith('from fastapi import')]
        assert not any('Depends' in l for l in import_lines), (
            "auth router imports Depends but never uses it directly — remove it"
        )

    def test_no_unused_async_session_import(self):
        """auth router must not import AsyncSession — uses DbSession alias from deps."""
        import inspect, app.routers.auth as r
        src = inspect.getsource(r)
        assert 'from sqlalchemy.ext.asyncio import AsyncSession' not in src, (
            "auth router imports AsyncSession but never uses it — remove it"
        )

    def test_no_unused_get_session_import(self):
        """auth router must not import get_session — uses DbSession alias from deps."""
        import inspect, app.routers.auth as r
        src = inspect.getsource(r)
        assert 'from app.db import get_session' not in src, (
            "auth router imports get_session but never uses it directly — remove it"
        )


# ---------------------------------------------------------------------------
# R-02/R-03: typing imports are at top of file, not mid-file
# ---------------------------------------------------------------------------

class TestImportsAtTopOfFile:
    def _first_import_line(self, src: str) -> int:
        for i, line in enumerate(src.split('\n')):
            if line.startswith('from typing') or line.startswith('import typing'):
                return i
        return -1

    def _router_definition_line(self, src: str) -> int:
        for i, line in enumerate(src.split('\n')):
            if line.startswith('router = APIRouter'):
                return i
        return -1

    def test_summarize_typing_import_before_router(self):
        """summarize.py must have 'from typing import' before router = APIRouter."""
        import inspect, app.routers.summarize as m
        src = inspect.getsource(m)
        typing_line = self._first_import_line(src)
        router_line = self._router_definition_line(src)
        assert typing_line != -1, "summarize.py must import from typing"
        assert typing_line < router_line, (
            f"'from typing import' (line {typing_line}) must come before "
            f"'router = APIRouter' (line {router_line}) in summarize.py"
        )

    def test_health_typing_import_before_router(self):
        """health.py must have 'from typing import' before router = APIRouter."""
        import inspect, app.routers.health as m
        src = inspect.getsource(m)
        typing_line = self._first_import_line(src)
        router_line = self._router_definition_line(src)
        assert typing_line != -1, "health.py must import from typing"
        assert typing_line < router_line, (
            f"'from typing import' (line {typing_line}) must come before "
            f"'router = APIRouter' (line {router_line}) in health.py"
        )