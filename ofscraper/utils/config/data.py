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

from diskcache import Disk, JSONDisk
from humanfriendly import parse_size

import ofscraper.utils.of_env.of_env as of_env
import ofscraper.utils.config.file as config_file
import ofscraper.utils.config.utils.wrapper as wrapper
import ofscraper.utils.const as const


def strip_path_quotes(val):
    # Windows "Copy as path" wraps paths in double quotes, which then end up
    # literally inside the json string
    if isinstance(val, str):
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1].strip()
    return val


def first_set(*values):
    """The first value that is set.

    The config menu saves its answers as top-level keys over the nested
    sections, so chaining the keys with "or" let a saved False, 0 or "" fall
    through to the old nested value and the change was lost.
    """
    return next((val for val in values if val is not None), None)


@wrapper.config_reader
def get_main_profile(config=None):
    if config is False:
        return of_env.getattr("PROFILE_DEFAULT")
    value = config.get(of_env.getattr("mainProfile"))
    return value or of_env.getattr("PROFILE_DEFAULT")


@wrapper.config_reader
def get_filesize_max(config=None):
    if config is False:
        return of_env.getattr("FILE_SIZE_MAX_DEFAULT")
    try:
        size = first_set(
            config.get("file_size_max"),
            config.get("download_options", {}).get("file_size_max"),
            config.get("download_options", {}).get("file_size_limit"),
            config.get("content_filter_options", {}).get("file_size_max"),
        )
        final_size = (
            size if size is not None else of_env.getattr("FILE_SIZE_MAX_DEFAULT")
        )
        return parse_size(str(final_size))
    except (ValueError, TypeError):
        return 0


@wrapper.config_reader
def get_filesize_min(config=None):
    if config is False:
        return of_env.getattr("FILE_SIZE_MIN_DEFAULT")
    try:
        size = first_set(
            config.get("file_size_min"),
            config.get("download_options", {}).get("file_size_min"),
            config.get("content_filter_options", {}).get("file_size_min"),
        )
        final_size = (
            size if size is not None else of_env.getattr("FILE_SIZE_MIN_DEFAULT")
        )
        return parse_size(str(final_size))
    except (ValueError, TypeError):
        return 0


@wrapper.config_reader
def get_min_length(config=None):
    if config is False:
        return of_env.getattr("MIN_LENGTH_DEFAULT")
    value = first_set(
        config.get("length_min"),
        config.get("download_options", {}).get("length_min"),
        config.get("content_filter_options", {}).get("length_min"),
    )
    return value if value is not None else of_env.getattr("MIN_LENGTH_DEFAULT")


@wrapper.config_reader
def get_max_length(config=None):
    if config is False:
        return of_env.getattr("MAX_LENGTH_DEFAULT")
    value = first_set(
        config.get("length_max"),
        config.get("download_options", {}).get("length_max"),
        config.get("content_filter_options", {}).get("length_max"),
    )
    return value if value is not None else of_env.getattr("MAX_LENGTH_DEFAULT")


@wrapper.config_reader
def get_system_freesize(config=None):
    if config is False:
        return of_env.getattr("SYSTEM_FREEMIN_DEFAULT")
    try:
        size = first_set(
            config.get("system_free_min"),
            config.get("download_options", {}).get("system_free_min"),
        )
        final_size = (
            size if size is not None else of_env.getattr("SYSTEM_FREEMIN_DEFAULT")
        )
        return parse_size(str(final_size))
    except (ValueError, TypeError):
        return 0


@wrapper.config_reader
def get_dirformat(config=None):
    if config is False:
        return of_env.getattr("DIR_FORMAT_DEFAULT")
    return first_set(
        config.get("dir_format"), config.get("file_options", {}).get("dir_format")
    ) or of_env.getattr("DIR_FORMAT_DEFAULT")


@wrapper.config_reader
def get_fileformat(config=None):
    if config is False:
        return of_env.getattr("FILE_FORMAT_DEFAULT")
    return first_set(
        config.get("file_format"), config.get("file_options", {}).get("file_format")
    ) or of_env.getattr("FILE_FORMAT_DEFAULT")


@wrapper.config_reader
def get_textlength(config=None):
    if config is False:
        return of_env.getattr("TEXTLENGTH_DEFAULT")
    try:
        length = first_set(
            config.get("textlength"), config.get("file_options", {}).get("textlength")
        )
        final_length = (
            length if length is not None else of_env.getattr("TEXTLENGTH_DEFAULT")
        )
        return int(final_length)
    except (ValueError, TypeError):
        return of_env.getattr("TEXTLENGTH_DEFAULT")


