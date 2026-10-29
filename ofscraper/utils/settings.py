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

import threading
from copy import deepcopy
import arrow
from diskcache import Disk, JSONDisk

import ofscraper.utils.of_env.of_env as of_env
import ofscraper.utils.config.data as config_data  # <-- IMPORTING THE REAL DATA.PY
import ofscraper.utils.ads as ads
import ofscraper.utils.args.accessors.read as read_args
import ofscraper.utils.args.mutators.write as write_args
from ofscraper.utils.args.mutators.user import (
    resetUserFilters as resetUserFiltersArgs,
    resetUserSelect as resetUserSelectArg,
)
from ofscraper.utils.of_env.load import load_env_files

# Global lock and settings cache
_init_lock = threading.Lock()
settings = {}

# =========================================================================
# SETTINGS MANAGEMENT & HELPERS
# =========================================================================


def get_args(copy=False):
    args = read_args.retriveArgs()
    return deepcopy(args) if copy else args


def update_args(args):
    global settings
    write_args.setArgs(args)
    with _init_lock:
        settings = setup_settings()


def update_settings():
    global settings
    with _init_lock:
        settings = setup_settings()


def get_settings():
    global settings
    if not settings:
        with _init_lock:
            if not settings:
                settings = setup_settings()
    return settings


def setup_settings():
    # 1. LOAD: the env files must be in place before of_env reads its defaults
    load_env_files(_env_files(read_args.retriveArgs()))
    of_env.get_all_configs(forced=True)

    # 2. MERGE: Now that defaults are loaded, merge everything into the final object
    merged = merged_settings()

    # Cache it globally
    global settings
    settings = merged
    return merged


def _env_files(args):
    """--env-files, else the config's env_files, as a list of paths."""
    env_files = args.env_files or config_data.get_env_files() or []
    if isinstance(env_files, str):
        # a hand-written config may hold "a.env,b.env"; iterating the string
        # would treat each character as a path
        env_files = env_files.split(",")
    return [str(path).strip() for path in env_files if str(path).strip()]


def resetUserFilters():
    global settings
    write_args.setArgs(resetUserFiltersArgs())
    settings = setup_settings()


def resetUserSelect():
    global settings
    write_args.setArgs(resetUserSelectArg())
    settings = setup_settings()


def merged_settings():
    args = read_args.retriveArgs()
    merged = deepcopy(args)

    # --- Cache Logic ---
    cache_mode = (
        config_data.cache_mode_helper()
        if hasattr(config_data, "cache_mode_helper")
        else of_env.getattr("CACHEDEFAULT")
    )
    merged.cached_disabled = args.no_cache or cache_mode == "disabled"
    merged.cache_disabled = args.no_cache or cache_mode == "disabled"
    merged.api_cache_disabled = (
        args.no_cache or args.no_api_cache or cache_mode in {"disabled", "api_disabled"}
    )

    # --- Basic Config Overrides ---
    # an empty "ffmpeg" in config means unset, so OFSC_FFMPEG_DEFAULT applies
    merged.ffmpeg = config_data.get_ffmpeg() or of_env.getattr("FFMPEG_DEFAULT")
    merged.users_first = args.users_first
    merged.userfirst = args.users_first
    merged.key_mode = args.key_mode or config_data.get_key_mode()
    merged.dynamic_rules = args.dynamic_rules or config_data.get_dynamic()
    merged.download_bars = args.downloadbars or config_data.get_show_downloadprogress()
    merged.discord_level = args.discord_level or config_data.get_discord()
    merged.log_level = args.log_level or of_env.getattr("DEFAULT_LOG_LEVEL")
    merged.trunicate = False if args.original else config_data.get_truncation()

    # --- Ad Blocking & Filters ---
    # a copy: appending to the args' own list repeated the ad filter on every rebuild
    neg = list(args.neg_filter or [])
    if args.block_ads or config_data.get_block_ads():
        neg.append(ads.get_ad_key_words())
    merged.neg_filter = neg

    # --- Lists ---
    def _listhelper(out):
        if not out:
            return []
        if isinstance(out, str):
            out = out.split(",")
        if isinstance(out, list):
            return [str(x).strip() for x in out if str(x).strip()]
        return []

    merged.userlist = _listhelper(args.userlist or config_data.get_default_userlist())
    merged.blacklist = _listhelper(
        args.blacklist or config_data.get_default_blacklist()
    )

    # --- File & Download Settings ---
    merged.text_type = args.text_type or config_data.get_textType()
    merged.space_replacer = args.space_replacer or config_data.get_spacereplacer()
    merged.text_length = (
        args.textlength
        if getattr(args, "textlength", None) is not None
        else args.text_length
        if getattr(args, "text_length", None) is not None
        else config_data.get_textlength()
    )
    merged.size_max = args.size_max or config_data.get_filesize_max()
    merged.size_min = args.size_min or config_data.get_filesize_min()
    merged.download_sems = args.downloadsem or config_data.get_download_semaphores()
    merged.system_free_min = args.system_free_min or config_data.get_system_freesize()
    merged.max_post_count = args.max_count or config_data.get_max_post_count()
    merged.mediatypes = args.mediatypes or config_data.get_filter()
    merged.verify_all_integrity = config_data.get_verify_all_integrity()

    dl_limit = args.download_limit or (
        config_data.get_download_limit()
        if hasattr(config_data, "get_download_limit")
        else 0
    )
    merged.download_limit = max(dl_limit, 1024) if dl_limit else dl_limit

    merged.length_max = (
        args.length_max if args.length_max is not None else config_data.get_max_length()
    )
    merged.length_min = (
        args.length_min if args.length_min is not None else config_data.get_min_length()
    )

    # --- Credentials & Scripts ---
    merged.private_key = args.private_key or config_data.get_private_key()
    merged.client_id = args.client_id or config_data.get_client_id()
    merged.hash = config_data.get_hash()
    merged.post_script = args.post_script or config_data.get_post_script()
    merged.after_action_script = (
        args.after_action_script or config_data.get_after_action_script()
    )
    merged.naming_script = args.naming_script or config_data.get_naming_script()
    merged.skip_download_script = (
        args.skip_download_script or config_data.get_skip_download_script()
    )
    merged.after_download_script = (
        args.after_download_script or config_data.get_after_download_script()
    )

    # --- System Flags ---
    merged.rotate_logs = config_data.get_rotate_logs()
    merged.auto_resume = (
        False if args.no_auto_resume else config_data.get_part_file_clean()
    )
    merged.incremental_downloads = (
        False if merged.cache_disabled else config_data.get_incremental_downloads()
    )
    merged.logs_expire_time = config_data.get_logs_expire()
    merged.ssl_verify = config_data.get_ssl_verify()

    merged.skip_unavailable_content = (
        config_data.get_skip_unavailable_content()
        if hasattr(config_data, "get_skip_unavailable_content")
        else False
    )

    # --- Environment Files ---
    merged.env_files = _env_files(args)

    # --- CLI Overrides ---
    merged.text = args.text or args.text_only
    merged.text_only = args.text_only

    if args.redownload:
        merged.force_all = True
        merged.after = arrow.get("2000")
        merged.before = arrow.now().shift(days=1)

    return merged
