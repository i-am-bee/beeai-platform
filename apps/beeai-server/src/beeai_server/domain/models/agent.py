# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, AwareDatetime

from acp_sdk.models import Agent as AcpAgentOriginal, Metadata as AcpMetadataOriginal

from beeai_server.utils.utils import utc_now


class EnvVar(BaseModel):
    name: str
    description: str | None = None
    required: bool = False


class AcpMetadata(AcpMetadataOriginal):
    env: list[EnvVar] = Field(default_factory=list, description="For configuration -- passed to the process")
    ui: dict[str, Any] | None = None
    provider_id: UUID


class Agent(AcpAgentOriginal, extra="allow"):
    id: UUID = Field(default_factory=uuid4)
    metadata: AcpMetadata

    @property
    def provider_id(self):
        return self.metadata.provider_id


class AgentRunRequest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    acp_run_id: UUID | None = None
    agent_id: UUID
    created_at: AwareDatetime = Field(default_factory=utc_now)
    finished_at: AwareDatetime | None = None

    def set_finished(self):
        self.finished_at = utc_now()