@wrapper.config_reader
def get_date(config=None):
    if config is False:
        return of_env.getattr("DATE_DEFAULT")
    return first_set(
        config.get("date"), config.get("file_options", {}).get("date")
    ) or of_env.getattr("DATE_DEFAULT")


@wrapper.config_reader
def get_InfiniteLoop(config=None):
    if config is False:
        return of_env.getattr("INFINITE_LOOP_DEFAULT")
    val = first_set(
        config.get("infinite_loop_action_mode"),
        config.get("advanced_options", {}).get("infinite_loop_action_mode"),
    )
    return val if val is not None else of_env.getattr("INFINITE_LOOP_DEFAULT")


@wrapper.config_reader
def get_incremental_downloads(config=None):
    if config is False:
        return of_env.getattr("INCREMENTAL_DOWNLOADS_DEFAULT")
    val = first_set(
        config.get("incremental_downloads"),
        config.get("advanced_options", {}).get("incremental_downloads"),
        config.get("advanced_options", {}).get("enable_auto_after"),
    )
    return val if val is not None else of_env.getattr("INCREMENTAL_DOWNLOADS_DEFAULT")


@wrapper.config_reader
def get_default_userlist(config=None):
    if config is False:
        return of_env.getattr("DEFAULT_USER_LIST") or []
    val = first_set(
        config.get("default_user_list"), config.get("advanced_options", {}).get("default_user_list")
    )
    return val or of_env.getattr("DEFAULT_USER_LIST") or []


@wrapper.config_reader
def get_default_blacklist(config=None):
    if config is False:
        return of_env.getattr("DEFAULT_BLACK_LIST") or []
    val = first_set(
        config.get("default_black_list"), config.get("advanced_options", {}).get("default_black_list")
    )
    return val or of_env.getattr("DEFAULT_BLACK_LIST") or []


@wrapper.config_reader
def get_logs_expire(config=None):
    if not config:
        return 0
    val = first_set(
        config.get("logs_expire_time"), config.get("advanced_options", {}).get("logs_expire_time")
    )
    return int(val) if val is not None else 0


@wrapper.config_reader
def get_ssl_verify(config=None):
    if not config:
        return of_env.getattr("SSL_VALIDATION_DEFAULT")

    # 1. Safely check for the key (avoiding 'or' so we don't accidentally skip a literal False)
    val = config.get("ssl_verify")
    if val is None:
        val = config.get("advanced_options", {}).get("ssl_verify")

    # 2. Legacy Migration: Convert JSON booleans (True/False) to the new default
    if isinstance(val, bool):
        return "custom"

    return val if val is not None else of_env.getattr("SSL_VALIDATION_DEFAULT")


@wrapper.config_reader
def get_after_action_script(config=None):
    if config is False:
        return of_env.getattr("AFTER_ACTION_SCRIPT_DEFAULT")
    val = first_set(
        config.get("after_action_script"),
        config.get("advanced_options", {}).get("after_action_script"),
        config.get("script_options", {}).get("after_action_script"),
    )
    return val if val is not None else of_env.getattr("AFTER_ACTION_SCRIPT_DEFAULT")


@wrapper.config_reader
def get_post_script(config=None):
    if config is False:
        return of_env.getattr("POST_SCRIPT_DEFAULT")
    val = first_set(
        config.get("post_script"),
        config.get("advanced_options", {}).get("post_script"),
        config.get("scripts", {}).get("post_script"),
        config.get("script_options", {}).get("post_script"),
    )
    return val if val is not None else of_env.getattr("POST_SCRIPT_DEFAULT")


@wrapper.config_reader
def get_naming_script(config=None):
    if config is False:
        return of_env.getattr("NAMING_SCRIPT_DEFAULT")
    val = first_set(
        config.get("naming_script"),
        config.get("advanced_options", {}).get("naming_script"),
        config.get("scripts", {}).get("naming_script"),
        config.get("script_options", {}).get("naming_script"),
    )
    return val if val is not None else of_env.getattr("NAMING_SCRIPT_DEFAULT")


@wrapper.config_reader
def get_skip_download_script(config=None):
    if config is False:
        return of_env.getattr("SKIP_DOWNLOAD_SCRIPT_DEFAULT")
    val = first_set(
        config.get("skip_download_script"),
        config.get("advanced_options", {}).get("skip_download_script"),
        config.get("scripts", {}).get("skip_download_script"),
        config.get("script_options", {}).get("skip_download_script"),
    )
    return val if val is not None else of_env.getattr("SKIP_DOWNLOAD_SCRIPT_DEFAULT")


