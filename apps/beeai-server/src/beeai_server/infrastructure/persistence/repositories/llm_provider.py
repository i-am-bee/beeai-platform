# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import Column, DateTime, Enum, Row, String, Table, Text
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import delete, select

from beeai_server.domain.models.llm_provider import LlmProvider, LlmProviderType
from beeai_server.domain.repositories.llm_provider import ILlmProviderRepository
from beeai_server.exceptions import DuplicateEntityError, EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata

llm_providers_table = Table(
    "llm_providers",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("name", String(256), nullable=False, unique=True),
    Column("type", Enum(LlmProviderType), nullable=False),
    Column("api_base", String(1024), nullable=True),
    Column("default_model", String(256), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("watsonx_project_id", String(256), nullable=True),
    Column("watsonx_space_id", String(256), nullable=True),
    Column("description", Text, nullable=True),
)


class SqlAlchemyLlmProviderRepository(ILlmProviderRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, *, llm_provider: LlmProvider) -> None:
        query = llm_providers_table.insert().values(
            {
                "id": llm_provider.id,
                "name": llm_provider.name,
                "type": llm_provider.type,
                "api_base": llm_provider.api_base,
                "default_model": llm_provider.default_model,
                "created_at": llm_provider.created_at,
                "watsonx_project_id": llm_provider.watsonx_project_id,
                "watsonx_space_id": llm_provider.watsonx_space_id,
                "description": llm_provider.description,
            }
        )
        try:
            await self.connection.execute(query)
        except IntegrityError as ex:
            raise DuplicateEntityError(entity="llm_provider", id=llm_provider.name) from ex

    async def get(self, *, llm_provider_id: UUID) -> LlmProvider:
        query = select(llm_providers_table).where(llm_providers_table.c.id == llm_provider_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="llm_provider", id=llm_provider_id)
        return self._row_to_llm_provider(row)

    async def list(self) -> AsyncIterator[LlmProvider]:
        query = select(llm_providers_table).order_by(llm_providers_table.c.created_at.desc())
        result = await self.connection.execute(query)
        for row in result:
            yield self._row_to_llm_provider(row)

    async def delete(self, *, llm_provider_id: UUID) -> int:
        query = delete(llm_providers_table).where(llm_providers_table.c.id == llm_provider_id)
        result = await self.connection.execute(query)
        return result.rowcount

    def _row_to_llm_provider(self, row: Row) -> LlmProvider:
        return LlmProvider(
            id=row.id,
            name=row.name,
            type=row.type,
            api_base=row.api_base,
            default_model=row.default_model,
            created_at=row.created_at,
            description=row.description,
        )