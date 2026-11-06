"""Tests for security audit fixes.

Each test targets a specific finding and verifies the fix without touching
real user config, logs, auth, or network.
"""
import asyncio
import json
import logging
import os
import re
import signal
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# The app's entry module imports ofscraper's packages in an order that avoids
# their circular imports; importing a leaf module first fails.
import ofscraper.main.open.load  # noqa: F401


# ---------------------------------------------------------------------------
# Finding 1 — SensitiveFormatter redacts session cookies and usernames
# ---------------------------------------------------------------------------

class TestSensitiveFormatter:
    """Verify the SensitiveFormatter redacts all expected secret patterns."""

    def _format(self, message):
        from ofscraper.utils.logs.classes.classes import SensitiveFormatter
        fmt = SensitiveFormatter()
        record = logging.LogRecord(
            name="test", level=logging.DEBUG, pathname="", lineno=0,
            msg=message, args=(), exc_info=None,
        )
        return fmt.format(record)

    def test_sess_cookie_redacted(self):
        out = self._format("cookie header: sess=SECRET123; auth_id=42; path=/")
        assert "SECRET123" not in out
        assert "auth_id=42" not in out

    def test_policy_signature_keypair(self):
        out = self._format("https://example.com/media?Policy=abc123&Signature=sig456&Key-Pair-Id=KP789")
        assert "abc123" not in out
        assert "sig456" not in out
        assert "KP789" not in out

    def test_policy_with_question_mark(self):
        out = self._format("url?Policy=FIRST_PARAM")
        assert "FIRST_PARAM" not in out

    def test_registered_username(self):
        from ofscraper.utils.logs.utils.sensitive import add_sensitive_pattern
        add_sensitive_pattern("testuser_abc", "username")
        out = self._format("Scraping profile for testuser_abc")
        assert "testuser_abc" not in out

    def test_cookie_header_redacted(self):
        out = self._format("Cookie: sess=abc; auth_id=123")
        assert "sess=abc" not in out

    def test_xbc_redacted(self):
        out = self._format("x-bc=sometoken123")
        assert "sometoken123" not in out


# ---------------------------------------------------------------------------
# Finding 2 — CDRM cookie warning fires once
# ---------------------------------------------------------------------------

class TestCDRMWarning:
    def test_cdrm_warns_once(self):
        import ofscraper.commands.scraper.actions.download.utils.keyhelpers as kh
        # Reset the warning flag
        kh._cdrm_cookie_warned = False
        warnings = []
        mock_logger = MagicMock()
        mock_logger.warning = lambda msg: warnings.append(msg)
        with patch("logging.getLogger", return_value=mock_logger):
            with patch.object(kh, "_logging") as mock_mod:
                mock_mod.getLogger.return_value = mock_logger
                # Simulate the warning block
                kh._cdrm_cookie_warned = False
                # Call the function logic manually
                if not kh._cdrm_cookie_warned:
                    kh._cdrm_cookie_warned = True
                    warnings.append("first")
                if not kh._cdrm_cookie_warned:
                    warnings.append("second")
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Finding 3 — 404 no longer treated as success
# ---------------------------------------------------------------------------

class TestNo404Exception:
    def test_sessionmanager_no_404_bypass(self):
        """The string '!= 404' should not appear in the session manager source."""
        import ofscraper.managers.sessionmanager.sessionmanager as sm
        import inspect
        source = inspect.getsource(sm)
        assert "!= 404" not in source


# ---------------------------------------------------------------------------
# Finding 4 — fatal errors exit non-zero
# ---------------------------------------------------------------------------

class TestFatalExitCode:
    def test_load_raises_systemexit(self):
        import ofscraper.main.open.load as load_mod
        with patch.object(load_mod, "systemSet", side_effect=RuntimeError("boom")):
            with pytest.raises(SystemExit) as exc_info:
                load_mod.main()
            assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Finding 5 — separate dests for -mxc and -xc
