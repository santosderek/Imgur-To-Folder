import asyncio
from typing import TypeVar


T = TypeVar('T')


def cast_as_awaitable(value: T) -> asyncio.Future[T]:
    future = asyncio.Future()
    future.set_result(value)
    return future
