r"""
 _______  _______         _______  _______  _______  _______  _______  _______  _______
(  ___  )(  ____ \       (  ____ \(  ____ \(  ____ )(  ___  )(  ____ )(  ____ \(  ____ )
| (   ) || (    \/       | (    \/| (    \/| (    )|| (   ) || (    )|| (    \/| (    )|
| |   | || (__     _____ | (_____ | |      | (____)|| (___) || (____)|| (__    | (____)|
| |   | ||  __)   (_____)(_____  )| |      |     __)|  ___  ||  _____)|  __)   |     __)
| |   | || (                   ) || |      | (\ (   | (   ) || (      | (      | (\ (
| (___) || )             /\____) || (____/\| ) \ \__| )   ( || )      | (____/\| ) \ \__
(_______)|/              \_______)(_______/|/   \__/|/     \||/       (_______/|/   \__/
"""

import asyncio
import logging
import traceback

from rich.console import Console

import ofscraper.data.api.subscriptions.common as common
import ofscraper.managers.manager as manager
import ofscraper.utils.of_env.of_env as of_env
import ofscraper.utils.live.screens as progress_utils
from ofscraper.utils.context.run_async import run
from ofscraper.utils.live.updater import userlist

log = logging.getLogger("shared")
console = Console()


@run
async def get_subscriptions(subscribe_count, account="active"):
    task1 = userlist.add_overall_task(
        f"Getting your {account} subscriptions (this may take awhile)..."
    )
    async with manager.Manager.session.aget_subscription_session(
        sem_count=of_env.getattr("SUBSCRIPTION_SEMS"),
    ) as c:
        if account == "active":
            out = await activeHelper(subscribe_count, c)
        else:
            out = await expiredHelper(subscribe_count, c)
    userlist.remove_overall_task(task1)
    log.debug(f"Total {account} subscriptions found {len(out)}")
    return out


@run
async def get_all_subscriptions(subscribe_count, account="active"):
    if account == "active":
        return await get_all_activive_subscriptions(subscribe_count)
    else:
        return await get_all_expired_subscriptions(subscribe_count)


async def get_all_activive_subscriptions(subscribe_count):
    async with manager.Manager.session.aget_subscription_session(
        sem_count=of_env.getattr("SUBSCRIPTION_SEMS"),
    ) as c:
        # Pass the generator function as a list to the orchestrator
        return await process_task([scrape_subscriptions_active(c)])


async def get_all_expired_subscriptions(subscribe_count):
    async with manager.Manager.session.aget_subscription_session(
        sem_count=of_env.getattr("SUBSCRIPTION_SEMS"),
    ) as c:
        return await process_task([scrape_subscriptions_disabled(c)])


async def _needs_multi_pass(subscribe_count):
    """Check if the expected subscription count exceeds the API's ~5000 offset cap."""
    return subscribe_count > 4500


async def _set_server_sort(c, order="users.name", direction="asc", sort_type="all"):
    """Use the sort endpoint to change the server-side ordering of the following list."""
    url = of_env.getattr("sortSubscriptions")
    try:
        async with c.requests_async(
            url=url,
            method="post",
            json={"order": order, "direction": direction, "type": sort_type},
        ) as r:
            log.debug(f"Server sort set to order={order} direction={direction} type={sort_type} (status={r.status})")
    except Exception as E:
        log.debug(f"Failed to set server sort: {E}")


