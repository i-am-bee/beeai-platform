# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Protocol, Self

from beeai_server.domain.repositories.agent import IAgentRepository
from beeai_server.domain.repositories.env import IEnvVariableRepository
from beeai_server.domain.repositories.provider import IProviderRepository


class IUnitOfWork(Protocol):
    providers: IProviderRepository
    agents: IAgentRepository
    env: IEnvVariableRepository

    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class IUnitOfWorkFactory(Protocol):
    def __call__(self) -> IUnitOfWork: ...
