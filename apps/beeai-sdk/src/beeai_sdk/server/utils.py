import asyncio
from asyncio import CancelledError
from contextlib import suppress


async def cancel_task(task: asyncio.Task[None] | None):
    if task:
        task.cancel()
        with suppress(CancelledError):
            await task
