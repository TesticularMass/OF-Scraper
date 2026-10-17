import ofscraper.utils.args.accessors.read as read_args


def low_output():
    args = read_args.retriveArgs()
    return (
        args.output_level in {"OFF", "LOW", "PROMPT"}
        or args.no_rich
    )
