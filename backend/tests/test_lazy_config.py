"""
tests/test_lazy_config.py — A-20: Lazy config loading in auth.py

Verifies that auth.py has no module-level cfg = get_config() assignment.
Config must be loaded inside functions so test overrides take effect.
"""
import inspect


class TestLazyConfigLoading:
    def test_no_module_level_cfg_in_auth_service(self):
        """auth.py must not have a module-level `cfg = get_config()` assignment."""
        import app.services.auth as auth_module
        src = inspect.getsource(auth_module)
        lines = src.split('\n')
        bad_lines = [l for l in lines if l.strip().startswith('cfg = get_config()')]
        assert not bad_lines, (
            f"Found module-level cfg = get_config() in auth.py: {bad_lines}"
        )

    def test_algorithm_constant_still_present(self):
        """ALGORITHM module constant must still be defined (it's a static deployment param)."""
        from app.services.auth import ALGORITHM
        assert isinstance(ALGORITHM, str)
        assert ALGORITHM in ("HS256", "RS256", "ES256")

    def test_get_config_called_inside_functions(self):
        """Functions in auth.py must call get_config() directly, not via module-level cfg."""
        import app.services.auth as auth_module
        src = inspect.getsource(auth_module)
        assert 'get_config().' in src, (
            "auth.py functions must call get_config() directly"
        )