@wrapper.config_reader
def get_after_download_script(config=None):
    if config is False:
        return of_env.getattr("AFTER_DOWNLOAD_SCRIPT_DEFAULT")
    val = first_set(
        config.get("after_download_script"),
        config.get("advanced_options", {}).get("after_download_script"),
        config.get("scripts", {}).get("after_download_script"),
        config.get("script_options", {}).get("after_download_script"),
    )
    return val if val is not None else of_env.getattr("AFTER_DOWNLOAD_SCRIPT_DEFAULT")


@wrapper.config_reader
def get_env_files(config=None):
    # This must remain "safe" to avoid chicken-and-egg loops
    if config is False:
        return []
    val = first_set(
        config.get("env_files"),
        config.get("advanced_options", {}).get("env_files"),
        config.get("scripts", {}).get("env_files"),
        config.get("script_options", {}).get("env_files"),
    )
    return val or []


@wrapper.config_reader
def get_metadata(config=None):
    if config is False:
        return of_env.getattr("METADATA_DEFAULT")
    return config.get("metadata", of_env.getattr("METADATA_DEFAULT"))


@wrapper.config_reader
def get_download_limit(config=None):
    if config is False:
        return of_env.getattr("DOWNLOAD_LIMIT_DEFAULT")
    try:
        limit = first_set(
            config.get("download_limit"),
            config.get("performance_options", {}).get("download_limit"),
        )
        final_limit = (
            limit if limit is not None else of_env.getattr("DOWNLOAD_LIMIT_DEFAULT")
        )
        return parse_size(str(final_limit))
    except (ValueError, TypeError):
        return 0


@wrapper.config_reader
def get_ffmpeg(config=None):
    if config is False:
        return of_env.getattr("FFMPEG_DEFAULT")
    val = first_set(config.get("ffmpeg"), config.get("binary_options", {}).get("ffmpeg"))
    val = strip_path_quotes(val)
    # "" is kept as-is so a config rewrite doesn't save OFSC_FFMPEG_DEFAULT
    # into the file; settings applies that fallback at runtime
    return val if val is not None else of_env.getattr("FFMPEG_DEFAULT")


@wrapper.config_reader
def get_discord(config=None):
    if config is False:
        return of_env.getattr("DISCORD_DEFAULT")
    val = config.get("discord")
    return val if val is not None else of_env.getattr("DISCORD_DEFAULT")


@wrapper.config_reader
def get_filter(config=None):
    if config is False:
        return of_env.getattr("FILTER_DEFAULT")
    filter_val = first_set(
        config.get("filter"),
        config.get("download_options", {}).get("filter"),
        config.get("content_filter_options", {}).get("filter"),
    )
    final_filter = (
        filter_val if filter_val is not None else of_env.getattr("FILTER_DEFAULT")
    )
    if isinstance(final_filter, str):
        return [x.capitalize().strip() for x in final_filter.split(",")]
    elif isinstance(final_filter, list):
        return [x.capitalize() for x in final_filter]
    return []


@wrapper.config_reader
def responsetype(config=None):
    if config is False:
        return of_env.getattr("RESPONSE_TYPE_DEFAULT")
    val = config.get("responsetype")
    return val or of_env.getattr("RESPONSE_TYPE_DEFAULT")


@wrapper.config_reader
def get_timeline_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["timeline"]
    if config is False:
        return default
    val = first_set(
        config.get("timeline"),
        config.get("post"),
        config.get("responsetype", {}).get("timeline"),
        config.get("responsetype", {}).get("post"),
    )
    return val or default


@wrapper.config_reader
def get_post_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["timeline"]
    if config is False:
        return default
    val = first_set(
        config.get("post"),
        config.get("timeline"),
        config.get("responsetype", {}).get("post"),
        config.get("responsetype", {}).get("timeline"),
    )
    return val or default


@wrapper.config_reader
def get_archived_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["archived"]
    if config is False:
        return default
    val = first_set(config.get("archived"), config.get("responsetype", {}).get("archived"))
    return val or default


@wrapper.config_reader
def get_stories_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["stories"]
    if config is False:
        return default
    val = first_set(config.get("stories"), config.get("responsetype", {}).get("stories"))
    return val or default


@wrapper.config_reader
def get_highlights_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["highlights"]
    if config is False:
        return default
    val = first_set(
        config.get("highlights"), config.get("responsetype", {}).get("highlights")
    )
    return val or default