async def activeHelper(subscribe_count, c):
    # Blacklist/Reserved list logic check
    if any(
        x in common.get_black_list_helper()
        for x in [
            of_env.getattr("OFSCRAPER_RESERVED_LIST"),
            of_env.getattr("OFSCRAPER_RESERVED_LIST_ALT"),
        ]
    ) or any(
        x in common.get_black_list_helper()
        for x in [
            of_env.getattr("OFSCRAPER_ACTIVE_LIST"),
            of_env.getattr("OFSCRAPER_ACTIVE_LIST_ALT"),
        ]
    ):
        return []
    if all(
        x not in common.get_user_list_helper()
        for x in [
            of_env.getattr("OFSCRAPER_RESERVED_LIST"),
            of_env.getattr("OFSCRAPER_RESERVED_LIST_ALT"),
        ]
    ) and all(
        x not in common.get_user_list_helper()
        for x in [
            of_env.getattr("OFSCRAPER_ACTIVE_LIST"),
            of_env.getattr("OFSCRAPER_ACTIVE_LIST_ALT"),
        ]
    ):
        return []

    if await _needs_multi_pass(subscribe_count):
        log.info(
            f"Active count ({subscribe_count}) exceeds API offset cap. "
            f"Using multi-pass sort strategy to fetch all subscriptions."
        )
        # Pass 1: ascending name sort (default)
        await _set_server_sort(c, direction="asc", sort_type="active")
        pass1 = await process_task([scrape_subscriptions_active(c)])
        # Pass 2: descending name sort (gets the tail the first pass missed)
        await _set_server_sort(c, direction="desc", sort_type="active")
        pass2 = await process_task([scrape_subscriptions_active(c)])
        # Restore default sort
        await _set_server_sort(c, direction="asc", sort_type="active")
        # Merge and deduplicate
        seen = {u["id"] for u in pass1}
        merged = list(pass1)
        new_from_pass2 = [u for u in pass2 if u["id"] not in seen]
        merged.extend(new_from_pass2)
        log.info(
            f"Active multi-pass results: pass1={len(pass1)}, pass2={len(pass2)}, "
            f"new from pass2={len(new_from_pass2)}, total unique={len(merged)}"
        )
        if len(merged) < int(subscribe_count * 0.95):
            log.warning(
                f"Active multi-pass result appears INCOMPLETE: merged={len(merged)} "
                f"vs site count {subscribe_count}. A pagination pass likely failed mid-run; "
                f"some accounts may be missing from this fetch."
            )
        return merged

    return await process_task([scrape_subscriptions_active(c)])


async def expiredHelper(subscribe_count, c):
    if any(
        x in common.get_black_list_helper()
        for x in [
            of_env.getattr("OFSCRAPER_RESERVED_LIST"),
            of_env.getattr("OFSCRAPER_RESERVED_LIST_ALT"),
        ]
    ) or any(
        x in common.get_black_list_helper()
        for x in [
            of_env.getattr("OFSCRAPER_EXPIRED_LIST"),
            of_env.getattr("OFSCRAPER_EXPIRED_LIST_ALT"),
        ]
    ):
        return []
    if all(
        x not in common.get_user_list_helper()
        for x in [
            of_env.getattr("OFSCRAPER_RESERVED_LIST"),
            of_env.getattr("OFSCRAPER_RESERVED_LIST_ALT"),
        ]
    ) and all(
        x not in common.get_user_list_helper()
        for x in [
            of_env.getattr("OFSCRAPER_EXPIRED_LIST"),
            of_env.getattr("OFSCRAPER_EXPIRED_LIST_ALT"),
        ]
    ):
        return []

    if await _needs_multi_pass(subscribe_count):
        log.info(
            f"Expired count ({subscribe_count}) exceeds API offset cap. "
            f"Using multi-pass sort strategy to fetch all subscriptions."
        )
        # Pass 1: ascending name sort
        await _set_server_sort(c, direction="asc", sort_type="expired")
        pass1 = await process_task([scrape_subscriptions_disabled(c)])
        # Pass 2: descending name sort
        await _set_server_sort(c, direction="desc", sort_type="expired")
        pass2 = await process_task([scrape_subscriptions_disabled(c)])
        # Restore default sort
        await _set_server_sort(c, direction="asc", sort_type="expired")
        # Merge and deduplicate
        seen = {u["id"] for u in pass1}
        merged = list(pass1)
        new_from_pass2 = [u for u in pass2 if u["id"] not in seen]
        merged.extend(new_from_pass2)
        log.info(
            f"Expired multi-pass results: pass1={len(pass1)}, pass2={len(pass2)}, "
            f"new from pass2={len(new_from_pass2)}, total unique={len(merged)}"
        )
        if len(merged) < int(subscribe_count * 0.95):
            log.warning(
                f"Expired multi-pass result appears INCOMPLETE: merged={len(merged)} "
                f"vs site count {subscribe_count}. A pagination pass likely failed mid-run; "
                f"some accounts may be missing from this fetch."
            )
        return merged

    return await process_task([scrape_subscriptions_disabled(c)])


