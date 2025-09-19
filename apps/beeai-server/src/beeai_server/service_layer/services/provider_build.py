# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging

from kink import inject

from beeai_server.service_layer.build_manager import IProviderBuildManager
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class ProviderBuildService:
    def __init__(self, build_manager: IProviderBuildManager, uow: IUnitOfWorkFactory):
        self._uow = uow
        self._build_manager = build_manager
