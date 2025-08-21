# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable
from uuid import UUID

from beeai_server.domain.models.model_provider import ModelCapability, ModelProvider


@runtime_checkable
class IModelProviderRepository(Protocol):
    async def create(self, *, model_provider: ModelProvider) -> None:
        """Create a new model provider."""

    async def get(self, *, model_provider_id: UUID) -> ModelProvider:
        """Get a model provider by ID."""

    async def list(self, *, capability: ModelCapability | None = None) -> AsyncIterator[ModelProvider]:
        """List model providers, optionally filtered by capability."""
        yield ...  # pyright: ignore [reportReturnType]

    async def delete(self, *, model_provider_id: UUID) -> int:
        """Delete a model provider by ID. Returns the number of deleted rows."""
