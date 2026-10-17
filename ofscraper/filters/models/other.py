"""
other filters
"""

import logging

from ofscraper.filters.models.utils.logs import trace_log_user
import ofscraper.utils.settings as settings


def otherFilters(filterusername):
    log = logging.getLogger("shared")
    log.debug(f"Excluded usernames: {settings.get_settings().excluded_username}")
    excluded = settings.get_settings().excluded_username or []
    if len(excluded) > 0:
        filterusername = list(
            filter(
                lambda x: x.name not in excluded,
                filterusername,
            )
        )
        log.debug(f"'excluded usernames' filter username count: {len(filterusername)}")
        trace_log_user(filterusername, "Excluded usernames")

    return filterusername
