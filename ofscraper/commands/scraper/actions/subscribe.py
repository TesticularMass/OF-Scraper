"""
Subscribe action — subscribe to OnlyFans accounts at no cost.

Filters selected models to those that are subscribable for free:
  - Base subscription price is 0, OR
  - A claimable promotion brings the price to 0

Only considers models whose subscription has expired (or was never active).

This action runs as a batch operation on all selected models at once,
before the per-model scraper pipeline — it does not need posts or media.
"""

import logging
import random
import time

import ofscraper.data.api.subscribe as subscribe_api
import ofscraper.managers.manager as manager
import ofscraper.utils.context.exit as exit

log = logging.getLogger("shared")


def _is_price_zero(value):
    """Safely check whether a price value is zero.

    The model's price fields can be ``None``, a number, or even an
    empty dict (the ``sub_price`` default).  This helper normalises
    all of those to a reliable boolean.
    """
    if value is None:
        return False
    try:
        return float(value) == 0
    except (TypeError, ValueError):
        return False


def _get_free_promo(model):
    """Return the first claimable promo with price == 0, or ``None``.

    Each promo dict typically has ``id``, ``price``, and ``canClaim``.
    """
    for promo in getattr(model, "all_claimable_promo", []) or []:
        try:
            if float(promo.get("price", -1)) == 0:
                return promo
        except (TypeError, ValueError):
            continue
    return None


def get_subscribable_models(models):
    """Return (model, promo_or_None) pairs for models that can be
    subscribed to at no cost.

    A model qualifies if its subscription is not active AND either:
      1. ``final_current_price`` is 0  (base price is free), or
      2. It has a claimable promotion at price 0.
    """
    out = []
    for m in models:
        name = getattr(m, "name", "?")
        active = getattr(m, "active", True)
        if active:
            log.debug(f"[subscribe] {name}: skipped (active subscription)")
            continue

        # Check base / current price
        price = getattr(m, "final_current_price", None)
        promo_claim = getattr(m, "lowest_promo_claim", None)
        regular = getattr(m, "regular_price", None)
        sub_price = getattr(m, "sub_price", None)

        log.debug(
            f"[subscribe] {name}: active={active}, "
            f"sub_price={sub_price!r}, final_current_price={price!r}, "
            f"lowest_promo_claim={promo_claim!r}, regular_price={regular!r}"
        )

        if _is_price_zero(price):
            log.debug(f"[subscribe] {name}: qualifies (final_current_price=0)")
            out.append((m, None))
            continue

        # Check for a claimable $0 promo
        free_promo = _get_free_promo(m)
        if free_promo is not None:
            log.debug(
                f"[subscribe] {name}: qualifies ($0 claimable promo: {free_promo})"
            )
            out.append((m, free_promo))
        else:
            log.debug(f"[subscribe] {name}: skipped (not free)")

    return out


@exit.exit_wrapper
def process_subscribe_batch(models=None, **kwargs):
    """Subscribe to all free / $0-promo expired models in *models*.

    Called as a batch operation with the full selected model list,
    before the per-model scraper pipeline starts.
    """
    if not models:
        log.info("No models provided for subscribe action")
        return []

    log.info(f"[bold]Checking {len(models)} model(s) for free subscriptions...[/bold]")
    candidates = get_subscribable_models(models)
    if not candidates:
        log.info(
            "[bold]No free or $0-promo expired subscriptions found to subscribe to[/bold]"
        )
        return []

    log.info(
        f"[bold]Found {len(candidates)} subscribable account(s) at no cost[/bold]"
    )
    results = _subscribe_batch(candidates)
    return results


def _subscribe_batch(candidates):
    """Send subscribe requests for each (model, promo) pair, with progress tracking."""
    results = []

    with manager.Manager.session.get_ofsession(
        sem_count=1,
        retries=3,
    ) as c:
        for model, promo in candidates:
            username = model.name
            user_id = model.id
            promo_id = promo.get("id") if promo else None

            if promo:
                log.info(
                    f"Subscribing to {username} (ID: {user_id}) "
                    f"using $0 promo (promo ID: {promo_id})..."
                )
            else:
                log.info(f"Subscribing to {username} (ID: {user_id})...")

            resp = subscribe_api.subscribe_by_id(c, user_id, promo_id=promo_id)

            if resp is not None:
                log.info(
                    f"[bold green]Successfully subscribed to {username}[/bold green]"
                )
                results.append({"username": username, "status": "success"})
            else:
                log.warning(f"[bold red]Failed to subscribe to {username}[/bold red]")
                results.append({"username": username, "status": "failed"})

            # Small delay between requests to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))

    succeeded = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    log.info(
        f"[bold]Subscribe complete: {succeeded} succeeded, {failed} failed[/bold]"
    )
    return results
