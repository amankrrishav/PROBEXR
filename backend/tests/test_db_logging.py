"""
tests/test_db_logging.py — A-04: print() replaced with logger.info() in db.py

Verifies that db.py uses the structured logging pipeline rather than
stdout print() calls which bypass JSON log formatting in production.
"""
import inspect


def test_no_print_calls_in_db_module():
    """db.py must not contain bare print() calls."""
    import app.db as db_module
    src = inspect.getsource(db_module)
    lines = src.split('\n')
    print_lines = [
        l.strip() for l in lines
        if l.strip().startswith('print(') and not l.strip().startswith('#')
    ]
    assert not print_lines, (
        f"db.py must use logger.info() not print(). Found: {print_lines}"
    )


def test_logger_used_in_db_module():
    """db.py must use the logger for engine initialisation messages."""
    import app.db as db_module
    src = inspect.getsource(db_module)
    assert 'logger' in src, "db.py must define and use a logger"
    assert 'logger.info' in src or 'logger.warning' in src, (
        "db.py must call logger.info() or logger.warning()"
    )