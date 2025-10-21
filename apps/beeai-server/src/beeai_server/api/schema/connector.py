# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from pydantic import AnyUrl, BaseModel

from beeai_server.domain.models.common import Metadata
from beeai_server.domain.models.connector import ConnectorState


class ConnectorCreateRequest(BaseModel):
    url: AnyUrl

    client_id: str | None = None
    client_secret: str | None = None

    metadata: Metadata | None = None


class ConnectorUpdateRequest(BaseModel):
    client_id: str | None = None
    client_secret: str | None = None

    metadata: Metadata | None = None


class ConnectorResponse(BaseModel):
    id: UUID
    url: AnyUrl
    state: ConnectorState
    auth: AnyUrl | None = None
    error: str | None = None
    metadata: Metadata | None = None


class ConnectorConnectResponse(BaseModel):
    authorization_endpoint: AnyUrl | None = None
