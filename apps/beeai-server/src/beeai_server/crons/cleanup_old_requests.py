# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import timedelta

from beeai_server.configuration import Configuration
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

from beeai_server.utils.periodic import periodic
from kink import inject

logger = logging.getLogger(__name__)


@periodic(period=timedelta(minutes=5))
@inject
async def clean_up_old_requests(configuration: Configuration, uow: IUnitOfWorkFactory):
    async with uow() as uow:
        deleted_count = await uow.agents.delete_requests_older_than(
            finished_threshold=timedelta(seconds=configuration.persistence.finished_requests_remove_after_sec),
            stale_threshold=timedelta(seconds=configuration.persistence.stale_requests_remove_after_sec),
        )
        await uow.commit()
    if deleted_count:
        logger.info(f"Deleted {deleted_count} old requests")
