# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from datetime import timedelta
from secrets import token_urlsafe
from uuid import UUID

import httpx
from async_lru import alru_cache
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc8414 import AuthorizationServerMetadata, get_well_known_url
from fastapi import status
from kink import inject
from pydantic import AnyUrl, BaseModel

from beeai_server.domain.models.common import Metadata
from beeai_server.domain.models.connector import Authorization, AuthorizationCodeFlow, Connector, ConnectorState
from beeai_server.domain.models.user import User
from beeai_server.exceptions import PlatformError
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class ConnectorService:
    def __init__(self, uow: IUnitOfWorkFactory):
        self._uow = uow

    async def create_connector(self, *, user: User, url: AnyUrl, metadata: Metadata | None) -> Connector:
        connector = Connector(url=url, created_by=user.id, metadata=metadata)
        async with self._uow() as uow:
            await uow.connectors.create(connector=connector)
            await uow.commit()
        return connector

    async def read_connector(self, *, connector_id: UUID, user: User | None = None) -> Connector:
        async with self._uow() as uow:
            return await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

    async def delete_connector(self, *, connector_id: UUID, user: User | None = None) -> None:
        async with self._uow() as uow:
            await uow.connectors.delete(connector_id=connector_id, user_id=user.id if user else None)
            await uow.commit()

    async def list_connectors(self, *, user: User | None = None) -> list[Connector]:
        async with self._uow() as uow:
            return [c async for c in uow.connectors.list(user_id=user.id if user else None)]

    async def connect_connector(self, *, connector_id: UUID, redirect_uri: str, user: User | None = None) -> Connector:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        if connector.state not in (ConnectorState.created, ConnectorState.disconnected):
            raise PlatformError("Connector must be created or disconnected", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            await self.probe_connector(connector=connector)
            connector.state = ConnectorState.connected
            connector.error = None
        except Exception as err:
            if isinstance(err, httpx.HTTPStatusError) and err.response.status_code == status.HTTP_401_UNAUTHORIZED:
                await self._bootstrap_auth(connector=connector, redirect_uri=redirect_uri)
                connector.state = ConnectorState.auth_required
            else:
                connector.error = str(err)

        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()
        return connector

    async def disconnect_connector(self, *, connector_id: UUID, user: User | None = None) -> Connector:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        if connector.state not in (ConnectorState.connected, ConnectorState.auth_required):
            raise PlatformError(
                "Connector must be in connected or auth_required state", status_code=status.HTTP_400_BAD_REQUEST
            )

        await self._clear_auth(connector=connector)

        connector.state = ConnectorState.disconnected
        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()
        return connector

    async def oauth_callback(self, *, callback_url: str, state: str) -> None:
        async with self._uow() as uow:
            connector = await uow.connectors.get_by_state(state=state)

        if connector.state not in (ConnectorState.auth_required):
            raise PlatformError("Connector must be in auth_required state", status_code=status.HTTP_400_BAD_REQUEST)
        assert connector.auth is not None

        async with await self._create_oauth_client(connector=connector) as client:
            auth_metadata = await self._discover_auth_metadata(connector=connector)
            if not auth_metadata:
                raise RuntimeError("Authorization server no longer contains necessary metadata")
            token = await client.fetch_token(auth_metadata.get("token_endpoint"), authorization_response=callback_url)
            connector.auth.token = token
            connector.auth.code = None
        try:
            await self.probe_connector(connector=connector)
            connector.state = ConnectorState.connected
        except Exception:
            logger.error("Failed to probe resource with valid token", exc_info=True)
            connector.state = ConnectorState.disconnected

        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()

    async def refresh_connector(self, *, connector_id: UUID, user: User | None = None) -> None:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        if connector.state != ConnectorState.connected:
            return

        try:
            await self.probe_connector(connector=connector)
        except Exception as err:
            connector.state = ConnectorState.disconnected
            connector.error = str(err)
        finally:
            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

    async def _bootstrap_auth(self, *, connector: Connector, redirect_uri: str) -> None:
        auth_metadata = await self._discover_auth_metadata(connector=connector)
        if not auth_metadata:
            raise RuntimeError("Not authorization server found for the connector")
        issuer = auth_metadata.get("issuer")
        assert isinstance(issuer, str)

        await self._clear_auth(connector=connector)
        connector.auth = Authorization(server=AnyUrl(issuer))
        code_verifier = token_urlsafe(64)
        async with await self._create_oauth_client(connector=connector) as client:
            uri, state = await client.create_authorization_url(
                auth_metadata.get("authorization_endpoint"),
                code_verifier=code_verifier,
                redirect_uri=redirect_uri,
            )
            connector.auth.code = AuthorizationCodeFlow(
                authorization_endpoint=uri, state=state, code_verifier=code_verifier
            )

    async def _clear_auth(self, *, connector: Connector) -> None:
        if not connector.auth or not connector.auth.token:
            return

        if connector.auth.token:
            try:
                async with await self._create_oauth_client(connector=connector) as client:
                    auth_metadata = await self._discover_auth_metadata(connector=connector)
                    if not auth_metadata:
                        raise RuntimeError("Authorization server no longer contains necessary metadata")
                    revoke_endpoint = auth_metadata.get("revocation_endpoint")
                    if not isinstance(revoke_endpoint, str):
                        raise RuntimeError("Authorization server does not support token revocation")
                    await client.revoke_token(revoke_endpoint, token=connector.auth.token.access_token)
            except Exception:
                logger.warning("Token revocation failed", exc_info=True)

        connector.auth = None
        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()

    async def _create_client(self, *, connector: Connector) -> httpx.AsyncClient:
        if not connector.auth:
            return httpx.AsyncClient(base_url=str(connector.url))
        else:
            return await self._create_oauth_client(connector=connector)

    async def _create_oauth_client(self, *, connector: Connector) -> AsyncOAuth2Client:
        if not connector.auth:
            raise RuntimeError("Connector does not support auth")
        await self._ensure_oauth_client_registered(connector=connector)

        async def update_token(token, refresh_token=None, access_token=None):
            if not connector.auth:
                raise RuntimeError("Authorization has been removed from the connector")
            connector.auth.token = token
            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

        return AsyncOAuth2Client(
            client_id=connector.auth.client_id,
            client_secret=connector.auth.client_secret,
            token=connector.auth.token,
            update_token=update_token,
            code_challenge_method="S256",
        )

    async def _discover_auth_metadata(self, *, connector: Connector) -> AuthorizationServerMetadata | None:
        resource_metadata = await _discover_resource_metadata(str(connector.url))
        if not resource_metadata or not resource_metadata.authorization_servers:
            return None
        auth_metadata = await _discover_auth_metadata(resource_metadata.authorization_servers[0])
        return auth_metadata

    async def _ensure_oauth_client_registered(self, *, connector: Connector) -> Connector:
        if not connector.auth:
            raise RuntimeError("Authoriztion hasn't been activated for connector")
        auth_metadata = await self._discover_auth_metadata(connector=connector)
        if not auth_metadata:
            raise RuntimeError("Authorization metadata missing")
        issuer = auth_metadata.get("issuer")
        assert isinstance(issuer, str)
        registration_response = await _register_client(issuer)
        async with self._uow() as uow:
            connector.auth.client_id = registration_response.client_id
            connector.auth.client_secret = registration_response.client_secret
            await uow.connectors.update(connector=connector)
            await uow.commit()
        return connector

    async def probe_connector(self, *, connector: Connector):
        async with await self._create_client(connector=connector) as client:
            response = await client.post("")
            response.raise_for_status()


@alru_cache(ttl=timedelta(days=1).seconds)
async def _register_client(authorization_server_url: str) -> _ClientRegistrationResponse:
    auth_metadata = await _discover_auth_metadata(authorization_server_url)
    if not auth_metadata:
        raise RuntimeError("Authorization server metadata not found")
    registration_endpoint = auth_metadata.get("registration_endpoint")
    if not isinstance(registration_endpoint, str):
        raise RuntimeError("Authorization server does not support dynamic client registration")
    async with httpx.AsyncClient() as client:
        response = await client.post(str(registration_endpoint), json={"client_name": "BeeAI"})
        response.raise_for_status()
        registration_response = _ClientRegistrationResponse.model_validate(response.json())
        return registration_response


@alru_cache(ttl=timedelta(minutes=10).seconds)
async def _discover_auth_metadata(authorization_server_url: str) -> AuthorizationServerMetadata | None:
    url = get_well_known_url(authorization_server_url, external=True)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None
        response.raise_for_status()
        metadata = AuthorizationServerMetadata(response.json())
        metadata.validate()
        return metadata


@alru_cache(ttl=timedelta(minutes=10).seconds)
async def _discover_resource_metadata(resource_server_url: str) -> _ResourceServerMetadata | None:
    # RFC9728 hasn't been implemented yet in authlib
    # Reusing util from RFC8414
    url = get_well_known_url(resource_server_url, external=True, suffix="oauth-protected-resource")
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None
        response.raise_for_status()
        return _ResourceServerMetadata.model_validate(response.json())


class _ResourceServerMetadata(BaseModel):
    authorization_servers: list[str]


class _ClientRegistrationResponse(BaseModel):
    client_id: str
    client_secret: str | None
