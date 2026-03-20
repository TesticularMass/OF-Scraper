import ofscraper.utils.settings as settings


def low_output():
    return (
        settings.get_args().output_level in {"OFF", "LOW", "PROMPT"}
        or settings.get_args().no_rich
    )
