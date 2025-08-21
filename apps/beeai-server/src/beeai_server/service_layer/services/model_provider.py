# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from kink import inject

from beeai_server.domain.models.model_provider import ModelProvider
from beeai_server.domain.repositories.env import EnvStoreEntity
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory


@inject
class ModelProviderService:
    def __init__(self, uow: IUnitOfWorkFactory):
        self._uow = uow

    async def create_model_provider(self, *, model_provider: ModelProvider, variables: dict[str, str | None]) -> None:
        async with self._uow() as uow:
            await uow.model_providers.create(model_provider=model_provider)
            await uow.env.update(
                parent_entity=EnvStoreEntity.model_provider,
                parent_entity_id=model_provider.id,
                variables=variables,
            )
            await uow.commit()

    async def get_model_provider(self, *, model_provider_id: UUID) -> ModelProvider:
        """Get a model provider by ID."""
        async with self._uow() as uow:
            return await uow.model_providers.get(model_provider_id=model_provider_id)

    async def list_model_providers(self) -> list[ModelProvider]:
        """List model providers, optionally filtered by capability."""
        async with self._uow() as uow:
            return [provider async for provider in uow.model_providers.list()]

    async def delete_model_provider(self, *, model_provider_id: UUID) -> None:
        """Delete a model provider and its environment variables."""
        async with self._uow() as uow:
            await uow.model_providers.delete(model_provider_id=model_provider_id)
            await uow.commit()

    async def get_model_provider_env(self, *, model_provider_id: UUID) -> dict[str, str]:
        """Get environment variables for a model provider."""
        async with self._uow() as uow:
            result = await uow.env.get_all(
                parent_entity=EnvStoreEntity.model_provider, parent_entity_ids=[model_provider_id]
            )
            return result[model_provider_id]

    async def discover_models(self, *, model_provider_id: UUID) -> dict[str, list[str]]:
        """Discover available models from a provider via their /models endpoint."""
        # This would typically make an HTTP request to the provider's API
        # For now, return a placeholder structure
        async with self._uow() as uow:
            provider = await uow.model_providers.get(model_provider_id=model_provider_id)

            # Placeholder - in real implementation, this would call the provider's API
            return {
                "llm_models": [] if not provider.supports_llm else ["model-1", "model-2"],
                "embedding_models": [] if not provider.supports_embedding else ["embedding-1"],
            }
