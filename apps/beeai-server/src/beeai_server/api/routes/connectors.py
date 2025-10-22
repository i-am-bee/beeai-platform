# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from beeai_server.api.dependencies import (
    ConnectorServiceDependency,
    RequiresPermissions,
)
from beeai_server.api.schema.connector import ConnectorCreateRequest, ConnectorResponse
from beeai_server.domain.models.common import PaginatedResult
from beeai_server.domain.models.connector import Connector
from beeai_server.domain.models.permissions import AuthorizedUser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_connector(
    request: ConnectorCreateRequest,
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"write"}))],
):
    return _to_response(
        await connector_service.create_connector(user=user.user, url=request.url, metadata=request.metadata)
    )


@router.get("/{connector_id}")
async def read_connector(
    connector_id: UUID,
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"read"}))],
):
    return _to_response(await connector_service.read_connector(connector_id=connector_id, user=user.user))


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: UUID,
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"write"}))],
):
    return await connector_service.delete_connector(connector_id=connector_id, user=user.user)


@router.get("")
async def list_connectors(
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"read"}))],
):
    connectors = await connector_service.list_connectors(user=user.user)
    return PaginatedResult(items=[_to_response(connector) for connector in connectors], total_count=len(connectors))


@router.post("/{connector_id}/connect")
async def connect_connector(
    connector_id: UUID,
    connector_service: ConnectorServiceDependency,
    request: Request,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"write"}))],
):
    return _to_response(
        await connector_service.connect_connector(
            connector_id=connector_id, user=user.user, redirect_uri=str(request.url_for(oauth_callback.__name__))
        )
    )


@router.post("/{connector_id}/disconnect")
async def disconnect_connector(
    connector_id: UUID,
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"write"}))],
):
    return _to_response(await connector_service.disconnect_connector(connector_id=connector_id, user=user.user))


@router.post("/oauth/callback")
async def oauth_callback(request: Request, state: str, connector_service: ConnectorServiceDependency):
    await connector_service.oauth_callback(callback_url=str(request.url), state=state)


def _to_response(connector: Connector) -> ConnectorResponse:
    return ConnectorResponse(
        id=connector.id,
        url=connector.url,
        state=connector.state,
        auth=connector.auth.code.authorization_endpoint if connector.auth and connector.auth.code else None,
        error=connector.error,
        metadata=connector.metadata,
    )
