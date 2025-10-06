# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from uuid import UUID, uuid4

from kink import inject
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.repositories.user_feedback import IUserFeedbackRepository
from beeai_server.exceptions import ForbiddenUpdateError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.utils.utils import utc_now

request_tasks_table = Table(
    "request_tasks",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("task_id", String(256), nullable=False, unique=True),
    Column("created_by", ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("last_active_at", DateTime(timezone=True), nullable=False),
)


@inject
class SqlAlchemyUserFeedbackRepository(IUserFeedbackRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create_or_update_a2a_task(self, *, task_id: str, user_id: UUID) -> None:
        now = utc_now()
        query = (
            insert(request_tasks_table)
            .values(id=uuid4(), task_id=task_id, created_by=user_id, created_at=now, last_active_at=now)
            .on_conflict_do_update(
                index_elements=["task_id"],
                set_={"last_active_at": now},
                where=request_tasks_table.c.created_by == user_id,
            )
        )
        result = await self.connection.execute(query)
        if not result.rowcount:
            raise ForbiddenUpdateError(entity="request_task", id=task_id)

    async def delete_tasks(self, *, older_than: timedelta):
        query = request_tasks_table.delete().where(request_tasks_table.c.last_active_at < utc_now() - older_than)
        await self.connection.execute(query)
