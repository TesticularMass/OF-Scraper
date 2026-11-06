import json
import pathlib
import sys
from contextlib import contextmanager

import ofscraper.utils.config.file as config_file
import ofscraper.utils.paths.common as common_paths

_MAX_INTERACTIVE_ATTEMPTS = 3


@contextmanager
def config_context():
    attempts = 0
    while True:
        try:
            p = pathlib.Path(common_paths.get_config_path())
            with open(p, "r") as f:
                json.load(f)
        except FileNotFoundError:
            attempts += 1
            if attempts > _MAX_INTERACTIVE_ATTEMPTS:
                raise RuntimeError(
                    f"config.json could not be created at {common_paths.get_config_path()}"
                )
            config_file.make_config()
            continue
        except json.JSONDecodeError as e:
            attempts += 1
            if not sys.stdin.isatty() or attempts > _MAX_INTERACTIVE_ATTEMPTS:
                raise RuntimeError(
                    f"config.json is invalid JSON (attempt {attempts}): {e}. "
                    f"Fix or delete {common_paths.get_config_path()}"
                ) from e
            try:
                import ofscraper.prompts.prompts as prompts
                print("Your config.json has a syntax error")
                import traceback
                print(traceback.format_exc())
                print(f"{e}\n\n")
                config_prompt = prompts.reset_config_prompt()
                if config_prompt == "manual":
                    configStr = prompts.manual_config_prompt(
                        config_file.config_string()
                    )
                    config_file.write_config(configStr)
                    config_file.open_config()
                elif config_prompt == "reset":
                    config_file.make_config_original()
            except (EOFError, ValueError, KeyboardInterrupt):
                raise RuntimeError(
                    f"config.json is invalid JSON and cannot be fixed interactively: {e}. "
                    f"Fix or delete {common_paths.get_config_path()}"
                ) from e
            except Exception as e:
                attempts += 1
                if attempts > _MAX_INTERACTIVE_ATTEMPTS:
                    raise RuntimeError(
                        f"config.json is invalid and could not be repaired: {e}"
                    ) from e
            continue
        yield
        break
