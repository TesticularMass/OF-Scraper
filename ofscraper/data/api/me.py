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

import logging
import traceback

import ofscraper.managers.manager as manager
import ofscraper.utils.of_env.of_env as of_env
import ofscraper.utils.logs.utils.sensitive as sensitive

log = logging.getLogger("shared")


def scrape_user():
    with manager.Manager.session.get_ofsession() as c:
        return _scraper_user_helper(c)


def _scraper_user_helper(c):
    try:
        with c.requests(of_env.getattr("meEP")) as r:
            data = r.json_()
            if data["isAuth"]:
                sensitive.add_sensitive_pattern(data["id"], "userid")
                # Register each username/name variant separately so re.escape
                # works correctly on each literal string
                for variant in [data.get('username')]:
                    if variant and variant.strip():
                        sensitive.add_sensitive_pattern(variant.strip(), 'username')
                for variant in [data.get('name')]:
                    if variant and variant.strip():
                        sensitive.add_sensitive_pattern(variant.strip(), 'name')
    except Exception as E:
        log.traceback_(E)
        log.traceback_(traceback.format_exc())
        raise E
    return data


def parse_subscriber_count():
    with manager.Manager.session.get_ofsession() as c:
        try:
            with c.requests(of_env.getattr("subscribeCountEP")) as r:
                data = r.json_()
                return (
                    data["subscriptions"]["active"],
                    data["subscriptions"]["expired"],
                )

        except Exception as E:
            log.traceback_(E)
            log.traceback_(traceback.format_exc())
            raise E
