"""Archived API posts."""

import logging

import arrow

import ofscraper.data.api.common.archived_streams as shared
import ofscraper.utils.of_env.of_env as of_env
import ofscraper.utils.settings as settings
from ofscraper.data.api.common.after import get_after_pre_checks
from ofscraper.data.api.common.check import update_check
from ofscraper.data.api.common.timeline import process_posts_as_individual
from ofscraper.db.operations_.media import (
    get_media_ids_downloaded_model,
    get_archived_media,
)
from ofscraper.db.operations_.posts import (
    get_archived_post_info,
    get_youngest_archived_date,
    get_deleted_post_ids,
    mark_post_as_deleted,
)
from ofscraper.utils.context.run_async import run


API = "Archived"
AREA = shared.ScanArea(
    name=API,
    old_trace_name="oldarchived",
    first_endpoint="archivedEP",
    next_endpoint="archivedNextEP",
    ghost_name="archived posts",
    final_trace=False,
)
log = logging.getLogger("shared")


@run
async def get_archived_posts(model_id, username, c=None, post_id=None):
    after = await get_after(model_id, username)
    time_log(username, after)
    post_id = post_id or []
    if len(post_id) == 0 or len(post_id) > of_env.getattr(
        "MAX_ARCHIVED_INDIVIDUAL_SEARCH"
    ):
        splitArrays = await get_split_array(model_id, username, after)
        generators = get_tasks(splitArrays, c, model_id, username, after)
        data = await process_tasks_batch(generators)
    elif len(post_id) <= of_env.getattr("MAX_ARCHIVED_INDIVIDUAL_SEARCH"):
        data = process_posts_as_individual()
    update_check(data, model_id, after, API)
    return data


async def get_oldarchived(model_id, username):
    return await shared.get_old_posts(AREA, model_id, username, get_archived_post_info)


async def process_tasks_batch(generators):
    return await shared.process_tasks_batch(AREA, generators)


async def get_split_array(model_id, username, after):
    return await shared.get_split_array(model_id, username, after, get_oldarchived)


def get_tasks(splitArrays, c, model_id, username, after):
    return shared.get_tasks(
        splitArrays, c, model_id, username, after, scrape_archived_posts
    )


async def scrape_archived_posts(
    c,
    model_id,
    username,
    timestamp=None,
    required_posts=None,
    is_last_chunk=False,
    offset=False,
):
    async for batch in shared.scrape_posts(
        AREA,
        c,
        model_id,
        username,
        mark_post_as_deleted,
        timestamp=timestamp,
        required_posts=required_posts,
        is_last_chunk=is_last_chunk,
        offset=offset,
    ):
        yield batch


async def get_after(model_id, username):
    return await shared.get_after(
        AREA,
        model_id,
        username,
        get_after_pre_checks,
        get_archived_media,
        get_media_ids_downloaded_model,
        get_deleted_post_ids,
        get_youngest_archived_date,
    )


def time_log(username, after):
    log.info(
        f"Setting {API.lower()} scan range for {username} from {arrow.get(after).format(of_env.getattr('API_DATE_FORMAT'))} to {arrow.get(settings.get_settings().before or arrow.now()).format((of_env.getattr('API_DATE_FORMAT')))}"
    )