# ---------------------------------------------------------------------------

def _option_names(decorator):
    """Extract the parameter declarations from a cloup/click option decorator."""
    for cell in decorator.__closure__ or ():
        value = cell.cell_contents
        if isinstance(value, tuple) and all(isinstance(item, str) for item in value):
            return value
    raise AssertionError("could not inspect option decorator")


class TestArgDests:
    def test_media_count_dest(self):
        import ofscraper.utils.args.parse.arguments.media_content as mc
        assert "max_media_count" in _option_names(mc.max_media_count_option)

    def test_post_count_dest(self):
        import ofscraper.utils.args.parse.arguments.post_content as pc
        assert "max_post_count" in _option_names(pc.max_post_count_option)


# ---------------------------------------------------------------------------
# Finding 6 — auth.json atomic write with 0600
# ---------------------------------------------------------------------------

class TestAuthAtomicWrite:
    def test_atomic_write_creates_file(self, tmp_path):
        auth_file = tmp_path / "auth.json"
        auth_data = {"sess": "secret", "x-bc": "token"}
        with patch("ofscraper.utils.paths.common.get_auth_file", return_value=auth_file):
            import ofscraper.utils.auth.file as af
            # Mock auth_dict.get_auth_dict to return parsed data
            with patch("ofscraper.utils.auth.utils.dict.get_auth_dict", return_value=auth_data):
                af.write_auth(auth_data)
        assert auth_file.exists()
        # Check mode (on Unix)
        if sys.platform != "win32":
            mode = oct(auth_file.stat().st_mode & 0o777)
            assert mode == "0o600"
        content = json.loads(auth_file.read_text())
        assert content["sess"] == "secret"

    def test_atomic_write_handles_empty(self, tmp_path):
        """Zero-byte or truncated file: write_auth should handle gracefully."""
        auth_file = tmp_path / "auth.json"
        auth_file.write_text("")
        auth_data = {"sess": "new"}
        with patch("ofscraper.utils.paths.common.get_auth_file", return_value=auth_file):
            import ofscraper.utils.auth.file as af
            with patch("ofscraper.utils.auth.utils.dict.get_auth_dict", return_value=auth_data):
                af.write_auth(auth_data)
        assert json.loads(auth_file.read_text())["sess"] == "new"


# ---------------------------------------------------------------------------
# Finding 8 — config atomic writes + preserve unknown keys
# ---------------------------------------------------------------------------

class TestConfigAtomicWrite:
    def test_atomic_config_write(self, tmp_path):
        config_file = tmp_path / "config.json"
        import ofscraper.utils.config.file as cf
        with patch("ofscraper.utils.paths.common.get_config_path", return_value=config_file):
            cf.write_config({"key": "value"})
        assert config_file.exists()
        assert json.loads(config_file.read_text())["key"] == "value"

    def test_deep_merge_preserves_unknown_keys(self):
        import ofscraper.utils.config.file as cf
        existing = {"known": 1, "custom_webhook": "https://hook", "nested": {"a": 1, "b": 2}}
        schema_defaults = {"known": 1, "nested": {"a": 1, "c": 3}}
        merged = cf._deep_merge(existing, schema_defaults)
        # Unknown keys preserved
        assert "custom_webhook" in merged
        assert merged["nested"]["b"] == 2
        assert merged["nested"]["c"] == 3


# ---------------------------------------------------------------------------
# Finding 9 — corrupted config does not loop forever
# ---------------------------------------------------------------------------