@wrapper.config_reader
def get_paid_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["paid"]
    if config is False:
        return default
    val = first_set(config.get("paid"), config.get("responsetype", {}).get("paid"))
    return val or default


@wrapper.config_reader
def get_messages_progress_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["message"]
    if config is False:
        return default
    val = first_set(config.get("message"), config.get("responsetype", {}).get("message"))
    return val or default


@wrapper.config_reader
def get_profile_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["profile"]
    if config is False:
        return default
    val = first_set(config.get("profile"), config.get("responsetype", {}).get("profile"))
    return val or default


@wrapper.config_reader
def get_pinned_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["pinned"]
    if config is False:
        return default
    val = first_set(config.get("pinned"), config.get("responsetype", {}).get("pinned"))
    return val or default


@wrapper.config_reader
def get_streams_responsetype(config=None):
    default = of_env.getattr("RESPONSE_TYPE_DEFAULT")["streams"]
    if config is False:
        return default
    val = first_set(config.get("streams"), config.get("responsetype", {}).get("streams"))
    return val or default


@wrapper.config_reader
def get_spacereplacer(config=None):
    if config is False:
        return of_env.getattr("SPACE_REPLACER_DEFAULT")
    val = first_set(
        config.get("space_replacer"),
        # the config menu saves it under this name
        config.get("space-replacer"),
        config.get("file_options", {}).get("space_replacer"),
        config.get("file_options", {}).get("space-replacer"),
    )
    return val or of_env.getattr("SPACE_REPLACER_DEFAULT")


@wrapper.config_reader
def get_private_key(config=None):
    if not config:
        return None
    return strip_path_quotes(
        first_set(config.get("private-key"), config.get("cdm_options", {}).get("private-key"))
    )


@wrapper.config_reader
def get_client_id(config=None):
    if not config:
        return None
    return strip_path_quotes(
        first_set(config.get("client-id"), config.get("cdm_options", {}).get("client-id"))
    )


@wrapper.config_reader
def get_key_mode(config=None):
    if config is False:
        return of_env.getattr("KEY_DEFAULT")
    value = first_set(
        config.get("key-mode-default"),
        config.get("cdm_options", {}).get("key-mode-default"),
    )
    final_value = value if value is not None else of_env.getattr("KEY_DEFAULT")
    return (
        final_value.lower()
        if final_value and final_value.lower() in of_env.getattr("KEY_OPTIONS")
        else of_env.getattr("KEY_DEFAULT")
    )


@wrapper.config_reader
def get_dynamic(config=None):
    if config is False:
        return of_env.getattr("DYNAMIC_RULE_DEFAULT")
    value = first_set(
        config.get("dynamic-mode-default"),
        config.get("advanced_options", {}).get("dynamic-mode-default"),
    )
    final_value = value if value is not None else of_env.getattr("DYNAMIC_RULE_DEFAULT")
    return (
        final_value.lower()
        if final_value and final_value.lower() in of_env.getattr("DYNAMIC_OPTIONS_ALL")
        else of_env.getattr("DYNAMIC_RULE_DEFAULT")
    )


@wrapper.config_reader
def get_part_file_clean(config=None):
    if config is False:
        return of_env.getattr("RESUME_DEFAULT")
    val = first_set(
        config.get("auto_resume"), config.get("download_options", {}).get("auto_resume")
    )
    if val is not None:
        return val
    legacy_val = config.get("partfileclean")
    if legacy_val is not None:
        return legacy_val is False
    return of_env.getattr("RESUME_DEFAULT")


@wrapper.config_reader
def get_download_semaphores(config=None):
    if config is False:
        return of_env.getattr("DOWNLOAD_SEM_DEFAULT")
    try:
        sem = first_set(
            config.get("download_sems"),
            config.get("performance_options", {}).get("download_sems"),
        )
        final_sem = sem if sem is not None else of_env.getattr("DOWNLOAD_SEM_DEFAULT")
        return int(final_sem)
    except (ValueError, TypeError):
        return int(of_env.getattr("DOWNLOAD_SEM_DEFAULT"))


@wrapper.config_reader
def get_show_downloadprogress(config=None):
    if config is False:
        return of_env.getattr("PROGRESS_DEFAULT")
    val = first_set(
        config.get("downloadbars"), config.get("advanced_options", {}).get("downloadbars")
    )
    return val if val is not None else of_env.getattr("PROGRESS_DEFAULT")


@wrapper.config_reader
def get_cache_mode(config=None):
    if cache_mode_helper(config=config) == "sqlite":
        return Disk
    else:
        return JSONDisk


