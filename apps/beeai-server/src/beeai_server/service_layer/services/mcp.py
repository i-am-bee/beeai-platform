# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterable
from contextlib import AsyncExitStack
import logging
from datetime import timedelta
from typing import NamedTuple

from beeai_server.api.schema.mcp import Server, Tool, Toolkit
from beeai_server.domain.models.gateway import GatewayLocation
from beeai_server.domain.models.user import User
import httpx
from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.service_layer.services.users import UserService
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class McpServerResponse(NamedTuple):
    content: bytes | None
    stream: AsyncIterable | None
    status_code: int
    headers: dict[str, str] | None
    media_type: str


class ProxyRequestContext(NamedTuple):
    client: httpx.AsyncClient
    user: User


@inject
class McpProxyService:
    STARTUP_TIMEOUT = timedelta(minutes=5)

    def __init__(
        self,
        uow: IUnitOfWorkFactory,
        user_service: UserService,
        configuration: Configuration,
    ):
        self._user_service = user_service
        self._config = configuration
        self._client = httpx.AsyncClient(base_url=self._config.mcp.gateway_endpoint_url, timeout=None)

    # Servers

    async def create_server(self, *, location: GatewayLocation) -> Server:
        response = await self._client.post("/gateways", json={"location": location})
        response.raise_for_status()
        gateway = await response.json()
        return Server(id=gateway["id"], location=GatewayLocation(gateway["location"]))

    async def list_servers(self) -> list[Server]:
        response = await self._client.get("/gateways")
        response.raise_for_status()
        gateways: list[dict] = await response.json()
        return [Server(id=gateway["id"], location=GatewayLocation(gateway["location"])) for gateway in gateways]

    async def delete_server(self, *, server_id: str) -> None:
        response = await self._client.delete(f"/gateways/{server_id}")
        response.raise_for_status()
        return

    # Tools

    async def list_tools(self) -> list[Tool]:
        response = await self._client.get("/tools")
        response.raise_for_status()
        tools: list[dict] = await response.json()
        return [Tool(id=tool["id"], name=tool["name"], description=tool["description"]) for tool in tools]

    # Toolkits

    async def create_toolkit(self, *, tools: list[str]) -> Toolkit:
        response = await self._client.post("/servers", json={"associated_tools": tools})
        response.raise_for_status()
        server = await response.json()
        exp = self._config.mcp.toolkit_expiration_seconds
        # TODO schedule cleanup task
        return Toolkit(
            id=server["id"],
            name=server["name"],
            description=server["description"],
            tools=server["associated_tools"],
            url=f"/toolkits/{server['id']}/mcp?exp={exp}",  # TODO is relative URL sufficient?
        )

    async def delete_toolkit(self, *, toolkit_id: str) -> None:
        response = await self._client.delete(f"/servers/{toolkit_id}")
        response.raise_for_status()

    # MCP Forwarding

    async def get_proxy_context(self, *, user: User) -> ProxyRequestContext:
        return ProxyRequestContext(client=self._client, user=user)

    async def send_request(
        self,
        context: ProxyRequestContext,
        method: str,
        url: str,
        payload: BaseModel | None = None,
    ) -> McpServerResponse:
        exit_stack = AsyncExitStack()
        json = payload
        try:
            client = await exit_stack.enter_async_context(context.client)

            resp: httpx.Response = await exit_stack.enter_async_context(client.stream(method, url, json=json))
            is_stream = resp.headers["content-type"].startswith("text/event-stream")

            async def stream_fn():
                try:
                    async for event in resp.stream:
                        yield event
                finally:
                    await exit_stack.pop_all().aclose()

            common = dict(status_code=resp.status_code, headers=resp.headers, media_type=resp.headers["content-type"])
            if is_stream:
                return McpServerResponse(content=None, stream=stream_fn(), **common)
            else:
                try:
                    await resp.aread()
                    return McpServerResponse(stream=None, content=resp.content, **common)
                finally:
                    await exit_stack.pop_all().aclose()
        except BaseException:
            await exit_stack.pop_all().aclose()
            raise
