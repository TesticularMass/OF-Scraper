import io

from rich.console import Console

from ofscraper.utils.console import replace_unencodable_output


def test_unencodable_output_is_replaced_not_raised():
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    replace_unencodable_output([stream])
    Console(file=stream, force_terminal=False).print("Cherry \U0001F352 model")
    stream.flush()
    assert stream.buffer.getvalue().decode("cp1252").strip() == "Cherry ? model"


def test_utf8_output_is_left_alone():
    stream = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    replace_unencodable_output([stream])
    assert stream.errors == "strict"


def test_missing_streams_are_skipped():
    # pythonw and windowed builds have no stdout/stderr
    replace_unencodable_output([None])
