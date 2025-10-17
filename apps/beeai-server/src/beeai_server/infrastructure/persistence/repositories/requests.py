# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from uuid import UUID

from kink import inject
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy import Column, DateTime, Row, String, Table, text
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.models.a2a_request import A2ARequestTask
from beeai_server.domain.repositories.a2a_request import IA2ARequestRepository
from beeai_server.exceptions import EntityNotFoundError, ForbiddenUpdateError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.utils.utils import utc_now

a2a_request_tasks_table = Table(
    "a2a_request_tasks",
    metadata,
    Column("task_id", String(256), primary_key=True),
    Column("created_by", SQL_UUID, nullable=False),  # not using reference integrity for performance
    Column("provider_id", SQL_UUID, nullable=False),  # not using reference integrity for performance
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("last_accessed_at", DateTime(timezone=True), nullable=False),
)

a2a_request_contexts_table = Table(
    "a2a_request_contexts",
    metadata,
    Column("context_id", String(256), primary_key=True),
    Column("created_by", SQL_UUID, nullable=False),  # not using reference integrity for performance
    Column("provider_id", SQL_UUID, nullable=False),  # not using reference integrity for performance
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("last_accessed_at", DateTime(timezone=True), nullable=False),
)


@inject
class SqlAlchemyA2ARequestRepository(IA2ARequestRepository):
    def __init__(self, connection: AsyncConnection):
        self._connection = connection

    def _to_task(self, row: Row) -> A2ARequestTask:
        return A2ARequestTask.model_validate(
            {
                "task_id": row.task_id,
                "created_by": row.created_by,
                "provider_id": row.provider_id,
                "created_at": row.created_at,
                "last_accessed_at": row.last_accessed_at,
            }
        )

    async def track_request_ids_ownership(
        self, user_id: UUID, provider_id: UUID, task_id: str | None = None, context_id: str | None = None
    ) -> None:
        """
        Verify ownership and record/update identifiers in a SINGLE query.

        Returns:
            (task_authorized, context_authorized) - False means unauthorized access attempt
        """

        # This handles all cases:
        # - New task_id/context_id: Creates ownership record
        # - Existing owned: Updates last_accessed_at and returns true
        # - Existing owned by OTHER user: ON CONFLICT WHERE clause prevents update, returns false

        query = text("""
                     WITH existing_task AS (SELECT true as exists
                                            FROM a2a_request_tasks
                                            WHERE task_id = :task_id
                                              AND created_by = :user_id
                                            LIMIT 1),
                          existing_context AS (SELECT true as exists
                                               FROM a2a_request_contexts
                                               WHERE context_id = :context_id
                                                 AND created_by = :user_id
                                               LIMIT 1),
                          task_upsert AS (
                              INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at)
                                  SELECT :task_id, :user_id, NOW(), NOW()
                                  WHERE :task_id IS NOT NULL
                                  ON CONFLICT (task_id) DO UPDATE
                                      SET last_accessed_at = NOW()
                                      WHERE a2a_request_tasks.created_by = :user_id
                                  RETURNING true as created_or_updated),
                          context_upsert AS (
                              INSERT INTO a2a_request_contexts (context_id, created_by, created_at, last_accessed_at)
                                  SELECT :context_id, :user_id, NOW(), NOW()
                                  WHERE :context_id IS NOT NULL
                                  ON CONFLICT (context_id) DO UPDATE
                                      SET last_accessed_at = NOW()
                                      WHERE a2a_request_contexts.created_by = :user_id
                                  RETURNING true as created_or_updated)
                     SELECT CASE
                                WHEN :task_id IS NULL THEN true
                                WHEN EXISTS (SELECT 1 FROM existing_task) THEN true
                                WHEN EXISTS (SELECT 1 FROM task_upsert) THEN true
                                ELSE false
                                END as task_authorized,
                            CASE
                                WHEN :context_id IS NULL THEN true
                                WHEN EXISTS (SELECT 1 FROM existing_context) THEN true
                                WHEN EXISTS (SELECT 1 FROM context_upsert) THEN true
                                ELSE false
                                END as context_authorized
                     """)

        result = await self._connection.execute(
            query,
            {"task_id": task_id, "context_id": context_id, "user_id": user_id, "provider_id": provider_id},
        )

        if not (row := result.first()):
            raise RuntimeError("Unexpected query result")
        if not row.task_authorized:
            assert task_id
            raise ForbiddenUpdateError(entity="a2a_request_task", id=task_id)
        if not row.context_authorized:
            assert context_id
            raise ForbiddenUpdateError(entity="a2a_request_context", id=context_id)

    async def get_task(self, *, task_id: str, user_id: UUID) -> A2ARequestTask:
        """Get a task by task_id if owned by the user."""
        query = a2a_request_tasks_table.select().where(
            a2a_request_tasks_table.c.task_id == task_id, a2a_request_tasks_table.c.created_by == user_id
        )
        result = await self._connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="a2a_request_task", id=task_id)
        return self._to_task(row)

    async def delete_tasks(self, *, older_than: timedelta) -> None:
        query = a2a_request_tasks_table.delete().where(
            a2a_request_tasks_table.c.last_accessed_at < utc_now() - older_than
        )
        await self._connection.execute(query)

    async def delete_contexts(self, *, older_than: timedelta) -> None:
        query = a2a_request_contexts_table.delete().where(
            a2a_request_contexts_table.c.last_accessed_at < utc_now() - older_than
        )
        await self._connection.execute(query)
