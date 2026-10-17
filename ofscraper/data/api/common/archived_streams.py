"""Shared pagination for archived posts and streams."""

import asyncio
import logging
import traceback
from dataclasses import dataclass

import arrow

import ofscraper.data.api.common.logs.strings as common_logs
import ofscraper.utils.const as const
import ofscraper.utils.live.updater as progress_utils
import ofscraper.utils.of_env.of_env as of_env
import ofscraper.utils.settings as settings
from ofscraper.data.api.common.logs.logs import trace_log_raw, trace_progress_log


log = logging.getLogger("shared")


@dataclass(frozen=True)
class ScanArea:
    name: str
    old_trace_name: str
    first_endpoint: str
    next_endpoint: str
    ghost_name: str
    final_trace: bool = False


async def get_old_posts(area, model_id, username, get_post_info):
    if not settings.get_settings().api_cache_disabled:
        old_posts = await get_post_info(model_id=model_id, username=username)
    else:
        old_posts = []
    old_posts = list(filter(lambda post: post is not None, old_posts))
    seen = set()
    old_posts = [
        post
        for post in old_posts
        if post["post_id"] not in seen and not seen.add(post["post_id"])
    ]
    log.debug(f"[bold]{area.name} Cache[/bold] {len(old_posts)} found")
    trace_log_raw(area.old_trace_name, old_posts)
    return old_posts


async def process_tasks_batch(area, generators):
    response_array = []
    page_count = 0
    seen = set()
    queue = asyncio.Queue()

    page_task = progress_utils.api.add_overall_task(
        f"{area.name} Content Pages Progress: {page_count}", visible=True
    )

    async def producer(gen):
        try:
            async for batch in gen:
                await queue.put(batch)
        except Exception as error:
            log.traceback_(error)
            log.traceback_(traceback.format_exc())
        finally:
            await queue.put(None)

    workers = [asyncio.create_task(producer(gen)) for gen in generators]
    active_workers = len(workers)

    while active_workers > 0:
        batch = await queue.get()
        if batch is None:
            active_workers -= 1
            continue

        page_count += 1
        progress_utils.api.update_overall_task(
            page_task,
            description=f"{area.name} Content Pages Progress: {page_count}",
        )

        if batch:
            new_posts = [
                post
                for post in batch
                if post.get("id") not in seen and not seen.add(post.get("id"))
            ]
            response_array.extend(new_posts)
            trace_progress_log(f"{area.name} task", new_posts)

    progress_utils.api.remove_overall_task(page_task)
    if area.final_trace:
        log.debug(
            f"{common_logs.FINAL_IDS.format(area.name)} {list(map(lambda post: post.get('id'), response_array))}"
        )
        trace_log_raw(f"{area.name} final", response_array, final_count=True)
        log.debug(common_logs.FINAL_COUNT_POST.format(area.name, len(response_array)))
    return response_array


async def get_split_array(model_id, username, after, get_old):
    old_posts = await get_old(model_id, username)
    if len(old_posts) == 0:
        return []
    min_posts = max(
        len(old_posts) // of_env.getattr("REASONABLE_MAX_PAGE"),
        of_env.getattr("MIN_PAGE_POST_COUNT"),
    )
    posts = sorted(old_posts, key=lambda post: post.get("created_at"))
    filtered = list(
        filter(
            lambda post: (
                arrow.get(post.get("created_at") or 0).float_timestamp >= after
            ),
            posts,
        )
    )
    return [filtered[i : i + min_posts] for i in range(0, len(filtered), min_posts)]


def get_tasks(split_arrays, client, model_id, username, after, scrape):
    tasks = []
    if len(split_arrays) == 0:
        tasks.append(
            scrape(
                client,
                model_id,
                username,
                timestamp=after,
                is_last_chunk=True,
                offset=True,
            )
        )
        return tasks

    first_known_post = split_arrays[0][0]
    first_known_timestamp = float(first_known_post.get("created_at"))

    if float(after) < first_known_timestamp:
        log.debug(
            f"Spawning Bridge Worker to cover gap from {after} to {first_known_timestamp}"
        )
        tasks.append(
            scrape(
                client,
                model_id,
                username,
                timestamp=after,
                required_posts=[
                    {
                        "post_id": first_known_post.get("post_id"),
                        "timestamp": first_known_timestamp,
                    }
                ],
                offset=True,
            )
        )

    for index, chunk in enumerate(split_arrays):
        is_first_chunk = index == 0
        is_final_chunk = index == len(split_arrays) - 1
        start_timestamp = (
            chunk[0].get("created_at")
            if is_first_chunk
            else split_arrays[index - 1][-1].get("created_at")
        )

        tasks.append(
            scrape(
                client,
                model_id,
                username,
                timestamp=start_timestamp,
                required_posts=[
                    {
                        "post_id": post.get("post_id"),
                        "timestamp": post.get("created_at"),
                    }
                    for post in chunk
                ],
                is_last_chunk=is_final_chunk,
                offset=is_first_chunk or is_final_chunk,
            )
        )

    return tasks


