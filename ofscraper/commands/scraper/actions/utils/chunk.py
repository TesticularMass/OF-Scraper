import pathlib

import ofscraper.commands.scraper.actions.utils.globals as common_globals
import ofscraper.utils.of_env.of_env as of_env
from ofscraper.utils.logs.utils.level import getNumber
from ofscraper.commands.scraper.actions.utils.log import get_medialog


def send_chunk_msg(ele, total, placeholderObj):
    try:
        size = pathlib.Path(placeholderObj.tempfilepath).absolute().stat().st_size
    except (FileNotFoundError, OSError):
        size = 0
    msg = f"{get_medialog(ele)} Download Progress:{size}/{total}"
    if of_env.getattr("SHOW_DL_CHUNKS"):
        common_globals.log.log(getNumber(of_env.getattr("SHOW_DL_CHUNKS_LEVEL")), msg)
    else:
        common_globals.log.trace(msg)