def cache_mode_helper(config=None):
    if config is False:
        return of_env.getattr("CACHEDEFAULT")
    if config is None:
        config = config_file.open_config()
    data = first_set(
        config.get("cache-mode"), config.get("advanced_options", {}).get("cache-mode")
    )
    final_data = data if data is not None else of_env.getattr("CACHEDEFAULT")
    if final_data in {"sqlite", "json", "disabled", "api_disabled"}:
        return final_data
    else:
        return of_env.getattr("CACHEDEFAULT")


@wrapper.config_reader
def get_rotate_logs(config=None):
    if config is False:
        return of_env.getattr("ROTATE_DEFAULT")
    value = first_set(
        config.get("rotate_logs"), config.get("advanced_options", {}).get("rotate_logs")
    )
    return value if value is not None else of_env.getattr("ROTATE_DEFAULT")


@wrapper.config_reader
def get_sanitizeDB(config=None):
    if config is False:
        return of_env.getattr("SANITIZE_DB_DEFAULT")
    val = first_set(
        config.get("sanitize_text"),
        config.get("advanced_options", {}).get("sanitize_text"),
    )
    return val if val is not None else of_env.getattr("SANITIZE_DB_DEFAULT")


@wrapper.config_reader
def get_textType(config=None):
    if config is False:
        return of_env.getattr("TEXT_TYPE_DEFAULT")
    value = first_set(
        config.get("text_type_default"),
        config.get("file_options", {}).get("text_type_default"),
    )
    final_value = value if value is not None else of_env.getattr("TEXT_TYPE_DEFAULT")
    return (
        final_value
        if final_value in {"letter", "word"}
        else of_env.getattr("TEXT_TYPE_DEFAULT")
    )


@wrapper.config_reader
def get_TempDir(config=None):
    if config is False:
        return of_env.getattr("TEMP_FOLDER_DEFAULT")
    val = first_set(
        config.get("temp_dir"), config.get("advanced_options", {}).get("temp_dir")
    )
    # the menu saves a blank answer as "", which means no temp dir
    return strip_path_quotes(val) or of_env.getattr("TEMP_FOLDER_DEFAULT")


@wrapper.config_reader
def get_truncation(config=None):
    if config is False:
        return of_env.getattr("TRUNCATION_DEFAULT")
    val = first_set(
        config.get("truncation_default"),
        config.get("file_options", {}).get("truncation_default"),
    )
    return val if val is not None else of_env.getattr("TRUNCATION_DEFAULT")


@wrapper.config_reader
def get_max_post_count(config=None):
    if config is False:
        return of_env.getattr("MAX_COUNT_DEFAULT")
    try:
        count = first_set(
            config.get("max_post_count"),
            config.get("download_options", {}).get("max_post_count"),
        )
        final_count = (
            count if count is not None else of_env.getattr("MAX_COUNT_DEFAULT")
        )
        return int(final_count)
    except (ValueError, TypeError):
        return of_env.getattr("MAX_COUNT_DEFAULT")


@wrapper.config_reader
def get_hash(config=None):
    if config is False:
        return of_env.getattr("HASHED_DEFAULT")
    val = first_set(
        config.get("remove_hash_match"),
        config.get("advanced_options", {}).get("remove_hash_match"),
    )
    return val if val is not None else of_env.getattr("HASHED_DEFAULT")


@wrapper.config_reader
def get_block_ads(config=None):
    if config is False:
        return of_env.getattr("BLOCKED_ADS_DEFAULT")
    val = first_set(
        config.get("block_ads"), config.get("content_filter_options", {}).get("block_ads")
    )
    return val if val is not None else of_env.getattr("BLOCKED_ADS_DEFAULT")


@wrapper.config_reader
def get_skip_unavailable_content(config=None):
    if config is False:
        return of_env.getattr("SKIP_UNAVAILABLE_DEFAULT")
    val = first_set(
        config.get("skip_unavailable_content"),
        config.get("advanced_options", {}).get("skip_unavailable_content"),
    )
    return val if val is not None else of_env.getattr("SKIP_UNAVAILABLE_DEFAULT")


@wrapper.config_reader
def get_verify_all_integrity(config=None):
    if config is False:
        return of_env.getattr("VERIFY_ALL_INTEGRITY")
    val = first_set(
        config.get("verify_all_integrity"),
        config.get("download_options", {}).get("verify_all_integrity"),
    )
    return val if val is not None else of_env.getattr("VERIFY_ALL_INTEGRITY")
