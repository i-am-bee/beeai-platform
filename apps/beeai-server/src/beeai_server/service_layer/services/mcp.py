# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import uuid
from collections.abc import AsyncIterable
from contextlib import AsyncExitStack
from datetime import UTC, datetime, timedelta
from typing import NamedTuple

import fastapi
import httpx
from kink import inject

from beeai_server.api.schema.mcp import McpProvider, Tool, Toolkit
from beeai_server.configuration import Configuration
from beeai_server.domain.models.mcp_provider import McpProviderDeploymentState, McpProviderLocation
from beeai_server.domain.models.user import User
from beeai_server.domain.utils import bridge_k8s_to_localhost, bridge_localhost_to_k8s
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.service_layer.services.users import UserService

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
class McpService:
    STARTUP_TIMEOUT = timedelta(minutes=5)
    DUMMY_JWT_TOKEN = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCJ9.oqr2TWWCSPGG6fhGnnNjY9-vkDk1halSpcPkng9EFOY"
    )

    def __init__(
        self,
        user_service: UserService,
        configuration: Configuration,
    ):
        self._user_service = user_service
        self._config = configuration
        self._client = httpx.AsyncClient(base_url=str(self._config.mcp.gateway_endpoint_url), timeout=None)

    # Providers

    async def create_provider(self, *, name: str, location: McpProviderLocation) -> McpProvider:
        response = await self._client.post(
            "/gateways", json={"name": name, "url": str(bridge_localhost_to_k8s(location.root))}
        )
        gateway = response.raise_for_status().json()
        return self._gateway_to_provider(gateway)

    async def list_providers(self) -> list[McpProvider]:
        response = await self._client.get("/gateways")
        gateways: list[dict] = response.raise_for_status().json()
        return [self._gateway_to_provider(gateway) for gateway in gateways]

    async def read_provider(self, *, provider_id: str) -> McpProvider:
        response = await self._client.get(f"/gateways/{provider_id}")
        gateway = response.raise_for_status().json()
        return self._gateway_to_provider(gateway)

    async def delete_provider(self, *, provider_id: str) -> None:
        response = await self._client.delete(f"/gateways/{provider_id}")
        response.raise_for_status()
        return

    # Tools

    async def list_tools(self) -> list[Tool]:
        response = await self._client.get("/tools")
        tools: list[dict] = response.raise_for_status().json()
        return [Tool(id=tool["id"], name=tool["name"], description=tool["description"]) for tool in tools]

    async def read_tool(self, *, tool_id: str) -> Tool:
        response = await self._client.get(f"/tools/{tool_id}")
        tool = response.raise_for_status().json()
        return Tool(id=tool["id"], name=tool["name"], description=tool["description"])

    # Toolkits

    async def create_toolkit(self, *, tools: list[str]) -> Toolkit:
        available_tools = await self.list_tools()
        available_tools_by_name = {tool.name: tool for tool in available_tools}

        associated_tools = []
        for tool in tools:
            if tool in available_tools_by_name:
                associated_tools.append(available_tools_by_name[tool].id)
            else:
                raise EntityNotFoundError("tool", tool)

        response = await self._client.post(
            "/servers", json={"name": str(uuid.uuid4()), "associatedTools": associated_tools}
        )
        server = response.raise_for_status().json()

        id = server["id"]
        expires_at = datetime.now(UTC) + timedelta(seconds=self._config.mcp.toolkit_expiration_seconds)

        from beeai_server.jobs.tasks.mcp import delete_toolkit  # Avoid circual import

        await delete_toolkit.configure(queueing_lock=id, schedule_at=expires_at).defer_async(toolkit_id=id)

        return Toolkit(
            url=f"http://{self._config.platform_service_url}/api/v1/mcp/toolkits/{id}/mcp",
            expires_at=expires_at,
        )

    async def delete_toolkit(self, *, toolkit_id: str) -> None:
        response = await self._client.delete(f"/servers/{toolkit_id}")
        response.raise_for_status()

    # MCP Forwarding

    async def streamable_http_proxy(self, request: fastapi.Request, *, toolkit_id: str | None) -> McpServerResponse:
        exit_stack = AsyncExitStack()
        try:
            resp: httpx.Response = await exit_stack.enter_async_context(
                self._client.stream(
                    request.method,
                    f"/servers/{toolkit_id}/mcp" if toolkit_id else "/mcp",
                    data=await request.body(),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.DUMMY_JWT_TOKEN}",
                        "Accept": "application/json, text/event-stream",
                    },
                    follow_redirects=True,
                )
            )

            is_stream = resp.headers["content-type"].startswith("text/event-stream")

            async def stream_fn():
                try:
                    async for event in resp.stream:
                        yield event
                finally:
                    await exit_stack.pop_all().aclose()

            common = {
                "status_code": resp.status_code,
                "headers": resp.headers,
                "media_type": resp.headers["content-type"],
            }
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

    def _gateway_to_provider(self, gateway: dict) -> McpProvider:
        return McpProvider(
            id=gateway["id"] or "missing-bug",  # TODO remove once fixed
            location=McpProviderLocation(bridge_k8s_to_localhost(gateway["url"])),
            state=self._gateway_to_provider_status(gateway),
        )

    def _gateway_to_provider_status(self, gateway: dict) -> McpProviderDeploymentState:
        if gateway["reachable"]:
            return McpProviderDeploymentState.running
        else:
            return McpProviderDeploymentState.missing
