# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import timedelta

from beeai_server.service_layer.services.provider import ProviderService

from beeai_server.utils.periodic import periodic
from kink import inject

logger = logging.getLogger(__name__)


@periodic(period=timedelta(minutes=1))
@inject
async def scale_down_providers(service: ProviderService):
    await service.scale_down_providers()
