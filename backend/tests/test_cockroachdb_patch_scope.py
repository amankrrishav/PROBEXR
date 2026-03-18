"""
tests/test_cockroachdb_patch_scope.py — A-19: CockroachDB version monkeypatch scope

Verifies that the PGDialect._get_server_version_info override is no longer
applied globally to the class (which would affect all engines), but is instead
scoped to the specific engine via an event listener.
"""
import inspect


def test_no_global_pgdialect_class_mutation():
    """db.py must not mutate PGDialect._get_server_version_info at the class level."""
    import app.db as db_module
    src = inspect.getsource(db_module)
    assert 'PGDialect._get_server_version_info = ' not in src, (
        "db.py must not globally mutate PGDialect._get_server_version_info. "
        "Use an engine-scoped event listener instead."
    )


def test_uses_engine_event_listener():
    """db.py must use SQLAlchemy event listener to scope the version fix."""
    import app.db as db_module
    src = inspect.getsource(db_module)
    assert 'event.listens_for' in src or 'listens_for' in src, (
        "db.py must use SQLAlchemy event listener for the CockroachDB version fix"
    )


def test_fix_function_exists():
    """_register_cockroachdb_version_fix must be defined in db.py."""
    import app.db as db_module
    assert hasattr(db_module, '_register_cockroachdb_version_fix'), (
        "db.py must define _register_cockroachdb_version_fix function"
    )
    assert callable(db_module._register_cockroachdb_version_fix)


def test_global_pgdialect_not_mutated_after_import():
    """After importing db.py, PGDialect class must retain its original method."""
    from sqlalchemy.dialects.postgresql.base import PGDialect
    # The original method should be the real one, not our lambda
    # We check it's not a lambda (our mock) by inspecting the source
    method = PGDialect._get_server_version_info
    src = inspect.getsource(method) if hasattr(method, '__code__') else ''
    # The real method has substantial implementation; our mock is trivial
    # Key check: the global class method should not be our override
    assert 'return (13, 0, 0)' not in src, (
        "PGDialect._get_server_version_info must not be globally replaced "
        "with the CockroachDB mock"
    )