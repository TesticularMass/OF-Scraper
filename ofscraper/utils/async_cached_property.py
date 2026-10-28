import asyncio
import functools
import inspect
from collections import defaultdict

_STATE_ATTR = "__async_cached_property_state__"


class _InstanceState:
    __slots__ = ("cache", "locks")

    def __init__(self):
        self.cache = {}
        self.locks = defaultdict(asyncio.Lock)


class _Awaitable:
    # Defers creating the coroutine until awaited, so reading the attribute
    # without awaiting it never leaves an un-awaited coroutine behind.
    __slots__ = ("_factory",)

    def __init__(self, factory):
        self._factory = factory

    def __await__(self):
        return self._factory().__await__()


class async_cached_property:
    """Property whose async getter runs once per instance.

    `await obj.attr` returns the cached result. Concurrent first awaits share a
    per-instance lock, so the getter is not run twice. Exceptions are not cached.
    """

    def __init__(self, fget):
        if not inspect.iscoroutinefunction(fget):
            raise TypeError(f"{fget.__qualname__} must be an async def function")
        self._fget = fget
        self._name = fget.__name__
        functools.update_wrapper(self, fget)

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return _Awaitable(functools.partial(self._load, instance))

    async def _load(self, instance):
        state = self._state(instance)
        if self._name in state.cache:
            return state.cache[self._name]
        async with state.locks[self._name]:
            if self._name not in state.cache:
                state.cache[self._name] = await self._fget(instance)
            return state.cache[self._name]

    @staticmethod
    def _state(instance):
        try:
            return getattr(instance, _STATE_ATTR)
        except AttributeError:
            state = _InstanceState()
            object.__setattr__(instance, _STATE_ATTR, state)
            return state
