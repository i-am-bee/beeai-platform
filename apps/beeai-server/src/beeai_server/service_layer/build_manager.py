# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from typing import Protocol
from uuid import UUID

from beeai_server.domain.models.provider_build import BuildState, ProviderBuild
from beeai_server.utils.logs_container import LogsContainer


class IProviderBuildManager(Protocol):
    async def create_job(self, *, provider_build: ProviderBuild) -> bool: ...
    async def cancel_job(self, *, provider_build_id: UUID) -> None: ...
    async def wait_for_completion(self, *, provider_build_id: UUID, timeout: timedelta) -> BuildState: ...  # noqa: ASYNC109 (the timeout actually corresponds to kubernetes timeout)
    async def stream_logs(self, *, provider_build_id: UUID, logs_container: LogsContainer) -> None: ...
