# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from kink import inject
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Row, String, Table
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.models.connector import Connector
from beeai_server.domain.repositories.connector import IConnectorRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata

connectors = Table(
    "connectors",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("url", String(256), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("auth", JSON, nullable=True),
    # Duplicate to allow indexing
    Column("state", String(256), nullable=True, unique=True, index=True),
)


@inject
class SqlAlchemyConnectorRepository(IConnectorRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, *, connector: Connector) -> None:
        query = connectors.insert().values(self._to_row(connector))
        await self.connection.execute(query)

    async def get(self, *, connector_id: UUID, user_id: UUID | None = None) -> Connector:
        query = connectors.select().where(connectors.c.id == connector_id)
        if user_id is not None:
            query = query.where(connectors.c.created_by == user_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="connector", id=connector_id)
        return self._to_connector(row)

    async def get_by_state(self, *, state: str) -> Connector:
        query = connectors.select().where(connectors.c.state == state)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="connector", id=state)
        return self._to_connector(row)

    async def update(self, *, connector: Connector) -> None:
        query = connectors.update().where(connectors.c.id == connector.id).values(self._to_row(connector))
        await self.connection.execute(query)

    async def delete(self, *, connector_id: UUID, user_id: UUID | None = None) -> int:
        query = connectors.delete().where(connectors.c.id == connector_id)
        if user_id is not None:
            query = query.where(connectors.c.created_by == user_id)
        result = await self.connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError(entity="connector", id=connector_id)
        return result.rowcount

    async def list(self, *, user_id: UUID | None = None) -> AsyncIterator[Connector]:
        query = connectors.select()
        if user_id is not None:
            query = query.where(connectors.c.created_by == user_id)
        async for row in await self.connection.stream(query):
            yield self._to_connector(row)

    def _to_row(self, connector: Connector) -> dict[str, Any]:
        return {
            "id": connector.id,
            "created_at": connector.created_at,
            "updated_at": connector.updated_at,
            "created_by": connector.created_by,
            "auth": connector.auth.model_dump(mode="json") if connector.auth else None,
            "state": connector.auth.code.state if connector.auth and connector.auth.code else None,
        }

    def _to_connector(self, row: Row):
        return Connector.model_validate(
            {
                "id": row.id,
                "url": row.url,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "created_by": row.created_by,
                "auth": row.auth,
            }
        )
