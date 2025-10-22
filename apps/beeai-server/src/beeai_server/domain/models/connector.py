# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import AnyUrl, AwareDatetime, BaseModel, Field

from beeai_server.domain.models.common import Metadata
from beeai_server.utils.utils import utc_now


class AuthorizationCodeFlow(BaseModel):
    authorization_endpoint: AnyUrl
    state: str
    code_verifier: str


class Token(BaseModel):
    access_token: str
    refresh_token: str | None
    token_type: Literal["bearer"]


class Authorization(BaseModel):
    server: AnyUrl
    client_id: str | None = None
    client_secret: str | None = None
    code: AuthorizationCodeFlow | None = None
    token: Token | None = None


class ConnectorState(str, Enum):
    created = "created"
    auth_required = "auth_required"
    connected = "connected"
    disconnected = "disconnected"


class Connector(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    url: AnyUrl

    state: ConnectorState = ConnectorState.created

    auth: Authorization | None = None
    error: str | None = None

    created_at: AwareDatetime = Field(default_factory=utc_now)
    updated_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID

    metadata: Metadata | None = None
