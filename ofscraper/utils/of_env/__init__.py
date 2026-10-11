"""Application configuration defaults."""

from .defaults import load_defaults

_cached_settings = None


def get_all_configs(forced=False):
    """Return cached defaults, or evaluate them again when forced."""
    global _cached_settings
    if not forced and _cached_settings is not None:
        return _cached_settings
    _cached_settings = load_defaults()
    return _cached_settings
