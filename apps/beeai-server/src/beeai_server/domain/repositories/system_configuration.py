# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Protocol, runtime_checkable

from beeai_server.domain.models.system_configuration import SystemConfiguration


@runtime_checkable
class ISystemConfigurationRepository(Protocol):
    async def get(self) -> SystemConfiguration:
        """Get the current system configuration."""
        ...

    async def update(self, *, configuration: SystemConfiguration) -> None:
        """Update the system configuration."""
        ...