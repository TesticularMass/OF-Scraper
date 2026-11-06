import logging
import os
import platform
import sys
import traceback

import ofscraper.main.open.run as run
import ofscraper.utils.config.config as config_
import ofscraper.utils.dates as dates
import ofscraper.utils.logs.logger as logger
import ofscraper.utils.paths.manage as paths_manage
import ofscraper.utils.system.system as system
import ofscraper.utils.settings as settings
import ofscraper.utils.context.exit as exit_context


def main():
    # Install SIGTERM handler early so containers (PID 1) shut down cleanly
    exit_context.sigterm_as_keyboard_interrupt()
    try:
        systemSet()
        settings_loader()
        setdate()
        readConfig()
        setLogger()
        make_folder()
        run.main()
    except Exception as E:
        try:
            logging.getLogger("shared").debug(traceback.format_exc())
            logging.getLogger("shared").debug(E)
        except Exception:
            pass
        print(f"Fatal error: {E}", file=sys.stderr)
        raise SystemExit(1)


def settings_loader():
    settings.get_settings()


def setdate():
    dates.resetLogDate()


def setLogger():
    logger.get_shared_logger()
    paths_manage.cleanup_logs()


def systemSet():
    system.set_terminal_blocking()
    system.setName()
    if platform.system() == "Windows":
        os.system("color")


def readConfig():
    config_.read_config()


def make_folder():
    paths_manage.make_folders()
