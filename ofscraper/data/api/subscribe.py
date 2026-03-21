"""
Subscribe API — subscribe to OnlyFans accounts at no cost.

Sends a POST to the OF subscribe endpoint for a given model.
Handles both genuinely free accounts (base price = 0) and accounts
with a claimable promotion that brings the price to 0.
"""

import logging
import traceback

import ofscraper.managers.manager as manager
import ofscraper.utils.of_env.of_env as of_env

log = logging.getLogger("shared")


def subscribe_by_id(c, user_id, promo_id=None):
    """Send a subscribe request for *user_id*.

    Parameters
    ----------
    c : session context
        An active OF session obtained via ``get_ofsession`` / ``aget_ofsession``.
    user_id : int | str
        The numeric OnlyFans user/model ID.
    promo_id : int | str | None
        Optional promotion ID to claim a specific promo offer.

    Returns
    -------
    dict | None
        The JSON response from the API on success, or ``None`` on failure.
    """
    url = of_env.getattr("subscribeEP").format(user_id)
    body = {}
    if promo_id is not None:
        body["promoId"] = promo_id
    try:
        with c.requests(
            url,
            method="post",
            json=body if body else None,
            retries=of_env.getattr("SUBSCRIBE_NUM_TRIES"),
        ) as r:
            if r.ok:
                return r.json_()
            else:
                log.warning(
                    f"Subscribe request for user {user_id} returned status {r.status}"
                )
                return None
    except Exception as e:
        log.warning(f"Subscribe request failed for user {user_id}: {e}")
        log.debug(traceback.format_exc())
        return None


async def async_subscribe_by_id(c, user_id, promo_id=None):
    """Async version of :func:`subscribe_by_id`."""
    url = of_env.getattr("subscribeEP").format(user_id)
    body = {}
    if promo_id is not None:
        body["promoId"] = promo_id
    try:
        async with c.requests_async(
            url,
            method="post",
            json=body if body else None,
            retries=of_env.getattr("SUBSCRIBE_NUM_TRIES"),
        ) as r:
            if r.ok:
                return await r.json_()
            else:
                log.warning(
                    f"Subscribe request for user {user_id} returned status {r.status}"
                )
                return None
    except Exception as e:
        log.warning(f"Subscribe request failed for user {user_id}: {e}")
        log.debug(traceback.format_exc())
        return None
