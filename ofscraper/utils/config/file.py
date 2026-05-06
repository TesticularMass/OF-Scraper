import json
import logging
import pathlib
import re

import ofscraper.utils.config.schema as schema
import ofscraper.utils.console as console_
import ofscraper.utils.paths.common as common_paths

log = logging.getLogger("shared")


def make_config(config=False):
    config = schema.get_current_config_schema(config=config)
    if isinstance(config, str):
        config = json_loads(config)

    p = pathlib.Path(common_paths.get_config_path())
    if not p.parent.is_dir():
        p.parent.mkdir(parents=True, exist_ok=True)

    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(config, indent=4))
    console_.get_shared_console().print(f"config file created at {p}")


def make_config_original():
    make_config(config=False)


def open_config():
    import ofscraper.utils.config.utils.context as config_context

    with config_context.config_context():
        configText = config_string()
        config = json_loads(configText)
        if config.get("config"):
            return config.get("config")
        return config


def config_string():
    p = pathlib.Path(common_paths.get_config_path())
    if not p.exists():
        raise FileNotFoundError(f"Config file not found at {p}")
    with open(p, "r", encoding="utf-8") as f:
        configText = f.read()
    return configText


def write_config(updated_config):
    if isinstance(updated_config, str):
        updated_config = json_loads(updated_config)
    if updated_config.get("config"):
        updated_config = updated_config["config"]
    p = common_paths.get_config_path()
    if not p.parent.is_dir():
        p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(updated_config, indent=4))


def auto_update_config(config: dict) -> dict:
    log.info("Auto updating config...")
    schema_defaults = schema.get_current_config_schema(config)
    if isinstance(config, dict) and config.get("config"):
        existing = config["config"]
    elif isinstance(config, dict):
        existing = config
    else:
        existing = {}
    merged = dict(existing)
    for key, default_value in schema_defaults.items():
        if key not in merged:
            merged[key] = default_value
        elif isinstance(default_value, dict) and isinstance(merged.get(key), dict):
            for sub_key, sub_default in default_value.items():
                if sub_key not in merged[key]:
                    merged[key][sub_key] = sub_default
    write_config(merged)
    return merged


def json_loads(configText):
    try:
        config = json.loads(configText)
    except json.JSONDecodeError:
        # Only fix Windows path backslashes, not JSON escape sequences
        configText = re.sub(r'(?<=[A-Za-z]):\\', ':/', configText)
        configText = re.sub(r'\\\\', '/', configText)
        try:
            config = json.loads(configText)
        except json.JSONDecodeError:
            config = {}
    return config
