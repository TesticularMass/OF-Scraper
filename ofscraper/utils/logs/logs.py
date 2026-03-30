import logging
import time
import platform
import ssl
import sys

import certifi

import ofscraper.utils.config.file as config_file
import ofscraper.utils.console as console
import ofscraper.utils.paths.common as common_paths
import ofscraper.utils.settings as settings
import ofscraper.utils.system.system as system
from ofscraper.__version__ import __version__


def printStartValues():
    print_system_log()
    print_args()
    print_config()
    time.sleep(3)


def printEndValues():
    print_system_log()


def print_system_log():
    log = logging.getLogger("shared")
    log.info(f"Log Level: {settings.get_settings().log_level}")
    log.info(f"version: {__version__}")
    log.debug(platform.platform())
    log.info(f"config path: {str(common_paths.get_config_path())}")
    log.info(f"profile path: {str(common_paths.get_profile_path())}")
    log.info(f"log folder: {str(common_paths.get_config_home()/'logging')}")
    log.debug(f"ssl {ssl.get_default_verify_paths()}")
    log.debug(f"python version {platform.python_version()}")
    log.debug(f"certifi {certifi.where()}")
    log.debug(f"number of threads available on system {system.getcpu_count()}")


def print_args():
    args = settings.get_args()
    log = logging.getLogger("shared")
    log.debug(args)
    log.debug(f"sys argv:{sys.argv[1:]}") if len(sys.argv) > 1 else None


def print_config():
    log = logging.getLogger("shared")
    log.debug(config_file.open_config())


def discord_warning():
    if settings.get_settings().discord_level == "DEBUG":
        console.get_shared_console().print(
            "[bold red]Warning Discord with DEBUG is not recommended\nAs processing messages is much slower compared to other[/bold red]"
        )