async def scrape_posts(
    area,
    client,
    model_id,
    username,
    mark_deleted,
    timestamp=None,
    required_posts=None,
    is_last_chunk=False,
    offset=False,
):
    required_posts = required_posts or []
    expected_missing = [post for post in required_posts]
    required_ids = {post["post_id"] for post in required_posts}

    before = arrow.get(settings.get_settings().before or arrow.now()).float_timestamp
    start_anchor = float(timestamp) if timestamp else 0
    all_ghosts_found = []

    current_timestamp = float(timestamp) - 0.001 if timestamp and offset else timestamp
    has_more = True

    try:
        while has_more:
            url = (
                of_env.getattr(area.next_endpoint).format(
                    model_id, str(current_timestamp)
                )
                if current_timestamp
                else of_env.getattr(area.first_endpoint).format(model_id)
            )

            async with client.requests_async(url=url) as response:
                if not (200 <= response.status < 300):
                    log.debug(f"{area.name} API Error: {response.status} for {url}")
                    break

                data = await response.json_()
                batch = data.get("list", [])
                has_more = data.get("hasMore", False)
                if not batch:
                    break

                batch_timestamps = [
                    float(post.get("postedAtPrecise", 0)) for post in batch
                ]
                max_ts = max(batch_timestamps)
                batch_ids = {post["id"] for post in batch}

                expected_missing = [
                    post
                    for post in expected_missing
                    if post["post_id"] not in batch_ids
                ]
                for post in batch:
                    required_ids.discard(post["id"])

                ghosts_in_batch = []
                for expected in expected_missing:
                    if max_ts >= expected["timestamp"] >= start_anchor:
                        ghosts_in_batch.append(expected["post_id"])

                if ghosts_in_batch:
                    all_ghosts_found.extend(ghosts_in_batch)
                    expected_missing = [
                        post
                        for post in expected_missing
                        if post["post_id"] not in ghosts_in_batch
                    ]
                    for ghost_id in ghosts_in_batch:
                        required_ids.discard(ghost_id)

                should_stop = False
                if not is_last_chunk and len(required_ids) == 0:
                    should_stop = True

                if max_ts > before:
                    should_stop = True

                current_timestamp = max_ts
                yield batch

                if should_stop:
                    break

    except Exception as error:
        log.traceback_(error)
        log.traceback_(traceback.format_exc())
    finally:
        if all_ghosts_found:
            log.info(
                f"Worker finished. Flagging {len(all_ghosts_found)} ghost {area.ghost_name}."
            )
            await mark_deleted(
                post_ids=all_ghosts_found, model_id=model_id, username=username
            )


async def get_after(
    area,
    model_id,
    username,
    pre_checks,
    get_media,
    get_downloaded_ids,
    get_deleted_ids,
    get_youngest_date,
):
    prechecks = pre_checks(model_id, area.name)
    if prechecks is not None:
        return max(
            arrow.get(prechecks).float_timestamp, arrow.get("2000").float_timestamp
        )

    current = await get_media(model_id=model_id, username=username)
    if len(current) == 0:
        return arrow.get("2000").float_timestamp

    downloaded_ids = await get_downloaded_ids(model_id=model_id, username=username)
    deleted_posts = await get_deleted_ids(model_id=model_id, username=username)

    active_media = settings.get_settings().mediatypes or ["Videos", "Audios", "Images"]
    active_media_mapped = {
        const.MEDIA_ALIASES.get(media.lower(), media.lower()) for media in active_media
    }

    filtered = [
        item
        for item in current
        if item.get("downloaded") != 1
        and item.get("media_id") not in downloaded_ids
        and item.get("post_id") not in deleted_posts
        and item.get("unlocked") != 0
        and const.MEDIA_ALIASES.get(
            str(item.get("media_type", "")).lower(),
            str(item.get("media_type", "")).lower(),
        )
        in active_media_mapped
    ]

    if len(filtered) == 0:
        youngest = await get_youngest_date(model_id=model_id, username=username)
        return arrow.get(youngest or "2000").float_timestamp

    unique_missing = {}
    for item in filtered:
        media_id = item.get("media_id")
        if media_id not in unique_missing or arrow.get(
            item.get("posted_at") or 0
        ) > arrow.get(unique_missing[media_id].get("posted_at") or 0):
            unique_missing[media_id] = item

    missing_items = sorted(
        list(unique_missing.values()),
        key=lambda item: arrow.get(item.get("posted_at") or 0),
    )
    return arrow.get(missing_items[0]["posted_at"] or "2000").float_timestamp
