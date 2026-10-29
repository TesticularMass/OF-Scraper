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

import traceback
import asyncio
import pathlib
from functools import partial

import ofscraper.classes.placeholder as placeholder
import ofscraper.utils.cache.cache as cache
import ofscraper.utils.hash as hash
import ofscraper.utils.settings as settings
from ofscraper.db.operations_.media import (
    mark_media_as_downloaded,
    prev_download_media_data,
)
from ofscraper.commands.scraper.actions.utils.retries import get_download_retries
from ofscraper.commands.scraper.actions.utils.params import get_alt_params
from ofscraper.managers.sessionmanager.sessionmanager import FORCED_NEW, SIGN
import ofscraper.utils.of_env.of_env as of_env
import ofscraper.commands.scraper.actions.utils.globals as common_globals
from ofscraper.commands.scraper.actions.utils.log import get_medialog


class MetaDataManager:

    async def metadata(self, c, ele, model_id, username):
        try:
            return await self._change_metadata(c, ele, username, model_id)
        except Exception as E:
            common_globals.log.debug(f"{get_medialog(ele)} exception {E}")
            common_globals.log.debug(
                f"{get_medialog(ele)} exception {traceback.format_exc()}"
            )
            common_globals.log.traceback_(f"{get_medialog(ele)} Metadata Failed\n")
            return "skipped"

    async def _change_metadata(self, c, ele, username, model_id, placeholderObj=None):
        common_globals.log.info(
            f"{get_medialog(ele)} skipping adding download to disk because metadata is on"
        )
        placeholderObj = placeholderObj or await self._placeholderObjHelper(c, ele)
        await placeholderObj.init(create=False)
        ele.add_filepath(placeholderObj.trunicated_filepath)
        effected = None
        if ele.id:
            prevData = (
                await prev_download_media_data(
                    ele, model_id=model_id, username=username
                )
                or {}
            )
            await mark_media_as_downloaded(
                ele,
                filename=self._metadata_file_helper(placeholderObj, prevData),
                directory=self._metadata_dir_helper(placeholderObj, prevData),
                model_id=model_id,
                username=username,
                downloaded=self._metadata_downloaded_helper(placeholderObj, prevData),
                hashdata=self._metadata_hash_helper(placeholderObj, prevData, ele),
                size=self._metadata_size_helper(placeholderObj, prevData),
            )
            effected = prevData != await prev_download_media_data(
                ele, model_id=model_id, username=username
            )
        return ele.mediatype if effected else "Forced_skipped"

    def _existing_file(self, placeholderObj, prevData):
        """The downloaded file on disk: the current template path, else the recorded one."""
        current = pathlib.Path(placeholderObj.trunicated_filepath)
        if current.is_file():
            return current
        if prevData.get("filename"):
            recorded = pathlib.Path(prevData.get("directory") or "", prevData["filename"])
            if recorded.is_file():
                return recorded
        return None

    def _metadata_downloaded_helper(self, placeholderObj, prevData):
        if settings.get_settings().metadata == "check":
            return prevData["downloaded"] if prevData else None
        elif settings.get_settings().metadata == "complete":
            return 1
        # for update
        return 1 if self._existing_file(placeholderObj, prevData) else 0

    # In update mode the directory and filename must name the same existing file,
    # or the record points at a path that does not exist.
    def _metadata_file_helper(self, placeholderObj, prevData):
        if settings.get_settings().metadata != "update":
            return str(placeholderObj.trunicated_filename)
        existing = self._existing_file(placeholderObj, prevData)
        return existing.name if existing else str(placeholderObj.trunicated_filename)

    def _metadata_dir_helper(self, placeholderObj, prevData):
        if settings.get_settings().metadata != "update":
            return str(placeholderObj.trunicated_filedir)
        existing = self._existing_file(placeholderObj, prevData)
        return str(existing.parent) if existing else str(placeholderObj.trunicated_filedir)

    def _metadata_hash_helper(self, placeholderObj, prevData, ele):
        if not settings.get_settings().hash:
            return prevData.get("hash")
        existing = self._existing_file(placeholderObj, prevData)
        return hash.get_hash(existing) if existing else None

    def _metadata_size_helper(self, placeholderObj, prevData):
        existing = self._existing_file(placeholderObj, prevData)
        return existing.stat().st_size if existing else prevData.get("size")

    async def _metadata_helper(self, c, ele):
        placeholderObj = None
        if not ele.url and not ele.mpd:
            placeholderObj = placeholder.Placeholders(ele, ext=ele.content_type)
            return placeholderObj
        else:
            url = ele.url or ele.mpd
            params = get_alt_params(ele) if ele.mpd else None
            actions = (
                [FORCED_NEW, SIGN]
                if ele.mpd and of_env.getattr("ALT_FORCE_KEY")
                else []
            )
            common_globals.attempt.set(common_globals.attempt.get() + 1)
            common_globals.log.debug(
                f"{get_medialog(ele)} [attempt {common_globals.attempt.get()}/{get_download_retries()}]  Getting data for metadata insert"
            )
            async with c.requests_async(
                url=url, headers=None, params=params, actions=actions
            ) as r:
                headers = r.headers
                content_type = (
                    (headers.get("content-type") or "application/octet-stream").split("/")[-1] or ele.content_type
                )
            # Only the headers matter here, so the body is left unread; the session
            # releases the connection. Protected media is downloaded as an MP4, and
            # this response is its DASH manifest.
            return placeholder.Placeholders(ele, ext="mp4" if ele.mpd and not ele.url else content_type)

    async def _placeholderObjHelper(self, c, ele):
        # Same key the download manager stores response headers under.
        download_data = await asyncio.get_running_loop().run_in_executor(
            common_globals.thread, partial(cache.get, f"{ele.id}_{ele.username}_headers")
        )
        if download_data:
            content_type = (
                (download_data.get("content-type") or "application/octet-stream").split("/")[-1] or ele.content_type
            )
            return placeholder.Placeholders(ele, content_type)
        # final fallback
        return await self._metadata_helper(c, ele)
