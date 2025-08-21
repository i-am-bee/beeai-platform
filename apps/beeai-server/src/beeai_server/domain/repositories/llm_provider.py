# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable
from uuid import UUID

from beeai_server.domain.models.llm_provider import LlmProvider


@runtime_checkable
class ILlmProviderRepository(Protocol):
    async def create(self, *, llm_provider: LlmProvider) -> None:
        """Create a new LLM provider."""
        ...

    async def get(self, *, llm_provider_id: UUID) -> LlmProvider:
        """Get an LLM provider by ID."""
        ...

    async def list(self) -> AsyncIterator[LlmProvider]:
        """List all LLM providers."""
        ...

    async def delete(self, *, llm_provider_id: UUID) -> int:
        """Delete an LLM provider by ID. Returns the number of deleted rows."""
        ...