import contextlib
import time

from ofscraper.utils.live.live import get_live, stop_live
from ofscraper.utils.live.clear import clear
from ofscraper.utils.live.tasks import reset_activity_tasks


@contextlib.contextmanager
def prompt_live():
    stop_live()
    clear()
    # give time for screen to clear
    time.sleep(0.3)
    yield
    # stop again for nested calls
    stop_live()
    # Reset task IDs since Progress objects will be recreated
    reset_activity_tasks()
    # NOTE: We do NOT restore the previous renderable here.
    # The caller is responsible for setting up the appropriate screen
    # (e.g., setup_live("api")) after prompts complete.
    # Restoring the old renderable would override the screen setup.
