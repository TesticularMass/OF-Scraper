import json
import logging
import os
import pathlib
import re

import ofscraper.utils.config.schema as schema
import ofscraper.utils.console as console_
import ofscraper.utils.paths.common as common_paths

console = console_.get_shared_console()
log = logging.getLogger("shared")


def _atomic_write(p, data_str):
    """Write data_str to path p atomically via temp+replace, with fsync."""
    p = pathlib.Path(p)
    if not p.parent.is_dir():
        p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        f.write(data_str)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(tmp, 0o600)
    os.replace(str(tmp), str(p))


def make_config(config=False):
    config = schema.get_current_config_schema(config=config)
    if isinstance(config, str):
        config = json_loads(config)

    p = pathlib.Path(common_paths.get_config_path())
    _atomic_write(p, json.dumps(config, indent=4))
    console.print(f"config file created at {p}")


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
    with open(p, "r") as f:
        configText = f.read()
    return configText


def write_config(updated_config):
    if isinstance(updated_config, str):
        updated_config = json_loads(updated_config)
    if updated_config.get("config"):
        updated_config = updated_config["config"]
    p = common_paths.get_config_path()
    _atomic_write(p, json.dumps(updated_config, indent=4))


def auto_update_config(config: dict) -> dict:
    """Merge schema defaults into the existing config, preserving unknown user keys."""
    log.info("Auto updating config...")
    new_config = schema.get_current_config_schema(config)
    merged = _deep_merge(config, new_config)
    write_config(merged)
    return merged


def _deep_merge(existing, schema_defaults):
    """Recursively merge schema_defaults into existing, keeping unknown keys from existing."""
    if not isinstance(existing, dict) or not isinstance(schema_defaults, dict):
        return schema_defaults
    result = dict(existing)
    for key, schema_val in schema_defaults.items():
        if key in result and isinstance(result[key], dict) and isinstance(schema_val, dict):
            result[key] = _deep_merge(result[key], schema_val)
        else:
            # Schema value takes precedence for known keys (adds missing defaults)
            if key not in result:
                result[key] = schema_val
    return result


def json_loads(configText):
    try:
        config = json.loads(configText)
    except json.JSONDecodeError:
        configText = re.sub(r"\\+", "/", configText)
        config = json.loads(configText)
    return config
