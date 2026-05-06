import logging

import ofscraper.data.api.init as init
import ofscraper.utils.auth.file as auth_file
import ofscraper.utils.auth.make as make
import ofscraper.utils.console as console
import ofscraper.utils.settings as settings


log = logging.getLogger("shared")


def check_auth():
    status = None
    max_retries = 5
    attempts = 0
    log.info("checking auth status")
    while status != "UP":
        attempts += 1
        status = init.getstatus()
        if status != "UP":
            log.info("Auth Failed")
            if attempts >= max_retries:
                log.error(f"Auth check failed after {max_retries} attempts; giving up")
                return
            # In GUI mode skip interactive prompts; the GUI auth dialog handles re-auth
            if getattr(settings.get_args(), "gui", False):
                log.debug("GUI mode: skipping interactive auth prompt on auth failure")
                return
            make.make_auth(auth=auth_file.read_auth())
        else:
            break