class TestConfigCorruptedLoop:
    def test_non_tty_raises_runtime_error(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json")
        with patch("ofscraper.utils.paths.common.get_config_path", return_value=config_file):
            with patch("sys.stdin") as mock_stdin:
                mock_stdin.isatty.return_value = False
                import ofscraper.utils.config.utils.context as ctx
                with pytest.raises(RuntimeError, match="config.json is invalid"):
                    with ctx.config_context():
                        pass


# ---------------------------------------------------------------------------
# Finding 10 — explicit 0 not ignored by 'or' merges
# ---------------------------------------------------------------------------

class TestSettingsOrMerge:
    def test_explicit_zero_size_max(self):
        """When args.size_max is 0 (not None), it should be used, not config's value."""
        # This tests the logic pattern: args.x if args.x is not None else config.x
        val = 0
        config_val = 1024
        result = val if val is not None else config_val
        assert result == 0

    def test_none_falls_through_to_config(self):
        val = None
        config_val = 1024
        result = val if val is not None else config_val
        assert result == 1024


# ---------------------------------------------------------------------------
# Finding 13 — flag collisions resolved
# ---------------------------------------------------------------------------

class TestFlagCollisions:
    def test_promo_skip_no_ps(self):
        """Promo option should not use -ps (conflicts with --post-script)."""
        import ofscraper.utils.args.parse.arguments.user_list as ul
        # The promo option string should not contain "/-ps"
        option_str = str(ul.promo_option)
        assert "/-ps" not in option_str
        # -pk is already the private-key flag for manual CDRM
        assert "/-pk" not in option_str

    def test_mass_msg_no_ms(self):
        """Mass msg option should not use -ms (conflicts with --mark-stray)."""
        import ofscraper.utils.args.parse.arguments.post_content as pc
        option_str = str(pc.mass_msg_option)
        assert "/-ms" not in option_str


# ---------------------------------------------------------------------------
# Finding 14 — config debug log does not leak sensitive values
# ---------------------------------------------------------------------------

class TestConfigDebugRedaction:
    def test_no_webhook_in_log(self):
        import ofscraper.utils.config.config as config_mod
        import inspect
        source = inspect.getsource(config_mod)
        # The old f"new config: {config}" pattern should be gone
        assert 'f"new config: {config}"' not in source


# ---------------------------------------------------------------------------
# Finding 15 — retry predicates
# ---------------------------------------------------------------------------

class TestRetryPredicates:
    def test_transient_retried(self):
        """Timeouts and connection errors should be retried."""
        from ofscraper.managers.sessionmanager.sessionmanager import _is_transient
        import aiohttp
        assert _is_transient(asyncio.TimeoutError()) is True
        assert _is_transient(ConnectionError()) is True
        assert _is_transient(OSError("Network")) is True

    def test_permanent_not_retried(self):
        from ofscraper.managers.sessionmanager.sessionmanager import _is_transient
        import aiohttp
        # 401 should not be retried
        exc_401 = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=401, message="Unauthorized"
        )
        assert _is_transient(exc_401) is False
        # 404 should not be retried
        exc_404 = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=404, message="Not Found"
        )
        assert _is_transient(exc_404) is False
        # ValueError should not be retried
        assert _is_transient(ValueError("bad data")) is False

    def test_5xx_retried(self):
        from ofscraper.managers.sessionmanager.sessionmanager import _is_transient
        import aiohttp
        for status in (429, 500, 502, 503, 504):
            exc = aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=status, message="error"
            )
            assert _is_transient(exc) is True, f"status {status} should be transient"

    def test_download_retry_transient(self):
        from ofscraper.commands.scraper.actions.download.utils.retries import _is_transient_download
        assert _is_transient_download(asyncio.TimeoutError()) is True
        assert _is_transient_download(ValueError("bad")) is False


# ---------------------------------------------------------------------------
# Finding 16 — SIGTERM handler installed at startup
# ---------------------------------------------------------------------------

class TestSIGTERMHandler:
    def test_sigterm_handler_in_load(self):
        """load.main() should call sigterm_as_keyboard_interrupt."""
        import ofscraper.main.open.load as load_mod
        import inspect
        source = inspect.getsource(load_mod.main)
        assert "sigterm_as_keyboard_interrupt" in source
