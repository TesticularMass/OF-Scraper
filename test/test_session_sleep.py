import asyncio
import threading

from ofscraper.managers.sessionmanager.sessionmanager import SessionSleep


def make_sleeper():
    sleeper = SessionSleep(
        sleep=0.02,
        min_sleep=0.01,
        difmin=0,
        max_sleep=0.05,
        decay_threshold=60,
        decay_factor=1.5,
        increase_factor=1.5,
        error_name="test",
    )
    sleeper.sleep = 0.02
    return sleeper


def contend(sleeper, second_method):
    async def run():
        await asyncio.gather(
            sleeper.async_do_sleep(), getattr(sleeper, second_method)()
        )

    asyncio.run(run())


def test_do_sleep_works_across_event_loops():
    # ofscraper runs async code in several loops (@run starts a new one per
    # call); a shared asyncio.Lock binds to the first loop that waits on it.
    sleeper = make_sleeper()
    contend(sleeper, "async_do_sleep")
    contend(sleeper, "async_do_sleep")


def test_toomany_req_works_across_event_loops():
    sleeper = make_sleeper()
    asyncio.run(sleeper.async_toomany_req())
    asyncio.run(sleeper.async_toomany_req())
    assert sleeper.sleep > 0.02  # the backoff was applied


def test_async_do_sleep_waits_for_a_caller_on_another_thread():
    # Worker threads run their own event loops against the same sleeper. A
    # caller that finds the lock taken by another thread must wait for it and
    # then finish, not hang on a future that the other thread can't wake.
    sleeper = make_sleeper()
    inside = threading.Event()
    release = threading.Event()
    decay = sleeper._maybe_decay_sleep

    def hold_first_caller():
        if threading.current_thread().name == "first":
            inside.set()
            release.wait(5)
        decay()

    sleeper._maybe_decay_sleep = hold_first_caller
    done = []

    def call(name):
        asyncio.run(sleeper.async_do_sleep())
        done.append(name)

    first = threading.Thread(target=call, args=("first",), name="first")
    second = threading.Thread(target=call, args=("second",), name="second")
    first.start()
    assert inside.wait(5)
    second.start()
    second.join(0.2)
    assert second.is_alive()  # waiting on the lock the first caller holds
    release.set()
    first.join(5)
    second.join(5)
    assert sorted(done) == ["first", "second"]

