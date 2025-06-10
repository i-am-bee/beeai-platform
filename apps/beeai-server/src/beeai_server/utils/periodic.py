# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import functools
import importlib
import inspect
import logging
import pkgutil
import time
from asyncio import Event, Task
from contextlib import asynccontextmanager
from datetime import timedelta
from functools import cached_property
from inspect import isfunction
from types import ModuleType
from typing import Any, Callable, Generic, TypeVar, Final

from asgiref.sync import sync_to_async

import beeai_server.crons

logger = logging.getLogger(__name__)


AnyCallableT = TypeVar("AnyCallableT", bound=Callable[..., Any])

CRON_REGISTRY: dict[str, Periodic] = {}
CRON_PACKAGE: Final[ModuleType] = beeai_server.crons


def periodic(*, period: timedelta, name: str | None = None) -> Callable[[AnyCallableT], Periodic]:
    """Run function periodically every "period_sec" seconds, add it to CRON_REGISTRY"""

    def create_cron(fn: AnyCallableT) -> Periodic[AnyCallableT]:
        periodic_name = name or fn.__name__

        if periodic_name in CRON_REGISTRY:
            raise ValueError(f"Cron with name {periodic_name} was already registered!")

        CRON_REGISTRY[periodic_name] = Periodic(executor=fn, period=period, name=periodic_name)
        return CRON_REGISTRY[periodic_name]

    return create_cron


class Periodic(Generic[AnyCallableT]):
    """
    Schedule callback every `period_sec` seconds using asyncio.

    :example:
        async def async_callback():
            ... # important work

        background_task = Periodic(executor=async_callback, period_sec=60, name='important_work')

        # use inside a context manager or with background_task.start() and background_task.stop()
        async with background_task:
            # running async_callback every 60 seconds inside this block
            ...
            background_task.poke() # run callback now
            ...
        # background_task is stopped
    """

    def __init__(self, *, executor: AnyCallableT, period: timedelta, name: str | None = None):
        self._callable = executor
        self._orig_executor = executor
        self._name = name
        self._period = period
        self._stopping = False
        self._wake_up_event = Event()
        self._task: Task | None = None

    @cached_property
    def name(self):
        if self._name:
            return self._name
        if isfunction(self._callable):
            return self._callable.__name__
        return type(self._callable).__name__

    async def _executor(self):
        @functools.wraps(self._orig_executor)
        async def _executor(*args, **kwargs):
            async_executor = self._orig_executor
            if not inspect.iscoroutinefunction(self._orig_executor):
                async_executor = functools.wraps(self._orig_executor)(sync_to_async(self._orig_executor))
            await async_executor(*args, **kwargs)

        return await _executor()

    async def _loop(self):
        while not self._stopping:
            logger.info(f"Periodic [{self.name}]: start")
            check_start = time.time()
            try:
                await self._executor()
            except BaseException as ex:
                logger.error(f"Exception occured during periodic run of {self.name}: {ex!r}")
            duration = time.time() - check_start
            remaining_sleep = max(0.0, self._period.total_seconds() - duration)
            logger.info(f"Periodic [{self.name}]: finish, next run in {remaining_sleep:.2f}s")
            await self._light_sleep(timeout=remaining_sleep)

    async def _light_sleep(self, *, timeout: float) -> None:
        if self._stopping:
            return
        try:
            await asyncio.wait_for(self._wake_up_event.wait(), timeout=timeout)
            self._wake_up_event.clear()
        except TimeoutError:
            pass

    def poke(self):
        """
        Run executor now and reset waiting period.

        :example:
            periodic = Periodic(executor=callback, period_sec=60)
            await periodic.start()
            # callback() runs
            # sleep 60s
            # callback() runs
            # sleep 10s
            periodic.poke()
            # callback() runs
            # sleep 60s
        """
        self._wake_up_event.set()

    async def start(self) -> None:
        self._stopping = False
        logger.info(f"Starting periodic worker: {self.name}")
        self._task = asyncio.create_task(self._loop(), name=self._name)
        logger.info(f"Periodic worker started successfully: {self.name}")

    async def stop(self):
        logger.info(f"Stopping periodic worker: {self.name}")
        self._stopping = True
        self._wake_up_event.set()
        if self._task:
            await self._task
        logger.info(f"Periodic worker finished successfully: {self.name}")

    async def __aenter__(self):
        await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


def register_all_crons():
    # Register all flows in FLOW_PACKAGE by importing them
    for _, name, _ in pkgutil.walk_packages(CRON_PACKAGE.__path__):
        importlib.import_module(CRON_PACKAGE.__name__ + "." + name)


@asynccontextmanager
async def run_all_crons():
    try:
        await asyncio.gather(*(cron.start() for cron in CRON_REGISTRY.values()))
        yield
    finally:
        await asyncio.gather(*(cron.stop() for cron in CRON_REGISTRY.values()))
