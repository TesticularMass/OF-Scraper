import cloup as click

from ofscraper.utils.args.callbacks.parse.string import (
    StringSplitParse,
)
from ofscraper.utils.args.types.choice import MutuallyExclusiveMultichoice

daemon_option = click.option(
    "-d",
    "--daemon",
    help="Run script in the background. Set value to minimum minutes between script runs. Overdue runs will run as soon as previous run finishes",
    type=float,
)

action_option = click.option(
    "-a",
    "--action",
    "--actions",
    "actions",
    help="""
    Select batch action(s) to perform [like,unlike,download,subscribe].
    Accepts space or comma-separated list. Like and unlike cannot be combined.
    Subscribe will subscribe to free (price=0) expired accounts.
    """,
    multiple=True,
    type=MutuallyExclusiveMultichoice(
        ["unlike", "like", "download", "subscribe"],
        exclusion=["like", "unlike"],
        case_sensitive=False,
    ),
    default=[],
    callback=StringSplitParse,
)
