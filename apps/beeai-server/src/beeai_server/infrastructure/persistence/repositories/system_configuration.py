# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from sqlalchemy import Column, DateTime, Enum, Row, String, Table, UniqueConstraint
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import select

from beeai_server.domain.models.system_configuration import SystemConfiguration
from beeai_server.domain.repositories.system_configuration import ISystemConfigurationRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata


class ConfigurationType(str):
    SYSTEM = "system"
    USER = "user"


configurations_table = Table(
    "configurations",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("configuration_type", String(50), nullable=False),
    Column("created_by", SQL_UUID, nullable=False),
    Column("default_llm_model", String(256), nullable=True),
    Column("default_embedding_model", String(256), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("configuration_type", name="uq_configurations_type"),
)


class SqlAlchemySystemConfigurationRepository(ISystemConfigurationRepository):
    def __init__(self, connection: AsyncConnection, created_by: UUID):
        self.connection = connection
        self.created_by = created_by

    async def get(self) -> SystemConfiguration:
        query = select(configurations_table).where(
            configurations_table.c.configuration_type == ConfigurationType.SYSTEM
        )
        result = await self.connection.execute(query)
        
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="system_configuration", id="system")
        
        return self._row_to_system_configuration(row)

    async def update(self, *, configuration: SystemConfiguration) -> None:
        # Use PostgreSQL's UPSERT (INSERT ... ON CONFLICT ... DO UPDATE)
        stmt = insert(configurations_table).values(
            id=configuration.id if hasattr(configuration, 'id') else None,
            configuration_type=ConfigurationType.SYSTEM,
            created_by=self.created_by,
            default_llm_model=configuration.default_llm_model,
            default_embedding_model=configuration.default_embedding_model,
            updated_at=configuration.updated_at,
        )
        
        # On conflict, update all fields except id, configuration_type, and created_by
        stmt = stmt.on_conflict_do_update(
            constraint="uq_configurations_type",
            set_={
                "default_llm_model": stmt.excluded.default_llm_model,
                "default_embedding_model": stmt.excluded.default_embedding_model,
                "updated_at": stmt.excluded.updated_at,
            }
        )
        
        await self.connection.execute(stmt)

    def _row_to_system_configuration(self, row: Row) -> SystemConfiguration:
        return SystemConfiguration(
            default_llm_model=row.default_llm_model,
            default_embedding_model=row.default_embedding_model,
            updated_at=row.updated_at,
        )