async def process_task(generators):
    """
    Fixed Orchestrator: Consumes async generators and returns a final LIST.
    This satisfies the 'await' in retriver.py.
    """
    output = []
    seen = set()

    # Iterate through the provided generator workers
    for gen in generators:
        try:
            # Consuming the AsyncGenerator using 'async for'
            async for batch in gen:
                if batch:
                    users = [
                        user
                        for user in batch
                        if user["id"] not in seen and not seen.add(user["id"])
                    ]
                    output.extend(users)
        except Exception as E:
            log.debug("Failed in subscription processing loop")
            log.traceback_(E)
            log.traceback_(traceback.format_exc())
            continue
    return output


async def _scrape_subscriptions_page(c, url, label, max_retries=3):
    """Fetch a single page of subscriptions with retry logic."""
    for attempt in range(1, max_retries + 1):
        try:
            async with c.requests_async(url=url) as r:
                if r.status == 429:
                    wait = min(2 ** attempt, 10)
                    log.debug(f"{label}: rate-limited (429), retry {attempt}/{max_retries} after {wait}s")
                    await asyncio.sleep(wait)
                    continue
                if not (200 <= r.status < 300):
                    log.debug(f"{label}: API error {r.status}, retry {attempt}/{max_retries}")
                    await asyncio.sleep(1)
                    continue
                return await r.json_()
        except asyncio.TimeoutError:
            log.debug(f"{label}: timeout, retry {attempt}/{max_retries}")
            await asyncio.sleep(1)
        except Exception as E:
            log.debug(f"{label}: error on attempt {attempt}/{max_retries}")
            log.traceback_(E)
            log.traceback_(traceback.format_exc())
            await asyncio.sleep(1)
    log.warning(f"{label}: all {max_retries} retries exhausted")
    return None


async def scrape_subscriptions_active(c, offset=0):
    """
    Async Generator Worker Loop for active subscriptions.
    Yields batches page-by-page.

    IMPORTANT: The offset must advance by the page limit (100), NOT by
    len(subscriptions).  The OF API uses absolute positioning — deleted/
    deactivated accounts are skipped server-side but still occupy offset
    slots.  Advancing by the (smaller) returned count causes overlapping
    ranges and massive duplicates on large accounts.
    """
    page_limit = of_env.getattr("SUBSCRIPTION_PAGE_LIMIT")
    current_offset = offset
    total_fetched = 0
    while True:
        url = of_env.getattr("subscriptionsActiveEP").format(current_offset)
        log.debug(f"usernames active offset {current_offset}")

        response = await _scrape_subscriptions_page(c, url, f"active offset {current_offset}")
        if response is None:
            log.warning(f"Active subscriptions: pagination stopped at offset {current_offset} (retries exhausted), fetched {total_fetched} so far")
            break

        subscriptions = response.get("list", [])
        if subscriptions:
            total_fetched += len(subscriptions)
            log.debug(
                f"active subscriptions offset {current_offset}: got {len(subscriptions)} users (total: {total_fetched})"
            )
            yield subscriptions

        if response.get("hasMore") is not True or not subscriptions:
            log.debug(f"Active subscriptions: pagination complete at offset {current_offset} (hasMore={response.get('hasMore')}, batch_size={len(subscriptions)}, total={total_fetched})")
            break

        current_offset += page_limit


async def scrape_subscriptions_disabled(c, offset=0):
    """
    Async Generator Worker Loop for expired subscriptions.
    Yields batches page-by-page.
    """
    page_limit = of_env.getattr("SUBSCRIPTION_PAGE_LIMIT")
    current_offset = offset
    total_fetched = 0
    while True:
        url = of_env.getattr("subscriptionsExpiredEP").format(current_offset)
        log.debug(f"usernames offset expired {current_offset}")

        response = await _scrape_subscriptions_page(c, url, f"expired offset {current_offset}")
        if response is None:
            log.warning(f"Expired subscriptions: pagination stopped at offset {current_offset} (retries exhausted), fetched {total_fetched} so far")
            break

        subscriptions = response.get("list", [])
        if subscriptions:
            total_fetched += len(subscriptions)
            log.debug(
                f"expired subscriptions offset {current_offset}: got {len(subscriptions)} users (total: {total_fetched})"
            )
            yield subscriptions

        if response.get("hasMore") is not True or not subscriptions:
            log.debug(f"Expired subscriptions: pagination complete at offset {current_offset} (hasMore={response.get('hasMore')}, batch_size={len(subscriptions)}, total={total_fetched})")
            break

        current_offset += page_limit