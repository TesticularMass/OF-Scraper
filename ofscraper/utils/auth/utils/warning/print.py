import json
import textwrap

import ofscraper.utils.auth.request as auth_requests
import ofscraper.utils.console as console
import ofscraper.utils.of_env.of_env as of_env
import ofscraper.utils.settings as settings

# Session secrets; showing them in full would leak the login if the output is shared.
SECRET_KEYS = {"sess", "x-bc", "auth_uid", "auth_uid_"}


def mask_secret(value):
    text = str(value or "")
    if len(text) <= 8:
        return "*" * len(text)
    return f"{'*' * 8}{text[-4:]}"


def print_auth_warning(auth=None):
    auth = auth or auth_requests.auth_file.read_auth()
    auth.update({"app-token": of_env.getattr("APP_TOKEN")})
    shown = {
        key: mask_secret(value) if key in SECRET_KEYS else value
        for key, value in auth.items()
    }

    console.get_console().print(
        textwrap.dedent(
            """
        [bold red]Secret values are masked; only their last 4 characters are shown[/bold red]
        """
        )
    )
    console.get_console().print_json(json.dumps(shown))
    console.get_console().print(
        f"[bold] Dynamic Rule: {settings.get_settings().dynamic_rules}"
    )
    console.get_console().print(
        textwrap.dedent(
            """
        ==============================================================
        Double check to make sure the [bold blue]\\[x-bc,user-agent][/bold blue] info is correct

        Double check to make sure the [bold blue]\\[sess, auth_id][/bold blue] info is correct
                        
        If 2fa is enabled double check that [bold blue]\\[auth_uid_][/bold blue] is set and not the same as auth_id

        Double check to make sure [bold blue]dynamic rule[/bold blue] is as desired
        ================================================
        """
        )
    )
