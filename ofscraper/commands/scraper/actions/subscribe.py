"""
Subscribe action — subscribe to free OnlyFans accounts.

Filters selected models to those whose current subscription price is 0
and whose subscription has expired (or was never active), then sends
a subscribe request for each.
"""

import logging
import random
import time

import ofscraper.data.api.subscribe as subscribe_api
import ofscraper.managers.manager as manager
import ofscraper.utils.context.exit as exit
import ofscraper.utils.live.screens as progress_utils
import ofscraper.utils.live.updater as progress_updater

log = logging.getLogger("shared")


def get_free_expired_models(models):
    """Return models that are free (price == 0) and not currently active."""
    out = []
    for m in models:
        price = getattr(m, "final_current_price", None)
        active = getattr(m, "active", True)
        if price is not None and float(price) == 0 and not active:
            out.append(m)
    return out


@exit.exit_wrapper
def process_subscribe(models=None, **kwargs):
    """Subscribe to all free, expired models in *models*.

    Called from the scraper action loop with the full model list.
    """
    if not models:
        log.info("No models provided for subscribe action")
        return []

    free_models = get_free_expired_models(models)
    if not free_models:
        log.info(
            "[bold]No free expired subscriptions found to subscribe to[/bold]"
        )
        return []

    log.info(
        f"[bold]Found {len(free_models)} free expired subscription(s) to subscribe to[/bold]"
    )
    results = _subscribe_batch(free_models)
    return results


def _subscribe_batch(models):
    """Send subscribe requests for each model, with progress tracking."""
    results = []

    with progress_utils.setup_live("subscribe"):
        with manager.Manager.session.get_ofsession(
            sem_count=1,
            retries=3,
        ) as c:
            task = progress_updater.activity.add_overall_task(
                "Subscribing to free accounts...\n", total=len(models)
            )
            success_task = progress_updater.activity.add_overall_task(
                "Subscribed...\n", total=None
            )

            for model in models:
                username = model.name
                user_id = model.id
                log.info(f"Subscribing to {username} (ID: {user_id})...")

                resp = subscribe_api.subscribe_by_id(c, user_id)

                if resp is not None:
                    log.info(
                        f"[bold green]Successfully subscribed to {username}[/bold green]"
                    )
                    progress_updater.activity.update_overall_task(
                        success_task, advance=1
                    )
                    results.append({"username": username, "status": "success"})
                else:
                    log.warning(f"[bold red]Failed to subscribe to {username}[/bold red]")
                    results.append({"username": username, "status": "failed"})

                progress_updater.activity.update_overall_task(task, advance=1)

                # Small delay between requests to avoid rate limiting
                time.sleep(random.uniform(0.5, 1.5))

            progress_updater.activity.remove_overall_task(task)
            progress_updater.activity.remove_overall_task(success_task)

    succeeded = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    log.info(
        f"[bold]Subscribe complete: {succeeded} succeeded, {failed} failed[/bold]"
    )
    return results
