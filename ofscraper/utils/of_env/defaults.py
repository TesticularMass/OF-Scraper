"""Application defaults, evaluated in the same order on each forced reload."""

import json
import os
import pathlib

import ofscraper.utils.const as const


def load_defaults():
    config = {}
    config["SANITIZE_DB_DEFAULT"] = os.getenv(
        "OFSC_SANITIZE_DB_DEFAULT", "False"
    ).lower() in ("true", "1")
    config["SUPPRESS_LOG_LEVEL"] = int(os.getenv("OFSC_SUPPRESS_LOG_LEVEL", "21"))
    config["RESUME_DEFAULT"] = os.getenv("OFSC_RESUME_DEFAULT", "True").lower() in (
        "true",
        "1",
    )
    config["CACHEDEFAULT"] = os.getenv("OFSC_CACHE_DEFAULT", "sqlite")
    config["KEY_DEFAULT"] = os.getenv("OFSC_KEY_DEFAULT", "cdrm")
    config["KEY_OPTIONS"] = const.KEY_OPTIONS
    config["FILE_SIZE_MAX_DEFAULT"] = int(os.getenv("OFSC_FILE_SIZE_MAX_DEFAULT", "0"))
    config["FILE_SIZE_MIN_DEFAULT"] = int(os.getenv("OFSC_FILE_SIZE_MIN_DEFAULT", "0"))
    config["MIN_LENGTH_DEFAULT"] = int(os.getenv("OFSC_MIN_LENGTH_DEFAULT", "0"))
    config["MAX_LENGTH_DEFAULT"] = int(os.getenv("OFSC_MAX_LENGTH_DEFAULT", "0"))
    config["TEXTLENGTH_DEFAULT"] = int(os.getenv("OFSC_TEXTLENGTH_DEFAULT", "0"))
    config["SPACE_REPLACER_DEFAULT"] = os.getenv("OFSC_SPACE_REPLACER_DEFAULT", " ")
    config["PROGRESS_DEFAULT"] = os.getenv(
        "OFSC_PROGRESS_DEFAULT", "False"
    ).lower() in ("true", "1")
    config["SAVE_PATH_DEFAULT"] = os.getenv(
        "OFSC_SAVE_PATH_DEFAULT", str(pathlib.Path.home() / "Data/ofscraper")
    )
    config["DATE_DEFAULT"] = os.getenv("OFSC_DATE_DEFAULT", "MM-DD-YYYY")
    config["PROFILE_DEFAULT"] = os.getenv("OFSC_PROFILE_DEFAULT", "main_profile")
    config["PREMIUM_DEFAULT"] = os.getenv("OFSC_PREMIUM_DEFAULT", "Premium")
    config["FFMPEG_DEFAULT"] = os.getenv("OFSC_FFMPEG_DEFAULT", "")
    config["DISCORD_DEFAULT"] = os.getenv("OFSC_DISCORD_DEFAULT", "")
    config["THREADS_DEFAULT"] = int(os.getenv("OFSC_THREADS_DEFAULT", "2"))
    config["DOWNLOAD_SEM_DEFAULT"] = int(os.getenv("OFSC_DOWNLOAD_SEM_DEFAULT", "6"))
    config["TEXT_TYPE_DEFAULT"] = os.getenv("OFSC_TEXT_TYPE_DEFAULT", "letter")
    config["TRUNCATION_DEFAULT"] = os.getenv(
        "OFSC_TRUNCATION_DEFAULT", "True"
    ).lower() in ("true", "1")
    config["MAX_COUNT_DEFAULT"] = int(os.getenv("OFSC_MAX_COUNT_DEFAULT", "0"))
    config["TEMP_FOLDER_DEFAULT"] = os.getenv("OFSC_TEMP_FOLDER_DEFAULT", None)
    config["ROTATE_DEFAULT"] = os.getenv("OFSC_ROTATE_DEFAULT", "True").lower() in (
        "true",
        "1",
    )
    config["SYSTEM_FREEMIN_DEFAULT"] = int(
        os.getenv("OFSC_SYSTEM_FREEMIN_DEFAULT", "0")
    )
    config["AVATAR_DEFAULT"] = os.getenv("OFSC_AVATAR_DEFAULT", "True").lower() in (
        "true",
        "1",
    )
    config["INFINITE_LOOP_DEFAULT"] = os.getenv(
        "OFSC_INFINITE_LOOP_DEFAULT", "False"
    ).lower() in ("true", "1")
    incremental_envs = [
        os.getenv("OFSC_INCREMENTAL_DOWNLOADS_DEFAULT"),
        os.getenv("OFSC_ENABLE_AUTO_AFTER_DEFAULT"),
    ]
    active_env_val = next((val for val in incremental_envs if val is not None), None)
    if active_env_val is not None:
        config["INCREMENTAL_DOWNLOADS_DEFAULT"] = active_env_val.lower() in (
            "true",
            "1",
        )
    else:
        config["INCREMENTAL_DOWNLOADS_DEFAULT"] = True
    config["DEFAULT_USER_LIST"] = os.getenv("OFSC_DEFAULT_USER_LIST", "main")
    config["DEFAULT_BLACK_LIST"] = os.getenv("OFSC_DEFAULT_BLACK_LIST", "")
    config["HASHED_DEFAULT"] = os.getenv("OFSC_HASHED_DEFAULT", None)
    config["BLOCKED_ADS_DEFAULT"] = os.getenv(
        "OFSC_BLOCKED_ADS_DEFAULT", "False"
    ).lower() in ("true", "1")
    config["DEFAULT_LOG_LEVEL"] = os.getenv("OFSC_DEFAULT_LOG_LEVEL", "DEBUG")
    config["INCLUDE_LABELS_ALL"] = os.getenv(
        "OFSC_INCLUDE_LABELS_ALL", "False"
    ).lower() in ("true", "1")
    config["DISCORD_THREAD_OVERRIDE"] = os.getenv(
        "OFSC_DISCORD_THREAD_OVERRIDE", "False"
    ).lower() in ("true", "1")
    config["DISCORD_ASYNC"] = os.getenv("OFSC_DISCORD_ASYNC", "False").lower() in (
        "true",
        "1",
    )
    config["USE_WIV_CACHE_KEY"] = os.getenv(
        "OFSC_USE_WIV_CACHE_KEY", "True"
    ).lower() in ("true", "1")
    config["AFTER_ACTION_SCRIPT_DEFAULT"] = os.getenv(
        "OFSC_AFTER_ACTION_SCRIPT_DEFAULT", None
    )
    config["POST_SCRIPT_DEFAULT"] = os.getenv("OFSC_POST_SCRIPT_DEFAULT", None)
    config["SKIP_DOWNLOAD_SCRIPT_DEFAULT"] = os.getenv(
        "OFSC_SKIP_DOWNLOAD_SCRIPT_DEFAULT", None
    )
    config["AFTER_DOWNLOAD_SCRIPT_DEFAULT"] = os.getenv(
        "OFSC_AFTER_DOWNLOAD_SCRIPT_DEFAULT", None
    )
    config["ENV_FILES_DEFAULT"] = os.getenv("OFSC_ENV_FILES_DEFAULT", "")
    config["NAMING_SCRIPT_DEFAULT"] = os.getenv("OFSC_NAMING_SCRIPT_DEFAULT", None)
    config["DOWNLOAD_LIMIT_DEFAULT"] = int(
        os.getenv("OFSC_DOWNLOAD_LIMIT_DEFAULT", "0")
    )
    config["DIR_FORMAT_DEFAULT"] = os.getenv(
        "OFSC_DIR_FORMAT_DEFAULT", "{model_username}/{responsetype}/{mediatype}/"
    )
    config["FILE_FORMAT_DEFAULT"] = os.getenv(
        "OFSC_FILE_FORMAT_DEFAULT", "{filename}.{ext}"
    )
    config["METADATA_DEFAULT"] = os.getenv(
        "OFSC_METADATA_DEFAULT", "{configpath}/{profile}/.data/{model_id}"
    )
    response_type_default_env = os.getenv("OFSC_RESPONSE_TYPE_DEFAULT")
    if response_type_default_env:
        try:
            config["RESPONSE_TYPE_DEFAULT"] = json.loads(response_type_default_env)
        except json.JSONDecodeError:
            print(
                f"Warning: OFSC_RESPONSE_TYPE_DEFAULT environment variable '{response_type_default_env}' is not valid JSON. Using default dictionary."
            )
            config["RESPONSE_TYPE_DEFAULT"] = {
                "message": "Messages",
                "timeline": "Posts",
                "archived": "Archived",
                "paid": "Purchased",
                "stories": "Stories",
                "highlights": "Stories",
                "profile": "Profile",
                "pinned": "Posts",
                "streams": "Streams",
            }
    else:
        config["RESPONSE_TYPE_DEFAULT"] = {
            "message": "Messages",
            "timeline": "Posts",
            "archived": "Archived",
            "paid": "Messages",
            "stories": "Stories",
            "highlights": "Stories",
            "profile": "Profile",
            "pinned": "Posts",
            "streams": "Streams",
        }
    empty_media_default_env = os.getenv("OFSC_EMPTY_MEDIA_DEFAULT")
    if empty_media_default_env:
        try:
            config["EMPTY_MEDIA_DEFAULT"] = json.loads(empty_media_default_env)
        except json.JSONDecodeError:
            print(
                f"Warning: OFSC_EMPTY_MEDIA_DEFAULT environment variable '{empty_media_default_env}' is not valid JSON. Using default empty dictionary."
            )
            config["EMPTY_MEDIA_DEFAULT"] = {}
    else:
        config["EMPTY_MEDIA_DEFAULT"] = {}
    filter_default_env = os.getenv("OFSC_FILTER_DEFAULT")
    if filter_default_env:
        config["FILTER_DEFAULT"] = [f.strip() for f in filter_default_env.split(",")]
    else:
        config["FILTER_DEFAULT"] = ["Images", "Audios", "Videos"]
    ssl_verify = os.getenv("OFSC_SSL_VALIDATION_DEFAULT", "custom")
    config["SSL_VALIDATION_DEFAULT"] = ssl_verify
    config["PROMPT_DATE_FORMAT"] = os.getenv("OFSC_PROMPT_DATE_FORMAT", "YYYY-MM-DD")
    config["API_DATE_FORMAT"] = os.getenv("OFSC_API_DATE_FORMAT", "YYYY-MM-DD HH:mm:ss")
    config["DYNAMIC_RULE_MANUAL"] = os.getenv("OFSC_DYNAMIC_RULE_MANUAL", None)
    dynamic_options_env = os.getenv("OFSC_DYNAMIC_OPTIONS")
    if dynamic_options_env:
        config["DYNAMIC_OPTIONS"] = [
            opt.strip() for opt in dynamic_options_env.split(",")
        ]
    else:
        config["DYNAMIC_OPTIONS"] = const.DYNAMIC_OPTIONS
    dynamic_options_all_env = os.getenv("OFSC_DYNAMIC_OPTIONS_ALL")
    if dynamic_options_all_env:
        config["DYNAMIC_OPTIONS_ALL"] = [
            opt.strip() for opt in dynamic_options_all_env.split(",")
        ]
    else:
        config["DYNAMIC_OPTIONS_ALL"] = config["DYNAMIC_OPTIONS"] + [
            "digitalcriminals",
            "dv",
            "dev",
            "dc",
            "digital",
            "digitals",
            "manual",
            "generic",
        ]
    config["DYNAMIC_RULE_DEFAULT"] = os.getenv("OFSC_DYNAMIC_RULE_DEFAULT", "digital")
    supress_outputs_env = os.getenv("OFSC_SUPRESS_OUTPUTS")
    if supress_outputs_env:
        config["SUPRESS_OUTPUTS"] = {s.strip() for s in supress_outputs_env.split(",")}
    else:
        config["SUPRESS_OUTPUTS"] = {
            "CRITICAL",
            "ERROR",
            "WARNING",
            "OFF",
            "LOW",
            "PROMPT",
        }
    config["refreshScreen"] = int(os.getenv("OFSC_REFRESH_SCREEN", "50"))
    config["SHOW_AVATAR"] = os.getenv("OFSC_SHOW_AVATAR", "True").lower() in (
        "true",
        "1",
    )
    config["SHOW_RESULTS_LOG"] = os.getenv("OFSC_SHOW_RESULTS_LOG", "True").lower() in (
        "true",
        "1",
    )
    config["MODEL_PRICE_PLACEHOLDER"] = os.getenv(
        "OFSC_MODEL_PRICE_PLACEHOLDER", "Unknown_Price"
    )
    config["DELETED_MODEL_PLACEHOLDER"] = os.getenv(
        "OFSC_DELETED_MODEL_PLACEHOLDER", "modeldeleted"
    )
    config["APP_TOKEN"] = os.getenv(
        "OFSC_APP_TOKEN", "33d57ade8c02dbc5a333db99ff9ae26a"
    )
    config["CONTINUE_BOOL"] = os.getenv("OFSC_CONTINUE_BOOL", "True").lower() in (
        "true",
        "1",
    )
    config["FILE_COUNT_PLACEHOLDER"] = os.getenv(
        "OFSC_FILE_COUNT_PLACEHOLDER", "True"
    ).lower() in ("true", "1")
    config["FILTER_SELF_MEDIA"] = os.getenv(
        "OFSC_FILTER_SELF_MEDIA", "True"
    ).lower() in ("true", "1")
    config["ALLOW_DUPE_MEDIA"] = os.getenv(
        "OFSC_ALLOW_DUPE_MEDIA", "False"
    ).lower() in ("true", "1")
    config["NUMBER_REGEX"] = os.getenv("OFSC_NUMBER_REGEX", "[0-9]")
    config["USERNAME_REGEX"] = os.getenv("OFSC_USERNAME_REGEX", "[^/]")
    config["BUF_SIZE"] = int(os.getenv("OFSC_BUF_SIZE", str(1024 * 1024)))
    config["LARGE_TRACE_CHUNK_SIZE"] = int(
        os.getenv("OFSC_LARGE_TRACE_CHUNK_SIZE", "100")
    )
    config["SKIP_UNAVAILABLE_DEFAULT"] = os.getenv(
        "OFSC_SKIP_UNAVAILABLE_DEFAULT", "True"
    ).lower() in ("true", "1")
    config["EXPIRED_GRACE_DEFAULT"] = int(os.getenv("OFSC_EXPIRED_GRACE_DEFAULT", "1"))
    config["OFSCRAPER_RESERVED_LIST"] = os.getenv(
        "OFSCRAPER_RESERVED_LIST", "ofscraper.main"
    )
    config["OFSCRAPER_RESERVED_LIST_ALT"] = os.getenv(
        "OFSCRAPER_RESERVED_LIST_ALT", "main"
    )
    config["OFSCRAPER_ACTIVE_LIST"] = os.getenv(
        "OFSCRAPER_ACTIVE_LIST", "ofscraper.active"
    )
    config["OFSCRAPER_ACTIVE_LIST_ALT"] = os.getenv(
        "OFSCRAPER_ACTIVE_LIST_ALT", "active"
    )
    config["OFSCRAPER_EXPIRED_LIST"] = os.getenv(
        "OFSCRAPER_EXPIRED_LIST", "ofscraper.expired"
    )
    config["OFSCRAPER_EXPIRED_LIST_ALT"] = os.getenv(
        "OFSCRAPER_EXPIRED_LIST_ALT", "expired"
    )
    config["SUPRESS_API_DISPLAY"] = os.getenv("OFSC_SUPRESS_API_DISPLAY", None)
    config["SUPRESS_DOWNLOAD_DISPLAY"] = os.getenv(
        "OFSC_SUPRESS_DOWNLOAD_DISPLAY", None
    )
    config["SUPRESS_SUBSCRIPTION_DISPLAY"] = os.getenv(
        "OFSC_SUPRESS_SUBSCRIPTION_DISPLAY", None
    )
    config["SUPRESS_LIKE_DISPLAY"] = os.getenv("OFSC_SUPRESS_LIKE_DISPLAY", None)
    config["DOWNLOAD_LIVE_DISPLAY"] = os.getenv(
        "OFSC_DOWNLOAD_LIVE_DISPLAY", "True"
    ).lower() in ("true", "1")
    config["LOGGER_TIMEOUT"] = float(os.getenv("OFSC_LOGGER_TIMEOUT", "0.4"))
    config["LOG_DISPLAY_TIMEOUT"] = float(os.getenv("OFSC_LOG_DISPLAY_TIMEOUT", "0.8"))
    config["FORCED_THREAD_TIMEOUT"] = int(os.getenv("OFSC_FORCED_THREAD_TIMEOUT", "5"))
    config["logname"] = os.getenv("OFSC_LOGNAME", "ofscraper")
    config["mainPromptChoices"] = {
        "Perform Action(s)": "action",
        "Edit auth.json file": "auth",
        "Edit config.json file": "config",
        "Edit Profile": "profile",
        "Merge Databases": "merge",
        "Quit": "quit",
    }
    config["configPromptChoices"] = {
        "General Options": "general",
        "File Options": "file",
        "Download Options": "download",
        "Binary Options": "binary",
        "Script Options": "script",
        "CDM Options": "cdm",
        "Performance Options": "performance",
        "Content Options": "content",
        "Response Type": "response",
        "Advanced Options": "advanced",
        "Go to main menu": "main",
        "Quit": "quit",
    }
    config["actionPromptChoices"] = {
        "Download content from a user": {"download"},
        "Like a selection of a user's posts": {"like"},
        "Unlike a selection of a user's posts": {"unlike"},
        "Download content from a user + Like a selection of a user's posts": {
            "like",
            "download",
        },
        "Download content from a user + Unlike a selection of a user's posts": {
            "unlike",
            "download",
        },
        "Subscribe to free / $0-promo accounts (expired subs only)": {"subscribe"},
        "Go to main menu": "main",
        "Quit": "quit",
    }
    config["usernameOrListChoices"] = {
        "Select from accounts on profile": "select",
        "Enter a username": "enter",
        "Scrape all users that I'm subscribed to": "sub",
    }
    config["profilesPromptChoices"] = {
        "Change the default profile": "default",
        "Switch profile for current run": "active",
        "Edit a profile name": "name",
        "Create a profile": "create",
        "Delete a profile": "delete",
        "View profiles": "view",
        "Go to main menu": "main",
        "Quit": "quit",
    }
    config["modelPrompt"] = {
        "Filter model list by subscription properties": "subtype",
        "Filter model list by account activity": "active",
        "Filter model list based on promotion status": "promo",
        "Filter model list based on status of prices": "price",
        "Change sorting of model list": "sort",
        "Change to a different userlist/blacklist [May require rescan]": "list",
        "Reset all filters": "reset_filters",
        "Clear blacklist and switch to the 'main' userlist [May require rescan]": "reset_list",
        "Rescan userlist": "rescan",
        "Go Back to model lists": "model_list",
    }
    config["AFTER_DOWNLOAD_ACTION_SCRIPT_SUBPROCESS_LEVEL"] = int(
        os.getenv("OFSC_AFTER_DOWNLOAD_ACTION_SCRIPT_SUBPROCESS_LEVEL", "10")
    )
    config["AFTER_LIKE_ACTION_SCRIPT_SUBPROCESS_LEVEL"] = int(
        os.getenv("OFSC_AFTER_LIKE_ACTION_SCRIPT_SUBPROCESS_LEVEL", "10")
    )
    config["NAMING_SCRIPT_SUBPROCESS_LEVEL"] = int(
        os.getenv("OFSC_NAMING_SCRIPT_SUBPROCESS_LEVEL", "10")
    )
    config["SKIP_DOWNLOAD_SCRIPT_SUBPROCESS_LEVEL"] = int(
        os.getenv("OFSC_SKIP_DOWNLOAD_SCRIPT_SUBPROCESS_LEVEL", "10")
    )
    config["AFTER_DOWNLOAD_SCRIPT_SUBPROCESS_LEVEL"] = int(
        os.getenv("OFSC_AFTER_DOWNLOAD_SCRIPT_SUBPROCESS_LEVEL", "10")
    )
    config["FINAL_SCRIPT_SUBPROCESS_LEVEL"] = int(
        os.getenv("OFSC_FINAL_SCRIPT_SUBPROCESS_LEVEL", "10")
    )
    config["LOG_SUBPROCESS_LEVEL"] = int(os.getenv("OFSC_LOG_SUBPROCESS_LEVEL", "10"))
    config["SCRIPT_OUTPUT_SUBPROCCESS"] = os.getenv("OFSC_SCRIPT_OUTPUT_SUBPROCCESS", "True").lower() in ("true", "1")
    config["SCRIPT_OUTPUT_SUBPROCCESS_LEVEL"] = int(os.getenv("OFSC_SCRIPT_OUTPUT_SUBPROCCESS_LEVEL", "10"))
    config["FFMPEG_SUBPROCESS_LEVEL"] = int(
        os.getenv("OFSC_FFMPEG_SUBPROCESS_LEVEL", "10")
    )
    config["FFPROBE_SUBPROCESS_LEVEL"] = int(
        os.getenv("OFSC_FFPROBE_SUBPROCESS_LEVEL", "10")
    )
    config["DISK_SPACE_CHECK_PATH"] = os.getenv("OFSC_DISK_SPACE_CHECK_PATH", "/")
    config["HOURLY_EXPIRY"] = int(os.getenv("OFSC_HOURLY_EXPIRY", "3600"))
    config["THIRTY_EXPIRY"] = int(os.getenv("OFSC_THIRTY_EXPIRY", "1800"))
    config["SIZE_TIMEOUT"] = int(os.getenv("OFSC_SIZE_TIMEOUT", "1209600"))
    config["DATABASE_TIMEOUT"] = int(os.getenv("OFSC_DATABASE_TIMEOUT", "300"))
    key_expiry_env = os.getenv("OFSC_KEY_EXPIRY", None)
    if key_expiry_env is not None:
        try:
            config["KEY_EXPIRY"] = int(key_expiry_env)
        except ValueError:
            print(
                f"Warning: OFSC_KEY_EXPIRY environment variable '{key_expiry_env}' is not a valid integer. Using default None."
            )
            config["KEY_EXPIRY"] = None
    else:
        config["KEY_EXPIRY"] = None
    config["RESPONSE_EXPIRY"] = int(os.getenv("OFSC_RESPONSE_EXPIRY", "5000000"))
    config["DBINTERVAL"] = int(os.getenv("OFSC_DBINTERVAL", "86400"))
    config["DAY_SECONDS"] = int(os.getenv("OFSC_DAY_SECONDS", "86400"))
    config["THREE_DAY_SECONDS"] = int(
        os.getenv("OFSC_THREE_DAY_SECONDS", str(86400 * 3))
    )
    config["PROFILE_DATA_EXPIRY"] = int(os.getenv("OFSC_PROFILE_DATA_EXPIRY", "86400"))
    config["PROFILE_DATA_EXPIRY_ASYNC"] = int(
        os.getenv("OFSC_PROFILE_DATA_EXPIRY_ASYNC", "86400")
    )
    config["MAXFILE_SEMAPHORE"] = os.getenv("MAXFILE_SEMAPHORE", None)
    if config["MAXFILE_SEMAPHORE"] is not None:
        try:
            config["MAXFILE_SEMAPHORE"] = int(config["MAXFILE_SEMAPHORE"])
        except ValueError:
            print(
                f"Warning: MAXFILE_SEMAPHORE environment variable '{os.getenv('MAXFILE_SEMAPHORE')}' is not a valid integer. Using default None."
            )
            config["MAXFILE_SEMAPHORE"] = None
    config["PATH_STR_MAX"] = int(os.getenv("PATH_STR_MAX", "200"))
    config["TABLE_STR_MAX"] = int(os.getenv("TABLE_STR_MAX", "100"))
    config["SPACE_DOWNLOAD_MESSAGE"] = os.getenv(
        "SPACE_DOWNLOAD_MESSAGE", "Skipping download because space min has been reached"
    )
    config["DOWNLOAD_THREAD_MIN"] = int(os.getenv("DOWNLOAD_THREAD_MIN", "35"))
    config["DOWNLOAD_NUM_TRIES"] = int(os.getenv("DOWNLOAD_NUM_TRIES", "3"))
    config["DOWNLOAD_NUM_TRIES_CHECK"] = int(os.getenv("DOWNLOAD_NUM_TRIES_CHECK", "3"))
    config["MAX_PROGRESS_BARS"] = int(os.getenv("MAX_PROGRESS_BARS", "60"))
    config["MIN_ADD_PROGRESS_BARS"] = int(os.getenv("MIN_ADD_PROGRESS_BARS", "40"))
    config["SHOW_DL_CHUNKS"] = os.getenv("SHOW_DL_CHUNKS", "False").lower() == "true"
    config["SHOW_DL_CHUNKS_LEVEL"] = os.getenv("SHOW_DL_CHUNKS_LEVEL", "Warning")
    config["MULTIPROGRESS_JOB_UPDATE_FREQ"] = float(
        os.getenv("MULTIPROGRESS_JOB_UPDATE_FREQ", "1.5")
    )
    config["PROGRESS_JOB_UPDATE_FREQ"] = float(
        os.getenv("PROGRESS_JOB_UPDATE_FREQ", "2.5")
    )
    config["OVERALL_MULTI_PROGRESS_THREAD_SLEEP"] = float(
        os.getenv("OVERALL_MULTI_PROGRESS_THREAD_SLEEP", "0.1")
    )
    config["JOB_MULTI_PROGRESS_THREAD_SLEEP"] = float(
        os.getenv("JOB_MULTI_PROGRESS_THREAD_SLEEP", "0.1")
    )
    config["CDM_FORCE_KEY"] = os.getenv("CDM_FORCE_KEY", "True").lower() == "true"
    config["META_FORCE_KEY"] = os.getenv("META_FORCE_KEY", "True").lower() == "true"
    config["DOWNLOAD_FORCE_KEY"] = (
        os.getenv("DOWNLOAD_FORCE_KEY", "True").lower() == "true"
    )
    config["MPD_FORCE_KEY"] = os.getenv("MPD_FORCE_KEY", "True").lower() == "true"
    config["API_FORCE_KEY"] = os.getenv("API_FORCE_KEY", "False").lower() == "true"
    config["PROFILE_FORCE_KEY"] = (
        os.getenv("PROFILE_FORCE_KEY", "False").lower() == "true"
    )
    config["VERIFY_ALL_INTEGRITY"] = os.getenv(
        "OFSC_VERIFY_ALL_INTEGRITY", "False"
    ).lower() in ("true", "1")
    config["MAX_SLEEP_DURATION_LIKE"] = float(
        os.getenv("MAX_SLEEP_DURATION_LIKE", "3.5")
    )
    config["MIN_SLEEP_DURATION_LIKE"] = float(
        os.getenv("MIN_SLEEP_DURATION_LIKE", ".9")
    )
    config["LIKE_MAX_RETRIES"] = int(os.getenv("LIKE_MAX_RETRIES", "5"))
    config["DOUBLE_TOGGLE_SLEEP_DURATION_LIKE"] = int(
        os.getenv("DOUBLE_TOGGLE_SLEEP_DURATION_LIKE", "5")
    )
    remove_unviewable_metadata_env = os.getenv("REMOVE_UNVIEWABLE_METADATA", "False")
    config["REMOVE_UNVIEWABLE_METADATA"] = remove_unviewable_metadata_env.lower() in (
        "true",
        "1",
    )
    config["QUALITY_UNKNOWN_DEFAULT"] = os.getenv("QUALITY_UNKNOWN_DEFAULT", "source")
    config["ALT_FORCE_KEY"] = os.getenv("OFSC_ALT_FORCE_KEY", "True").lower() in (
        "true",
        "1",
    )
    config["NORMAL_CHAR_SIZE_WINDOWS"] = int(os.getenv("NORMAL_CHAR_SIZE_WINDOWS", "2"))
    config["SPECIAL_CHAR_SIZE_WINDOWS"] = int(
        os.getenv("SPECIAL_CHAR_SIZE_WINDOWS", "4")
    )
    config["SPECIAL_CHAR_SIZE_UNIX"] = int(os.getenv("SPECIAL_CHAR_SIZE_UNIX", "4"))
    config["NORMAL_CHAR_SIZE_UNIX"] = int(os.getenv("NORMAL_CHAR_SIZE_UNIX", "2"))
    config["UTF"] = os.getenv("UTF", None)
    config["preferences"] = os.getenv("OFSC_PREFERENCES_FILE", "pref_config.py")
    config["configPath"] = os.getenv("OFSC_CONFIG_DIR", ".config/ofscraper")
    config["configFile"] = os.getenv("OFSC_CONFIG_FILE_NAME", "config.json")
    config["authFile"] = os.getenv("OFSC_AUTH_FILE_NAME", "auth.json")
    config["databaseFile"] = os.getenv("OFSC_DATABASE_FILE_NAME", "models.db")
    config["mainProfile"] = os.getenv("OFSC_MAIN_PROFILE_NAME", "main_profile")
    config["requestAuth"] = os.getenv(
        "OFSC_REQUEST_AUTH_FILE_NAME", "request_auth.json"
    )
    config["SKIP_FILENAME_RETRIVAL"] = os.getenv(
        "OFSC_SKIP_FILENAME_RETRIVAL", "False"
    ).lower() in ("true", "1")
    config["SKIP_MEDIADIR_RETRIVAL"] = os.getenv(
        "OFSC_SKIP_MEDIADIR_RETRIVAL", "False"
    ).lower() in ("true", "1")
    config["BATCH_TEMPFILE_CLEANUP"] = os.getenv(
        "OFSC_BATCH_TEMPFILE_CLEANUP", "False"
    ).lower() in ("true", "1")
    config["MAX_TEXT_LENGTH"] = int(os.getenv("OFSC_MAX_TEXT_LENGTH", "70"))
    config["MAX_TEXT_WORKER"] = int(os.getenv("OFSC_MAX_TEXT_WORKER", "30"))
    config["WINDOWS_MAX_PATH_BYTES"] = int(
        os.getenv("OFSC_WINDOWS_MAX_PATH_BYTES", "530")
    )
    config["MAC_MAX_PATH"] = int(os.getenv("OFSC_MAC_MAX_PATH", "255"))
    config["LINUX_MAX_FILE_NAME_BYTES"] = int(
        os.getenv("OFSC_LINUX_MAX_FILE_NAME_BYTES", "254")
    )
    config["ANON_USERAGENT"] = os.getenv(
        "OFSC_ANON_USERAGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    )
    config["MAX_TIMELINE_INDIVIDUAL_SEARCH"] = int(
        os.getenv("OFSC_MAX_TIMELINE_INDIVIDUAL_SEARCH", "10")
    )
    config["MAX_PINNED_INDIVIDUAL_SEARCH"] = int(
        os.getenv("OFSC_MAX_PINNED_INDIVIDUAL_SEARCH", "10")
    )
    config["MAX_ARCHIVED_INDIVIDUAL_SEARCH"] = int(
        os.getenv("OFSC_MAX_ARCHIVED_INDIVIDUAL_SEARCH", "10")
    )
    config["MAX_MESSAGES_INDIVIDUAL_SEARCH"] = int(
        os.getenv("OFSC_MAX_MESSAGES_INDIVIDUAL_SEARCH", "10")
    )
    config["MAX_STREAMS_INDIVIDUAL_SEARCH"] = int(
        os.getenv("OFSC_MAX_STREAMS_INDIVIDUAL_SEARCH", "10")
    )
    config["API_INDVIDIUAL_NUM_TRIES"] = int(
        os.getenv("OFSC_API_INDIVIDUAL_NUM_TRIES", "3")
    )
    config["API_PAID_NUM_TRIES"] = int(os.getenv("OFSC_API_PAID_NUM_TRIES", "8"))
    config["API_CHECK_NUM_TRIES"] = int(os.getenv("OFSC_API_CHECK_NUM_TRIES", "10"))
    config["API_NUM_TRIES"] = int(os.getenv("OFSC_API_NUM_TRIES", "10"))
    config["API_LIKE_NUM_TRIES"] = int(os.getenv("OFSC_API_LIKE_NUM_TRIES", "5"))
    config["API_MAX_AREAS"] = int(os.getenv("OFSC_API_MAX_AREAS", "2"))
    config["REASONABLE_MAX_PAGE"] = int(os.getenv("OFSC_REASONABLE_MAX_PAGE", "50"))
    config["MIN_PAGE_POST_COUNT"] = int(os.getenv("OFSC_MIN_PAGE_POST_COUNT", "50"))
    config["REASONABLE_MAX_PAGE_MESSAGES"] = int(
        os.getenv("OFSC_REASONABLE_MAX_PAGE_MESSAGES", "80")
    )
    config["API_TIMEOUT_PER_TASK"] = int(os.getenv("OFSC_API_TIMEOUT_PER_TASK", "500"))
    api_request_threadonly_env = os.getenv("OFSC_API_REQUEST_THREADONLY")
    if api_request_threadonly_env:
        config["API_REQUEST_THREADONLY"] = [
            os_name.strip() for os_name in api_request_threadonly_env.split(",")
        ]
    else:
        config["API_REQUEST_THREADONLY"] = ["Windows", "Linux", "Darwin"]
    config["API_REQ_SEM_MAX"] = int(os.getenv("OFSC_API_REQ_SEM_MAX", "12"))
    config["API_REQ_CHECK_MAX"] = int(os.getenv("OFSC_API_REQ_CHECK_MAX", "12"))
    config["CDM_TEST_TIMEOUT"] = int(os.getenv("OFSC_CDM_TEST_TIMEOUT", "30"))
    config["CDM_TIMEOUT"] = int(os.getenv("OFSC_CDM_TIMEOUT", "40"))
    config["CDM_MIN_WAIT"] = float(os.getenv("OFSC_CDM_MIN_WAIT", "1.5"))
    config["CDM_MAX_WAIT"] = float(os.getenv("OFSC_CDM_MAX_WAIT", "6"))
    config["CDM_NUM_TRIES"] = int(os.getenv("OFSC_CDM_NUM_TRIES", "8"))
    config["CDM_NUM_TRIES_CHECK"] = int(os.getenv("OFSC_CDM_NUM_TRIES_CHECK", "1"))
    config["CDM_TEST_NUM_TRIES"] = int(os.getenv("OFSC_CDM_TEST_NUM_TRIES", "2"))
    discord_total_timeout_env = os.getenv("OFSC_DISCORD_TOTAL_TIMEOUT", None)
    if discord_total_timeout_env is not None:
        try:
            config["DISCORD_TOTAL_TIMEOUT"] = int(discord_total_timeout_env)
        except ValueError:
            print(
                f"Warning: OFSC_DISCORD_TOTAL_TIMEOUT environment variable '{discord_total_timeout_env}' is not a valid integer. Using default None."
            )
            config["DISCORD_TOTAL_TIMEOUT"] = None
    else:
        config["DISCORD_TOTAL_TIMEOUT"] = None
    config["DISCORD_MIN_WAIT"] = float(os.getenv("OFSC_DISCORD_MIN_WAIT", "1"))
    config["DISCORD_MAX_WAIT"] = float(os.getenv("OFSC_DISCORD_MAX_WAIT", "5"))
    config["DISCORD_NUM_TRIES"] = int(os.getenv("OFSC_DISCORD_NUM_TRIES", "3"))
    config["GIT_MIN_WAIT"] = float(os.getenv("OFSC_GIT_MIN_WAIT", "1"))
    config["GIT_MAX_WAIT"] = float(os.getenv("OFSC_GIT_MAX_WAIT", "5"))
    config["GIT_NUM_TRIES"] = int(os.getenv("OFSC_GIT_NUM_TRIES", "3"))
    config["MPD_CONNECT_TIMEOUT"] = int(os.getenv("OFSC_MPD_CONNECT_TIMEOUT", "45"))
    mpd_total_timeout_env = os.getenv("OFSC_MPD_TOTAL_TIMEOUT", None)
    if mpd_total_timeout_env is not None:
        try:
            config["MPD_TOTAL_TIMEOUT"] = int(mpd_total_timeout_env)
        except ValueError:
            print(
                f"Warning: OFSC_MPD_TOTAL_TIMEOUT environment variable '{mpd_total_timeout_env}' is not a valid integer. Using default None."
            )
            config["MPD_TOTAL_TIMEOUT"] = None
    else:
        config["MPD_TOTAL_TIMEOUT"] = None
    config["MPD_READ_TIMEOUT"] = int(os.getenv("OFSC_MPD_READ_TIMEOUT", "200"))
    config["MPD_POOL_CONNECT_TIMEOUT"] = int(
        os.getenv("OFSC_MPD_POOL_CONNECT_TIMEOUT", "45")
    )
    config["MPD_MAX_SEMS"] = int(os.getenv("OFSC_MPD_MAX_SEMS", "10"))
    config["MPD_NUM_TRIES"] = int(os.getenv("OFSC_MPD_NUM_TRIES", "5"))
    config["MPD_SESSION_SLEEP_INIT"] = int(
        os.getenv("OFSC_MPD_SESSION_SLEEP_INIT", "45")
    )
    config["CONNECT_TIMEOUT"] = int(os.getenv("OFSC_CONNECT_TIMEOUT", "15"))
    config["POOL_CONNECT_TIMEOUT"] = int(os.getenv("OFSC_POOL_CONNECT_TIMEOUT", "15"))
    config["MAX_CONNECTIONS"] = int(os.getenv("OFSC_MAX_CONNECTIONS", "200"))
    config["API_MAX_CONNECTION"] = int(os.getenv("OFSC_API_MAX_CONNECTION", "100"))
    total_timeout_env = os.getenv("OFSC_TOTAL_TIMEOUT", None)
    if total_timeout_env is not None:
        try:
            config["TOTAL_TIMEOUT"] = int(total_timeout_env)
        except ValueError:
            print(
                f"Warning: OFSC_TOTAL_TIMEOUT environment variable '{total_timeout_env}' is not a valid integer. Using default None."
            )
            config["TOTAL_TIMEOUT"] = None
    else:
        config["TOTAL_TIMEOUT"] = None
    config["KEEP_ALIVE"] = int(os.getenv("OFSC_KEEP_ALIVE", "20"))
    config["KEEP_ALIVE_EXP"] = int(os.getenv("OFSC_KEEP_ALIVE_EXP", "10"))
    config["PROXY"] = os.getenv("OFSC_PROXY", None)
    config["PROXY_MOUNTS"] = os.getenv("OFSC_PROXY_MOUNTS", None)
    config["PROXY_AUTH"] = os.getenv("OFSC_PROXY_AUTH", None)
    config["MAX_CHUNK_SIZE"] = int(
        os.getenv("OFSC_MAX_CHUNK_SIZE", str(1024 * 1024 * 128))
    )
    config["MIN_CHUNK_SIZE"] = int(os.getenv("OFSC_MIN_CHUNK_SIZE", str(64 * 1024)))
    config["CHUNK_UPDATE_COUNT"] = int(os.getenv("OFSC_CHUNK_UPDATE_COUNT", "12"))
    config["CHUNK_SIZE_UPDATE_COUNT"] = int(
        os.getenv("OFSC_CHUNK_SIZE_UPDATE_COUNT", "15")
    )
    config["CHUNK_MEMORY_SPLIT"] = int(os.getenv("OFSC_CHUNK_MEMORY_SPLIT", "64"))
    config["CHUNK_FILE_SPLIT"] = int(os.getenv("OFSC_CHUNK_FILE_SPLIT", "64"))
    config["MAX_READ_SIZE"] = int(
        os.getenv("OFSC_MAX_READ_SIZE", str(1024 * 1024 * 16))
    )
    config["CHUNK_TIMEOUT_SEC"] = int(os.getenv("OFSC_CHUNK_TIMEOUT_SEC", "30"))
    config["REQ_SEMAPHORE_MULTI"] = int(os.getenv("OFSC_REQ_SEMAPHORE_MULTI", "5"))
    config["SCRAPE_PAID_SEMS"] = int(os.getenv("OFSC_SCRAPE_PAID_SEMS", "10"))
    config["SUBSCRIPTION_SEMS"] = int(os.getenv("OFSC_SUBSCRIPTION_SEMS", "5"))
    config["SUBSCRIPTION_PAGE_LIMIT"] = int(
        os.getenv("OFSC_SUBSCRIPTION_PAGE_LIMIT", "100")
    )
    config["LIKE_MAX_SEMS"] = int(os.getenv("OFSC_LIKE_MAX_SEMS", "12"))
    config["MAX_SEMS_BATCH_DOWNLOAD"] = int(
        os.getenv("OFSC_MAX_SEMS_BATCH_DOWNLOAD", "12")
    )
    config["MAX_SEMS_SINGLE_THREAD_DOWNLOAD"] = int(
        os.getenv("OFSC_MAX_SEMS_SINGLE_THREAD_DOWNLOAD", "50")
    )
    config["SESSION_MANAGER_SYNC_SEM_DEFAULT"] = int(
        os.getenv("OFSC_SESSION_MANAGER_SYNC_SEM_DEFAULT", "3")
    )
    config["SESSION_MANAGER_SEM_DEFAULT"] = int(
        os.getenv("OFSC_SESSION_MANAGER_SEM_DEFAULT", "10")
    )
    config["MAX_THREAD_WORKERS"] = int(os.getenv("OFSC_MAX_THREAD_WORKERS", "20"))
    config["OF_MIN_WAIT_SESSION_DEFAULT"] = float(
        os.getenv("OFSC_MIN_WAIT_SESSION_DEFAULT", "2")
    )
    config["OF_MAX_WAIT_SESSION_DEFAULT"] = float(
        os.getenv("OFSC_MAX_WAIT_SESSION_DEFAULT", "3")
    )
    config["OF_NUM_RETRIES_SESSION_DEFAULT"] = int(
        os.getenv("OFSC_NUM_RETRIES_SESSION_DEFAULT", "10")
    )
    config["OF_MIN_WAIT_API"] = float(os.getenv("OFSC_MIN_WAIT_API", "2"))
    config["OF_MAX_WAIT_API"] = float(os.getenv("OFSC_MAX_WAIT_API", "3"))
    config["OF_AUTH_MIN_WAIT"] = float(os.getenv("OFSC_AUTH_MIN_WAIT", "3"))
    config["OF_AUTH_MAX_WAIT"] = float(os.getenv("OFSC_AUTH_MAX_WAIT", "3"))
    config["DOWNLOAD_NUM_TRIES_REQ"] = int(
        os.getenv("OFSC_DOWNLOAD_NUM_TRIES_REQ", "5")
    )
    config["DOWNLOAD_NUM_TRIES_CHECK_REQ"] = int(
        os.getenv("OFSC_DOWNLOAD_NUM_TRIES_CHECK_REQ", "2")
    )
    config["AUTH_NUM_TRIES"] = int(os.getenv("OFSC_AUTH_NUM_TRIES", "3"))
    config["MESSAGE_SLEEP_DEFAULT"] = int(os.getenv("OFSC_MESSAGE_SLEEP_DEFAULT", "0"))
    config["SESSION_SLEEP_INIT"] = float(os.getenv("OFSC_SESSION_SLEEP_INIT", "2.5"))
    config["SESSION_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_SESSION_SLEEP_INCREASE_TIME_DIFF", "30")
    )
    config["SESSION_SLEEP_MAX"] = float(os.getenv("OFSC_SESSION_SLEEP_MAX", "180"))
    config["SESSION_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_SESSION_SLEEP_INCREASE_FACTOR", "2.0")
    )
    config["SESSION_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_SESSION_SLEEP_DECAY_THRESHOLD", "120")
    )
    config["SESSION_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_SESSION_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["SESSION_MIN_SLEEP"] = float(os.getenv("OFSC_SESSION_MIN_SLEEP", "0.5"))
    config["SESSION_403_SLEEP_INIT"] = float(
        os.getenv("OFSC_SESSION_403_SLEEP_INIT", "15")
    )
    config["SESSION_403_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_SESSION_403_SLEEP_INCREASE_TIME_DIFF", "60")
    )
    config["SESSION_403_SLEEP_MAX"] = float(
        os.getenv("OFSC_SESSION_403_SLEEP_MAX", "180")
    )
    config["SESSION_403_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_SESSION_403_SLEEP_INCREASE_FACTOR", "1.5")
    )
    config["SESSION_403_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_SESSION_403_SLEEP_DECAY_THRESHOLD", "65")
    )
    config["SESSION_403_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_SESSION_403_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["SESSION_403_MIN_SLEEP"] = float(
        os.getenv("OFSC_SESSION_403_MIN_SLEEP", "0")
    )
    config["DOWNLOAD_SESSION_SLEEP_INIT"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_SLEEP_INIT", "0")
    )
    config["DOWNLOAD_SESSION_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_SLEEP_INCREASE_TIME_DIFF", "30")
    )
    config["DOWNLOAD_SESSION_SLEEP_MAX"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_SLEEP_MAX", "180")
    )
    config["DOWNLOAD_SESSION_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_SLEEP_INCREASE_FACTOR", "2.0")
    )
    config["DOWNLOAD_SESSION_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_SLEEP_DECAY_THRESHOLD", "120")
    )
    config["DOWNLOAD_SESSION_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["DOWNLOAD_SESSION_MIN_SLEEP"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_MIN_SLEEP", "0")
    )
    config["DOWNLOAD_SESSION_403_SLEEP_INIT"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_403_SLEEP_INIT", "15")
    )
    config["DOWNLOAD_SESSION_403_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_403_SLEEP_INCREASE_TIME_DIFF", "80")
    )
    config["DOWNLOAD_SESSION_403_SLEEP_MAX"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_403_SLEEP_MAX", "180")
    )
    config["DOWNLOAD_SESSION_403_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_403_SLEEP_INCREASE_FACTOR", "1.5")
    )
    config["DOWNLOAD_SESSION_403_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_403_SLEEP_DECAY_THRESHOLD", "70")
    )
    config["DOWNLOAD_SESSION_403_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_403_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["DOWNLOAD_SESSION_403_MIN_SLEEP"] = float(
        os.getenv("OFSC_DOWNLOAD_SESSION_403_MIN_SLEEP", "0")
    )
    config["CDM_SESSION_SLEEP_INIT"] = float(
        os.getenv("OFSC_CDM_SESSION_SLEEP_INIT", "0")
    )
    config["CDM_SESSION_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_CDM_SESSION_SLEEP_INCREASE_TIME_DIFF", "30")
    )
    config["CDM_SESSION_SLEEP_MAX"] = float(
        os.getenv("OFSC_CDM_SESSION_SLEEP_MAX", "180")
    )
    config["CDM_SESSION_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_CDM_SESSION_SLEEP_INCREASE_FACTOR", "2.0")
    )
    config["CDM_SESSION_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_CDM_SESSION_SLEEP_DECAY_THRESHOLD", "120")
    )
    config["CDM_SESSION_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_CDM_SESSION_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["CDM_SESSION_MIN_SLEEP"] = float(
        os.getenv("OFSC_CDM_SESSION_MIN_SLEEP", "1.0")
    )
    config["CDM_SESSION_403_SLEEP_INIT"] = float(
        os.getenv("OFSC_CDM_SESSION_403_SLEEP_INIT", "8")
    )
    config["CDM_SESSION_403_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_CDM_SESSION_403_SLEEP_INCREASE_TIME_DIFF", "60")
    )
    config["CDM_SESSION_403_SLEEP_MAX"] = float(
        os.getenv("OFSC_CDM_SESSION_403_SLEEP_MAX", "180")
    )
    config["CDM_SESSION_403_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_CDM_SESSION_403_SLEEP_INCREASE_FACTOR", "1.5")
    )
    config["CDM_SESSION_403_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_CDM_SESSION_403_SLEEP_DECAY_THRESHOLD", "65")
    )
    config["CDM_SESSION_403_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_CDM_SESSION_403_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["CDM_SESSION_403_MIN_SLEEP"] = float(
        os.getenv("OFSC_CDM_SESSION_403_MIN_SLEEP", "0")
    )
    config["LIKE_SESSION_SLEEP_INIT"] = float(
        os.getenv("OFSC_LIKE_SESSION_SLEEP_INIT", "8")
    )
    config["LIKE_SESSION_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_LIKE_SESSION_SLEEP_INCREASE_TIME_DIFF", "4")
    )
    config["LIKE_SESSION_SLEEP_MAX"] = float(
        os.getenv("OFSC_LIKE_SESSION_SLEEP_MAX", "120")
    )
    config["LIKE_SESSION_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_LIKE_SESSION_SLEEP_INCREASE_FACTOR", "2.0")
    )
    config["LIKE_SESSION_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_LIKE_SESSION_SLEEP_DECAY_THRESHOLD", "120")
    )
    config["LIKE_SESSION_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_LIKE_SESSION_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["LIKE_SESSION_MIN_SLEEP"] = float(
        os.getenv("OFSC_LIKE_SESSION_MIN_SLEEP", "0")
    )
    config["LIKE_SESSION_403_SLEEP_INIT"] = float(
        os.getenv("OFSC_LIKE_SESSION_403_SLEEP_INIT", "8")
    )
    config["LIKE_SESSION_403_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_LIKE_SESSION_403_SLEEP_INCREASE_TIME_DIFF", "4")
    )
    config["LIKE_SESSION_403_SLEEP_MAX"] = float(
        os.getenv("OFSC_LIKE_SESSION_403_SLEEP_MAX", "120")
    )
    config["LIKE_SESSION_403_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_LIKE_SESSION_403_SLEEP_INCREASE_FACTOR", "1.5")
    )
    config["LIKE_SESSION_403_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_LIKE_SESSION_403_SLEEP_DECAY_THRESHOLD", "65")
    )
    config["LIKE_SESSION_403_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_LIKE_SESSION_403_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["LIKE_SESSION_403_MIN_SLEEP"] = float(
        os.getenv("OFSC_LIKE_SESSION_403_MIN_SLEEP", "0")
    )
    config["METADATA_SESSION_SLEEP_INIT"] = float(
        os.getenv("OFSC_METADATA_SESSION_SLEEP_INIT", "4")
    )
    config["METADATA_SESSION_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_METADATA_SESSION_SLEEP_INCREASE_TIME_DIFF", "35")
    )
    config["METADATA_SESSION_SLEEP_MAX"] = float(
        os.getenv("OFSC_METADATA_SESSION_SLEEP_MAX", "60")
    )
    config["METADATA_SESSION_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_METADATA_SESSION_SLEEP_INCREASE_FACTOR", "1.5")
    )
    config["METADATA_SESSION_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_METADATA_SESSION_SLEEP_DECAY_THRESHOLD", "35")
    )
    config["METADATA_SESSION_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_METADATA_SESSION_SLEEP_DECAY_FACTOR", "2")
    )
    config["METADATA_SESSION_MIN_SLEEP"] = float(
        os.getenv("OFSC_METADATA_SESSION_MIN_SLEEP", "0.5")
    )
    config["METADATA_SESSION_403_SLEEP_INIT"] = float(
        os.getenv("OFSC_METADATA_SESSION_403_SLEEP_INIT", "4")
    )
    config["METADATA_SESSION_403_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_METADATA_SESSION_403_SLEEP_INCREASE_TIME_DIFF", "35")
    )
    config["METADATA_SESSION_403_SLEEP_MAX"] = float(
        os.getenv("OFSC_METADATA_SESSION_403_SLEEP_MAX", "60")
    )
    config["METADATA_SESSION_403_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_METADATA_SESSION_403_SLEEP_INCREASE_FACTOR", "1.5")
    )
    config["METADATA_SESSION_403_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_METADATA_SESSION_403_SLEEP_DECAY_THRESHOLD", "30")
    )
    config["METADATA_SESSION_403_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_METADATA_SESSION_403_SLEEP_DECAY_FACTOR", "2")
    )
    config["METADATA_SESSION_403_MIN_SLEEP"] = float(
        os.getenv("OFSC_METADATA_SESSION_403_MIN_SLEEP", "2")
    )
    config["DISCORD_SESSION_SLEEP_INIT"] = float(
        os.getenv("OFSC_DISCORD_SESSION_SLEEP_INIT", "5")
    )
    config["DISCORD_SESSION_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_DISCORD_SESSION_SLEEP_INCREASE_TIME_DIFF", "30")
    )
    config["DISCORD_SESSION_SLEEP_MAX"] = float(
        os.getenv("OFSC_DISCORD_SESSION_SLEEP_MAX", "60")
    )
    config["DISCORD_SESSION_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_DISCORD_SESSION_SLEEP_INCREASE_FACTOR", "2.0")
    )
    config["DISCORD_SESSION_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_DISCORD_SESSION_SLEEP_DECAY_THRESHOLD", "120")
    )
    config["DISCORD_SESSION_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_DISCORD_SESSION_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["DISCORD_SESSION_MIN_SLEEP"] = float(
        os.getenv("OFSC_DISCORD_SESSION_MIN_SLEEP", "2")
    )
    config["DISCORD_SESSION_403_SLEEP_INIT"] = float(
        os.getenv("OFSC_DISCORD_SESSION_403_SLEEP_INIT", "4")
    )
    config["DISCORD_SESSION_403_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_DISCORD_SESSION_403_SLEEP_INCREASE_TIME_DIFF", "30")
    )
    config["DISCORD_SESSION_403_SLEEP_MAX"] = float(
        os.getenv("OFSC_DISCORD_SESSION_403_SLEEP_MAX", "300")
    )
    config["DISCORD_SESSION_403_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_DISCORD_SESSION_403_SLEEP_INCREASE_FACTOR", "4")
    )
    config["DISCORD_SESSION_403_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_DISCORD_SESSION_403_SLEEP_DECAY_THRESHOLD", "60")
    )
    config["DISCORD_SESSION_403_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_DISCORD_SESSION_403_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["DISCORD_SESSION_403_MIN_SLEEP"] = float(
        os.getenv("OFSC_DISCORD_SESSION_403_MIN_SLEEP", "30")
    )
    config["SUBSCRIPTION_SESSION_SLEEP_INIT"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_SLEEP_INIT", "1")
    )
    config["SUBSCRIPTION_SESSION_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_SLEEP_INCREASE_TIME_DIFF", "30")
    )
    config["SUBSCRIPTION_SESSION_SLEEP_MAX"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_SLEEP_MAX", "180")
    )
    config["SUBSCRIPTION_SESSION_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_SLEEP_INCREASE_FACTOR", "2.0")
    )
    config["SUBSCRIPTION_SESSION_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_SLEEP_DECAY_THRESHOLD", "120")
    )
    config["SUBSCRIPTION_SESSION_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["SUBSCRIPTION_SESSION_MIN_SLEEP"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_MIN_SLEEP", ".5")
    )
    config["SUBSCRIPTION_SESSION_403_SLEEP_INIT"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_403_SLEEP_INIT", "2")
    )
    config["SUBSCRIPTION_SESSION_403_SLEEP_INCREASE_TIME_DIFF"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_403_SLEEP_INCREASE_TIME_DIFF", "60")
    )
    config["SUBSCRIPTION_SESSION_403_SLEEP_MAX"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_403_SLEEP_MAX", "180")
    )
    config["SUBSCRIPTION_SESSION_403_SLEEP_INCREASE_FACTOR"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_403_SLEEP_INCREASE_FACTOR", "1.5")
    )
    config["SUBSCRIPTION_SESSION_403_SLEEP_DECAY_THRESHOLD"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_403_SLEEP_DECAY_THRESHOLD", "65")
    )
    config["SUBSCRIPTION_SESSION_403_SLEEP_DECAY_FACTOR"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_403_SLEEP_DECAY_FACTOR", "1.5")
    )
    config["SUBSCRIPTION_SESSION_403_MIN_SLEEP"] = float(
        os.getenv("OFSC_SUBSCRIPTION_SESSION_403_MIN_SLEEP", "0")
    )
    config["AUTH_WARNING_TIMEOUT"] = float(
        os.getenv("OFSC_AUTH_WARNING_TIMEOUT", "1800")
    )
    config["CDRM"] = os.getenv("OFSC_CDRM_URL", "https://cdrm-project.com/api/decrypt")
    bad_url_host_env = os.getenv("OFSC_BAD_URL_HOSTS")
    if bad_url_host_env:
        config["BAD_URL_HOST"] = {host.strip() for host in bad_url_host_env.split(",")}
    else:
        config["BAD_URL_HOST"] = {
            ".*\\.upload.onlyfans.com",
            "of2transcoder.s3-accelerate.amazonaws.com",
            ".*\\.convert.onlyfans.com",
        }
    config["initEP"] = os.getenv(
        "OFSC_API_INIT_EP", "https://onlyfans.com/api2/v2/init"
    )
    config["LICENCE_URL"] = os.getenv(
        "OFSC_API_LICENCE_URL",
        "https://onlyfans.com/api2/v2/users/media/{}/drm/{}/{}?type=widevine",
    )
    config["INDIVIDUAL_TIMELINE"] = os.getenv(
        "OFSC_API_INDIVIDUAL_TIMELINE",
        "https://onlyfans.com/api2/v2/posts/{}?skip_users=all",
    )
    config["meEP"] = os.getenv(
        "OFSC_API_ME_EP", "https://onlyfans.com/api2/v2/users/me"
    )
    config["subscriptionsEP"] = os.getenv(
        "OFSC_API_SUBSCRIPTIONS_EP",
        "https://onlyfans.com/api2/v2/subscriptions/subscribes?offset={}&limit=10&type=all&format=infinite",
    )
    config["subscriptionsActiveEP"] = os.getenv(
        "OFSC_API_SUBSCRIPTIONS_ACTIVE_EP",
        "https://onlyfans.com/api2/v2/subscriptions/subscribes?offset={}&limit=100&type=active&format=infinite",
    )
    config["subscriptionsExpiredEP"] = os.getenv(
        "OFSC_API_SUBSCRIPTIONS_EXPIRED_EP",
        "https://onlyfans.com/api2/v2/subscriptions/subscribes?offset={}&limit=100&type=expired&format=infinite",
    )
    config["subscribeCountEP"] = os.getenv(
        "OFSC_API_SUBSCRIBE_COUNT_EP",
        "https://onlyfans.com/api2/v2/subscriptions/count/all",
    )
    config["sortSubscriptions"] = os.getenv(
        "OFSC_API_SORT_SUBSCRIPTIONS",
        "https://onlyfans.com/api2/v2/lists/following/sort",
    )
    config["profileEP"] = os.getenv(
        "OFSC_API_PROFILE_EP", "https://onlyfans.com/api2/v2/users/{}"
    )
    config["timelineEP"] = os.getenv(
        "OFSC_API_TIMELINE_EP",
        "https://onlyfans.com/api2/v2/users/{}/posts?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&pinned=0&format=infinite",
    )
    config["timelineNextEP"] = os.getenv(
        "OFSC_API_TIMELINE_NEXT_EP",
        "https://onlyfans.com/api2/v2/users/{}/posts?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&afterPublishTime={}&pinned=0&format=infinite",
    )
    config["timelinePinnedEP"] = os.getenv(
        "OFSC_API_TIMELINE_PINNED_EP",
        "https://onlyfans.com/api2/v2/users/{}/posts?skip_users=all&pinned=1&counters={}&format=infinite",
    )
    config["streamsEP"] = os.getenv(
        "OFSC_API_STREAMS_EP",
        "https://onlyfans.com/api2/v2/users/{}/posts/streams?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&format=infinite",
    )
    config["streamsNextEP"] = os.getenv(
        "OFSC_API_STREAMS_NEXT_EP",
        "https://onlyfans.com/api2/v2/users/{}/posts/streams?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&afterPublishTime={}&format=infinite",
    )
    config["archivedEP"] = os.getenv(
        "OFSC_API_ARCHIVED_EP",
        "https://onlyfans.com/api2/v2/users/{}/posts/archived?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&format=infinite",
    )
    config["archivedNextEP"] = os.getenv(
        "OFSC_API_ARCHIVED_NEXT_EP",
        "https://onlyfans.com/api2/v2/users/{}/posts/archived?limit=100&order=publish_date_asc&skip_users=all&skip_users_dups=1&afterPublishTime={}&format=infinite",
    )
    config["highlightsWithStoriesEP"] = os.getenv(
        "OFSC_API_HIGHLIGHTS_WITH_STORIES_EP",
        "https://onlyfans.com/api2/v2/users/{}/stories/highlights?limit=5&offset={}&unf=1",
    )
    config["highlightsWithAStoryEP"] = os.getenv(
        "OFSC_API_HIGHLIGHTS_WITH_A_STORY_EP",
        "https://onlyfans.com/api2/v2/users/{}/stories?unf=1",
    )
    config["storyEP"] = os.getenv(
        "OFSC_API_STORY_EP", "https://onlyfans.com/api2/v2/stories/highlights/{}?unf=1"
    )
    config["messagesEP"] = os.getenv(
        "OFSC_API_MESSAGES_EP",
        "https://onlyfans.com/api2/v2/chats/{}/messages?limit=100&order=desc&skip_users=all&skip_users_dups=1",
    )
    config["messagesNextEP"] = os.getenv(
        "OFSC_API_MESSAGES_NEXT_EP",
        "https://onlyfans.com/api2/v2/chats/{}/messages?limit=100&id={}&order=desc&skip_users=all&skip_users_dups=1",
    )
    config["favoriteEP"] = os.getenv(
        "OFSC_API_FAVORITE_EP", "https://onlyfans.com/api2/v2/posts/{}/favorites/{}"
    )
    config["postURL"] = os.getenv("OFSC_POST_URL", "https://onlyfans.com/{}/{}")
    config["subscribeEP"] = os.getenv(
        "OFSC_API_SUBSCRIBE_EP", "https://onlyfans.com/api2/v2/users/{}/subscribe"
    )
    config["SUBSCRIBE_NUM_TRIES"] = int(os.getenv("SUBSCRIBE_NUM_TRIES", "3"))
    config["donateEP"] = os.getenv(
        "OFSC_DONATE_EP", "https://www.buymeacoffee.com/excludedBittern"
    )
    config["purchased_contentEP"] = os.getenv(
        "OFSC_PURCHASED_CONTENT_EP",
        "https://onlyfans.com/api2/v2/posts/paid/all?limit=100&skip_users=all&format=infinite&offset={}&author={}",
    )
    config["purchased_contentALL"] = os.getenv(
        "OFSC_PURCHASED_CONTENT_ALL_EP",
        "https://onlyfans.com/api2/v2/posts/paid/all?limit=100&skip_users=all&format=infinite&offset={}",
    )
    config["highlightSPECIFIC"] = os.getenv(
        "OFSC_HIGHLIGHT_SPECIFIC_EP",
        "https://onlyfans.com/api2/v2/stories/highlights/{}",
    )
    config["storiesSPECIFIC"] = os.getenv(
        "OFSC_STORIES_SPECIFIC_EP", "https://onlyfans.com/api2/v2/stories/{}"
    )
    config["messageSPECIFIC"] = os.getenv(
        "OFSC_MESSAGE_SPECIFIC_EP",
        "https://onlyfans.com/api2/v2/chats/{}/messages?limit=10&order=desc&skip_users=all&firstId={}",
    )
    config["messageTableSPECIFIC"] = os.getenv(
        "OFSC_MESSAGE_TABLE_SPECIFIC_URL", "https://onlyfans.com/my/chats/{}/?id={}"
    )
    config["labelsEP"] = os.getenv(
        "OFSC_LABELS_EP",
        "https://onlyfans.com/api2/v2/users/{}/labels?limit=100&offset={}&order=desc&non-empty=1",
    )
    config["labelledPostsEP"] = os.getenv(
        "OFSC_LABELLED_POSTS_EP",
        "https://onlyfans.com/api2/v2/users/{}/posts?limit=100&offset={}&order=publish_date_desc&skip_users=all&counters=0&format=infinite&label={}",
    )
    config["listEP"] = os.getenv(
        "OFSC_LIST_EP",
        "https://onlyfans.com/api2/v2/lists?offset={}&skip_users=all&limit=100&format=infinite",
    )
    config["listusersEP"] = os.getenv(
        "OFSC_LIST_USERS_EP",
        "https://onlyfans.com/api2/v2/lists/{}/users?offset={}&limit=100&format=infinite",
    )
    config["XAGLER_URL"] = os.getenv(
        "OF_XAGLER_URL",
        "https://raw.githubusercontent.com/xagler/dynamic-rules/main/onlyfans.json",
    )
    config["RAFA_URL"] = os.getenv(
        "OF_RAFA_URL",
        "https://raw.githubusercontent.com/rafa-9/dynamic-rules/main/rules.json",
    )
    config["DIGITALCRIMINALS"] = os.getenv(
        "OF_DIGITALCRIMINALS_URL",
        "https://raw.githubusercontent.com/DATAHOARDERS/dynamic-rules/main/onlyfans.json",
    )
    config["DATAWHORES_URL"] = os.getenv(
        "OF_DATAWHORES_URL",
        "https://raw.githubusercontent.com/datawhores/onlyfans-dynamic-rules/main/dynamicRules.json",
    )
    config["DEVIINT_URL"] = os.getenv(
        "OF_DEVIINT_URL",
        "https://raw.githubusercontent.com/deviint/onlyfans-dynamic-rules/main/dynamicRules.json",
    )
    config["RILEY_URL"] = os.getenv(
        "OF_RILEY_URL",
        "https://raw.githubusercontent.com/riley-access-labs/onlyfans-dynamic-rules-1/refs/heads/main/dynamicRules.json",
    )
    config["DYNAMIC_GENERIC_URL"] = os.getenv("OF_DYNAMIC_GENERIC_URL", None)
    return config
