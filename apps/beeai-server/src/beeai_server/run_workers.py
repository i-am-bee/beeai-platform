import asyncio
import logging
from contextlib import nullcontext, asynccontextmanager

import procrastinate
from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.service_layer.tasks.procrastinate import create_app

logger = logging.getLogger(__name__)


@asynccontextmanager
@inject
async def run_workers_lifespan(configuration: Configuration, app: procrastinate.App | None = None):
    async with create_app().open_async() if not app else nullcontext():
        worker = asyncio.create_task(app.run_worker_async(install_signal_handlers=False))
        logger.info(f"Starting procrastinate workers for tasks: {app.tasks.keys()}")
        yield
        logger.info("Stopping procrastinate workers")
        worker.cancel()
        try:
            await asyncio.wait_for(worker, timeout=10)
        except asyncio.TimeoutError:
            logger.info("Procrastinate workers did not terminate gracefully")
        except asyncio.CancelledError:
            logger.info("Procrastinate workers did terminate successfully")
